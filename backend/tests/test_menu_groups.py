from app.extensions import db
from app.models.menu import MenuCategory, MenuGroup
from menu_fakes import make_category


def test_group_crud_and_reorder(menu_client, admin_headers):
    a = menu_client.post('/api/v1/menu/groups', json={'name': 'Desayuno'}, headers=admin_headers).get_json()
    b = menu_client.post('/api/v1/menu/groups', json={'name': 'Almuerzos'}, headers=admin_headers).get_json()
    assert (a['slug'], a['sort_order'], b['sort_order']) == ('desayuno', 0, 1)
    assert menu_client.post('/api/v1/menu/groups', json={'name': ' '}, headers=admin_headers).status_code == 400

    renamed = menu_client.put(f"/api/v1/menu/groups/{a['id']}", json={'name': 'Desayuno y merienda'}, headers=admin_headers).get_json()
    assert renamed['slug'] == 'desayuno-y-merienda'

    assert menu_client.put('/api/v1/menu/groups/reorder', json={'ids': [b['id'], a['id']]}, headers=admin_headers).status_code == 200
    groups = menu_client.get('/api/v1/menu', headers=admin_headers).get_json()['groups']
    assert [g['name'] for g in groups] == ['Almuerzos', 'Desayuno y merienda']
    assert menu_client.put('/api/v1/menu/groups/reorder', json={'ids': [a['id']]}, headers=admin_headers).status_code == 400


def test_delete_group_ungroups_categories(menu_client, admin_headers):
    group = menu_client.post('/api/v1/menu/groups', json={'name': 'Bebidas'}, headers=admin_headers).get_json()
    category = make_category('Licuados')
    menu_client.put(f'/api/v1/menu/categories/{category.id}', json={'group_id': group['id']}, headers=admin_headers)
    assert menu_client.delete(f"/api/v1/menu/groups/{group['id']}", headers=admin_headers).status_code == 200
    assert db.session.get(MenuCategory, category.id).group_id is None


def test_update_category_fields(menu_client, admin_headers):
    group = menu_client.post('/api/v1/menu/groups', json={'name': 'Bebidas'}, headers=admin_headers).get_json()
    category = make_category('Licuados', '7')
    data = menu_client.put(f'/api/v1/menu/categories/{category.id}', json={
        'group_id': group['id'], 'show_title': False, 'is_visible': False, 'description': 'Con leche o agua',
    }, headers=admin_headers).get_json()
    assert (data['group_id'], data['show_title'], data['is_visible'], data['description']) == (group['id'], False, False, 'Con leche o agua')
    assert data['sort_order'] == 0  # al final del grupo nuevo

    assert menu_client.put(f'/api/v1/menu/categories/{category.id}', json={'name': 'Otro'}, headers=admin_headers).status_code == 400
    assert menu_client.put(f'/api/v1/menu/categories/{category.id}', json={'group_id': 999}, headers=admin_headers).status_code == 400
    assert menu_client.put(f'/api/v1/menu/categories/{category.id}', json={'group_id': None}, headers=admin_headers).get_json()['group_id'] is None


def test_reorder_categories_within_group(menu_client, admin_headers):
    a = make_category('A', '1')
    b = make_category('B', '2')
    ok = menu_client.put('/api/v1/menu/categories/reorder', json={'group_id': None, 'ids': [b.id, a.id]}, headers=admin_headers)
    assert ok.status_code == 200
    assert [c.name for c in MenuCategory.query.order_by(MenuCategory.sort_order)] == ['B', 'A']
    assert menu_client.put('/api/v1/menu/categories/reorder', json={'group_id': None, 'ids': [a.id]}, headers=admin_headers).status_code == 400


def test_categories_cannot_be_created_and_only_legacy_empty_can_be_deleted(menu_client, admin_headers):
    assert menu_client.post('/api/v1/menu/categories', json={'name': 'X'}, headers=admin_headers).status_code in (404, 405)
    fudo_cat = make_category('Fudo', '1')
    legacy = make_category('Manual', None)
    assert menu_client.delete(f'/api/v1/menu/categories/{fudo_cat.id}', headers=admin_headers).status_code == 409
    assert menu_client.delete(f'/api/v1/menu/categories/{legacy.id}', headers=admin_headers).status_code == 200
