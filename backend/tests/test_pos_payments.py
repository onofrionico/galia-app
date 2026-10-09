from decimal import Decimal

import pytest

from app.extensions import db
from app.models import Sale
from app.services.pos import discount_service, payment_service, sale_service
from app.services.pos.errors import PosError
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401


def _billing_sale(user, cat, table):
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=3)
    sale_service.add_item(user, sale.id, cat.unidad.id, quantity=4)  # 3600
    sale_service.confirm_batch(user, sale.id)
    return sale_service.request_bill(user, sale.id)


def test_partial_payments_then_close_and_project(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _billing_sale(cashier, cat, t1)
    sale = payment_service.add_payment(cashier, sale.id, cat.debito.id, 1600)
    assert sale.status == 'billing' and sale.paid_total == Decimal('1600')
    sale = payment_service.add_payment(cashier, sale.id, cat.efectivo.id, 2000, tendered=5000)
    assert sale.status == 'closed' and sale.closed_by == cashier.id
    cash = sale.payments[1]
    assert cash.tendered == Decimal('5000') and cash.change == Decimal('3000')
    row = db.session.get(Sale, sale.sale_id)
    assert row.source == 'galia' and row.total == Decimal('3600') and row.medio_pago == 'Mixto'
    assert row.mesa == 'Mesa 1' and row.sala == 'Salón' and row.personas == 3 and row.estado == 'Cerrada'
    assert row.tipo_venta == 'Local' and row.id_origen == str(sale.id) and row.fecha == sale.closed_at.date()


def test_payment_cannot_exceed_balance(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _billing_sale(cashier, cat, t1)
    with pytest.raises(PosError) as exc:
        payment_service.add_payment(cashier, sale.id, cat.debito.id, 4000)
    assert exc.value.status == 400


def test_tendered_only_for_cash_and_not_less_than_amount(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _billing_sale(cashier, cat, t1)
    with pytest.raises(PosError):
        payment_service.add_payment(cashier, sale.id, cat.debito.id, 100, tendered=200)
    with pytest.raises((PosError, ValueError)):
        payment_service.add_payment(cashier, sale.id, cat.efectivo.id, 100, tendered=50)


def test_open_salon_sale_cannot_be_paid(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = sale_service.open_sale(cashier, 'salon', table_id=t1.id, people=1)
    sale_service.add_item(cashier, sale.id, cat.unidad.id)
    sale_service.confirm_batch(cashier, sale.id)
    with pytest.raises(PosError) as exc:
        payment_service.add_payment(cashier, sale.id, cat.efectivo.id, 900)
    assert exc.value.status == 409


def test_counter_sale_pays_while_open_confirming_pending(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    sale = sale_service.open_sale(cashier, 'counter', customer_name='Ana')
    sale_service.add_item(cashier, sale.id, cat.unidad.id, quantity=2)
    sale = payment_service.add_payment(cashier, sale.id, cat.efectivo.id, 1800)
    assert sale.status == 'closed' and sale.items[0].status == 'confirmed'
    row = db.session.get(Sale, sale.sale_id)
    assert row.tipo_venta == 'Mostrador' and row.cliente == 'Ana' and row.medio_pago == 'Efectivo'


def test_idempotent_payment(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _billing_sale(cashier, cat, t1)
    payment_service.add_payment(cashier, sale.id, cat.debito.id, 1000, client_request_id='abc-1')
    sale = payment_service.add_payment(cashier, sale.id, cat.debito.id, 1000, client_request_id='abc-1')
    assert len(sale.payments) == 1 and sale.paid_total == Decimal('1000')


def test_close_zero_total_sale(pos_app):
    boss = make_user('jefe@test.com', modules=('POS', 'Descuentos'))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _billing_sale(boss, cat, t1)
    discount_service.add_discount(boss, sale.id, kind='percent', value=100, reason='Invita la casa')
    sale = payment_service.close_sale(boss, sale.id)
    assert sale.status == 'closed' and db.session.get(Sale, sale.sale_id).total == Decimal('0')


def test_close_with_balance_is_409(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = _billing_sale(cashier, cat, t1)
    with pytest.raises(PosError) as exc:
        payment_service.close_sale(cashier, sale.id)
    assert exc.value.status == 409
