from decimal import Decimal

import pytest

from app.services.pos import discount_service, sale_service
from app.services.pos.errors import PosError
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401


def _confirmed_sale(user, cat, table):
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=2)
    sale_service.add_item(user, sale.id, cat.taza.id, modifier_option_ids=[cat.entera.id])  # 2000
    sale_service.add_item(user, sale.id, cat.unidad.id, quantity=2)  # 1800
    return sale_service.confirm_batch(user, sale.id)


def test_unrestricted_item_template_for_waiter(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _confirmed_sale(waiter, cat, t1)
    sale = discount_service.add_discount(waiter, sale.id, item_id=sale.items[0].id, template_id=cat.cortesia.id)
    assert sale.discount_total == Decimal('2000') and sale.total == Decimal('1800')
    assert sale.discounts[0].reason == 'Cortesía'


def test_restricted_template_needs_permission(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    boss = make_user('jefe@test.com', modules=('Camarero', 'Descuentos'))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _confirmed_sale(waiter, cat, t1)
    with pytest.raises(PosError) as exc:
        discount_service.add_discount(waiter, sale.id, template_id=cat.empleado.id)
    assert exc.value.status == 403
    sale = discount_service.add_discount(boss, sale.id, template_id=cat.empleado.id)
    assert sale.discount_total == Decimal('760') and sale.total == Decimal('3040')


def test_free_discount_needs_permission_and_reason(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    boss = make_user('jefe@test.com', modules=('Camarero', 'Descuentos'))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _confirmed_sale(waiter, cat, t1)
    with pytest.raises(PosError) as exc:
        discount_service.add_discount(waiter, sale.id, kind='amount', value=100, reason='x')
    assert exc.value.status == 403
    with pytest.raises(PosError, match='motivo'):
        discount_service.add_discount(boss, sale.id, kind='amount', value=100)
    sale = discount_service.add_discount(boss, sale.id, kind='amount', value=5000, reason='Reclamo')
    assert sale.total == Decimal('0') and sale.discounts[0].amount == Decimal('3800')


def test_template_scope_must_match(pos_app):
    boss = make_user('jefe@test.com', modules=('Camarero', 'Descuentos'))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _confirmed_sale(boss, cat, t1)
    with pytest.raises(PosError) as exc:
        discount_service.add_discount(boss, sale.id, template_id=cat.cortesia.id)
    assert exc.value.status == 400


def test_item_discount_only_on_confirmed_items(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = sale_service.open_sale(waiter, 'salon', table_id=t1.id, people=1)
    sale = sale_service.add_item(waiter, sale.id, cat.unidad.id)
    with pytest.raises(PosError) as exc:
        discount_service.add_discount(waiter, sale.id, item_id=sale.items[0].id, template_id=cat.cortesia.id)
    assert exc.value.status == 400


def test_cancel_discount_recalculates(pos_app):
    boss = make_user('jefe@test.com', modules=('Camarero', 'Descuentos'))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _confirmed_sale(boss, cat, t1)
    sale = discount_service.add_discount(boss, sale.id, template_id=cat.empleado.id)
    sale = discount_service.cancel_discount(boss, sale.discounts[0].id)
    assert sale.discount_total == Decimal('0') and sale.total == Decimal('3800')
    assert sale.discounts[0].cancelled_at is not None
