"""
Tests para la funcionalidad de eliminación de nóminas en borrador
Verifica que solo las nóminas en estado 'draft' puedan ser eliminadas
"""
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.employee import Employee
from app.models.job_position import JobPosition
from app.models.payroll import Payroll
from datetime import datetime, date
from decimal import Decimal
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
        job_position = JobPosition(
            name='Empleado Test',
            contract_type='por_hora',
            hourly_rate=5000,
            is_active=True
        )
        db.session.add(job_position)
        db.session.flush()
        
        user = User(
            email='employee@test.com',
            role='employee',
            is_active=True
        )
        user.set_password('employee123')
        db.session.add(user)
        db.session.flush()
        
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
        
        return user, employee


def get_auth_token(client, email, password):
    """Helper to get JWT token"""
    response = client.post('/api/v1/auth/login', 
                          json={'email': email, 'password': password})
    data = json.loads(response.data)
    return data.get('access_token')


class TestPayrollDeletion:
    """Test payroll deletion functionality"""
    
    def test_delete_draft_payroll_success(self, client, admin_user, employee_user):
        """Admin should be able to delete a draft payroll"""
        with client.application.app_context():
            user, employee = employee_user
            
            # Create draft payroll
            payroll = Payroll(
                employee_id=employee.id,
                month=1,
                year=2026,
                hours_worked=Decimal('160.00'),
                scheduled_hours=Decimal('160.00'),
                hourly_rate=Decimal('5000.00'),
                gross_salary=Decimal('800000.00'),
                status='draft',
                generated_by=admin_user.id
            )
            db.session.add(payroll)
            db.session.commit()
            payroll_id = payroll.id
        
        # Get admin token
        token = get_auth_token(client, 'admin@test.com', 'admin123')
        
        # Delete draft payroll
        response = client.delete(
            f'/api/v1/payroll/{payroll_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Nómina eliminada exitosamente'
        assert data['payroll_id'] == payroll_id
        
        # Verify payroll was deleted
        with client.application.app_context():
            deleted_payroll = Payroll.query.get(payroll_id)
            assert deleted_payroll is None
    
    def test_cannot_delete_validated_payroll(self, client, admin_user, employee_user):
        """Admin should NOT be able to delete a validated payroll"""
        with client.application.app_context():
            user, employee = employee_user
            
            # Create validated payroll
            payroll = Payroll(
                employee_id=employee.id,
                month=2,
                year=2026,
                hours_worked=Decimal('160.00'),
                scheduled_hours=Decimal('160.00'),
                hourly_rate=Decimal('5000.00'),
                gross_salary=Decimal('800000.00'),
                status='validated',
                validated_at=datetime.utcnow(),
                validated_by=admin_user.id,
                generated_by=admin_user.id
            )
            db.session.add(payroll)
            db.session.commit()
            payroll_id = payroll.id
        
        # Get admin token
        token = get_auth_token(client, 'admin@test.com', 'admin123')
        
        # Try to delete validated payroll
        response = client.delete(
            f'/api/v1/payroll/{payroll_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'borrador' in data['message'].lower()
        
        # Verify payroll still exists
        with client.application.app_context():
            existing_payroll = Payroll.query.get(payroll_id)
            assert existing_payroll is not None
            assert existing_payroll.status == 'validated'
    
    def test_employee_cannot_delete_payroll(self, client, admin_user, employee_user):
        """Employee should NOT be able to delete any payroll"""
        with client.application.app_context():
            user, employee = employee_user
            
            # Create draft payroll
            payroll = Payroll(
                employee_id=employee.id,
                month=3,
                year=2026,
                hours_worked=Decimal('160.00'),
                scheduled_hours=Decimal('160.00'),
                hourly_rate=Decimal('5000.00'),
                gross_salary=Decimal('800000.00'),
                status='draft',
                generated_by=admin_user.id
            )
            db.session.add(payroll)
            db.session.commit()
            payroll_id = payroll.id
        
        # Get employee token
        token = get_auth_token(client, 'employee@test.com', 'employee123')
        
        # Try to delete payroll as employee
        response = client.delete(
            f'/api/v1/payroll/{payroll_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data
        
        # Verify payroll still exists
        with client.application.app_context():
            existing_payroll = Payroll.query.get(payroll_id)
            assert existing_payroll is not None
    
    def test_delete_nonexistent_payroll(self, client, admin_user):
        """Deleting non-existent payroll should return 404"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')
        
        response = client.delete(
            '/api/v1/payroll/99999',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 404
    
    def test_delete_without_auth(self, client, admin_user, employee_user):
        """Deleting without authentication should fail"""
        with client.application.app_context():
            user, employee = employee_user
            
            payroll = Payroll(
                employee_id=employee.id,
                month=4,
                year=2026,
                hours_worked=Decimal('160.00'),
                scheduled_hours=Decimal('160.00'),
                hourly_rate=Decimal('5000.00'),
                gross_salary=Decimal('800000.00'),
                status='draft',
                generated_by=admin_user.id
            )
            db.session.add(payroll)
            db.session.commit()
            payroll_id = payroll.id
        
        # Try to delete without token
        response = client.delete(f'/api/v1/payroll/{payroll_id}')
        
        assert response.status_code == 401
        
        # Verify payroll still exists
        with client.application.app_context():
            existing_payroll = Payroll.query.get(payroll_id)
            assert existing_payroll is not None
