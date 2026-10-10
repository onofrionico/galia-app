from decimal import Decimal

import pytest

from app.extensions import db
from app.models import ProductVariant, Sale
from app.models.pos import PosSaleEvent
from app.services.pos import discount_service, payment_service, sale_service
from app.services.pos.errors import PosError
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401


def _confirmed(user, cat, table, quantity=3):
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=2)
    sale_service.add_item(user, sale.id, cat.unidad.id, quantity=quantity)
    return sale_service.confirm_batch(user, sale.id)


def test_cancel_confirmed_item_restores_stock_and_discounts(pos_app):
    boss = make_user('jefe@test.com', modules=('POS', 'Descuentos'))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _confirmed(boss, cat, t1)
    item_id = sale.items[0].id
    discount_service.add_discount(boss, sale.id, item_id=item_id, kind='amount', value=100, reason='x')
    sale = sale_service.cancel_item(boss, sale.id, item_id, 'El cliente cambió')
    item = sale.items[0]
    assert item.status == 'cancelled' and item.cancel_reason == 'El cliente cambió'
    assert sale.discounts[0].cancelled_at is not None and sale.total == Decimal('0')
    assert Decimal(db.session.get(ProductVariant, cat.unidad.id).stock_quantity) == Decimal('5')
    assert PosSaleEvent.query.filter_by(event_type='item_cancelled').one().payload['reason'] == 'El cliente cambió'


def test_cancel_item_requires_reason_and_confirmed_status(pos_app):
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = sale_service.open_sale(boss, 'salon', table_id=t1.id, people=1)
    sale = sale_service.add_item(boss, sale.id, cat.unidad.id)
    with pytest.raises(PosError, match='motivo'):
        sale_service.cancel_item(boss, sale.id, sale.items[0].id, '  ')
    with pytest.raises(PosError, match='pendiente'):
        sale_service.cancel_item(boss, sale.id, sale.items[0].id, 'x')


def test_cancel_item_below_paid_is_409(pos_app):
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _confirmed(boss, cat, t1, quantity=2)
    sale_service.request_bill(boss, sale.id)
    payment_service.add_payment(boss, sale.id, cat.debito.id, 1000)
    with pytest.raises(PosError) as exc:
        sale_service.cancel_item(boss, sale.id, sale.items[0].id, 'x')
    assert exc.value.status == 409


def test_cancel_payment_reopens_closed_sale_and_removes_projection(pos_app):
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _confirmed(boss, cat, t1, quantity=1)
    sale_service.request_bill(boss, sale.id)
    sale = payment_service.add_payment(boss, sale.id, cat.debito.id, 900)
    projected_id = sale.sale_id
    sale = payment_service.cancel_payment(boss, sale.payments[0].id, 'Se cobró mal')
    assert sale.status == 'billing' and sale.sale_id is None and sale.paid_total == Decimal('0')
    assert db.session.get(Sale, projected_id) is None


def test_cancel_sale_restores_stock_and_requires_no_payments(pos_app):
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _confirmed(boss, cat, t1, quantity=2)
    sale_service.request_bill(boss, sale.id)
    payment_service.add_payment(boss, sale.id, cat.debito.id, 100)
    with pytest.raises(PosError, match='pagos'):
        sale_service.cancel_sale(boss, sale.id, 'x')
    payment_service.cancel_payment(boss, sale.payments[0].id, 'x')
    sale = sale_service.cancel_sale(boss, sale.id, 'Se fueron')
    assert sale.status == 'cancelled' and sale.cancel_reason == 'Se fueron'
    assert {i.status for i in sale.items} == {'cancelled'}
    assert Decimal(db.session.get(ProductVariant, cat.unidad.id).stock_quantity) == Decimal('5')
