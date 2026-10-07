import pytest

from app import create_app
from app.extensions import db
from app.models.user import User
from menu_fakes import FakeStorage


@pytest.fixture
def menu_app(monkeypatch):
    monkeypatch.setenv('MENU_PUBLIC_BASE_URL', 'https://cdn.test/menu')
    app = create_app('testing')
    app.extensions['menu_storage'] = FakeStorage()
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def menu_client(menu_app):
    return menu_app.test_client()


@pytest.fixture
def storage(menu_app):
    return menu_app.extensions['menu_storage']


def _login_headers(client, email, role):
    user = User(email=email, role=role, is_active=True)
    user.set_password('secret123')
    db.session.add(user)
    db.session.commit()
    response = client.post('/api/v1/auth/login', json={'email': email, 'password': 'secret123'})
    return {'Authorization': f"Bearer {response.get_json()['access_token']}"}


@pytest.fixture
def admin_headers(menu_client):
    return _login_headers(menu_client, 'menu-admin@test.com', 'admin')


@pytest.fixture
def employee_headers(menu_client):
    return _login_headers(menu_client, 'menu-employee@test.com', 'employee')
