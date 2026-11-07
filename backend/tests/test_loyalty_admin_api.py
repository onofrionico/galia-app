from app.extensions import db
from app.models.loyalty import LoyaltyChangeLog, LoyaltyMovement, LoyaltySettings
from loyalty_helpers import auth_headers, make_catalog, make_customer, make_reward, make_user, pos_app  # noqa: F401

BASE = '/api/v1/loyalty/admin'


def _admin(pos_app):
    client = pos_app.test_client()
    manager = make_user('fide@test.com', modules=('Fidelizacion',))
    return client, auth_headers(client, manager), manager


def test_pos_only_user_gets_403_on_admin_api(pos_app):
    client = pos_app.test_client()
    cashier = make_user('caja@test.com', modules=('POS',))
    headers = auth_headers(client, cashier)
    for method, path in [('get', '/settings'), ('get', '/rewards'), ('get', '/customers'),
                         ('post', '/customers/1/adjustments'), ('get', '/reports/active'), ('get', '/change-log')]:
        assert getattr(client, method)(BASE + path, headers=headers, json={}).status_code == 403


def test_set_variant_cafecitos_logs_old_and_new(pos_app):
    client, headers, manager = _admin(pos_app)
    cat = make_catalog()
    resp = client.put(f'{BASE}/variants/cafecitos', headers=headers,
                      json={'variant_ids': [cat.taza.id, cat.unidad.id], 'cafecitos': 2})
    assert resp.status_code == 200
    assert cat.taza.cafecitos == 2 and cat.unidad.cafecitos == 2
    logs = LoyaltyChangeLog.query.filter_by(entity='variant').order_by(LoyaltyChangeLog.entity_id).all()
    assert [(l.entity_id, l.field, l.old_value, l.new_value, l.user_id) for l in logs] == [
        (cat.taza.id, 'cafecitos', '0', '2', manager.id), (cat.unidad.id, 'cafecitos', '0', '2', manager.id)]
    assert client.put(f'{BASE}/variants/cafecitos', headers=headers,
                      json={'variant_ids': [cat.taza.id], 'cafecitos': -1}).status_code == 400
    listed = client.get(f'{BASE}/variants?q=cortado', headers=headers).get_json()
    assert listed == [{'id': cat.taza.id, 'product_id': cat.cortado.id, 'product_name': 'Cortado',
                       'variant_name': 'Taza', 'cafecitos': 2}]


def test_unchanged_variant_does_not_log(pos_app):
    client, headers, _ = _admin(pos_app)
    cat = make_catalog()
    client.put(f'{BASE}/variants/cafecitos', headers=headers, json={'variant_ids': [cat.taza.id], 'cafecitos': 0})
    assert LoyaltyChangeLog.query.count() == 0


def test_reward_crud_logs_and_cost_change_does_not_touch_past_redemptions(pos_app):
    client, headers, _ = _admin(pos_app)
    cat = make_catalog()
    created = client.post(f'{BASE}/rewards', headers=headers,
                          json={'name': 'Café gratis', 'product_variant_id': cat.taza.id, 'cost': 8})
    assert created.status_code == 201
    reward_id = created.get_json()['id']
    customer = make_customer()
    db.session.add(LoyaltyMovement(customer_id=customer.id, kind='redeem', amount=-8, reward_id=reward_id,
                                   reward_cost=8))
    db.session.commit()
    updated = client.put(f'{BASE}/rewards/{reward_id}', headers=headers, json={'cost': 10, 'is_active': False})
    assert updated.status_code == 200 and updated.get_json()['cost'] == 10
    assert LoyaltyMovement.query.filter_by(kind='redeem').one().reward_cost == 8
    fields = {(l.field, l.old_value, l.new_value) for l in LoyaltyChangeLog.query.filter_by(entity='reward')}
    assert ('created', None, 'Café gratis') in fields
    assert ('cost', '8', '10') in fields and ('is_active', 'True', 'False') in fields
    assert client.post(f'{BASE}/rewards', headers=headers,
                       json={'name': 'X', 'product_variant_id': cat.taza.id, 'cost': 0}).status_code == 400


def test_settings_validates_range(pos_app):
    client, headers, _ = _admin(pos_app)
    assert client.get(f'{BASE}/settings', headers=headers).get_json() == {'active_days': 30}
    assert client.put(f'{BASE}/settings', headers=headers, json={'active_days': 0}).status_code == 400
    assert client.put(f'{BASE}/settings', headers=headers, json={'active_days': 366}).status_code == 400
    assert client.put(f'{BASE}/settings', headers=headers, json={'active_days': 45}).get_json() == {'active_days': 45}
    assert LoyaltySettings.get().active_days == 45
    log = LoyaltyChangeLog.query.filter_by(entity='settings').one()
    assert (log.field, log.old_value, log.new_value) == ('active_days', '30', '45')


def test_adjustment_endpoint_requires_reason(pos_app):
    client, headers, _ = _admin(pos_app)
    customer = make_customer()
    url = f'{BASE}/customers/{customer.id}/adjustments'
    assert client.post(url, headers=headers, json={'amount': 6}).status_code == 400
    ok = client.post(url, headers=headers, json={'amount': 6, 'reason': 'Sellos de tarjeta de papel'})
    assert ok.status_code == 200 and ok.get_json()['balance'] == 6
    detail = client.get(f'{BASE}/customers/{customer.id}', headers=headers).get_json()
    assert detail['balance'] == 6 and detail['movements'][0]['reason'] == 'Sellos de tarjeta de papel'
    listed = client.get(f'{BASE}/customers?q=lucia', headers=headers).get_json()
    assert listed[0]['id'] == customer.id and listed[0]['balance'] == 6


def test_regenerate_qr_changes_token_and_logs(pos_app):
    client, headers, _ = _admin(pos_app)
    customer = make_customer()
    old = customer.qr_token
    resp = client.post(f'{BASE}/customers/{customer.id}/regenerate-qr', headers=headers)
    assert resp.status_code == 200 and customer.qr_token != old
    assert LoyaltyChangeLog.query.filter_by(entity='customer', field='qr_token').count() == 1


def test_change_log_lists_newest_first(pos_app):
    client, headers, _ = _admin(pos_app)
    client.put(f'{BASE}/settings', headers=headers, json={'active_days': 40})
    client.put(f'{BASE}/settings', headers=headers, json={'active_days': 50})
    rows = client.get(f'{BASE}/change-log?entity=settings', headers=headers).get_json()
    assert [r['new_value'] for r in rows] == ['50', '40'] and rows[0]['user'] == 'fide@test.com'
