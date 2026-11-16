from datetime import date, datetime, timedelta

import pytest

from app.extensions import db
from app.models.pos import PosDiscount
from app.models.vouchers import VoucherChangeLog
from app.services.pos.errors import PosError
from app.services.vouchers import batches
from app.services.vouchers.codes import format_code
from app.utils.timezone_utils import get_current_date_argentina
from voucher_helpers import make_batch, make_catalog, make_user, open_sale, pos_app  # noqa: F401


def _tomorrow():
    return (get_current_date_argentina() + timedelta(days=1)).isoformat()


def _data(**overrides):
    data = {'name': 'Sorteo Instagram', 'amount': '5000', 'quantity': 5, 'expires_at': _tomorrow(),
            'terms': 'Consumo en el local'}
    data.update(overrides)
    return data


def _apply(sale, user, voucher, closed=False):
    db.session.add(PosDiscount(sale_id=sale.id, voucher_id=voucher.id, kind='amount', value=1000, amount=1000,
                               created_by=user.id, created_at=datetime.utcnow()))
    if closed:
        sale.status = 'closed'
    db.session.commit()


def test_create_batch_generates_unique_codes(pos_app):
    admin = make_user('admin@test.com', role='admin')
    batch = batches.create_batch(admin, _data(quantity=20))
    assert batch.quantity == 20
    codes = [v.code for v in batch.vouchers]
    assert len(codes) == len(set(codes)) == 20


@pytest.mark.parametrize('overrides', [
    {'amount': '0'}, {'quantity': 0}, {'quantity': 501}, {'name': ''},
    {'expires_at': (date.today() - timedelta(days=2)).isoformat()}, {'expires_at': 'mañana'},
    {'min_sale_amount': '-1'},
])
def test_create_batch_validates(pos_app, overrides):
    admin = make_user('admin@test.com', role='admin')
    with pytest.raises(PosError) as error:
        batches.create_batch(admin, _data(**overrides))
    assert error.value.status == 400


def test_status_precedence(pos_app):
    admin = make_user('admin@test.com', role='admin')
    today = get_current_date_argentina()
    batch = make_batch(quantity=1, expires_at=today - timedelta(days=1), created_by=admin.id)
    voucher = batch.vouchers[0]
    assert batches.voucher_status(voucher, None, today) == 'expired'
    voucher.voided_at = datetime.utcnow()
    assert batches.voucher_status(voucher, None, today) == 'voided'


def test_used_voucher_is_not_expired_and_shows_sale_state(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    sale = open_sale(cashier, make_catalog())
    today = get_current_date_argentina()
    voucher = make_batch(quantity=1, expires_at=today - timedelta(days=1)).vouchers[0]
    _apply(sale, cashier, voucher)
    row = (PosDiscount.query.filter_by(voucher_id=voucher.id).one(), sale)
    assert batches.voucher_status(voucher, row, today) == 'in_use'
    sale.status = 'closed'
    assert batches.voucher_status(voucher, row, today) == 'redeemed'


def test_extend_expiry_logs_change(pos_app):
    admin = make_user('admin@test.com', role='admin')
    batch = make_batch(quantity=1, created_by=admin.id)
    old = batch.expires_at
    new = (old + timedelta(days=10)).isoformat()
    batches.extend_expiry(admin, batch.id, new)
    assert batch.expires_at.isoformat() == new
    log = VoucherChangeLog.query.one()
    assert (log.field, log.old_value, log.new_value, log.user_id) == ('expires_at', old.isoformat(), new, admin.id)
    with pytest.raises(PosError):
        batches.extend_expiry(admin, batch.id, old.isoformat())


def test_void_requires_reason(pos_app):
    admin = make_user('admin@test.com', role='admin')
    voucher = make_batch(quantity=1, created_by=admin.id).vouchers[0]
    with pytest.raises(PosError):
        batches.void_voucher(admin, voucher.id, '  ')
    batches.void_voucher(admin, voucher.id, 'Impreso con error')
    assert voucher.voided_by == admin.id and voucher.void_reason == 'Impreso con error' and voucher.voided_at


def test_cannot_void_redeemed_voucher(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    sale = open_sale(cashier, make_catalog())
    voucher = make_batch(quantity=1).vouchers[0]
    _apply(sale, cashier, voucher)
    with pytest.raises(PosError):
        batches.void_voucher(cashier, voucher.id, 'Prueba')


def test_batch_summary_counts(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    batch = make_batch(quantity=4, name='Concurso')
    redeemed, in_use, voided, free = batch.vouchers
    _apply(open_sale(cashier, cat), cashier, redeemed, closed=True)
    _apply(open_sale(cashier, cat), cashier, in_use)
    batches.void_voucher(cashier, voided.id, 'Roto')
    detail = batches.batch_detail(batch.id)
    assert {k: detail[k] for k in ('issued', 'available', 'in_use', 'redeemed', 'expired', 'voided')} == {
        'issued': 4, 'available': 1, 'in_use': 1, 'redeemed': 1, 'expired': 0, 'voided': 1}
    assert detail['discount_total'] == 1000
    statuses = {v['id']: v['status'] for v in detail['vouchers']}
    assert statuses[redeemed.id] == 'redeemed' and statuses[free.id] == 'available'
    assert detail['vouchers'][0]['code'] == format_code(redeemed.code)
    listing = batches.list_batches()
    assert listing[0]['redeemed'] == 1 and 'vouchers' not in listing[0]
