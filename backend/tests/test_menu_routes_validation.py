import pytest

from app.models.menu import MenuCategory, MenuItem, MenuTag
from menu_fakes import make_category


def _category(client, headers, name='Cafés'):
    return make_category(name).to_dict()


def _item(client, headers, category_id, **overrides):
    payload = {'category_id': category_id, 'name': 'Latte', 'variants': [{'price': 6900}]}
    payload.update(overrides)
    return client.post('/api/v1/menu/items', json=payload, headers=headers)


@pytest.mark.parametrize('bad_ids', [['2', '1'], [{}], [True, False], 'x', {'a': 1}])
def test_reorder_categories_rejects_bad_types(menu_client, admin_headers, bad_ids):
    _category(menu_client, admin_headers, 'A')
    _category(menu_client, admin_headers, 'B')
    response = menu_client.put('/api/v1/menu/categories/reorder', json={'ids': bad_ids}, headers=admin_headers)
    assert response.status_code == 400


def test_reorder_categories_requires_all_records(menu_client, admin_headers):
    _category(menu_client, admin_headers, 'A')
    b = _category(menu_client, admin_headers, 'B')
    response = menu_client.put('/api/v1/menu/categories/reorder', json={'ids': [b['id']]}, headers=admin_headers)
    assert response.status_code == 400
    names = [c.name for c in MenuCategory.query.order_by(MenuCategory.sort_order).all()]
    assert names == ['A', 'B']


def test_reorder_items_requires_all_items_of_category(menu_client, admin_headers):
    category = _category(menu_client, admin_headers)
    _item(menu_client, admin_headers, category['id'], name='Uno')
    second = _item(menu_client, admin_headers, category['id'], name='Dos').get_json()
    url = f"/api/v1/menu/categories/{category['id']}/items/reorder"
    assert menu_client.put(url, json={'ids': [second['id']]}, headers=admin_headers).status_code == 400
    assert menu_client.put(url, json={'ids': [str(second['id'])]}, headers=admin_headers).status_code == 400
    assert [i.name for i in MenuItem.query.order_by(MenuItem.sort_order).all()] == ['Uno', 'Dos']


@pytest.mark.parametrize('overrides', [
    {'tag_ids': 5},
    {'tag_ids': ['1']},
    {'tag_ids': [True]},
    {'variants': ['x']},
    {'variants': 'x'},
    {'name': 5},
    {'description': 5},
    {'variants': [{'label': 5, 'price': 1}]},
    {'category_id': 'abc'},
    {'category_id': True},
])
def test_create_item_rejects_wrong_types(menu_client, admin_headers, overrides):
    category = _category(menu_client, admin_headers)
    payload = {'category_id': category['id'], 'name': 'Latte', 'variants': [{'price': 6900}], **overrides}
    response = menu_client.post('/api/v1/menu/items', json=payload, headers=admin_headers)
    assert response.status_code == 400
    assert MenuItem.query.count() == 0


def test_update_item_rejects_wrong_types(menu_client, admin_headers):
    category = _category(menu_client, admin_headers)
    item = _item(menu_client, admin_headers, category['id']).get_json()
    url = f"/api/v1/menu/items/{item['id']}"
    for payload in ({'name': 5}, {'tag_ids': 5}, {'variants': ['x']}, {'category_id': 'abc'}):
        assert menu_client.put(url, json=payload, headers=admin_headers).status_code == 400
    assert MenuItem.query.get(item['id']).name == 'Latte'


def test_length_limits(menu_client, admin_headers):
    category = _category(menu_client, admin_headers)
    response = _item(menu_client, admin_headers, category['id'], name='x' * 201)
    assert response.status_code == 400
    assert 'máximo 200' in response.get_json()['error']
    assert _item(menu_client, admin_headers, category['id'], variants=[{'label': 'x' * 101, 'price': 1}]).status_code == 400
    assert _item(menu_client, admin_headers, category['id'], name='x' * 200).status_code == 201

    assert menu_client.post('/api/v1/menu/tags', json={'name': 'x' * 51}, headers=admin_headers).status_code == 400
    assert MenuTag.query.count() == 0


def test_price_upper_bound(menu_client, admin_headers):
    category = _category(menu_client, admin_headers)
    too_big = _item(menu_client, admin_headers, category['id'], variants=[{'price': 100000000}])
    assert too_big.status_code == 400
    assert too_big.get_json()['error'] == 'Precio inválido'
    assert _item(menu_client, admin_headers, category['id'], variants=[{'price': 99999999.99}]).status_code == 201


@pytest.mark.parametrize('color', ['#123456\n', 5, None, '#12345', ['#123456']])
def test_tag_color_strict(menu_client, admin_headers, color):
    response = menu_client.post('/api/v1/menu/tags', json={'name': 'X', 'color': color}, headers=admin_headers)
    assert response.status_code == 400
    assert MenuTag.query.count() == 0


@pytest.mark.parametrize('payload', [
    {'footer_text': 123},
    {'instagram': ['x']},
    {'footer_text': 'x' * 2001},
    {'instagram': 'x' * 101},
])
def test_settings_reject_invalid_values(menu_client, admin_headers, payload):
    response = menu_client.put('/api/v1/menu/settings', json=payload, headers=admin_headers)
    assert response.status_code == 400
    assert response.get_json()['error']


@pytest.mark.parametrize('raw,expected', [
    ('  @galia.cafe ', 'galia.cafe'),
    ('https://www.instagram.com/galia.cafe/?hl=es', 'galia.cafe'),
    ('instagram.com/galia.cafe', 'galia.cafe'),
    (None, ''),
])
def test_settings_normalize_instagram(menu_client, admin_headers, raw, expected):
    response = menu_client.put('/api/v1/menu/settings', json={'instagram': raw}, headers=admin_headers)
    assert response.status_code == 200
    assert response.get_json()['instagram'] == expected
