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


def test_waiters_lists_active_users_with_pos_or_camarero(pos_app):
    client = pos_app.test_client()
    admin = make_user('admin@test.com', role='admin')
    make_user('mozo@test.com', modules=('Camarero',))
    make_user('caja@test.com', modules=('POS',))
    make_user('cocina@test.com')
    gone = make_user('viejo@test.com', modules=('Camarero',))
    gone.is_active = False
    db.session.commit()
    data = client.get('/api/v1/pos/waiters', headers=auth_headers(client, admin)).get_json()
    assert [w['name'] for w in data['waiters']] == ['admin@test.com', 'caja@test.com', 'mozo@test.com']


def test_waiters_requires_pos(pos_app):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    assert client.get('/api/v1/pos/waiters', headers=auth_headers(client, waiter)).status_code == 403


def test_change_waiter(pos_app):
    client = pos_app.test_client()
    cashier = make_user('caja@test.com', modules=('POS',))
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    _s, t1, _t = make_floor()
    sale = sale_service.open_sale(cashier, 'salon', table_id=t1.id, people=2)
    response = client.post(f'/api/v1/pos/sales/{sale.id}/waiter', json={'waiter_id': waiter.id},
                           headers=auth_headers(client, cashier))
    assert response.status_code == 200, response.get_json()
    assert response.get_json()['waiter'] == {'id': waiter.id, 'name': 'mozo@test.com'}
    events = client.get(f'/api/v1/pos/sales/{sale.id}/events', headers=auth_headers(client, cashier)).get_json()
    changed = [e for e in events['events'] if e['event_type'] == 'waiter_changed']
    assert changed[0]['payload'] == {'from_waiter_id': cashier.id, 'to_waiter_id': waiter.id}


def test_change_waiter_rules(pos_app):
    client = pos_app.test_client()
    cashier = make_user('caja@test.com', modules=('POS',))
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cook = make_user('cocina@test.com')
    cat = make_catalog()
    _s, t1, _t = make_floor()
    sale = sale_service.open_sale(cashier, 'salon', table_id=t1.id, people=2)
    c = auth_headers(client, cashier)
    bad = client.post(f'/api/v1/pos/sales/{sale.id}/waiter', json={'waiter_id': cook.id}, headers=c)
    assert bad.status_code == 400
    denied = client.post(f'/api/v1/pos/sales/{sale.id}/waiter', json={'waiter_id': waiter.id},
                         headers=auth_headers(client, waiter))
    assert denied.status_code == 403
    counter = sale_service.open_sale(cashier, 'counter')
    sale_service.add_item(cashier, counter.id, cat.unidad.id)
    from app.services.pos import payment_service
    closed = payment_service.add_payment(cashier, counter.id, cat.efectivo.id, 900)
    assert closed.status == 'closed'
    conflict = client.post(f'/api/v1/pos/sales/{counter.id}/waiter', json={'waiter_id': waiter.id}, headers=c)
    assert conflict.status_code == 409


def test_open_sale_rejects_waiter_without_permission(pos_app):
    client = pos_app.test_client()
    cashier = make_user('caja@test.com', modules=('POS',))
    cook = make_user('cocina@test.com')
    _s, t1, _t = make_floor()
    response = client.post('/api/v1/pos/sales', headers=auth_headers(client, cashier),
                           json={'sale_type': 'salon', 'table_id': t1.id, 'people': 2, 'waiter_id': cook.id})
    assert response.status_code == 400
