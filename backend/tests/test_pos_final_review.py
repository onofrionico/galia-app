from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import DataError

from app.extensions import db
from app.models import ProductVariant, Sale
from app.routes import pos_config
from app.services.pos import discount_service, payment_service, sale_service
from app.services.pos.errors import PosError
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401


def _confirmed(user, cat, table, quantity=2):
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=2)
    sale_service.add_item(user, sale.id, cat.unidad.id, quantity=quantity)
    return sale_service.confirm_batch(user, sale.id)


def test_non_string_client_request_id_is_400(pos_app):
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = sale_service.request_bill(cashier, _confirmed(cashier, cat, t1).id)
    with pytest.raises(PosError) as exc:
        payment_service.add_payment(cashier, sale.id, cat.efectivo.id, 100, client_request_id=12345)
    assert exc.value.status == 400


def test_cancel_closed_zero_total_sale_unprojects_and_restores_stock(pos_app):
    boss = make_user('jefe@test.com', modules=('POS', 'Descuentos'))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = sale_service.request_bill(boss, _confirmed(boss, cat, t1).id)
    discount_service.add_discount(boss, sale.id, kind='percent', value=100, reason='Invita la casa')
    sale = payment_service.close_sale(boss, sale.id)
    projected_id = sale.sale_id
    assert sale.status == 'closed' and db.session.get(Sale, projected_id) is not None
    sale = sale_service.cancel_sale(boss, sale.id, 'Error de carga')
    assert sale.status == 'cancelled' and sale.sale_id is None
    assert db.session.get(Sale, projected_id) is None
    assert Decimal(db.session.get(ProductVariant, cat.unidad.id).stock_quantity) == Decimal('5')


def test_cancel_closed_sale_with_payments_is_409(pos_app):
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = sale_service.request_bill(boss, _confirmed(boss, cat, t1).id)
    sale = payment_service.add_payment(boss, sale.id, cat.efectivo.id, 1800)
    assert sale.status == 'closed'
    with pytest.raises(PosError, match='pagos'):
        sale_service.cancel_sale(boss, sale.id, 'x')


def test_data_error_maps_to_400(pos_app, monkeypatch):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    admin = make_user('admin@test.com', role='admin')
    _s, t1, _t = make_floor()

    def boom(*args, **kwargs):
        raise DataError('x', {}, Exception('y'))
    monkeypatch.setattr(sale_service, 'open_sale', boom)
    response = client.post('/api/v1/pos/sales', headers=auth_headers(client, waiter),
                           json={'sale_type': 'salon', 'table_id': t1.id, 'people': 1})
    assert response.status_code == 400 and 'demasiado grande' in response.get_json()['error']
    monkeypatch.setattr(pos_config, 'Salon', boom)
    response = client.post('/api/v1/pos/config/salons', json={'name': 'X'}, headers=auth_headers(client, admin))
    assert response.status_code == 400 and 'demasiado grande' in response.get_json()['error']


def test_money_values_are_quantized(pos_app):
    client = pos_app.test_client()
    admin = make_user('admin@test.com', role='admin')
    headers = auth_headers(client, admin)
    template = client.post('/api/v1/pos/config/discount-templates', headers=headers,
                           json={'name': 'Raro', 'kind': 'amount', 'value': 15.555, 'scope': 'sale'})
    assert template.status_code == 201 and template.get_json()['value'] == 15.56
    tiny = client.post('/api/v1/pos/config/discount-templates', headers=headers,
                       json={'name': 'Nada', 'kind': 'amount', 'value': 0.004, 'scope': 'sale'})
    assert tiny.status_code == 400
    group = client.post('/api/v1/pos/config/modifier-groups', headers=headers, json={
        'name': 'G', 'min_select': 0, 'max_select': 1, 'options': [{'name': 'A', 'price_delta': 50.004}]})
    assert group.status_code == 201, group.get_json()
    assert group.get_json()['options'][0]['price_delta'] == 50.0


def test_projected_sales_are_protected_in_legacy_endpoints(pos_app):
    client = pos_app.test_client()
    admin = make_user('admin@test.com', role='admin')
    row = Sale(fecha=date(2026, 3, 5), creacion=datetime(2026, 3, 5, 10, 0), estado='Cerrada', total=10, source='galia')
    db.session.add(row)
    db.session.commit()
    headers = auth_headers(client, admin)
    put = client.put(f'/api/v1/sales/{row.id}', json={'total': 5}, headers=headers)
    assert put.status_code == 409 and 'POS' in put.get_json()['error']
    assert client.delete(f'/api/v1/sales/{row.id}', headers=headers).status_code == 409
    assert db.session.get(Sale, row.id) is not None


def test_reopen_clears_billing_at(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = sale_service.request_bill(waiter, _confirmed(waiter, cat, t1).id)
    assert sale.billing_at is not None
    sale = sale_service.reopen(waiter, sale.id)
    assert sale.status == 'open' and sale.billing_at is None
