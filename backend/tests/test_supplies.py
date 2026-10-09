import pytest

from app import create_app
from app.extensions import db
from app.models.user import User


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


def _headers(client, email, role):
    user = User(email=email, role=role, is_active=True)
    user.set_password('secret123')
    db.session.add(user)
    db.session.commit()
    token = client.post('/api/v1/auth/login', json={'email': email, 'password': 'secret123'}).get_json()['token']
    return {'Authorization': f'Bearer {token}'}


def test_admin_creates_and_lists_supply(client):
    headers = _headers(client, 'a@test.com', 'admin')
    created = client.post('/api/v1/supplies', headers=headers,
                          json={'name': 'Harina', 'unit': 'kg', 'stock_quantity': 25, 'min_stock': 5})
    assert created.status_code in (200, 201), created.get_json()
    listed = client.get('/api/v1/supplies', headers=headers)
    assert listed.status_code == 200
    assert 'Harina' in str(listed.get_json())


def test_supply_rejects_bad_input(client):
    headers = _headers(client, 'a@test.com', 'admin')
    for payload in ({'name': 'A', 'unit': 'kg', 'stock_quantity': 'abc'},
                    {'name': 'A', 'unit': 'kg', 'stock_quantity': -1},
                    {'name': 'A', 'unit': 'kg', 'min_stock': 'NaN'},
                    {'name': 'A', 'unit': 'kg', 'stock_quantity': 10000000},
                    {'name': 5, 'unit': 'kg'},
                    {'name': 'A', 'unit': 'u' * 51},
                    {'name': 'x' * 201, 'unit': 'kg'},
                    {'name': 'A'}):
        response = client.post('/api/v1/supplies', headers=headers, json=payload)
        assert response.status_code == 400, payload
    assert client.post('/api/v1/supplies', headers=headers, json=[1]).status_code == 400


def test_update_supply_rejects_bad_numbers(client):
    headers = _headers(client, 'a@test.com', 'admin')
    created = client.post('/api/v1/supplies', headers=headers, json={'name': 'Harina', 'unit': 'kg'}).get_json()
    for payload in ({'stock_quantity': 'abc'}, {'min_stock': -2}, {'unit': 7}, {'name': 3}):
        response = client.put(f"/api/v1/supplies/{created['id']}", headers=headers, json=payload)
        assert response.status_code == 400, payload


def test_add_supply_price_validation(client):
    headers = _headers(client, 'a@test.com', 'admin')
    created = client.post('/api/v1/supplies', headers=headers, json={'name': 'Harina', 'unit': 'kg'}).get_json()
    url = f"/api/v1/supplies/{created['id']}/prices"
    for payload in ({'price': 'abc'}, {'price': -1}, {'price': 5, 'recorded_at': 'ayer'},
                    {'price': 5, 'supplier': 's' * 500}):
        assert client.post(url, headers=headers, json=payload).status_code == 400, payload
    assert client.post(url, headers=headers, json={'price': 5}).status_code == 201


def test_list_supplies_caps_per_page(client):
    headers = _headers(client, 'a@test.com', 'admin')
    assert client.get('/api/v1/supplies?per_page=99999', headers=headers).get_json()['per_page'] == 200


def test_employee_cannot_create_supply(client):
    headers = _headers(client, 'e@test.com', 'employee')
    response = client.post('/api/v1/supplies', headers=headers, json={'name': 'Harina', 'unit': 'kg'})
    assert response.status_code == 403
