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


def test_employee_cannot_create_supply(client):
    headers = _headers(client, 'e@test.com', 'employee')
    response = client.post('/api/v1/supplies', headers=headers, json={'name': 'Harina', 'unit': 'kg'})
    assert response.status_code == 403
