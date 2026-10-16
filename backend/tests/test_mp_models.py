from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import MpPointOrder
from app.services.pos import payment_service, sale_service
from app.services.pos.common import now
from app.services.pos.serializers import payment_to_dict
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401


def _order(sale, user, terminal='T1', status='created'):
    order = MpPointOrder(sale_id=sale.id, amount=Decimal('100'), terminal_id=terminal,
                         external_reference=f'galia-venta-{sale.id}-{terminal}-{status}',
                         idempotency_key=f'k-{status}-{terminal}', status=status, created_by=user.id,
                         created_at=now(), updated_at=now())
    db.session.add(order)
    db.session.commit()
    return order


def test_one_active_order_per_terminal(pos_app):
    user = make_user('caja@test.com', modules=('POS',))
    make_catalog()
    _salon, t1, _t2 = make_floor()
    sale = sale_service.open_sale(user, 'salon', table_id=t1.id, people=1)
    _order(sale, user, status='created')
    with pytest.raises(IntegrityError):
        _order(sale, user, status='processing')
    db.session.rollback()
    _order(sale, user, status='approved')  # los finales no cuentan
    _order(sale, user, terminal='T2', status='created')


def test_payment_method_is_mercadopago_flag(pos_app):
    client = pos_app.test_client()
    admin = auth_headers(client, make_user('admin@test.com', role='admin'))
    created = client.post('/api/v1/pos/config/payment-methods', json={'name': 'Point', 'kind': 'card',
                                                                       'is_mercadopago': True}, headers=admin)
    assert created.status_code == 201 and created.get_json()['is_mercadopago'] is True
    other = client.post('/api/v1/pos/config/payment-methods', json={'name': 'Visa', 'kind': 'card'}, headers=admin)
    assert other.get_json()['is_mercadopago'] is False


def test_payment_dict_includes_mp_payment_id(pos_app):
    user = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    sale = sale_service.open_sale(user, 'counter')
    sale_service.add_item(user, sale.id, cat.unidad.id)
    payment_service.add_payment(user, sale.id, cat.debito.id, 900)
    payment = sale.payments[0]
    payment.mp_payment_id = '123'
    db.session.commit()
    assert payment_to_dict(payment)['mp_payment_id'] == '123'
