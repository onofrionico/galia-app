from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import MpMovement, MpReconciliation
from app.services import mercadopago
from app.services.mercadopago import point_service
from app.services.mercadopago import reconciliation_service as rs
from app.services.mercadopago.fake import FakeMercadoPago
from app.services.pos import payment_service
from app.services.pos.errors import PosError
from mp_helpers import billing_sale, configure_mp
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401

TODAY = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-3))).date()


def _mp_payment(pid, amount, minutes_ago=1, status='approved', ptype='account_money', poi='INSTORE', ref=None):
    moment = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    return {'id': pid, 'date_created': moment.isoformat(timespec='milliseconds'), 'transaction_amount': amount,
            'status': status, 'status_detail': 'accredited', 'payment_type_id': ptype, 'payment_method_id': 'qr',
            'currency_id': 'ARS', 'external_reference': ref, 'point_of_interaction': {'type': poi}}


@pytest.fixture
def ctx(pos_app, monkeypatch):
    FakeMercadoPago.reset()
    monkeypatch.setattr(mercadopago, 'get_client', lambda settings: FakeMercadoPago())
    user = make_user('admin@test.com', role='admin')
    cat = make_catalog()
    _salon, t1, t2 = make_floor()
    configure_mp()
    cat.debito.is_mercadopago = True
    db.session.commit()
    return user, cat, t1, t2


def test_point_payment_matches_automatically(ctx):
    user, cat, t1, _t2 = ctx
    sale = billing_sale(user, cat, t1)
    order = point_service.start(user, sale.id, Decimal('1800'))
    FakeMercadoPago().simulate(order.mp_order_id, 'approved')
    point_service.apply(order.id)
    rs.fetch(user, TODAY)
    data = rs.day(TODAY)
    assert len(data['matched']) == 1 and data['only_mp'] == [] and data['only_galia'] == []
    assert data['status'] == 'conciliado'


def test_point_payment_matches_by_external_reference(ctx):
    user, cat, t1, _t2 = ctx
    sale = billing_sale(user, cat, t1)
    order = point_service.start(user, sale.id, Decimal('1800'))
    FakeMercadoPago().simulate(order.mp_order_id, 'approved')
    point_service.apply(order.id)
    FakeMercadoPago.payments[0]['id'] = 99999  # el id del movimiento no coincide con el de la orden
    rs.fetch(user, TODAY)
    data = rs.day(TODAY)
    assert len(data['matched']) == 1 and data['status'] == 'conciliado'


def test_only_lists_and_suggestions(ctx):
    user, cat, t1, _t2 = ctx
    sale = billing_sale(user, cat, t1)
    payment_service.add_payment(user, sale.id, cat.debito.id, 1800)  # cargado a mano, sin id de MP
    FakeMercadoPago().add_payment_movement(_mp_payment(555, 1800))
    FakeMercadoPago().add_payment_movement(_mp_payment(556, 5000, ptype='bank_transfer', poi=''))
    FakeMercadoPago().add_payment_movement(_mp_payment(557, 300, status='rejected'))
    rs.fetch(user, TODAY)
    data = rs.day(TODAY)
    only_mp = {row['mp_payment_id']: row for row in data['only_mp']}
    assert set(only_mp) == {'555', '556'} and [r['mp_payment_id'] for r in data['rejected']] == ['557']
    assert [s['payment_id'] for s in only_mp['555']['suggestions']] == [sale.payments[0].id]
    assert only_mp['556']['suggestions'] == [] and only_mp['556']['channel'] == 'transfer'
    assert len(data['only_galia']) == 1 and data['status'] == 'con_diferencias' and data['pending'] == 3
    assert data['totals']['only_mp'] == '6800.00'


def test_resolutions_and_undo(ctx):
    user, cat, t1, t2 = ctx
    sale = billing_sale(user, cat, t1)
    payment_service.add_payment(user, sale.id, cat.debito.id, 1800)
    other = billing_sale(user, cat, t2)
    FakeMercadoPago().add_payment_movement(_mp_payment(555, 1800))
    FakeMercadoPago().add_payment_movement(_mp_payment(556, 5000, ptype='bank_transfer', poi=''))
    FakeMercadoPago().add_payment_movement(_mp_payment(558, 900))
    rs.fetch(user, TODAY)
    movements = {m.mp_payment_id: m for m in MpMovement.query}
    matched = rs.resolve(user, 'matched_manual', movement_id=movements['555'].id, payment_id=sale.payments[0].id)
    assert sale.payments[0].mp_payment_id == '555' and matched['kind'] == 'matched_manual'
    with pytest.raises(PosError):
        rs.resolve(user, 'not_a_sale', movement_id=movements['556'].id)  # nota obligatoria
    db.session.rollback()
    rs.resolve(user, 'not_a_sale', movement_id=movements['556'].id, note='Transferencia de un proveedor')
    created = rs.resolve(user, 'payment_created', movement_id=movements['558'].id, sale_id=other.id,
                         payment_method_id=cat.debito.id)
    db.session.refresh(other)
    assert created['kind'] == 'payment_created' and other.paid_total == Decimal('900')
    assert rs.day(TODAY)['status'] == 'conciliado'
    rs.undo(user, created['id'])
    db.session.refresh(other)
    assert other.payments[0].mp_payment_id is None and other.payments[0].cancelled_at is None
    assert rs.day(TODAY)['pending'] == 2  # el movimiento vuelve a "solo en MP" y el pago queda "solo en Galia"
    with pytest.raises(PosError):
        rs.resolve(user, 'reviewed', payment_id=sale.payments[0].id, note='ok')  # ya cruzado
    db.session.rollback()


def test_fetch_twice_is_idempotent(ctx):
    user, *_ = ctx
    FakeMercadoPago().add_payment_movement(_mp_payment(555, 1800))
    rs.fetch(user, TODAY)
    movement = MpMovement.query.one()
    rs.resolve(user, 'not_a_sale', movement_id=movement.id, note='prueba')
    FakeMercadoPago.payments[0]['status'] = 'refunded'
    FakeMercadoPago.payments[0]['transaction_amount_refunded'] = 1800
    rs.fetch(user, TODAY)
    assert MpMovement.query.count() == 1 and MpReconciliation.query.count() == 1
    assert MpMovement.query.one().refunded_amount == Decimal('1800.00')


def test_summary_and_permissions(ctx):
    user, *_ = ctx
    assert rs.summary(TODAY, TODAY) == [{'day': TODAY.isoformat(), 'status': 'sin_traer', 'pending': 0}]
    rs.fetch(user, TODAY)  # un día sin movimientos queda traído
    assert rs.summary(TODAY, TODAY)[0]['status'] == 'conciliado'
    FakeMercadoPago().add_payment_movement(_mp_payment(555, 1800))
    rs.fetch(user, TODAY)
    assert rs.summary(TODAY, TODAY)[0]['status'] == 'con_diferencias'
    cashier = make_user('caja@test.com', modules=('POS',))
    with pytest.raises(PosError) as error:
        rs.fetch(cashier, TODAY)
    assert error.value.status == 403


def test_day_bounds_are_argentina():
    begin, end = rs.day_bounds(date(2026, 10, 15))
    assert begin == datetime(2026, 10, 15, 3, 0) and end == datetime(2026, 10, 16, 2, 59, 59)
