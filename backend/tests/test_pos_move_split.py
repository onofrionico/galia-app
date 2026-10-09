from decimal import Decimal

import pytest

from app.models.pos import PosSale
from app.services.pos import discount_service, payment_service, sale_service
from app.services.pos.errors import PosError
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401


def _sale(user, cat, table):
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=3)
    sale_service.add_item(user, sale.id, cat.unidad.id, quantity=3)  # 2700
    sale_service.add_item(user, sale.id, cat.taza.id, modifier_option_ids=[cat.entera.id])  # 2000
    return sale_service.confirm_batch(user, sale.id)


def test_move_to_free_table(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cat = make_catalog()
    _s, t1, t2 = make_floor()
    sale = _sale(waiter, cat, t1)
    sale = sale_service.move_sale(waiter, sale.id, t2.id)
    assert sale.table_id == t2.id


def test_move_to_busy_table_is_409(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cat = make_catalog()
    _s, t1, t2 = make_floor()
    sale = _sale(waiter, cat, t1)
    sale_service.open_sale(waiter, 'salon', table_id=t2.id, people=1)
    with pytest.raises(PosError) as exc:
        sale_service.move_sale(waiter, sale.id, t2.id)
    assert exc.value.status == 409


def test_split_part_of_a_line_with_amount_discount(pos_app):
    boss = make_user('jefe@test.com', modules=('POS', 'Descuentos'))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _sale(boss, cat, t1)
    medialunas = sale.items[0]
    discount_service.add_discount(boss, sale.id, item_id=medialunas.id, kind='amount', value=300, reason='x')
    new = sale_service.split_sale(boss, sale.id, [{'item_id': medialunas.id, 'quantity': 1}])
    origin = PosSale.query.get(sale.id)
    assert new.status == 'billing' and new.split_from_id == origin.id and new.table_id == t1.id
    assert new.items[0].quantity == Decimal('1') and new.items[0].line_total == Decimal('900')
    assert origin.items[0].quantity == Decimal('2') and origin.items[0].line_total == Decimal('1800')
    assert new.discount_total == Decimal('100') and new.total == Decimal('800')
    assert origin.discount_total == Decimal('200') and origin.total == Decimal('3600')


def test_split_whole_items_moves_them(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _sale(waiter, cat, t1)
    cortado_id = sale.items[1].id
    new = sale_service.split_sale(waiter, sale.id, [{'item_id': cortado_id, 'quantity': 1}])
    assert [i.id for i in new.items] == [cortado_id] and new.total == Decimal('2000')
    assert PosSale.query.get(sale.id).total == Decimal('2700')


def test_split_everything_cancels_origin(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _sale(waiter, cat, t1)
    lines = [{'item_id': i.id, 'quantity': float(i.quantity)} for i in sale.items]
    sale_service.split_sale(waiter, sale.id, lines)
    origin = PosSale.query.get(sale.id)
    assert origin.status == 'cancelled' and origin.cancel_reason == 'Dividida'


def test_split_with_payments_is_409(pos_app):
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _sale(boss, cat, t1)
    sale_service.request_bill(boss, sale.id)
    payment_service.add_payment(boss, sale.id, cat.debito.id, 100)
    with pytest.raises(PosError) as exc:
        sale_service.split_sale(boss, sale.id, [{'item_id': sale.items[0].id, 'quantity': 1}])
    assert exc.value.status == 409


def test_split_more_than_available_is_400(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _sale(waiter, cat, t1)
    with pytest.raises(PosError) as exc:
        sale_service.split_sale(waiter, sale.id, [{'item_id': sale.items[0].id, 'quantity': 4}])
    assert exc.value.status == 400
