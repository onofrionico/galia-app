import io
import json
from decimal import Decimal

from PIL import Image

from app.extensions import db
from app.models.menu import FudoProduct, MenuCategory, MenuItem, MenuItemVariant
from menu_fakes import FakeFudoClient, fudo_product


def _item(fudo_id=None, status=None):
    category = MenuCategory(name='Cafés', slug='cafes')
    db.session.add(category)
    db.session.flush()
    item = MenuItem(category_id=category.id, name='Latte')
    item.variants = [MenuItemVariant(price=Decimal('6900'), fudo_product_id=fudo_id, fudo_status=status)]
    db.session.add(item)
    db.session.commit()
    return item


def _png():
    buffer = io.BytesIO()
    Image.new('RGB', (1200, 900), (10, 20, 30)).save(buffer, format='PNG')
    buffer.seek(0)
    return buffer


def test_upload_and_delete_item_image(menu_client, admin_headers, storage):
    item = _item()
    response = menu_client.post(f'/api/v1/menu/items/{item.id}/image',
                                data={'image': (_png(), 'latte.png')},
                                headers=admin_headers, content_type='multipart/form-data')
    data = response.get_json()
    assert response.status_code == 200
    assert data['image_key'] in storage.objects
    assert storage.objects[data['image_key']]['cache_control'] == 'public, max-age=31536000, immutable'
    assert data['image_url'] == f"https://cdn.test/menu/{data['image_key']}"

    deleted = menu_client.delete(f'/api/v1/menu/items/{item.id}/image', headers=admin_headers).get_json()
    assert deleted['image_key'] is None


def test_upload_rejects_invalid_file(menu_client, admin_headers):
    item = _item()
    response = menu_client.post(f'/api/v1/menu/items/{item.id}/image',
                                data={'image': (io.BytesIO(b'nope'), 'x.png')},
                                headers=admin_headers, content_type='multipart/form-data')
    assert response.status_code == 400
    assert menu_client.post(f'/api/v1/menu/items/{item.id}/image', headers=admin_headers).status_code == 400


def test_fudo_products_list_marks_linked_and_filters(menu_client, admin_headers):
    db.session.add_all([
        FudoProduct(fudo_id='1', name='Latte', price=1, is_active=True),
        FudoProduct(fudo_id='2', name='Moka', price=1, is_active=True),
        FudoProduct(fudo_id='3', name='Viejo', price=1, is_active=False),
    ])
    db.session.commit()
    _item(fudo_id='1', status='ok')

    products = menu_client.get('/api/v1/menu/fudo-products', headers=admin_headers).get_json()
    assert [(p['fudo_id'], p['linked']) for p in products] == [('1', True), ('2', False)]

    filtered = menu_client.get('/api/v1/menu/fudo-products?q=MOK', headers=admin_headers).get_json()
    assert [p['fudo_id'] for p in filtered] == ['2']

    unassigned = menu_client.get('/api/v1/menu/fudo-products?unassigned=true', headers=admin_headers).get_json()
    assert [p['fudo_id'] for p in unassigned] == ['2']


def test_ignore_fudo_product(menu_client, admin_headers):
    db.session.add(FudoProduct(fudo_id='2', name='Moka', price=1, is_active=True))
    db.session.commit()
    assert menu_client.post('/api/v1/menu/fudo-products/2/ignore', headers=admin_headers).status_code == 200
    assert db.session.get(FudoProduct, '2').ignored is True
    assert menu_client.post('/api/v1/menu/fudo-products/999/ignore', headers=admin_headers).status_code == 404


def test_inbox(menu_client, admin_headers):
    db.session.add(FudoProduct(fudo_id='2', name='Moka', price=1, is_active=True))
    db.session.commit()
    item = _item(fudo_id='9', status='missing')

    data = menu_client.get('/api/v1/menu/inbox', headers=admin_headers).get_json()
    assert [p['fudo_id'] for p in data['unassigned']] == ['2']
    alert = data['alerts'][0]
    assert (alert['item_id'], alert['item_name'], alert['fudo_status'], alert['fudo_name']) == (item.id, 'Latte', 'missing', None)


def test_sync_endpoint(menu_client, admin_headers, monkeypatch):
    monkeypatch.setattr('app.routes.menu.FudoClient', lambda: FakeFudoClient(products=[fudo_product(1, 'Latte', 6900)]))
    data = menu_client.post('/api/v1/menu/sync', headers=admin_headers).get_json()
    assert (data['products'], data['price_changes'], data['alerts']) == (1, 0, 0)
    assert data['status']['unassigned_count'] == 1


def test_sync_endpoint_reports_fudo_errors(menu_client, admin_headers, monkeypatch):
    def broken_client():
        raise ValueError('FUDO_API_KEY and FUDO_API_SECRET must be set')
    monkeypatch.setattr('app.routes.menu.FudoClient', broken_client)
    response = menu_client.post('/api/v1/menu/sync', headers=admin_headers)
    assert response.status_code == 502
    assert 'Fudo' in response.get_json()['error']


def test_publish_endpoint(menu_client, admin_headers, storage):
    _item()
    response = menu_client.post('/api/v1/menu/publish', headers=admin_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert data['status']['has_unpublished_changes'] is False
    assert json.loads(storage.objects['menu.json']['body'])['categories'][0]['items'][0]['name'] == 'Latte'


def test_upload_rejects_oversized_request(menu_client, admin_headers, storage):
    item = _item()
    response = menu_client.post(f'/api/v1/menu/items/{item.id}/image',
                                data={'image': (io.BytesIO(b'0' * (12 * 1024 * 1024)), 'big.png')},
                                headers=admin_headers, content_type='multipart/form-data')
    assert response.status_code == 400
    assert response.get_json()['error'] == 'La imagen supera los 10 MB'
    assert storage.objects == {}


def test_upload_storage_failure_returns_502(menu_client, admin_headers, storage, monkeypatch):
    item = _item()

    def broken_put(*args, **kwargs):
        raise RuntimeError('s3 down: secret-detail')
    monkeypatch.setattr(storage, 'put', broken_put)
    response = menu_client.post(f'/api/v1/menu/items/{item.id}/image',
                                data={'image': (_png(), 'latte.png')},
                                headers=admin_headers, content_type='multipart/form-data')
    assert response.status_code == 502
    assert 'secret-detail' not in response.get_json()['error']
    assert db.session.get(MenuItem, item.id).image_key is None


def test_sync_and_publish_hide_internal_errors(menu_client, admin_headers, monkeypatch):
    def broken_client():
        raise ValueError('secret-detail')
    monkeypatch.setattr('app.routes.menu.FudoClient', broken_client)
    assert 'secret-detail' not in menu_client.post('/api/v1/menu/sync', headers=admin_headers).get_json()['error']

    def broken_publish(storage):
        raise RuntimeError('secret-detail')
    monkeypatch.setattr('app.routes.menu.menu_publish_service.publish', broken_publish)
    response = menu_client.post('/api/v1/menu/publish', headers=admin_headers)
    assert response.status_code == 502
    assert 'secret-detail' not in response.get_json()['error']
