from decimal import Decimal

from app.extensions import db
from app.models.menu import FudoProduct, MenuItem
from menu_fakes import make_category


def _create_category(client, headers, name='Cafés'):
    return make_category(name).to_dict()


def _create_item(client, headers, category_id, **overrides):
    payload = {'category_id': category_id, 'name': 'Latte', 'variants': [{'label': None, 'price': 6900}]}
    payload.update(overrides)
    return client.post('/api/v1/menu/items', json=payload, headers=headers)


def test_requires_admin(menu_client, employee_headers):
    assert menu_client.get('/api/v1/menu', headers=employee_headers).status_code == 403
    assert menu_client.get('/api/v1/menu').status_code == 401


def test_get_menu_tree_and_status(menu_client, admin_headers):
    category = _create_category(menu_client, admin_headers)
    _create_item(menu_client, admin_headers, category['id'])

    data = menu_client.get('/api/v1/menu', headers=admin_headers).get_json()

    assert data['categories'][0]['items'][0]['name'] == 'Latte'
    assert data['status'] == {
        'has_unpublished_changes': True,
        'last_published_at': None,
        'unassigned_count': 0,
        'alerts_count': 0,
    }


def test_cannot_delete_category_with_items(menu_client, admin_headers):
    category = _create_category(menu_client, admin_headers)
    _create_item(menu_client, admin_headers, category['id'])
    assert menu_client.delete(f"/api/v1/menu/categories/{category['id']}", headers=admin_headers).status_code == 409


def test_delete_empty_category(menu_client, admin_headers):
    category = _create_category(menu_client, admin_headers)
    assert menu_client.delete(f"/api/v1/menu/categories/{category['id']}", headers=admin_headers).status_code == 200


def test_reorder_categories(menu_client, admin_headers):
    a = _create_category(menu_client, admin_headers, 'A')
    b = _create_category(menu_client, admin_headers, 'B')
    response = menu_client.put('/api/v1/menu/categories/reorder', json={'ids': [b['id'], a['id']]}, headers=admin_headers)
    assert response.status_code == 200
    names = [c['name'] for c in menu_client.get('/api/v1/menu', headers=admin_headers).get_json()['categories']]
    assert names == ['B', 'A']


def test_reorder_rejects_incomplete_ids(menu_client, admin_headers):
    a = _create_category(menu_client, admin_headers, 'A')
    response = menu_client.put('/api/v1/menu/categories/reorder', json={'ids': [a['id'], 999]}, headers=admin_headers)
    assert response.status_code == 400


def test_create_item_with_manual_price(menu_client, admin_headers):
    category = _create_category(menu_client, admin_headers)
    response = _create_item(menu_client, admin_headers, category['id'], description='Con leche')
    data = response.get_json()
    assert response.status_code == 201
    assert data['variants'] == [{'id': data['variants'][0]['id'], 'label': None, 'fudo_product_id': None,
                                 'price': 6900.0, 'fudo_status': None, 'sort_order': 0}]


def test_create_item_validations(menu_client, admin_headers):
    category = _create_category(menu_client, admin_headers)
    assert _create_item(menu_client, admin_headers, category['id'], name='').status_code == 400
    assert _create_item(menu_client, admin_headers, 999).status_code == 400
    assert _create_item(menu_client, admin_headers, category['id'], variants=[]).status_code == 400
    assert _create_item(menu_client, admin_headers, category['id'], variants=[{'price': -1}]).status_code == 400
    assert _create_item(menu_client, admin_headers, category['id'], variants=[{'price': 'abc'}]).status_code == 400
    assert MenuItem.query.count() == 0


def test_linked_variant_uses_fudo_price(menu_client, admin_headers):
    db.session.add(FudoProduct(fudo_id='7', name='Latte', price=Decimal('7100'), is_active=True))
    db.session.commit()
    category = _create_category(menu_client, admin_headers)

    response = _create_item(menu_client, admin_headers, category['id'],
                            variants=[{'fudo_product_id': '7', 'price': 1}])

    variant = response.get_json()['variants'][0]
    assert (variant['price'], variant['fudo_product_id'], variant['fudo_status']) == (7100.0, '7', 'ok')


def test_fudo_product_cannot_be_linked_twice(menu_client, admin_headers):
    db.session.add(FudoProduct(fudo_id='7', name='Latte', price=Decimal('7100'), is_active=True))
    db.session.commit()
    category = _create_category(menu_client, admin_headers)
    _create_item(menu_client, admin_headers, category['id'], variants=[{'fudo_product_id': '7'}])

    response = _create_item(menu_client, admin_headers, category['id'], name='Otro', variants=[{'fudo_product_id': '7'}])
    assert response.status_code == 400
    assert 'ya está en otro ítem' in response.get_json()['error']


def test_unknown_fudo_product_is_rejected(menu_client, admin_headers):
    category = _create_category(menu_client, admin_headers)
    assert _create_item(menu_client, admin_headers, category['id'], variants=[{'fudo_product_id': '404'}]).status_code == 400


def test_update_item_can_keep_same_fudo_link(menu_client, admin_headers):
    db.session.add(FudoProduct(fudo_id='7', name='Latte', price=Decimal('7100'), is_active=True))
    db.session.commit()
    category = _create_category(menu_client, admin_headers)
    item = _create_item(menu_client, admin_headers, category['id'], variants=[{'fudo_product_id': '7'}]).get_json()

    response = menu_client.put(f"/api/v1/menu/items/{item['id']}", json={
        'name': 'Latte grande',
        'variants': [{'label': 'Grande', 'fudo_product_id': '7'}, {'label': 'Chico', 'price': 5000}],
    }, headers=admin_headers)

    data = response.get_json()
    assert response.status_code == 200
    assert data['name'] == 'Latte grande'
    assert [(v['label'], v['price']) for v in data['variants']] == [('Grande', 7100.0), ('Chico', 5000.0)]


def test_moving_item_to_other_category_appends_it(menu_client, admin_headers):
    a = _create_category(menu_client, admin_headers, 'A')
    b = _create_category(menu_client, admin_headers, 'B')
    _create_item(menu_client, admin_headers, b['id'], name='Existente')
    item = _create_item(menu_client, admin_headers, a['id']).get_json()

    data = menu_client.put(f"/api/v1/menu/items/{item['id']}", json={'category_id': b['id']}, headers=admin_headers).get_json()
    assert (data['category_id'], data['sort_order']) == (b['id'], 1)


def test_reorder_items(menu_client, admin_headers):
    category = _create_category(menu_client, admin_headers)
    first = _create_item(menu_client, admin_headers, category['id'], name='Uno').get_json()
    second = _create_item(menu_client, admin_headers, category['id'], name='Dos').get_json()

    response = menu_client.put(f"/api/v1/menu/categories/{category['id']}/items/reorder",
                               json={'ids': [second['id'], first['id']]}, headers=admin_headers)
    assert response.status_code == 200
    items = menu_client.get('/api/v1/menu', headers=admin_headers).get_json()['categories'][0]['items']
    assert [i['name'] for i in items] == ['Dos', 'Uno']


def test_delete_item(menu_client, admin_headers):
    category = _create_category(menu_client, admin_headers)
    item = _create_item(menu_client, admin_headers, category['id']).get_json()
    assert menu_client.delete(f"/api/v1/menu/items/{item['id']}", headers=admin_headers).status_code == 200
    assert MenuItem.query.count() == 0


def test_tags_crud_and_assignment(menu_client, admin_headers):
    created = menu_client.post('/api/v1/menu/tags', json={'name': 'Sin TACC', 'color': '#7FA34A'}, headers=admin_headers)
    tag = created.get_json()
    assert created.status_code == 201
    assert tag['slug'] == 'sin-tacc'

    assert menu_client.post('/api/v1/menu/tags', json={'name': 'X', 'color': 'rojo'}, headers=admin_headers).status_code == 400

    category = _create_category(menu_client, admin_headers)
    item = _create_item(menu_client, admin_headers, category['id'], tag_ids=[tag['id']]).get_json()
    assert item['tag_ids'] == [tag['id']]
    assert _create_item(menu_client, admin_headers, category['id'], tag_ids=[999]).status_code == 400

    updated = menu_client.put(f"/api/v1/menu/tags/{tag['id']}", json={'name': 'Apto celíacos'}, headers=admin_headers).get_json()
    assert updated['name'] == 'Apto celíacos'

    assert menu_client.delete(f"/api/v1/menu/tags/{tag['id']}", headers=admin_headers).status_code == 200
    assert MenuItem.query.get(item['id']).tags == []


def test_settings(menu_client, admin_headers):
    assert menu_client.get('/api/v1/menu/settings', headers=admin_headers).get_json() == {'footer_text': '', 'instagram': ''}
    response = menu_client.put('/api/v1/menu/settings',
                               json={'footer_text': '¡Que disfrutes!', 'instagram': '@galia', 'otro': 'x'},
                               headers=admin_headers)
    assert response.get_json() == {'footer_text': '¡Que disfrutes!', 'instagram': 'galia'}
