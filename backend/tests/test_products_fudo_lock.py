from decimal import Decimal

from app.extensions import db
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_variant import ProductVariant
from app.services import menu_sync_service
from menu_fakes import FakeFudoClient, fudo_category, fudo_product


def _linked(products=None):
    menu_sync_service.sync_fudo_products(FakeFudoClient(
        products=products or [fudo_product(1, 'Latte', 6500)], categories=[fudo_category(1, 'Cafés')]))
    variant = ProductVariant.query.filter_by(fudo_product_id='1').one()
    return db.session.get(Product, variant.product_id), variant


def test_get_product_reports_locked_fields(menu_client, admin_headers):
    product, _ = _linked()
    data = menu_client.get(f'/api/v1/products/{product.id}', headers=admin_headers).get_json()

    assert data['fudo_linked'] is True
    assert data['fudo_locked_fields'] == ['name', 'category_id', 'is_active']
    assert data['fudo_alerts'] == 0
    assert data['variants'][0]['fudo_product_id'] == '1'


def test_list_reports_fudo_fields(menu_client, admin_headers):
    _linked()
    data = menu_client.get('/api/v1/products', headers=admin_headers).get_json()

    assert data['products'][0]['fudo_linked'] is True


def test_update_linked_product_locked_fields_is_409(menu_client, admin_headers):
    product, _ = _linked()
    other = ProductCategory(name='Otra')
    db.session.add(other)
    db.session.commit()
    url = f'/api/v1/products/{product.id}'

    for body in ({'name': 'Otro'}, {'category_id': other.id}, {'is_active': False}):
        response = menu_client.put(url, json=body, headers=admin_headers)
        assert response.status_code == 409, body
        assert response.get_json()['error'] == 'Este dato se edita en Fudo'
    assert product.name == 'Latte'


def test_update_linked_product_with_same_values_is_ok(menu_client, admin_headers):
    product, _ = _linked()
    response = menu_client.put(f'/api/v1/products/{product.id}', json={
        'name': ' Latte ', 'category_id': product.category_id, 'description': 'Rico', 'image_url': '',
        'has_recipe': True, 'track_stock': True,
    }, headers=admin_headers)

    assert response.status_code == 200
    assert response.get_json()['description'] == 'Rico'


def test_grouped_product_name_is_editable(menu_client, admin_headers):
    product, _ = _linked([fudo_product(1, 'Café chico', 3000), fudo_product(2, 'Café grande', 3500)])
    ProductVariant.query.filter_by(fudo_product_id='2').one().product_id = product.id
    db.session.commit()

    data = menu_client.get(f'/api/v1/products/{product.id}', headers=admin_headers).get_json()
    assert data['fudo_locked_fields'] == ['category_id', 'is_active']
    response = menu_client.put(f'/api/v1/products/{product.id}', json={'name': 'Café'}, headers=admin_headers)
    assert response.status_code == 200


def test_delete_linked_product_is_409(menu_client, admin_headers):
    product, _ = _linked()
    response = menu_client.delete(f'/api/v1/products/{product.id}', headers=admin_headers)

    assert response.status_code == 409
    assert product.is_active is True


def test_update_linked_variant_locked_fields_is_409(menu_client, admin_headers):
    product, variant = _linked()
    url = f'/api/v1/products/{product.id}/variants/{variant.id}'

    for body in ({'name': 'Otro'}, {'price': 1}, {'is_active': False}):
        assert menu_client.put(url, json=body, headers=admin_headers).status_code == 409, body


def test_update_linked_variant_stock_is_ok(menu_client, admin_headers):
    product, variant = _linked()
    response = menu_client.put(f'/api/v1/products/{product.id}/variants/{variant.id}',
                               json={'stock_quantity': 5, 'min_stock': 1}, headers=admin_headers)

    assert response.status_code == 200
    assert Decimal(str(variant.stock_quantity)) == Decimal('5')


def test_update_linked_variant_same_price_as_float_is_ok(menu_client, admin_headers):
    product, variant = _linked()
    response = menu_client.put(f'/api/v1/products/{product.id}/variants/{variant.id}',
                               json={'price': 6500.0, 'name': 'Latte'}, headers=admin_headers)

    assert response.status_code == 200


def test_delete_linked_variant_is_409(menu_client, admin_headers):
    product, variant = _linked()
    response = menu_client.delete(f'/api/v1/products/{product.id}/variants/{variant.id}', headers=admin_headers)

    assert response.status_code == 409
    assert variant.is_active is True


def test_manual_variant_on_linked_product_is_editable(menu_client, admin_headers):
    product, _ = _linked()
    created = menu_client.post(f'/api/v1/products/{product.id}/variants',
                               json={'name': 'Extra shot', 'price': 800}, headers=admin_headers)
    assert created.status_code == 201
    variant_id = created.get_json()['id']

    response = menu_client.put(f'/api/v1/products/{product.id}/variants/{variant_id}',
                               json={'price': 900}, headers=admin_headers)
    assert response.status_code == 200
    assert menu_client.delete(f'/api/v1/products/{product.id}/variants/{variant_id}',
                              headers=admin_headers).status_code == 200


def test_linked_category_locks_name_and_active(menu_client, admin_headers):
    product, _ = _linked()
    url = f'/api/v1/product-categories/{product.category_id}'

    assert menu_client.put(url, json={'name': 'Otra'}, headers=admin_headers).status_code == 409
    assert menu_client.put(url, json={'is_active': False}, headers=admin_headers).status_code == 409
    assert menu_client.delete(url, headers=admin_headers).status_code == 409
    response = menu_client.put(url, json={'name': 'Cafés', 'color': '#00ff00', 'icon': 'C', 'description': 'x'},
                               headers=admin_headers)
    assert response.status_code == 200
    assert response.get_json()['color'] == '#00ff00'


def test_fudo_alerts_filter(menu_client, admin_headers):
    _linked([fudo_product(1, 'Latte', 6500), fudo_product(2, 'Té', 3000)])
    menu_sync_service.sync_fudo_products(FakeFudoClient(
        products=[fudo_product(1, 'Latte', 6500)], categories=[fudo_category(1, 'Cafés')]))

    data = menu_client.get('/api/v1/products?fudo_alerts=true', headers=admin_headers).get_json()

    assert [p['name'] for p in data['products']] == ['Té']
    assert data['products'][0]['fudo_alerts'] == 1
