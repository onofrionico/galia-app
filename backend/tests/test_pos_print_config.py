from collections import defaultdict

from app.extensions import db
from app.models import ProductCategory
from app.services.product_sync_service import sync_product_categories
from pos_helpers import auth_headers, make_user, pos_app  # noqa: F401
from print_helpers import make_station


def test_category_station_via_api(pos_app):
    client = pos_app.test_client()
    headers = auth_headers(client, make_user('prod@test.com', modules=('Products',)))
    cocina = make_station('Cocina')
    created = client.post('/api/v1/product-categories', json={'name': 'Platos', 'station_id': cocina.id},
                          headers=headers)
    assert created.status_code == 201 and created.get_json()['station_id'] == cocina.id
    category_id = created.get_json()['id']
    cleared = client.put(f'/api/v1/product-categories/{category_id}', json={'station_id': None}, headers=headers)
    assert cleared.status_code == 200 and cleared.get_json()['station_id'] is None
    assert client.put(f'/api/v1/product-categories/{category_id}', json={'station_id': 999},
                      headers=headers).status_code == 400
    assert client.put(f'/api/v1/product-categories/{category_id}', json={'station_id': 'x'},
                      headers=headers).status_code == 400


def test_inactive_station_is_rejected(pos_app):
    client = pos_app.test_client()
    headers = auth_headers(client, make_user('prod@test.com', modules=('Products',)))
    station = make_station('Barra')
    station.is_active = False
    db.session.commit()
    response = client.post('/api/v1/product-categories', json={'name': 'Bebidas', 'station_id': station.id},
                           headers=headers)
    assert response.status_code == 400


def test_station_can_be_set_on_fudo_category_and_sync_keeps_it(pos_app):
    client = pos_app.test_client()
    headers = auth_headers(client, make_user('prod@test.com', modules=('Products',)))
    cocina = make_station('Cocina')
    category = ProductCategory(name='Platos', fudo_category_id='7')
    db.session.add(category)
    db.session.commit()
    response = client.put(f'/api/v1/product-categories/{category.id}', json={'station_id': cocina.id},
                          headers=headers)
    assert response.status_code == 200
    sync_product_categories([{'id': 7, 'attributes': {'name': 'Platos calientes'}}], defaultdict(int))
    db.session.commit()
    db.session.refresh(category)
    assert category.name == 'Platos calientes' and category.station_id == cocina.id
