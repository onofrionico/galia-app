from app.extensions import db
from app.models.pos import CancelReason
from app.services.pos import sale_service
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401


def test_cancel_reasons_config_is_admin_only(pos_app):
    client = pos_app.test_client()
    cashier = make_user('caja@test.com', modules=('POS',))
    admin = make_user('admin@test.com', role='admin')
    denied = client.post('/api/v1/pos/config/cancel-reasons', json={'name': 'Rotura'},
                         headers=auth_headers(client, cashier))
    assert denied.status_code == 403
    headers = auth_headers(client, admin)
    created = client.post('/api/v1/pos/config/cancel-reasons', json={'name': 'Rotura', 'position': 3}, headers=headers)
    assert created.status_code == 201 and created.get_json()['name'] == 'Rotura'
    duplicate = client.post('/api/v1/pos/config/cancel-reasons', json={'name': 'Rotura'}, headers=headers)
    assert duplicate.status_code == 409
    reason_id = created.get_json()['id']
    updated = client.put(f'/api/v1/pos/config/cancel-reasons/{reason_id}', json={'is_active': False}, headers=headers)
    assert updated.status_code == 200 and updated.get_json()['is_active'] is False
    listed = client.get('/api/v1/pos/config/cancel-reasons', headers=headers).get_json()['cancel_reasons']
    assert [r['name'] for r in listed] == ['Rotura']


def test_cancel_reason_lookup_lists_active_only(pos_app):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    nobody = make_user('x@test.com')
    db.session.add_all([CancelReason(name='B', position=1), CancelReason(name='A', position=0),
                        CancelReason(name='Vieja', position=2, is_active=False)])
    db.session.commit()
    data = client.get('/api/v1/pos/cancel-reasons', headers=auth_headers(client, waiter)).get_json()
    assert [r['name'] for r in data['cancel_reasons']] == ['A', 'B']
    assert client.get('/api/v1/pos/cancel-reasons', headers=auth_headers(client, nobody)).status_code == 403


def test_cancel_item_route_accepts_reason_id(pos_app):
    client = pos_app.test_client()
    boss = make_user('jefe@test.com', modules=('POS', 'Anular'))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    reason = CancelReason(name='Error de carga')
    db.session.add(reason)
    db.session.commit()
    sale = sale_service.open_sale(boss, 'salon', table_id=t1.id, people=1)
    sale_service.add_item(boss, sale.id, cat.unidad.id)
    sale = sale_service.confirm_batch(boss, sale.id)
    response = client.post(f'/api/v1/pos/sales/{sale.id}/items/{sale.items[0].id}/cancel',
                           json={'reason_id': reason.id}, headers=auth_headers(client, boss))
    assert response.status_code == 200, response.get_json()
    item = response.get_json()['items'][0]
    assert item['cancel_reason'] == 'Error de carga' and item['cancel_reason_id'] == reason.id
