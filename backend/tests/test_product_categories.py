import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.product_category import ProductCategory
import json


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_user(app):
    with app.app_context():
        user = User(email='admin@test.com', role='admin', is_active=True)
        user.set_password('admin123')
        db.session.add(user)
        db.session.commit()
        return user


def get_auth_token(client, email, password):
    response = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    return json.loads(response.data).get('token')


def test_create_category(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    response = client.post(
        '/api/v1/product-categories',
        json={'name': 'Cafés', 'description': 'Bebidas calientes', 'color': '#16a34a', 'icon': '☕'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == 'Cafés'
    assert data['is_active'] == True


def test_create_category_missing_name(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    response = client.post(
        '/api/v1/product-categories',
        json={'description': 'Sin nombre'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400


def test_create_category_duplicate_name(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    client.post(
        '/api/v1/product-categories',
        json={'name': 'Cafés'},
        headers={'Authorization': f'Bearer {token}'}
    )
    response = client.post(
        '/api/v1/product-categories',
        json={'name': 'Cafés'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 409


def test_list_categories(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    client.post(
        '/api/v1/product-categories',
        json={'name': 'Cafés'},
        headers={'Authorization': f'Bearer {token}'}
    )
    client.post(
        '/api/v1/product-categories',
        json={'name': 'Panadería'},
        headers={'Authorization': f'Bearer {token}'}
    )
    response = client.get('/api/v1/product-categories', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total'] == 2


def test_list_categories_exclude_inactive(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    response = client.post(
        '/api/v1/product-categories',
        json={'name': 'Cafés'},
        headers={'Authorization': f'Bearer {token}'}
    )
    cat_id = json.loads(response.data)['id']
    client.delete(f'/api/v1/product-categories/{cat_id}', headers={'Authorization': f'Bearer {token}'})

    response = client.get('/api/v1/product-categories', headers={'Authorization': f'Bearer {token}'})
    data = json.loads(response.data)
    assert data['total'] == 0


def test_get_category(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    create_resp = client.post(
        '/api/v1/product-categories',
        json={'name': 'Cafés', 'color': '#16a34a'},
        headers={'Authorization': f'Bearer {token}'}
    )
    cat_id = json.loads(create_resp.data)['id']

    response = client.get(f'/api/v1/product-categories/{cat_id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Cafés'
    assert data['color'] == '#16a34a'


def test_update_category(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    create_resp = client.post(
        '/api/v1/product-categories',
        json={'name': 'Cafés'},
        headers={'Authorization': f'Bearer {token}'}
    )
    cat_id = json.loads(create_resp.data)['id']

    response = client.put(
        f'/api/v1/product-categories/{cat_id}',
        json={'name': 'Cafés Premium', 'color': '#fbbf24'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Cafés Premium'
    assert data['color'] == '#fbbf24'


def test_delete_category(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    create_resp = client.post(
        '/api/v1/product-categories',
        json={'name': 'Cafés'},
        headers={'Authorization': f'Bearer {token}'}
    )
    cat_id = json.loads(create_resp.data)['id']

    response = client.delete(f'/api/v1/product-categories/{cat_id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200

    # After deletion, the category is inactive but still exists
    response = client.get(f'/api/v1/product-categories/{cat_id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['is_active'] == False
