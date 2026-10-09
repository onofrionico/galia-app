import pytest

from app import create_app
from app.extensions import db
from app.models import Module, RolePermission, User
from app.utils.permissions import check_module_access


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        for name in ('Products', 'MySchedule'):
            db.session.add(Module(name=name, display_name=name, is_active=True))
        db.session.commit()
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


def _module_id(name):
    return Module.query.filter_by(name=name).first().id


def test_admin_my_modules_lists_all_active(client):
    headers = _headers(client, 'a@test.com', 'admin')
    response = client.get('/api/v1/permissions/modules/my-modules', headers=headers)
    assert response.status_code == 200
    assert sorted(m['name'] for m in response.get_json()['modules']) == ['MySchedule', 'Products']


def test_employee_my_modules_lists_only_granted(client):
    db.session.add(RolePermission(role='employee', module_id=_module_id('MySchedule'), is_granted=True))
    db.session.commit()
    headers = _headers(client, 'e@test.com', 'employee')
    response = client.get('/api/v1/permissions/modules/my-modules', headers=headers)
    assert [m['name'] for m in response.get_json()['modules']] == ['MySchedule']


def test_employee_cannot_list_catalog(client):
    headers = _headers(client, 'e@test.com', 'employee')
    assert client.get('/api/v1/permissions/modules', headers=headers).status_code == 403


def test_admin_grants_module_to_role(client):
    headers = _headers(client, 'a@test.com', 'admin')
    products_id = _module_id('Products')
    response = client.put('/api/v1/permissions/role/employee', headers=headers,
                          json={'permissions': [{'module_id': products_id, 'is_granted': True}]})
    assert response.status_code == 200
    employee = User(email='e2@test.com', role='employee', is_active=True)
    employee.set_password('x12345678')
    db.session.add(employee)
    db.session.commit()
    assert check_module_access(employee, 'Products') is True


def test_admin_sets_user_override_by_user_id(client):
    headers = _headers(client, 'a@test.com', 'admin')
    employee = User(email='e@test.com', role='employee', is_active=True)
    employee.set_password('x12345678')
    db.session.add(employee)
    db.session.commit()
    products_id = _module_id('Products')
    response = client.put(f'/api/v1/permissions/user/{employee.id}', headers=headers,
                          json={'permissions': [{'module_id': products_id, 'is_granted': True}]})
    assert response.status_code == 200
    assert check_module_access(employee, 'Products') is True
