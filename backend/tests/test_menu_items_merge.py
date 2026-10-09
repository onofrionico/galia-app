from datetime import datetime
from decimal import Decimal

from app.extensions import db
from app.models.menu import FudoProduct, MenuItem
from app.services.menu_sync_service import sync_fudo_products
from menu_fakes import FakeFudoClient, fudo_category, fudo_product, make_category

CATS = [fudo_category(1, 'Tortas'), fudo_category(2, 'Cafés')]


def _sync(*products):
    sync_fudo_products(FakeFudoClient(products=list(products), categories=CATS))


def test_merge_moves_variants_and_deletes_source(menu_client, admin_headers):
    _sync(fudo_product(1, 'Torta Galia porción', 11200), fudo_product(2, 'Torta Galia entera', 12600))
    target = MenuItem.query.filter_by(name='Torta Galia porción').one()
    source = MenuItem.query.filter_by(name='Torta Galia entera').one()

    response = menu_client.post(f'/api/v1/menu/items/{target.id}/merge', json={'source_item_id': source.id}, headers=admin_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert [v['fudo_product_id'] for v in data['variants']] == ['1', '2']
    assert data['reviewed'] is True
    assert db.session.get(MenuItem, source.id) is None

    assert menu_client.post(f'/api/v1/menu/items/{target.id}/merge', json={'source_item_id': target.id}, headers=admin_headers).status_code == 400
    assert menu_client.post(f'/api/v1/menu/items/{target.id}/merge', json={'source_item_id': 999}, headers=admin_headers).status_code == 400


def test_ignore_deletes_item_and_marks_products(menu_client, admin_headers):
    _sync(fudo_product(1, 'Envío', 500))
    item = MenuItem.query.one()
    assert menu_client.post(f'/api/v1/menu/items/{item.id}/ignore', headers=admin_headers).status_code == 200
    assert MenuItem.query.count() == 0
    assert db.session.get(FudoProduct, '1').ignored is True
    _sync(fudo_product(1, 'Envío', 500))
    assert MenuItem.query.count() == 0


def test_update_marks_reviewed_and_ignores_category_for_linked_items(menu_client, admin_headers):
    _sync(fudo_product(1, 'Latte', 6900, category_id='2'))
    item = MenuItem.query.one()
    other = make_category('Manual', None)
    data = menu_client.put(f'/api/v1/menu/items/{item.id}', json={'is_visible': True, 'category_id': other.id}, headers=admin_headers).get_json()
    assert data['reviewed'] is True and data['is_visible'] is True
    assert db.session.get(MenuItem, item.id).category.fudo_category_id == '2'


def test_create_item_only_for_manual_prices(menu_client, admin_headers):
    _sync(fudo_product(1, 'Latte', 6900))
    category = make_category('Extras', None)
    linked = menu_client.post('/api/v1/menu/items', json={'category_id': category.id, 'name': 'X', 'variants': [{'fudo_product_id': '1'}]}, headers=admin_headers)
    assert linked.status_code == 400
    manual = menu_client.post('/api/v1/menu/items', json={'category_id': category.id, 'name': 'Agua', 'variants': [{'label': 'Sin gas', 'price': 2900}]}, headers=admin_headers)
    assert manual.status_code == 201 and manual.get_json()['reviewed'] is True


def test_inbox_lists_new_items_and_alerts(menu_client, admin_headers):
    _sync(fudo_product(1, 'Latte', 1, category_id='1'), fudo_product(2, 'Moka', 1, category_id='2'))
    MenuItem.query.filter_by(name='Moka').one().reviewed_at = datetime.utcnow()
    db.session.commit()
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'Latte', 1, category_id='1')], categories=[fudo_category(1, 'Tortas')]))
    data = menu_client.get('/api/v1/menu/inbox', headers=admin_headers).get_json()
    assert [i['name'] for i in data['new_items']] == ['Latte']
    assert {a['type'] for a in data['alerts']} == {'variant', 'category'}
    status = menu_client.get('/api/v1/menu', headers=admin_headers).get_json()['status']
    assert status['new_count'] == 1 and status['alerts_count'] == 2


def test_merge_keeps_visible_content(menu_client, admin_headers):
    from app.models.menu import MenuTag
    _sync(fudo_product(1, 'Torta A', 100), fudo_product(2, 'Torta B', 200))
    target = MenuItem.query.filter_by(name='Torta A').one()
    source = MenuItem.query.filter_by(name='Torta B').one()
    tag = MenuTag(name='Vegano', slug='vegano')
    db.session.add(tag)
    source.is_visible = True
    source.image_key = 'menu/b.jpg'
    source.tags = [tag]
    target.is_visible = False
    db.session.commit()

    data = menu_client.post(f'/api/v1/menu/items/{target.id}/merge', json={'source_item_id': source.id}, headers=admin_headers).get_json()
    assert data['is_visible'] is True
    assert data['image_key'] == 'menu/b.jpg'
    assert data['tag_ids'] == [tag.id]


def test_linked_item_ignores_category_change_and_keeps_order(menu_client, admin_headers):
    _sync(fudo_product(1, 'Latte', 6900, category_id='2'))
    item = MenuItem.query.one()
    before = (item.category_id, item.sort_order)
    other = make_category('Manual', None)
    data = menu_client.put(f'/api/v1/menu/items/{item.id}', json={'category_id': other.id}, headers=admin_headers).get_json()
    assert (data['category_id'], data['sort_order']) == before
