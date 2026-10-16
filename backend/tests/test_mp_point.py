from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.extensions import db
from app.services import mercadopago
from app.services.mercadopago import point_service
from app.services.mercadopago.fake import FakeMercadoPago
from app.services.pos import payment_service, sale_service
from app.services.pos.errors import PosError
from app.services.pos.serializers import sale_to_dict
from mp_helpers import billing_sale, configure_mp
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401


@pytest.fixture
def ctx(pos_app, monkeypatch):
    FakeMercadoPago.reset()
    monkeypatch.setattr(mercadopago, 'get_client', lambda settings: FakeMercadoPago())
    user = make_user('caja@test.com', modules=('POS', 'Anular'))
    cat = make_catalog()
    _salon, t1, t2 = make_floor()
    settings = configure_mp()
    return user, cat, t1, t2, settings


def _approve(order, amount=None):
    FakeMercadoPago().simulate(order.mp_order_id, 'approved', paid_amount=amount)
    return point_service.apply(order.id)


def test_start_creates_order_at_terminal(ctx):
    user, cat, t1, _t2, _s = ctx
    sale = billing_sale(user, cat, t1)
    order = point_service.start(user, sale.id, Decimal('1800'))
    assert order.status == 'created' and order.mp_order_id and order.external_reference.startswith(
        f'galia-venta-{sale.id}-')
    assert sale_to_dict(sale)['point_order'] == {'id': order.id, 'status': 'created', 'amount': '1800.00'}


def test_approved_registers_payment_and_closes_sale(ctx):
    user, cat, t1, _t2, settings = ctx
    sale = billing_sale(user, cat, t1)
    order = point_service.start(user, sale.id, Decimal('1800'))
    order = _approve(order)
    db.session.refresh(sale)
    assert order.status == 'approved' and sale.status == 'closed'
    payment = order.payment
    assert payment.payment_method_id == settings.point_payment_method_id and payment.amount == Decimal('1800')
    assert payment.mp_payment_id == order.mp_payment_id and payment.client_request_id == f'mp-order-{order.id}'
    assert sale_to_dict(sale)['point_order'] is None


def test_apply_twice_creates_one_payment(ctx):
    user, cat, t1, _t2, _s = ctx
    sale = billing_sale(user, cat, t1)
    order = point_service.start(user, sale.id, Decimal('1000'))
    _approve(order)
    point_service.apply(order.id)
    order.status = 'processing'  # como si otra vía lo viera antes de terminar
    db.session.commit()
    order = point_service.apply(order.id)
    db.session.refresh(sale)
    assert len([p for p in sale.payments if p.cancelled_at is None]) == 1 and sale.balance == Decimal('800')
    assert order.error is None


def test_one_order_per_terminal_and_amount_rules(ctx):
    user, cat, t1, t2, _s = ctx
    sale = billing_sale(user, cat, t1)
    other = billing_sale(user, cat, t2)
    point_service.start(user, sale.id, Decimal('500'))
    with pytest.raises(PosError) as error:
        point_service.start(user, other.id, Decimal('500'))
    assert 'El Point está cobrando Mesa 1' in error.value.message
    db.session.rollback()
    for bad in (Decimal('0'), Decimal('5000')):
        with pytest.raises(PosError):
            point_service.start(user, other.id, bad)
        db.session.rollback()


def test_requires_bill_requested(ctx):
    user, cat, _t1, t2, _s = ctx
    open_sale = sale_service.open_sale(user, 'salon', table_id=t2.id, people=1)
    with pytest.raises(PosError) as error:
        point_service.start(user, open_sale.id, Decimal('1'))
    assert 'Pedí la cuenta' in error.value.message


def test_rejected_and_retry(ctx):
    user, cat, t1, _t2, _s = ctx
    sale = billing_sale(user, cat, t1)
    order = point_service.start(user, sale.id, Decimal('1800'))
    FakeMercadoPago().simulate(order.mp_order_id, 'rejected')
    order = point_service.apply(order.id)
    assert order.status == 'failed' and 'rechazado' in order.error
    again = point_service.start(user, sale.id, Decimal('1800'))
    assert again.status == 'created'


def test_unavailable_on_create_retries_once_with_same_key(ctx):
    user, cat, t1, _t2, _s = ctx
    sale = billing_sale(user, cat, t1)
    FakeMercadoPago.fail_next('create')
    order = point_service.start(user, sale.id, Decimal('1800'))
    assert order.status == 'created'
    assert len(FakeMercadoPago.by_key) == 1


def test_approved_over_balance_is_flagged(ctx):
    user, cat, t1, _t2, _s = ctx
    sale = billing_sale(user, cat, t1)
    order = point_service.start(user, sale.id, Decimal('1800'))
    payment_service.add_payment(user, sale.id, cat.efectivo.id, 1000)  # se cobró parte en efectivo mientras tanto
    order = _approve(order)
    db.session.refresh(sale)
    assert order.status == 'approved' and order.payment.amount == Decimal('800')
    assert order.error == 'Cobrado de más: $1000.00, revisalo en Conciliación' and sale.status == 'closed'


def test_cancel_created_and_at_terminal(ctx):
    user, cat, t1, _t2, _s = ctx
    sale = billing_sale(user, cat, t1)
    order = point_service.start(user, sale.id, Decimal('1800'))
    order = point_service.cancel(user, order.id)
    assert order.status == 'canceled'
    second = point_service.start(user, sale.id, Decimal('1800'))
    FakeMercadoPago().simulate(second.mp_order_id, 'processing')
    point_service.apply(second.id)
    second = point_service.cancel(user, second.id)
    assert second.status == 'canceling'
    second = point_service.apply(second.id)  # MercadoPago confirma la cancelación
    assert second.status == 'canceled'


def test_refresh_only_checks_when_stale(ctx):
    user, cat, t1, _t2, _s = ctx
    sale = billing_sale(user, cat, t1)
    order = point_service.start(user, sale.id, Decimal('1800'))
    FakeMercadoPago().simulate(order.mp_order_id, 'approved')
    order.last_checked_at = datetime.utcnow()
    db.session.commit()
    assert point_service.refresh(order.id).status == 'created'
    order.last_checked_at = datetime.utcnow() - timedelta(seconds=6)
    db.session.commit()
    assert point_service.refresh(order.id).status == 'approved'


def test_requires_charge_permission_and_configuration(ctx):
    _user, cat, t1, _t2, settings = ctx
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cashier = make_user('caja2@test.com', modules=('POS',))
    sale = billing_sale(cashier, cat, t1)
    with pytest.raises(PosError) as error:
        point_service.start(waiter, sale.id, Decimal('100'))
    assert error.value.status == 403
    settings.terminal_id = None
    db.session.commit()
    with pytest.raises(PosError) as error:
        point_service.start(cashier, sale.id, Decimal('100'))
    assert error.value.message.startswith('Falta configurar MercadoPago')
