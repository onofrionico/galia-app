from datetime import date

import pytest

from app import create_app
from app.extensions import db
from app.models import Employee, JobPosition, Module, RolePermission, Sale, User


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        for name in ('Sales', 'Employees'):
            db.session.add(Module(name=name, display_name=name, is_active=True))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _headers(client, email, role, password='secret123'):
    user = User(email=email, role=role, is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    token = client.post('/api/v1/auth/login', json={'email': email, 'password': password}).get_json()['token']
    return {'Authorization': f'Bearer {token}'}


def _grant(role, module_name):
    module = Module.query.filter_by(name=module_name).first()
    db.session.add(RolePermission(role=role, module_id=module.id, is_granted=True))
    db.session.commit()


def _position():
    position = JobPosition(name='Barista', contract_type='por_hora', hourly_rate=1500)
    db.session.add(position)
    db.session.commit()
    return position


SALE = {'fecha': '2026-10-31', 'total': 1000}


def test_employee_without_sales_module_cannot_create_sale(client):
    headers = _headers(client, 'e@test.com', 'employee')
    assert client.post('/api/v1/sales', headers=headers, json=SALE).status_code == 403
    assert Sale.query.count() == 0


def test_employee_with_sales_module_can_create_sale(client):
    _grant('employee', 'Sales')
    headers = _headers(client, 'e@test.com', 'employee')
    assert client.post('/api/v1/sales', headers=headers, json=SALE).status_code == 201


def test_deactivated_user_token_stops_working(client):
    _grant('employee', 'Sales')
    headers = _headers(client, 'e@test.com', 'employee')
    assert client.get('/api/v1/sales', headers=headers).status_code == 200

    User.query.filter_by(email='e@test.com').first().is_active = False
    db.session.commit()

    # 401 y no 403: el frontend cierra la sesión solo ante un 401.
    assert client.get('/api/v1/sales', headers=headers).status_code == 401


def test_employee_deactivation_route_ends_the_session(client):
    admin_headers = _headers(client, 'a@test.com', 'admin')
    employee_headers = _headers(client, 'e@test.com', 'employee')
    user = User.query.filter_by(email='e@test.com').first()
    employee = Employee(user_id=user.id, first_name='Ana', last_name='Paz', dni='30111222',
                        cuil='27301112224', birth_date=date(1990, 1, 1), phone='1', address='x',
                        employment_relationship='dependencia', emergency_contact_name='y',
                        emergency_contact_phone='2', emergency_contact_relationship='z',
                        hire_date=date(2026, 1, 1), status='activo')
    db.session.add(employee)
    db.session.commit()

    response = client.patch(f'/api/v1/employees/{employee.id}/deactivate', headers=admin_headers)
    assert response.status_code == 200
    assert client.get('/api/v1/auth/me', headers=employee_headers).status_code == 401


@pytest.mark.parametrize('path', ['/api/v1/job-positions', '/api/v1/job-positions/{id}'])
def test_employee_without_module_cannot_read_job_position_pay(client, path):
    position = _position()
    headers = _headers(client, 'e@test.com', 'employee')
    assert client.get(path.format(id=position.id), headers=headers).status_code == 403


def test_employees_module_can_read_job_position_pay(client):
    _position()
    _grant('employee', 'Employees')
    headers = _headers(client, 'e@test.com', 'employee')
    response = client.get('/api/v1/job-positions', headers=headers)
    assert response.status_code == 200
    assert response.get_json()[0]['hourly_rate'] == 1500
