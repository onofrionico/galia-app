import hashlib
import hmac

import pytest

from app.extensions import db
from app.models import MpPointOrder
from app.services import mercadopago
from app.services.mercadopago.fake import FakeMercadoPago
from mp_helpers import billing_sale, configure_mp
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401


@pytest.fixture
def ctx(pos_app, monkeypatch):
    FakeMercadoPago.reset()
    monkeypatch.setattr(mercadopago, 'get_client', lambda settings: FakeMercadoPago())
    client = pos_app.test_client()
    user = make_user('caja@test.com', modules=('POS', 'Anular'))
    headers = auth_headers(client, user)
    cat = make_catalog()
    _salon, t1, t2 = make_floor()
    configure_mp()
    return client, headers, user, cat, t1, t2


def _signed(data_id, secret='whsec', request_id='req-1', ts='1704908010'):
    manifest = f'id:{data_id.lower()};request-id:{request_id};ts:{ts};'
    digest = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return {'x-signature': f'ts={ts},v1={digest}', 'x-request-id': request_id}


def test_point_flow_through_the_api(ctx):
    client, headers, user, cat, t1, _t2 = ctx
    sale = billing_sale(user, cat, t1)
    config = client.get('/api/v1/mp/point-config', headers=headers).get_json()
    assert config['enabled'] is True
    created = client.post(f'/api/v1/mp/sales/{sale.id}/point', json={'amount': '1800'}, headers=headers)
    assert created.status_code == 201 and created.get_json()['status'] == 'created'
    order_id = created.get_json()['id']
    sale_data = client.get(f'/api/v1/pos/sales/{sale.id}', headers=headers).get_json()
    assert sale_data['point_order']['id'] == order_id
    mp_order_id = db.session.get(MpPointOrder, order_id).mp_order_id
    FakeMercadoPago().simulate(mp_order_id, 'approved')
    hook = client.post(f'/api/v1/mercadopago/webhook?data.id={mp_order_id}&type=order',
                       json={'type': 'order', 'action': 'order.processed', 'data': {'id': mp_order_id}},
                       headers=_signed(mp_order_id))
    assert hook.status_code == 200
    status = client.get(f'/api/v1/mp/point-orders/{order_id}', headers=headers).get_json()
    assert status['status'] == 'approved' and status['payment_id']
    orders = client.get(f'/api/v1/mp/sales/{sale.id}/point-orders', headers=headers).get_json()['orders']
    assert orders[0]['id'] == order_id


def test_webhook_signature(ctx):
    client, *_ = ctx
    bad = client.post('/api/v1/mercadopago/webhook?data.id=X', json={'type': 'order', 'data': {'id': 'X'}},
                      headers={'x-signature': 'ts=1,v1=00', 'x-request-id': 'r'})
    assert bad.status_code == 401
    other = client.post('/api/v1/mercadopago/webhook?data.id=123', json={'type': 'payment', 'data': {'id': '123'}},
                        headers=_signed('123'))
    assert other.status_code == 200
    unknown = client.post('/api/v1/mercadopago/webhook?data.id=NOPE', json={'type': 'order', 'data': {'id': 'NOPE'}},
                          headers=_signed('NOPE'))
    assert unknown.status_code == 200


def test_cancel_and_permissions(ctx):
    client, headers, user, cat, t1, t2 = ctx
    sale = billing_sale(user, cat, t1)
    order_id = client.post(f'/api/v1/mp/sales/{sale.id}/point', json={'amount': '100'},
                           headers=headers).get_json()['id']
    busy = client.post(f'/api/v1/mp/sales/{billing_sale(user, cat, t2).id}/point', json={'amount': '100'},
                       headers=headers)
    assert busy.status_code == 409 and 'El Point está cobrando' in busy.get_json()['error']
    canceled = client.post(f'/api/v1/mp/point-orders/{order_id}/cancel', headers=headers).get_json()
    assert canceled['status'] == 'canceled'
    waiter = auth_headers(client, make_user('mozo@test.com', modules=('Camarero',)))
    assert client.post(f'/api/v1/mp/sales/{sale.id}/point', json={'amount': '1'}, headers=waiter).status_code == 403
    charger = auth_headers(client, make_user('mozo2@test.com', modules=('Camarero', 'Cobrar')))
    assert client.post(f'/api/v1/mp/sales/{sale.id}/point', json={'amount': '1'}, headers=charger).status_code == 201
    assert client.post(f'/api/v1/mp/sales/{sale.id}/point', json={'amount': 'x'}, headers=charger).status_code in (
        400, 409)
    assert client.get('/api/v1/mp/settings', headers=headers).status_code == 403
    assert client.get('/api/v1/mp/reconciliation/2026-10-15', headers=headers).status_code == 403


def test_reconciliation_api(ctx):
    client, *_ = ctx
    concilia = auth_headers(client, make_user('conc@test.com', modules=('Conciliar',)))
    FakeMercadoPago().add_payment_movement({'id': 1, 'date_created': '2026-10-15T12:00:00.000-03:00',
                                            'transaction_amount': 500, 'status': 'approved',
                                            'payment_type_id': 'bank_transfer'})
    assert client.post('/api/v1/mp/reconciliation/2026-10-15/fetch', headers=concilia).get_json()['fetched'] == 1
    day = client.get('/api/v1/mp/reconciliation/2026-10-15', headers=concilia).get_json()
    movement_id = day['only_mp'][0]['movement_id']
    resolved = client.post('/api/v1/mp/reconciliation/resolutions', json={
        'kind': 'not_a_sale', 'movement_id': movement_id, 'note': 'Aporte del dueño'}, headers=concilia)
    assert resolved.status_code == 201
    summary = client.get('/api/v1/mp/reconciliation?from=2026-10-15&to=2026-10-15', headers=concilia).get_json()
    assert summary['days'][0]['status'] == 'conciliado'
    assert client.delete(f"/api/v1/mp/reconciliation/resolutions/{resolved.get_json()['id']}",
                         headers=concilia).status_code == 200
    assert client.get('/api/v1/mp/reconciliation/xx', headers=concilia).status_code == 400


def test_settings_admin(ctx):
    client, *_ = ctx
    admin = auth_headers(client, make_user('admin@test.com', role='admin'))
    data = client.get('/api/v1/mp/settings', headers=admin).get_json()
    assert data['terminal_id'] and 'TEST-TOKEN' not in str(data)
    saved = client.put('/api/v1/mp/settings/token', json={'environment': 'test', 'access_token': 'TEST-2'},
                       headers=admin)
    assert saved.status_code == 200 and saved.get_json()['user_id'] == '1'
    terminals = client.get('/api/v1/mp/settings/terminals', headers=admin).get_json()['terminals']
    assert terminals[0]['operating_mode'] == 'PDV'
    assert client.post('/api/v1/mp/settings/terminals/PAX_A910__SMARTPOS1/pdv', headers=admin).status_code == 200
    put = client.put('/api/v1/mp/settings', json={'terminal_id': 'PAX_A910__SMARTPOS1', 'webhook_secret': 'nuevo',
                                                  'environment': 'test'}, headers=admin)
    assert put.status_code == 200 and put.get_json()['has_webhook_secret'] is True
    assert client.post('/api/v1/mp/settings/test', headers=admin).get_json()['ok'] is True
    assert client.put('/api/v1/mp/settings', json={'environment': 'x'}, headers=admin).status_code == 400
    bad_method = client.put('/api/v1/mp/settings', json={'point_payment_method_id': 9999}, headers=admin)
    assert bad_method.status_code == 400


def test_fake_debug_endpoint_only_with_fake(ctx, monkeypatch):
    client, headers, user, cat, t1, _t2 = ctx
    sale = billing_sale(user, cat, t1)
    order_id = client.post(f'/api/v1/mp/sales/{sale.id}/point', json={'amount': '1800'},
                           headers=headers).get_json()['id']
    assert client.post(f'/api/v1/mp/fake/point-orders/{order_id}/approved', headers=headers).status_code == 404
    monkeypatch.setenv('MP_FAKE', '1')
    simulated = client.post(f'/api/v1/mp/fake/point-orders/{order_id}/approved', headers=headers)
    assert simulated.status_code == 200 and simulated.get_json()['status'] == 'approved'
