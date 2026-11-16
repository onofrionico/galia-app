from datetime import timedelta
from decimal import Decimal

import pytest

from app.extensions import db
from app.models.pos import PosDiscount, PosSaleEvent
from app.services.pos import discount_service, payment_service, sale_service
from app.services.pos.errors import PosError
from app.services.pos.serializers import sale_to_dict
from app.services.vouchers import batches, redeem
from app.services.vouchers.codes import format_code
from app.utils.timezone_utils import get_current_date_argentina
from voucher_helpers import make_batch, make_catalog, make_user, open_sale, pos_app  # noqa: F401


def _setup():
    cashier = make_user('caja@test.com', modules=('POS', 'Anular', 'Cobrar'))
    return cashier, make_catalog()


def _code(voucher):
    return format_code(voucher.code)


def _status(voucher):
    row = batches.active_discount_rows(voucher_ids=[voucher.id]).get(voucher.id)
    return batches.voucher_status(voucher, row, get_current_date_argentina())


def _pay(cashier, cat, sale):
    sale_service.request_bill(cashier, sale.id)
    return payment_service.add_payment(cashier, sale.id, cat.efectivo.id, sale.balance)


def test_redeem_applies_amount_discount(pos_app):
    cashier, cat = _setup()
    sale = open_sale(cashier, cat)
    voucher = make_batch(amount='1000').vouchers[0]
    sale = redeem.redeem_voucher(cashier, sale.id, _code(voucher))
    assert sale.discount_total == Decimal('1000') and sale.total == Decimal('1700')
    discount = sale.discounts[0]
    assert (discount.kind, discount.voucher_id, discount.reason) == ('amount', voucher.id, 'Voucher Sorteo Instagram')
    assert PosSaleEvent.query.filter_by(sale_id=sale.id, event_type='voucher_redeemed').count() == 1
    assert sale_to_dict(sale)['discounts'][0]['voucher_code'] == _code(voucher)
    assert _status(voucher) == 'in_use'


def test_redeem_code_typed_loosely(pos_app):
    cashier, cat = _setup()
    sale = open_sale(cashier, cat)
    voucher = make_batch().vouchers[0]
    redeem.redeem_voucher(cashier, sale.id, f' {_code(voucher).lower()} ')
    assert _status(voucher) == 'in_use'


@pytest.mark.parametrize('code', ['', 'GAL-ZZZZZ-ZZZZZ', 'nada'])
def test_unknown_code_rejected(pos_app, code):
    cashier, cat = _setup()
    sale = open_sale(cashier, cat)
    with pytest.raises(PosError) as error:
        redeem.redeem_voucher(cashier, sale.id, code)
    assert error.value.status == 404 and error.value.message == 'Código de voucher inválido'


def test_voided_rejected(pos_app):
    cashier, cat = _setup()
    sale = open_sale(cashier, cat)
    voucher = make_batch().vouchers[0]
    batches.void_voucher(cashier, voucher.id, 'Roto')
    with pytest.raises(PosError, match='anulado'):
        redeem.redeem_voucher(cashier, sale.id, _code(voucher))


def test_expired_rejected_but_today_is_valid(pos_app):
    cashier, cat = _setup()
    sale = open_sale(cashier, cat)
    today = get_current_date_argentina()
    expired = make_batch(expires_at=today - timedelta(days=1), name='Viejo').vouchers[0]
    with pytest.raises(PosError, match='venció el'):
        redeem.redeem_voucher(cashier, sale.id, _code(expired))
    last_day = make_batch(expires_at=today, name='Hoy').vouchers[0]
    redeem.redeem_voucher(cashier, sale.id, _code(last_day))
    assert _status(last_day) == 'in_use'


def test_min_sale_amount(pos_app):
    cashier, cat = _setup()
    sale = open_sale(cashier, cat)  # 2.700
    voucher = make_batch(min_sale_amount='5000').vouchers[0]
    with pytest.raises(PosError, match=r'llegar a \$5\.000'):
        redeem.redeem_voucher(cashier, sale.id, _code(voucher))
    ok = make_batch(min_sale_amount='2700', name='Justo').vouchers[0]
    redeem.redeem_voucher(cashier, sale.id, _code(ok))


def test_voucher_larger_than_sale_is_capped(pos_app):
    cashier, cat = _setup()
    sale = open_sale(cashier, cat)
    voucher = make_batch(amount='10000').vouchers[0]
    sale = redeem.redeem_voucher(cashier, sale.id, _code(voucher))
    assert sale.total == Decimal('0') and sale.discounts[0].amount == Decimal('2700')


def test_already_applied_other_sale_rejected(pos_app):
    cashier, cat = _setup()
    first, second = open_sale(cashier, cat), open_sale(cashier, cat)
    voucher = make_batch().vouchers[0]
    redeem.redeem_voucher(cashier, first.id, _code(voucher))
    with pytest.raises(PosError, match=f'ya está aplicado a la venta #{first.number}') as error:
        redeem.redeem_voucher(cashier, second.id, _code(voucher))
    assert error.value.status == 409


def test_already_redeemed_after_close_rejected(pos_app):
    cashier, cat = _setup()
    first, second = open_sale(cashier, cat), open_sale(cashier, cat)
    voucher = make_batch(amount='1000').vouchers[0]
    redeem.redeem_voucher(cashier, first.id, _code(voucher))
    assert _pay(cashier, cat, first).status == 'closed'
    assert _status(voucher) == 'redeemed'
    with pytest.raises(PosError, match='ya fue canjeado el .* en la venta #'):
        redeem.redeem_voucher(cashier, second.id, _code(voucher))


def test_same_sale_twice_rejected(pos_app):
    cashier, cat = _setup()
    sale = open_sale(cashier, cat)
    voucher = make_batch().vouchers[0]
    redeem.redeem_voucher(cashier, sale.id, _code(voucher))
    with pytest.raises(PosError, match='ya está aplicado a esta venta'):
        redeem.redeem_voucher(cashier, sale.id, _code(voucher))


def test_two_vouchers_in_one_sale_ok(pos_app):
    cashier, cat = _setup()
    sale = open_sale(cashier, cat)
    one, two = make_batch(quantity=2).vouchers
    redeem.redeem_voucher(cashier, sale.id, _code(one))
    sale = redeem.redeem_voucher(cashier, sale.id, _code(two))
    assert sale.discount_total == Decimal('2000') and sale.total == Decimal('700')


def test_practice_sale_rejected(pos_app):
    cashier, cat = _setup()
    sale = open_sale(cashier, cat)
    sale.is_practice = True
    db.session.commit()
    voucher = make_batch().vouchers[0]
    with pytest.raises(PosError, match='práctica'):
        redeem.redeem_voucher(cashier, sale.id, _code(voucher))
    assert _status(voucher) == 'available'


def test_cancel_sale_frees_voucher(pos_app):
    cashier, cat = _setup()
    first, second = open_sale(cashier, cat), open_sale(cashier, cat)
    voucher = make_batch().vouchers[0]
    redeem.redeem_voucher(cashier, first.id, _code(voucher))
    sale_service.cancel_sale(cashier, first.id, 'Se fue el cliente')
    assert _status(voucher) == 'available'
    redeem.redeem_voucher(cashier, second.id, _code(voucher))
    assert _status(voucher) == 'in_use'


def test_cancel_discount_frees_voucher_and_requires_reason(pos_app):
    cashier, cat = _setup()
    sale = open_sale(cashier, cat)
    voucher = make_batch().vouchers[0]
    sale = redeem.redeem_voucher(cashier, sale.id, _code(voucher))
    discount = sale.discounts[0]
    with pytest.raises(PosError, match='motivo'):
        discount_service.cancel_discount(cashier, discount.id)
    sale = discount_service.cancel_discount(cashier, discount.id, reason='Lo pidió el cliente')
    assert sale.total == Decimal('2700') and _status(voucher) == 'available'
    event = PosSaleEvent.query.filter_by(sale_id=sale.id, event_type='discount_cancelled').one()
    assert event.payload['reason'] == 'Lo pidió el cliente'


def test_cashier_without_descuentos_module_can_redeem_and_remove(pos_app):
    cashier = make_user('cobra@test.com', modules=('Cobrar',))
    owner = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    sale = open_sale(owner, cat)
    voucher = make_batch().vouchers[0]
    sale = redeem.redeem_voucher(cashier, sale.id, _code(voucher))
    discount_service.cancel_discount(cashier, sale.discounts[0].id, reason='Error')
    assert _status(voucher) == 'available'


def test_user_without_pos_or_cobrar_cannot_remove_voucher_discount(pos_app):
    cashier, cat = _setup()
    waiter = make_user('mozo@test.com', modules=('Camarero', 'Descuentos'))
    sale = open_sale(cashier, cat)
    voucher = make_batch().vouchers[0]
    sale = redeem.redeem_voucher(cashier, sale.id, _code(voucher))
    with pytest.raises(PosError) as error:
        discount_service.cancel_discount(waiter, sale.discounts[0].id, reason='Quiero')
    assert error.value.status == 403 and _status(voucher) == 'in_use'


def test_cancel_payment_reopens_sale_and_voucher_can_be_released(pos_app):
    cashier, cat = _setup()
    sale = open_sale(cashier, cat)
    voucher = make_batch().vouchers[0]
    redeem.redeem_voucher(cashier, sale.id, _code(voucher))
    sale = _pay(cashier, cat, sale)
    assert _status(voucher) == 'redeemed'
    sale = payment_service.cancel_payment(cashier, sale.payments[0].id, 'Cobro mal cargado')
    assert sale.status == 'billing' and _status(voucher) == 'in_use'
    discount_service.cancel_discount(cashier, sale.discounts[0].id, reason='Corrección')
    assert _status(voucher) == 'available'


def test_integrity_error_becomes_in_use_message(pos_app, monkeypatch):
    cashier, cat = _setup()
    first, second = open_sale(cashier, cat), open_sale(cashier, cat)
    voucher = make_batch().vouchers[0]
    redeem.redeem_voucher(cashier, first.id, _code(voucher))
    monkeypatch.setattr(redeem, '_active_row', lambda _voucher: None)  # la otra caja ganó la carrera
    with pytest.raises(PosError, match='ya está en uso') as error:
        redeem.redeem_voucher(cashier, second.id, _code(voucher))
    assert error.value.status == 409
    assert PosDiscount.query.filter_by(voucher_id=voucher.id, cancelled_at=None).count() == 1
