from app.services.pos import sale_service
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401


def test_salon_and_table_crud(pos_app):
    client = pos_app.test_client()
    cashier = make_user('caja@test.com', modules=('POS',))
    headers = auth_headers(client, cashier)
    salon = client.post('/api/v1/pos/config/salons', json={'name': 'Terraza'}, headers=headers)
    assert salon.status_code == 201, salon.get_json()
    salon_id = salon.get_json()['id']
    table = client.post('/api/v1/pos/config/tables', json={'salon_id': salon_id, 'number': 7, 'capacity': 4},
                        headers=headers)
    assert table.status_code == 201
    dup = client.post('/api/v1/pos/config/tables', json={'salon_id': salon_id, 'number': 7}, headers=headers)
    assert dup.status_code == 409
    moved = client.put(f"/api/v1/pos/config/tables/{table.get_json()['id']}", json={'pos_x': 30, 'pos_y': 40},
                       headers=headers)
    assert moved.get_json()['pos_x'] == 30


def test_cannot_deactivate_busy_table(pos_app):
    client = pos_app.test_client()
    cashier = make_user('caja@test.com', modules=('POS',))
    _s, t1, _t = make_floor()
    sale_service.open_sale(cashier, 'salon', table_id=t1.id, people=1)
    response = client.put(f'/api/v1/pos/config/tables/{t1.id}', json={'is_active': False},
                          headers=auth_headers(client, cashier))
    assert response.status_code == 409


def test_modifier_group_crud_and_assignment(pos_app):
    client = pos_app.test_client()
    admin = make_user('admin@test.com', role='admin')
    cat = make_catalog()
    headers = auth_headers(client, admin)
    created = client.post('/api/v1/pos/config/modifier-groups', headers=headers, json={
        'name': 'Endulzante', 'min_select': 0, 'max_select': 1,
        'options': [{'name': 'Azúcar'}, {'name': 'Stevia', 'price_delta': 50}]})
    assert created.status_code == 201, created.get_json()
    group = created.get_json()
    assert [o['name'] for o in group['options']] == ['Azúcar', 'Stevia']
    bad = client.post('/api/v1/pos/config/modifier-groups', headers=headers,
                      json={'name': 'X', 'min_select': 2, 'max_select': 1, 'options': [{'name': 'a'}]})
    assert bad.status_code == 400
    assigned = client.put(f'/api/v1/pos/config/products/{cat.medialuna.id}/modifier-groups', headers=headers,
                          json={'group_ids': [group['id']]})
    assert assigned.status_code == 200 and assigned.get_json()['group_ids'] == [group['id']]


def test_payment_methods_and_templates_admin_only(pos_app):
    client = pos_app.test_client()
    cashier = make_user('caja@test.com', modules=('POS',))
    admin = make_user('admin@test.com', role='admin')
    denied = client.post('/api/v1/pos/config/payment-methods', json={'name': 'Cheque', 'kind': 'other'},
                         headers=auth_headers(client, cashier))
    assert denied.status_code == 403
    ok = client.post('/api/v1/pos/config/discount-templates', headers=auth_headers(client, admin),
                     json={'name': 'Happy hour', 'kind': 'percent', 'value': 15, 'scope': 'sale'})
    assert ok.status_code == 201 and ok.get_json()['restricted'] is False


def test_floor_shows_active_sales(pos_app):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    salon, t1, t2 = make_floor()
    sale = sale_service.open_sale(waiter, 'salon', table_id=t1.id, people=2)
    data = client.get('/api/v1/pos/floor', headers=auth_headers(client, waiter)).get_json()
    assert data['salon_id'] == salon.id
    by_number = {t['number']: t for t in data['tables']}
    assert by_number[1]['sales'][0]['id'] == sale.id and by_number[2]['sales'] == []


def test_catalog_lists_variants_and_modifiers(pos_app):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    make_catalog()
    data = client.get('/api/v1/pos/catalog', headers=auth_headers(client, waiter)).get_json()
    cortado = next(p for p in data['products'] if p['name'] == 'Cortado')
    assert cortado['variants'][0]['price'] == 2000.0
    assert [g['name'] for g in cortado['modifier_groups']] == ['Tipo de leche', 'Extras']
    lookups = client.get('/api/v1/pos/payment-methods', headers=auth_headers(client, waiter)).get_json()
    assert [m['name'] for m in lookups['payment_methods']] == ['Efectivo', 'Débito']


def test_floor_requires_pos_or_camarero(pos_app):
    client = pos_app.test_client()
    nobody = make_user('x@test.com')
    assert client.get('/api/v1/pos/floor', headers=auth_headers(client, nobody)).status_code == 403
