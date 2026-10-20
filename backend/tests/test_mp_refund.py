from decimal import Decimal

import pytest

from app.extensions import db
from app.services import mercadopago
from app.services.mercadopago import point_service, refund_service
from app.services.mercadopago.fake import FakeMercadoPago
from app.services.pos.errors import PosError
from app.services.pos.serializers import payment_to_dict
from mp_helpers import billing_sale, configure_mp
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401


@pytest.fixture
def paid(pos_app, monkeypatch):
    FakeMercadoPago.reset()
    monkeypatch.setattr(mercadopago, 'get_client', lambda settings: FakeMercadoPago())
    user = make_user('caja@test.com', modules=('POS', 'Anular'))
    cat = make_catalog()
    _salon, t1, _t2 = make_floor()
    configure_mp()
    sale = billing_sale(user, cat, t1)
    order = point_service.start(user, sale.id, Decimal('1800'))
    FakeMercadoPago().simulate(order.mp_order_id, 'approved')
    order = point_service.apply(order.id)
    return pos_app, user, sale, order


def test_payment_dict_marks_refundable(paid):
    _app, _user, _sale, order = paid
    assert payment_to_dict(order.payment)['refundable_mp'] is True


def test_refund_then_cancel(paid):
    _app, user, _sale, order = paid
    refund_service.cancel_with_refund(user, order.payment_id, 'Cliente se arrepintió')
    db.session.refresh(order)
    assert order.refunded_at is not None and order.payment.cancelled_at is not None
    assert FakeMercadoPago.orders[order.mp_order_id]['status'] == 'refunded'
    assert payment_to_dict(order.payment)['refundable_mp'] is False


def test_refund_rejected_keeps_payment(paid):
    _app, user, _sale, order = paid
    FakeMercadoPago.orders[order.mp_order_id]['status'] = 'expired'  # MercadoPago no la acepta
    with pytest.raises(PosError) as error:
        refund_service.cancel_with_refund(user, order.payment_id, 'x')
    assert error.value.message.startswith('MercadoPago rechazó la devolución')
    db.session.rollback()
    FakeMercadoPago.orders[order.mp_order_id]['status'] = 'processed'
    FakeMercadoPago.fail_next('refund')
    with pytest.raises(PosError) as error:
        refund_service.cancel_with_refund(user, order.payment_id, 'x')
    assert error.value.message == 'MercadoPago no responde: no se anuló el pago'
    db.session.rollback()
    db.session.refresh(order.payment)
    assert order.payment.cancelled_at is None and order.refunded_at is None


def test_invalid_cancel_does_not_refund(paid):
    _app, user, _sale, order = paid
    with pytest.raises(PosError):
        refund_service.cancel_with_refund(user, order.payment_id, '')  # falta el motivo
    db.session.rollback()
    assert FakeMercadoPago.orders[order.mp_order_id]['status'] == 'processed'


def test_route_refund_flag(paid):
    app, _user, _sale, order = paid
    client = app.test_client()
    headers = auth_headers(client, make_user('anula@test.com', modules=('POS', 'Anular')))
    only_galia = client.post(f'/api/v1/pos/payments/{order.payment_id}/cancel',
                             json={'reason': 'Error', 'refund_mp': False}, headers=headers)
    assert only_galia.status_code == 200
    assert FakeMercadoPago.orders[order.mp_order_id]['status'] == 'processed'


def test_route_refund_mp(paid):
    app, _user, _sale, order = paid
    client = app.test_client()
    headers = auth_headers(client, make_user('anula@test.com', modules=('POS', 'Anular')))
    response = client.post(f'/api/v1/pos/payments/{order.payment_id}/cancel',
                           json={'reason': 'Error', 'refund_mp': True}, headers=headers)
    assert response.status_code == 200
    assert FakeMercadoPago.orders[order.mp_order_id]['status'] == 'refunded'
