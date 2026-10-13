from app.extensions import db
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.services import menu_sync_service
from menu_fakes import FakeFudoClient, fudo_category, fudo_product

CATEGORIES = [fudo_category(1, 'Cafés')]
PRODUCTS = [fudo_product(1, 'Café chico', 3000), fudo_product(2, 'Café grande', 3500)]


def _sync(products=PRODUCTS):
    menu_sync_service.sync_fudo_products(FakeFudoClient(products=products, categories=CATEGORIES))


def _product_of(fudo_id):
    variant = ProductVariant.query.filter_by(fudo_product_id=str(fudo_id)).one()
    return db.session.get(Product, variant.product_id)


def test_sync_endpoint(menu_client, admin_headers, monkeypatch):
    monkeypatch.setattr('app.routes.products.FudoClient', lambda: FakeFudoClient(products=PRODUCTS, categories=CATEGORIES))
    response = menu_client.post('/api/v1/products/sync', headers=admin_headers)

    assert response.status_code == 200
    assert response.get_json()['catalog']['products_created'] == 2


def test_sync_endpoint_reports_fudo_errors(menu_client, admin_headers, monkeypatch):
    def broken_client():
        raise RuntimeError('credenciales inválidas')
    monkeypatch.setattr('app.routes.products.FudoClient', broken_client)
    response = menu_client.post('/api/v1/products/sync', headers=admin_headers)

    assert response.status_code == 502
    assert response.get_json()['error'] == 'Error sincronizando con Fudo. Revisá las credenciales o probá más tarde.'


def test_sync_endpoint_requires_products_module(menu_client, employee_headers):
    assert menu_client.post('/api/v1/products/sync', headers=employee_headers).status_code == 403


def test_fudo_candidates(menu_client, admin_headers):
    _sync()
    data = menu_client.get('/api/v1/products/fudo-candidates', headers=admin_headers).get_json()

    by_id = {p['fudo_id']: p for p in data['products']}
    assert by_id['1']['product_id'] == _product_of(1).id
    assert by_id['1']['product_name'] == 'Café chico'
    assert by_id['2']['price'] == 3500


def test_attach_moves_variant_and_deactivates_empty_source(menu_client, admin_headers):
    _sync()
    target, source = _product_of(1), _product_of(2)

    response = menu_client.post(f'/api/v1/products/{target.id}/variants/attach',
                                json={'fudo_product_id': '2'}, headers=admin_headers)

    assert response.status_code == 200
    body = response.get_json()
    assert sorted(v['fudo_product_id'] for v in body['variants']) == ['1', '2']
    assert body['fudo_locked_fields'] == ['category_id', 'is_active']
    assert source.is_active is False


def test_sync_after_attach_keeps_source_inactive(menu_client, admin_headers):
    _sync()
    target, source = _product_of(1), _product_of(2)
    menu_client.post(f'/api/v1/products/{target.id}/variants/attach',
                     json={'fudo_product_id': '2'}, headers=admin_headers)
    menu_client.put(f'/api/v1/products/{target.id}', json={'name': 'Café'}, headers=admin_headers)

    _sync()

    assert source.is_active is False
    assert target.name == 'Café'
    assert ProductVariant.query.filter_by(fudo_product_id='2').one().product_id == target.id
    assert Product.query.count() == 2


def test_attach_into_inactive_product_reactivates_it(menu_client, admin_headers):
    _sync([fudo_product(1, 'Café chico', 3000)])
    old = _product_of(1)
    _sync([fudo_product(7, 'Café chico nuevo', 3100)])
    assert old.is_active is False

    response = menu_client.post(f'/api/v1/products/{old.id}/variants/attach',
                                json={'fudo_product_id': '7'}, headers=admin_headers)

    assert response.status_code == 200
    assert response.get_json()['is_active'] is True
    assert old.is_active is True


def test_delete_missing_variant_clears_the_alert(menu_client, admin_headers):
    _sync([fudo_product(1, 'Café chico', 3000), fudo_product(2, 'Café grande', 3500)])
    product = _product_of(1)
    menu_client.post(f'/api/v1/products/{product.id}/variants/attach',
                     json={'fudo_product_id': '2'}, headers=admin_headers)
    _sync([fudo_product(2, 'Café grande', 3500)])
    missing = ProductVariant.query.filter_by(fudo_product_id='1').one()

    response = menu_client.delete(f'/api/v1/products/{product.id}/variants/{missing.id}', headers=admin_headers)

    assert response.status_code == 200
    assert missing.fudo_product_id is None and missing.fudo_status is None
    assert missing.is_active is False
    data = menu_client.get(f'/api/v1/products/{product.id}', headers=admin_headers).get_json()
    assert data['fudo_alerts'] == 0
    ok = ProductVariant.query.filter_by(fudo_product_id='2').one()
    assert menu_client.delete(f'/api/v1/products/{product.id}/variants/{ok.id}',
                              headers=admin_headers).status_code == 409


def test_attach_creates_variant_for_unlinked_fudo_product(menu_client, admin_headers):
    _sync([fudo_product(1, 'Café chico', 3000), fudo_product(3, 'Café XL', 4000, active=False)])
    target = _product_of(1)

    response = menu_client.post(f'/api/v1/products/{target.id}/variants/attach',
                                json={'fudo_product_id': '3'}, headers=admin_headers)

    assert response.status_code == 200
    variant = ProductVariant.query.filter_by(fudo_product_id='3').one()
    assert variant.product_id == target.id
    assert variant.is_active is False
    assert variant.fudo_status == 'inactive'


def test_attach_errors(menu_client, admin_headers):
    _sync()
    target = _product_of(1)
    url = f'/api/v1/products/{target.id}/variants/attach'

    assert menu_client.post(url, json={}, headers=admin_headers).status_code == 400
    assert menu_client.post(url, json={'fudo_product_id': 2}, headers=admin_headers).status_code == 400
    assert menu_client.post(url, json={'fudo_product_id': '999'}, headers=admin_headers).status_code == 404
    assert menu_client.post(url, json={'fudo_product_id': '1'}, headers=admin_headers).status_code == 409
    assert menu_client.post('/api/v1/products/9999/variants/attach', json={'fudo_product_id': '2'},
                            headers=admin_headers).status_code == 404


def test_detach_creates_product(menu_client, admin_headers):
    _sync()
    target = _product_of(1)
    menu_client.post(f'/api/v1/products/{target.id}/variants/attach',
                     json={'fudo_product_id': '2'}, headers=admin_headers)
    variant = ProductVariant.query.filter_by(fudo_product_id='2').one()

    response = menu_client.post(f'/api/v1/products/{target.id}/variants/{variant.id}/detach', headers=admin_headers)

    assert response.status_code == 201
    body = response.get_json()
    assert body['name'] == 'Café grande'
    assert body['category_id'] == target.category_id
    assert variant.product_id == body['id']
    assert target.is_active is True


def test_detach_errors(menu_client, admin_headers):
    _sync()
    target = _product_of(1)
    only = ProductVariant.query.filter_by(fudo_product_id='1').one()
    manual = menu_client.post(f'/api/v1/products/{target.id}/variants', json={'name': 'Extra', 'price': 100},
                              headers=admin_headers).get_json()

    assert menu_client.post(f'/api/v1/products/{target.id}/variants/{manual["id"]}/detach',
                            headers=admin_headers).status_code == 409
    db.session.delete(db.session.get(ProductVariant, manual['id']))
    db.session.commit()
    assert menu_client.post(f'/api/v1/products/{target.id}/variants/{only.id}/detach',
                            headers=admin_headers).status_code == 409
    assert menu_client.post(f'/api/v1/products/{target.id}/variants/9999/detach',
                            headers=admin_headers).status_code == 404
