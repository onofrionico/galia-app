from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401


def _open(client, headers, table_id, people=2):
    return client.post('/api/v1/pos/sales', headers=headers,
                       json={'sale_type': 'salon', 'table_id': table_id, 'people': people})


def test_full_salon_flow_over_api(pos_app):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    w = auth_headers(client, waiter)
    c = auth_headers(client, cashier)
    sale = _open(client, w, t1.id).get_json()
    assert sale['status'] == 'open' and sale['table']['label'] == 'Mesa 1'
    sid = sale['id']
    added = client.post(f'/api/v1/pos/sales/{sid}/items', headers=w,
                        json={'product_variant_id': cat.taza.id, 'modifier_option_ids': [cat.almendras.id],
                              'note': 'sin azúcar'})
    assert added.status_code == 200 and added.get_json()['total'] == 2300.0
    assert client.post(f'/api/v1/pos/sales/{sid}/confirm', headers=w).status_code == 200
    assert client.post(f'/api/v1/pos/sales/{sid}/request-bill', headers=w).get_json()['status'] == 'billing'
    paid = client.post(f'/api/v1/pos/sales/{sid}/payments', headers=c,
                       json={'payment_method_id': cat.efectivo.id, 'amount': 2300, 'tendered': 3000})
    body = paid.get_json()
    assert paid.status_code == 200 and body['status'] == 'closed' and body['payments'][0]['change'] == 700.0
    events = client.get(f'/api/v1/pos/sales/{sid}/events', headers=c).get_json()['events']
    assert [e['event_type'] for e in events][:2] == ['opened', 'item_added']


def test_waiter_without_cobrar_cannot_pay(pos_app):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    w = auth_headers(client, waiter)
    sid = _open(client, w, t1.id).get_json()['id']
    response = client.post(f'/api/v1/pos/sales/{sid}/payments', headers=w,
                           json={'payment_method_id': cat.efectivo.id, 'amount': 1})
    assert response.status_code == 403


def test_waiter_with_cobrar_can_pay(pos_app):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero', 'Cobrar'))
    cat = make_catalog()
    _s, t1, _t = make_floor()
    w = auth_headers(client, waiter)
    sid = _open(client, w, t1.id).get_json()['id']
    client.post(f'/api/v1/pos/sales/{sid}/items', headers=w, json={'product_variant_id': cat.unidad.id})
    client.post(f'/api/v1/pos/sales/{sid}/confirm', headers=w)
    client.post(f'/api/v1/pos/sales/{sid}/request-bill', headers=w)
    response = client.post(f'/api/v1/pos/sales/{sid}/payments', headers=w,
                           json={'payment_method_id': cat.debito.id, 'amount': 900})
    assert response.status_code == 200 and response.get_json()['status'] == 'closed'


def test_errors_are_json_with_spanish_messages(pos_app):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    _s, t1, _t = make_floor()
    w = auth_headers(client, waiter)
    first = _open(client, w, t1.id).get_json()
    busy = _open(client, w, t1.id)
    assert busy.status_code == 409 and busy.get_json() == {'error': 'La mesa ya tiene una venta abierta',
                                                           'sale_id': first['id']}
    bad = client.post('/api/v1/pos/sales', headers=w, json=['no', 'es', 'objeto'])
    assert bad.status_code == 400
    missing = client.get('/api/v1/pos/sales/999', headers=w)
    assert missing.status_code == 404


def test_cancel_endpoints_require_anular(pos_app):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    _s, t1, _t = make_floor()
    w = auth_headers(client, waiter)
    sid = _open(client, w, t1.id).get_json()['id']
    assert client.post(f'/api/v1/pos/sales/{sid}/cancel', headers=w, json={'reason': 'x'}).status_code == 403


def test_list_open_sales(pos_app):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    _s, t1, t2 = make_floor()
    w = auth_headers(client, waiter)
    _open(client, w, t1.id)
    _open(client, w, t2.id)
    data = client.get('/api/v1/pos/sales', headers=w).get_json()
    assert len(data['sales']) == 2 and 'items' not in data['sales'][0]
