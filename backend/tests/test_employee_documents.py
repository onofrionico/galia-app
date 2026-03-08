"""
Tests for Employee Documents Portal (Mis Recibos)
Tests access control and document retrieval for employees
"""
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.employee import Employee
from app.models.job_position import JobPosition
from app.models.payroll import Payroll
from app.models.social_security_document import SocialSecurityDocument
from app.models.absence_request import AbsenceRequest
from datetime import datetime, date
from decimal import Decimal


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
            name='Cajero',
            contract_type='full_time',
            base_hourly_rate=2500.0
        )
        db.session.add(job_position)
        db.session.commit()
        
        user = User(
            email='employee@test.com',
            role='employee',
            is_active=True
        )
        user.set_password('employee123')
        db.session.add(user)
        db.session.commit()
        
        employee = Employee(
            user_id=user.id,
            first_name='Juan',
            last_name='Perez',
            dni='12345678',
            cuil='20-12345678-9',
            hire_date=date(2024, 1, 1),
            current_job_position_id=job_position.id,
            status='activo'
        )
        db.session.add(employee)
        db.session.commit()
        
        return user


@pytest.fixture
def other_employee_user(app):
    """Create another employee user"""
    with app.app_context():
        job_position = JobPosition.query.first()
        
        user = User(
            email='other@test.com',
            role='employee',
            is_active=True
        )
        user.set_password('other123')
        db.session.add(user)
        db.session.commit()
        
        employee = Employee(
            user_id=user.id,
            first_name='Maria',
            last_name='Garcia',
            dni='87654321',
            cuil='27-87654321-3',
            hire_date=date(2024, 1, 1),
            current_job_position_id=job_position.id,
            status='activo'
        )
        db.session.add(employee)
        db.session.commit()
        
        return user


def get_auth_token(client, email, password):
    """Helper to get authentication token"""
    response = client.post('/api/v1/auth/login', json={
        'email': email,
        'password': password
    })
    return response.json.get('token')


class TestEmployeeDocumentsAccess:
    """Test suite for employee documents access control"""
    
    def test_employee_can_access_my_documents(self, client, employee_user, app):
        """Test that employee can access their own documents endpoint"""
        with app.app_context():
            token = get_auth_token(client, 'employee@test.com', 'employee123')
            
            response = client.get(
                '/api/v1/my-documents',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            assert response.status_code == 200
            assert 'documents' in response.json
            assert 'employee' in response.json
    
    def test_user_without_employee_cannot_access(self, client, admin_user, app):
        """Test that admin user without employee record cannot access employee endpoints"""
        with app.app_context():
            token = get_auth_token(client, 'admin@test.com', 'admin123')
            
            response = client.get(
                '/api/v1/my-documents',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            assert response.status_code == 403
            assert 'empleado' in response.json.get('error', '').lower()
    
    def test_unauthenticated_access_denied(self, client, app):
        """Test that unauthenticated users cannot access documents"""
        with app.app_context():
            response = client.get('/api/v1/my-documents')
            
            assert response.status_code == 401


class TestMyDocumentsEndpoint:
    """Test suite for /my-documents endpoint"""
    
    def test_get_all_documents(self, client, employee_user, admin_user, app):
        """Test retrieving all documents for an employee"""
        with app.app_context():
            employee = Employee.query.filter_by(user_id=employee_user.id).first()
            
            # Create test payroll
            payroll = Payroll(
                employee_id=employee.id,
                month=1,
                year=2026,
                hours_worked=Decimal('160.00'),
                scheduled_hours=Decimal('160.00'),
                hourly_rate=Decimal('2500.00'),
                gross_salary=Decimal('400000.00'),
                status='validated',
                pdf_generated=True,
                pdf_path='/test/payroll.pdf',
                generated_by=admin_user.id
            )
            db.session.add(payroll)
            
            # Create test social security document
            ss_doc = SocialSecurityDocument(
                employee_id=employee.id,
                document_type='cargas_sociales',
                period_month=1,
                period_year=2026,
                file_name='cargas_sociales.pdf',
                file_path='/test/ss_doc.pdf',
                file_size=1024,
                mime_type='application/pdf',
                uploaded_by_id=admin_user.id
            )
            db.session.add(ss_doc)
            
            db.session.commit()
            
            token = get_auth_token(client, 'employee@test.com', 'employee123')
            
            response = client.get(
                '/api/v1/my-documents',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            assert response.status_code == 200
            assert len(response.json['documents']) == 2
            assert response.json['total'] == 2
    
    def test_filter_by_type(self, client, employee_user, admin_user, app):
        """Test filtering documents by type"""
        with app.app_context():
            employee = Employee.query.filter_by(user_id=employee_user.id).first()
            
            # Create test payroll
            payroll = Payroll(
                employee_id=employee.id,
                month=1,
                year=2026,
                hours_worked=Decimal('160.00'),
                scheduled_hours=Decimal('160.00'),
                hourly_rate=Decimal('2500.00'),
                gross_salary=Decimal('400000.00'),
                status='validated',
                pdf_generated=True,
                pdf_path='/test/payroll.pdf',
                generated_by=admin_user.id
            )
            db.session.add(payroll)
            db.session.commit()
            
            token = get_auth_token(client, 'employee@test.com', 'employee123')
            
            response = client.get(
                '/api/v1/my-documents?type=payroll',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            assert response.status_code == 200
            assert all(doc['type'] == 'payroll' for doc in response.json['documents'])
    
    def test_filter_by_year_and_month(self, client, employee_user, admin_user, app):
        """Test filtering documents by year and month"""
        with app.app_context():
            employee = Employee.query.filter_by(user_id=employee_user.id).first()
            
            # Create payrolls for different months
            payroll1 = Payroll(
                employee_id=employee.id,
                month=1,
                year=2026,
                hours_worked=Decimal('160.00'),
                scheduled_hours=Decimal('160.00'),
                hourly_rate=Decimal('2500.00'),
                gross_salary=Decimal('400000.00'),
                status='validated',
                pdf_generated=True,
                pdf_path='/test/payroll1.pdf',
                generated_by=admin_user.id
            )
            payroll2 = Payroll(
                employee_id=employee.id,
                month=2,
                year=2026,
                hours_worked=Decimal('160.00'),
                scheduled_hours=Decimal('160.00'),
                hourly_rate=Decimal('2500.00'),
                gross_salary=Decimal('400000.00'),
                status='validated',
                pdf_generated=True,
                pdf_path='/test/payroll2.pdf',
                generated_by=admin_user.id
            )
            db.session.add_all([payroll1, payroll2])
            db.session.commit()
            
            token = get_auth_token(client, 'employee@test.com', 'employee123')
            
            response = client.get(
                '/api/v1/my-documents?year=2026&month=1',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            assert response.status_code == 200
            assert all(doc['period_month'] == 1 for doc in response.json['documents'])


class TestMyPayrollsEndpoint:
    """Test suite for /my-documents/payrolls endpoint"""
    
    def test_get_my_payrolls(self, client, employee_user, admin_user, app):
        """Test retrieving only payroll documents"""
        with app.app_context():
            employee = Employee.query.filter_by(user_id=employee_user.id).first()
            
            payroll = Payroll(
                employee_id=employee.id,
                month=1,
                year=2026,
                hours_worked=Decimal('160.00'),
                scheduled_hours=Decimal('160.00'),
                hourly_rate=Decimal('2500.00'),
                gross_salary=Decimal('400000.00'),
                status='validated',
                pdf_generated=True,
                pdf_path='/test/payroll.pdf',
                generated_by=admin_user.id
            )
            db.session.add(payroll)
            db.session.commit()
            
            token = get_auth_token(client, 'employee@test.com', 'employee123')
            
            response = client.get(
                '/api/v1/my-documents/payrolls',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            assert response.status_code == 200
            assert 'payrolls' in response.json
            assert len(response.json['payrolls']) == 1
            assert response.json['payrolls'][0]['gross_salary'] == 400000.00
    
    def test_only_pdf_generated_payrolls(self, client, employee_user, admin_user, app):
        """Test that only payrolls with generated PDFs are returned"""
        with app.app_context():
            employee = Employee.query.filter_by(user_id=employee_user.id).first()
            
            # Payroll with PDF
            payroll1 = Payroll(
                employee_id=employee.id,
                month=1,
                year=2026,
                hours_worked=Decimal('160.00'),
                scheduled_hours=Decimal('160.00'),
                hourly_rate=Decimal('2500.00'),
                gross_salary=Decimal('400000.00'),
                status='validated',
                pdf_generated=True,
                pdf_path='/test/payroll1.pdf',
                generated_by=admin_user.id
            )
            
            # Payroll without PDF
            payroll2 = Payroll(
                employee_id=employee.id,
                month=2,
                year=2026,
                hours_worked=Decimal('160.00'),
                scheduled_hours=Decimal('160.00'),
                hourly_rate=Decimal('2500.00'),
                gross_salary=Decimal('400000.00'),
                status='draft',
                pdf_generated=False,
                generated_by=admin_user.id
            )
            
            db.session.add_all([payroll1, payroll2])
            db.session.commit()
            
            token = get_auth_token(client, 'employee@test.com', 'employee123')
            
            response = client.get(
                '/api/v1/my-documents/payrolls',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            assert response.status_code == 200
            assert len(response.json['payrolls']) == 1


class TestDocumentIsolation:
    """Test that employees can only access their own documents"""
    
    def test_employee_cannot_see_other_payrolls(self, client, employee_user, other_employee_user, admin_user, app):
        """Test that employee only sees their own payrolls"""
        with app.app_context():
            employee1 = Employee.query.filter_by(user_id=employee_user.id).first()
            employee2 = Employee.query.filter_by(user_id=other_employee_user.id).first()
            
            # Create payroll for employee1
            payroll1 = Payroll(
                employee_id=employee1.id,
                month=1,
                year=2026,
                hours_worked=Decimal('160.00'),
                scheduled_hours=Decimal('160.00'),
                hourly_rate=Decimal('2500.00'),
                gross_salary=Decimal('400000.00'),
                status='validated',
                pdf_generated=True,
                pdf_path='/test/payroll1.pdf',
                generated_by=admin_user.id
            )
            
            # Create payroll for employee2
            payroll2 = Payroll(
                employee_id=employee2.id,
                month=1,
                year=2026,
                hours_worked=Decimal('160.00'),
                scheduled_hours=Decimal('160.00'),
                hourly_rate=Decimal('2500.00'),
                gross_salary=Decimal('400000.00'),
                status='validated',
                pdf_generated=True,
                pdf_path='/test/payroll2.pdf',
                generated_by=admin_user.id
            )
            
            db.session.add_all([payroll1, payroll2])
            db.session.commit()
            
            token = get_auth_token(client, 'employee@test.com', 'employee123')
            
            response = client.get(
                '/api/v1/my-documents',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            assert response.status_code == 200
            assert len(response.json['documents']) == 1
            assert response.json['employee']['dni'] == '12345678'
    
    def test_employee_cannot_see_other_social_security_docs(self, client, employee_user, other_employee_user, admin_user, app):
        """Test that employee only sees their own social security documents"""
        with app.app_context():
            employee1 = Employee.query.filter_by(user_id=employee_user.id).first()
            employee2 = Employee.query.filter_by(user_id=other_employee_user.id).first()
            
            # Create doc for employee1
            doc1 = SocialSecurityDocument(
                employee_id=employee1.id,
                document_type='cargas_sociales',
                period_month=1,
                period_year=2026,
                file_name='doc1.pdf',
                file_path='/test/doc1.pdf',
                file_size=1024,
                mime_type='application/pdf',
                uploaded_by_id=admin_user.id
            )
            
            # Create doc for employee2
            doc2 = SocialSecurityDocument(
                employee_id=employee2.id,
                document_type='cargas_sociales',
                period_month=1,
                period_year=2026,
                file_name='doc2.pdf',
                file_path='/test/doc2.pdf',
                file_size=1024,
                mime_type='application/pdf',
                uploaded_by_id=admin_user.id
            )
            
            db.session.add_all([doc1, doc2])
            db.session.commit()
            
            token = get_auth_token(client, 'employee@test.com', 'employee123')
            
            response = client.get(
                '/api/v1/my-documents/social-security',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            assert response.status_code == 200
            assert len(response.json['social_security_documents']) == 1
