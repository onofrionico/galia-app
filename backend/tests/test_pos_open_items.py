from decimal import Decimal

import pytest

from app.extensions import db
from app.models.pos import PosSaleEvent
from app.services.pos import sale_service
from app.services.pos.errors import PosError
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401


def test_open_salon_sale_numbers_daily(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    _salon, t1, t2 = make_floor()
    first = sale_service.open_sale(waiter, 'salon', table_id=t1.id, people=2)
    second = sale_service.open_sale(waiter, 'salon', table_id=t2.id, people=1)
    assert (first.number, second.number) == (1, 2)
    assert first.status == 'open' and first.waiter_id == waiter.id
    assert PosSaleEvent.query.filter_by(sale_id=first.id, event_type='opened').count() == 1


def test_open_on_busy_table_is_409_with_existing_sale(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    _salon, t1, _t2 = make_floor()
    sale = sale_service.open_sale(waiter, 'salon', table_id=t1.id, people=2)
    with pytest.raises(PosError) as exc:
        sale_service.open_sale(waiter, 'salon', table_id=t1.id, people=2)
    assert exc.value.status == 409 and exc.value.extra == {'sale_id': sale.id}


def test_salon_sale_requires_people(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    _salon, t1, _t2 = make_floor()
    with pytest.raises(PosError) as exc:
        sale_service.open_sale(waiter, 'salon', table_id=t1.id, people=0)
    assert exc.value.status == 400


def test_counter_sale_needs_pos_module(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cashier = make_user('caja@test.com', modules=('POS',))
    with pytest.raises(PosError) as exc:
        sale_service.open_sale(waiter, 'counter')
    assert exc.value.status == 403
    sale = sale_service.open_sale(cashier, 'counter', customer_name='Ana')
    assert sale.table_id is None and sale.customer_name == 'Ana'


def test_add_item_with_modifiers_and_note(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    sale = sale_service.open_sale(cashier, 'counter')
    sale = sale_service.add_item(cashier, sale.id, cat.taza.id, quantity=2,
                                 modifier_option_ids=[cat.almendras.id, cat.canela.id], note='bien caliente')
    item = sale.items[0]
    assert item.status == 'pending' and item.product_name == 'Cortado' and item.variant_name == 'Taza'
    assert item.modifiers_total == Decimal('400') and item.line_total == Decimal('4800')
    assert [m.option_name for m in item.modifiers] == ['Almendras', 'Canela']
    assert sale.subtotal == Decimal('4800') and sale.total == Decimal('4800')


@pytest.mark.parametrize('options, message', [
    ([], 'Elegí al menos 1 en "Tipo de leche"'),
    (['entera', 'almendras'], 'Podés elegir hasta 1 en "Tipo de leche"'),
])
def test_modifier_rules(pos_app, options, message):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    sale = sale_service.open_sale(cashier, 'counter')
    with pytest.raises(PosError) as exc:
        sale_service.add_item(cashier, sale.id, cat.taza.id, modifier_option_ids=[getattr(cat, o).id for o in options])
    assert exc.value.status == 400 and exc.value.message == message


def test_modifier_from_other_product_is_rejected(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    sale = sale_service.open_sale(cashier, 'counter')
    with pytest.raises(PosError) as exc:
        sale_service.add_item(cashier, sale.id, cat.unidad.id, modifier_option_ids=[cat.canela.id])
    assert 'no corresponde' in exc.value.message


def test_delete_pending_item_is_audited(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    sale = sale_service.open_sale(cashier, 'counter')
    sale = sale_service.add_item(cashier, sale.id, cat.unidad.id, quantity=3)
    item_id = sale.items[0].id
    sale = sale_service.delete_item(cashier, sale.id, item_id)
    assert sale.items == [] and sale.total == Decimal('0')
    event = PosSaleEvent.query.filter_by(event_type='item_deleted').one()
    assert event.item_id == item_id and event.payload['product'] == 'Medialuna' and event.payload['quantity'] == '3.000'


def test_inactive_variant_is_rejected(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    cat.unidad.is_active = False
    db.session.commit()
    sale = sale_service.open_sale(cashier, 'counter')
    with pytest.raises(PosError) as exc:
        sale_service.add_item(cashier, sale.id, cat.unidad.id)
    assert exc.value.status == 400
