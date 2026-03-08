"""
Tests de permisos y seguridad para endpoints del backend
Verifica que empleados no puedan acceder a endpoints de admin
"""
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.employee import Employee
from app.models.job_position import JobPosition
from datetime import datetime, date
import json


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def admin_user(app):
    """Create admin user"""
    with app.app_context():
        user = User(
            email='admin@test.com',
            role='admin',
            is_active=True
        )
        user.set_password('admin123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def employee_user(app):
    """Create employee user with job position"""
    with app.app_context():
        # Create job position first
        job_position = JobPosition(
            name='Empleado Test',
            contract_type='por_hora',
            hourly_rate=5000,
            is_active=True
        )
        db.session.add(job_position)
        db.session.flush()
        
        # Create user
        user = User(
            email='employee@test.com',
            role='employee',
            is_active=True
        )
        user.set_password('employee123')
        db.session.add(user)
        db.session.flush()
        
        # Create employee
        employee = Employee(
            user_id=user.id,
            first_name='Juan',
            last_name='Pérez',
            dni='12345678',
            hire_date=date(2024, 1, 1),
            current_job_position_id=job_position.id,
            status='activo'
        )
        db.session.add(employee)
        db.session.commit()
        
        return user


def get_auth_token(client, email, password):
    """Helper to get JWT token"""
    response = client.post('/api/v1/auth/login', 
                          json={'email': email, 'password': password})
    data = json.loads(response.data)
    return data.get('access_token')


class TestSalesPermissions:
    """Test sales endpoints permissions"""
    
    def test_employee_cannot_access_sales_list(self, client, employee_user):
        """Employee should not access sales list"""
        token = get_auth_token(client, 'employee@test.com', 'employee123')
        response = client.get('/api/v1/sales',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data
        assert 'administrador' in data['error'].lower()
    
    def test_admin_can_access_sales_list(self, client, admin_user):
        """Admin should access sales list"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')
        response = client.get('/api/v1/sales',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200
    
    def test_employee_cannot_access_sales_stats(self, client, employee_user):
        """Employee should not access sales stats"""
        token = get_auth_token(client, 'employee@test.com', 'employee123')
        response = client.get('/api/v1/sales/stats',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 403
    
    def test_employee_cannot_export_sales(self, client, employee_user):
        """Employee should not export sales"""
        token = get_auth_token(client, 'employee@test.com', 'employee123')
        response = client.get('/api/v1/sales/export',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 403
    
    def test_employee_cannot_delete_sale(self, client, employee_user):
        """Employee should not delete sales"""
        token = get_auth_token(client, 'employee@test.com', 'employee123')
        response = client.delete('/api/v1/sales/1',
                               headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 403


class TestReportsPermissions:
    """Test reports endpoints permissions"""
    
    def test_employee_cannot_access_dashboard(self, client, employee_user):
        """Employee should not access reports dashboard"""
        token = get_auth_token(client, 'employee@test.com', 'employee123')
        response = client.get('/api/v1/reports/dashboard',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 403
    
    def test_admin_can_access_dashboard(self, client, admin_user):
        """Admin should access reports dashboard"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')
        response = client.get('/api/v1/reports/dashboard',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200


class TestExpensesPermissions:
    """Test expenses endpoints permissions"""
    
    def test_employee_cannot_access_expenses(self, client, employee_user):
        """Employee should not access expenses"""
        token = get_auth_token(client, 'employee@test.com', 'employee123')
        response = client.get('/api/v1/expenses',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 403
    
    def test_admin_can_access_expenses(self, client, admin_user):
        """Admin should access expenses"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')
        response = client.get('/api/v1/expenses',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200
    
    def test_employee_cannot_create_expense(self, client, employee_user):
        """Employee should not create expenses"""
        token = get_auth_token(client, 'employee@test.com', 'employee123')
        response = client.post('/api/v1/expenses',
                             headers={'Authorization': f'Bearer {token}'},
                             json={'fecha': '2026-03-08', 'importe': 1000})
        assert response.status_code == 403


class TestPayrollPermissions:
    """Test payroll endpoints permissions"""
    
    def test_employee_cannot_access_payrolls(self, client, employee_user):
        """Employee should not access all payrolls"""
        token = get_auth_token(client, 'employee@test.com', 'employee123')
        response = client.get('/api/v1/payroll',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 403
    
    def test_admin_can_access_payrolls(self, client, admin_user):
        """Admin should access payrolls"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')
        response = client.get('/api/v1/payroll',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200
    
    def test_employee_cannot_generate_payroll(self, client, employee_user):
        """Employee should not generate payrolls"""
        token = get_auth_token(client, 'employee@test.com', 'employee123')
        response = client.post('/api/v1/payroll/generate',
                             headers={'Authorization': f'Bearer {token}'},
                             json={'employee_id': 1, 'month': 3, 'year': 2026})
        assert response.status_code == 403


class TestMLDashboardPermissions:
    """Test ML dashboard endpoints permissions"""
    
    def test_employee_cannot_access_ml_accuracy(self, client, employee_user):
        """Employee should not access ML accuracy metrics"""
        token = get_auth_token(client, 'employee@test.com', 'employee123')
        response = client.get('/api/v1/ml/dashboard/accuracy',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 403
    
    def test_admin_can_access_ml_accuracy(self, client, admin_user):
        """Admin should access ML accuracy metrics"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')
        response = client.get('/api/v1/ml/dashboard/accuracy',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200


class TestSchedulesPermissions:
    """Test schedules endpoints permissions"""
    
    def test_employee_cannot_create_schedule(self, client, employee_user):
        """Employee should not create schedules"""
        token = get_auth_token(client, 'employee@test.com', 'employee123')
        response = client.post('/api/v1/schedules',
                             headers={'Authorization': f'Bearer {token}'},
                             json={'start_date': '2026-03-10', 'end_date': '2026-03-16'})
        assert response.status_code == 403
    
    def test_employee_cannot_delete_schedule(self, client, employee_user):
        """Employee should not delete schedules"""
        token = get_auth_token(client, 'employee@test.com', 'employee123')
        response = client.delete('/api/v1/schedules/1',
                               headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 403
    
    def test_admin_can_create_schedule(self, client, admin_user):
        """Admin should create schedules"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')
        response = client.post('/api/v1/schedules',
                             headers={'Authorization': f'Bearer {token}'},
                             json={'start_date': '2026-03-10', 'end_date': '2026-03-16'})
        # May fail due to business logic, but should not be 403
        assert response.status_code != 403


class TestEmployeesPermissions:
    """Test employees endpoints permissions"""
    
    def test_employee_can_access_own_profile(self, client, employee_user):
        """Employee should access their own profile"""
        token = get_auth_token(client, 'employee@test.com', 'employee123')
        response = client.get('/api/v1/employees/me',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200
    
    def test_employee_cannot_create_employee(self, client, employee_user):
        """Employee should not create employees"""
        token = get_auth_token(client, 'employee@test.com', 'employee123')
        response = client.post('/api/v1/employees',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'first_name': 'Test',
                                 'last_name': 'User',
                                 'dni': '99999999',
                                 'email': 'test@test.com',
                                 'hire_date': '2026-03-08',
                                 'job_position_id': 1,
                                 'password': 'test123'
                             })
        assert response.status_code == 403
    
    def test_admin_can_create_employee(self, client, admin_user):
        """Admin should create employees"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')
        
        # First create a job position
        job_response = client.post('/api/v1/job-positions',
                                   headers={'Authorization': f'Bearer {token}'},
                                   json={
                                       'name': 'Test Position',
                                       'contract_type': 'por_hora',
                                       'hourly_rate': 5000
                                   })
        
        response = client.post('/api/v1/employees',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'first_name': 'Test',
                                 'last_name': 'User',
                                 'dni': '99999999',
                                 'email': 'newtest@test.com',
                                 'hire_date': '2026-03-08',
                                 'job_position_id': 1,
                                 'password': 'test123'
                             })
        # May fail due to business logic, but should not be 403
        assert response.status_code != 403


class TestUnauthorizedAccess:
    """Test access without authentication"""
    
    def test_no_token_returns_401(self, client):
        """Endpoints without token should return 401"""
        endpoints = [
            '/api/v1/sales',
            '/api/v1/reports/dashboard',
            '/api/v1/expenses',
            '/api/v1/payroll',
            '/api/v1/schedules'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
    
    def test_invalid_token_returns_401(self, client):
        """Invalid token should return 401"""
        response = client.get('/api/v1/sales',
                            headers={'Authorization': 'Bearer invalid_token'})
        assert response.status_code in [401, 422]  # 422 for invalid JWT format


class TestJobPositionsPermissions:
    """Test job positions endpoints permissions"""
    
    def test_employee_can_read_job_positions(self, client, employee_user):
        """Employee should read job positions (for reference)"""
        token = get_auth_token(client, 'employee@test.com', 'employee123')
        response = client.get('/api/v1/job-positions',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200
    
    def test_employee_cannot_create_job_position(self, client, employee_user):
        """Employee should not create job positions"""
        token = get_auth_token(client, 'employee@test.com', 'employee123')
        response = client.post('/api/v1/job-positions',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'name': 'Test Position',
                                 'contract_type': 'por_hora',
                                 'hourly_rate': 5000
                             })
        assert response.status_code == 403
    
    def test_employee_cannot_update_job_position(self, client, employee_user):
        """Employee should not update job positions"""
        token = get_auth_token(client, 'employee@test.com', 'employee123')
        response = client.put('/api/v1/job-positions/1',
                            headers={'Authorization': f'Bearer {token}'},
                            json={'hourly_rate': 10000})
        assert response.status_code == 403
    
    def test_admin_can_create_job_position(self, client, admin_user):
        """Admin should create job positions"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')
        response = client.post('/api/v1/job-positions',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'name': 'New Position',
                                 'contract_type': 'por_hora',
                                 'hourly_rate': 6000
                             })
        assert response.status_code in [200, 201]
