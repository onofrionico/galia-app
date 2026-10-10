from decimal import Decimal

import pytest

from app.extensions import db
from app.models import Sale
from app.models.pos import PosSale, PosSaleEvent, PosTable
from app.services.pos import discount_service, payment_service, sale_service
from app.services.pos.errors import PosError
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401


def _billing_sale(user, cat, table):
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=3)
    sale_service.add_item(user, sale.id, cat.unidad.id, quantity=4)  # 3600
    sale_service.confirm_batch(user, sale.id)
    return sale_service.request_bill(user, sale.id)


def _split_sale(user, cat, table):
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=3)
    sale_service.add_item(user, sale.id, cat.unidad.id, quantity=3)  # 2700
    sale_service.add_item(user, sale.id, cat.taza.id, modifier_option_ids=[cat.entera.id])  # 2000
    return sale_service.confirm_batch(user, sale.id)


def test_idempotent_payment_that_closed_the_sale(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _billing_sale(cashier, cat, t1)
    sale = payment_service.add_payment(cashier, sale.id, cat.efectivo.id, 3600, client_request_id='full-1')
    assert sale.status == 'closed'
    sale = payment_service.add_payment(cashier, sale.id, cat.efectivo.id, 3600, client_request_id='full-1')
    assert sale.status == 'closed' and len(sale.payments) == 1


def test_request_id_on_another_sale_is_409(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, t2 = make_floor()
    first = _billing_sale(cashier, cat, t1)
    second = _billing_sale(cashier, cat, t2)
    payment_service.add_payment(cashier, first.id, cat.debito.id, 100, client_request_id='dup-1')
    with pytest.raises(PosError) as exc:
        payment_service.add_payment(cashier, second.id, cat.debito.id, 100, client_request_id='dup-1')
    assert exc.value.status == 409


def test_projection_truncates_to_column_lengths(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    table = db.session.get(PosTable, t1.id)
    table.name = 'Mesa de la terraza junto a la ventana grande norte'
    db.session.commit()
    sale = _billing_sale(cashier, cat, table)
    sale = payment_service.add_payment(cashier, sale.id, cat.efectivo.id, 3600)
    row = db.session.get(Sale, sale.sale_id)
    limit = Sale.__table__.c['mesa'].type.length
    assert limit < len(table.name)
    assert row.mesa == table.name[:limit] and len(row.mesa) == limit


def test_partial_payment_on_counter_sale_moves_it_to_billing(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    sale = sale_service.open_sale(cashier, 'counter')
    sale_service.add_item(cashier, sale.id, cat.unidad.id, quantity=2)
    sale = payment_service.add_payment(cashier, sale.id, cat.efectivo.id, 500)
    assert sale.status == 'billing' and sale.billing_at is not None and sale.paid_total == Decimal('500')
    assert PosSaleEvent.query.filter_by(event_type='bill_requested').count() == 1
    sale = payment_service.cancel_payment(cashier, sale.payments[0].id, 'Error')
    assert sale.status == 'billing' and sale.paid_total == Decimal('0')


def test_close_sale_without_items_is_rejected(pos_app):
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _billing_sale(boss, cat, t1)
    for item in list(sale.items):
        sale = sale_service.cancel_item(boss, sale.id, item.id, 'x')
    assert sale.status == 'billing' and sale.balance == 0
    with pytest.raises(PosError, match='no tiene ítems'):
        payment_service.close_sale(boss, sale.id)


def test_cancel_payment_on_closed_sale_records_reopened_event(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _billing_sale(cashier, cat, t1)
    sale = payment_service.add_payment(cashier, sale.id, cat.efectivo.id, 3600)
    payment_id = sale.payments[0].id
    payment_service.cancel_payment(cashier, payment_id, 'Error')
    event = PosSaleEvent.query.filter_by(event_type='reopened').one()
    assert event.payload == {'reason': 'payment_cancelled', 'payment_id': payment_id}


def test_cancelling_item_of_partially_paid_sale_closes_it_when_settled(pos_app):
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = sale_service.open_sale(boss, 'salon', table_id=t1.id, people=2)
    sale_service.add_item(boss, sale.id, cat.unidad.id, quantity=1)
    sale_service.add_item(boss, sale.id, cat.unidad.id, quantity=1)
    sale_service.confirm_batch(boss, sale.id)
    sale = sale_service.request_bill(boss, sale.id)
    sale = payment_service.add_payment(boss, sale.id, cat.efectivo.id, 900)
    assert sale.status == 'billing'
    sale = sale_service.cancel_item(boss, sale.id, sale.items[0].id, 'x')
    assert sale.status == 'closed' and sale.sale_id is not None
    assert db.session.get(Sale, sale.sale_id).total == Decimal('900')


def test_discount_that_settles_a_partially_paid_sale_closes_it(pos_app):
    boss = make_user('jefe@test.com', modules=('POS', 'Descuentos'))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _billing_sale(boss, cat, t1)
    sale = payment_service.add_payment(boss, sale.id, cat.efectivo.id, 1800)
    sale = discount_service.add_discount(boss, sale.id, kind='amount', value=1800, reason='x')
    assert sale.status == 'closed' and sale.sale_id is not None


def test_reopen_after_partial_payment_keeps_paid_total(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _billing_sale(cashier, cat, t1)
    payment_service.add_payment(cashier, sale.id, cat.efectivo.id, 1000)
    sale = sale_service.reopen(cashier, sale.id)
    assert sale.status == 'open' and sale.paid_total == Decimal('1000')


def test_free_amount_discount_is_rounded_to_cents(pos_app):
    boss = make_user('jefe@test.com', modules=('POS', 'Descuentos'))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _split_sale(boss, cat, t1)
    sale = discount_service.add_discount(boss, sale.id, kind='amount', value='33.333', reason='x')
    assert sale.discounts[0].value == Decimal('33.33')
    with pytest.raises((PosError, ValueError)):
        discount_service.add_discount(boss, sale.id, kind='amount', value='0.004', reason='x')


def test_split_carries_percent_item_discount_to_both_parts(pos_app):
    boss = make_user('jefe@test.com', modules=('POS', 'Descuentos'))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _split_sale(boss, cat, t1)
    medialunas = sale.items[0]
    discount_service.add_discount(boss, sale.id, item_id=medialunas.id, kind='percent', value=50, reason='x')
    new = sale_service.split_sale(boss, sale.id, [{'item_id': medialunas.id, 'quantity': 1}])
    origin = db.session.get(PosSale, sale.id)
    assert [d.value for d in new.discounts if d.cancelled_at is None] == [Decimal('50')]
    assert [d.value for d in origin.discounts if d.cancelled_at is None] == [Decimal('50')]
    assert new.discount_total == Decimal('450') and new.total == Decimal('450')
    assert origin.discount_total == Decimal('900') and origin.total == Decimal('2900')


def test_split_leaves_sale_discount_on_origin_and_recalculates(pos_app):
    boss = make_user('jefe@test.com', modules=('POS', 'Descuentos'))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _split_sale(boss, cat, t1)
    discount_service.add_discount(boss, sale.id, kind='percent', value=10, reason='x')
    new = sale_service.split_sale(boss, sale.id, [{'item_id': sale.items[1].id, 'quantity': 1}])
    origin = db.session.get(PosSale, sale.id)
    assert new.discount_total == Decimal('0') and new.total == Decimal('2000')
    assert origin.discount_total == Decimal('270') and origin.total == Decimal('2430')


def test_split_with_pending_item_keeps_origin_open(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _split_sale(waiter, cat, t1)
    sale_service.add_item(waiter, sale.id, cat.unidad.id)
    new = sale_service.split_sale(waiter, sale.id, [{'item_id': sale.items[1].id, 'quantity': 1}])
    origin = db.session.get(PosSale, sale.id)
    assert new.status == 'billing' and origin.status == 'open'
    assert sorted(i.status for i in origin.items) == ['confirmed', 'pending']
