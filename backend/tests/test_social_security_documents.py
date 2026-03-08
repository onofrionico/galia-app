"""
Tests for Social Security Documents management
Tests upload, download, list, and delete operations with proper permissions
"""
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.employee import Employee
from app.models.job_position import JobPosition
from app.models.social_security_document import SocialSecurityDocument
from datetime import datetime, date
from io import BytesIO
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


def get_auth_token(client, email, password):
    """Helper to get authentication token"""
    response = client.post('/api/v1/auth/login', json={
        'email': email,
        'password': password
    })
    return response.json.get('token')


def create_test_pdf():
    """Create a simple test PDF file"""
    pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/Resources <<\n/Font <<\n/F1 4 0 R\n>>\n>>\n/MediaBox [0 0 612 792]\n/Contents 5 0 R\n>>\nendobj\n4 0 obj\n<<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\nendobj\n5 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test PDF) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000262 00000 n\n0000000341 00000 n\ntrailer\n<<\n/Size 6\n/Root 1 0 R\n>>\nstartxref\n435\n%%EOF'
    return BytesIO(pdf_content)


class TestSocialSecurityDocuments:
    """Test suite for social security documents"""
    
    def test_upload_document_as_admin(self, client, admin_user, employee_user, app, monkeypatch):
        """Test that admin can upload documents"""
        with app.app_context():
            token = get_auth_token(client, 'admin@test.com', 'admin123')
            employee = Employee.query.filter_by(user_id=employee_user.id).first()
            
            # Mock S3 upload
            class MockS3Client:
                def upload_fileobj(self, *args, **kwargs):
                    pass
            
            class MockS3Service:
                def __init__(self):
                    self.s3_client = MockS3Client()
                    self.bucket_name = 'test-bucket'
            
            from app.services import document_service
            monkeypatch.setattr(document_service, 's3_service', MockS3Service())
            
            pdf_file = create_test_pdf()
            
            response = client.post(
                '/api/v1/social-security/upload',
                data={
                    'employee_id': employee.id,
                    'document_type': 'cargas_sociales',
                    'period_month': 1,
                    'period_year': 2026,
                    'file': (pdf_file, 'test_document.pdf'),
                    'notes': 'Test document'
                },
                headers={'Authorization': f'Bearer {token}'},
                content_type='multipart/form-data'
            )
            
            assert response.status_code == 201
            assert 'document' in response.json
            assert response.json['document']['document_type'] == 'cargas_sociales'
    
    def test_upload_document_as_employee_forbidden(self, client, employee_user, app):
        """Test that regular employee cannot upload documents"""
        with app.app_context():
            token = get_auth_token(client, 'employee@test.com', 'employee123')
            employee = Employee.query.filter_by(user_id=employee_user.id).first()
            
            pdf_file = create_test_pdf()
            
            response = client.post(
                '/api/v1/social-security/upload',
                data={
                    'employee_id': employee.id,
                    'document_type': 'cargas_sociales',
                    'period_month': 1,
                    'period_year': 2026,
                    'file': (pdf_file, 'test_document.pdf')
                },
                headers={'Authorization': f'Bearer {token}'},
                content_type='multipart/form-data'
            )
            
            assert response.status_code == 403
    
    def test_upload_invalid_file_type(self, client, admin_user, employee_user, app):
        """Test that only PDF files are accepted"""
        with app.app_context():
            token = get_auth_token(client, 'admin@test.com', 'admin123')
            employee = Employee.query.filter_by(user_id=employee_user.id).first()
            
            txt_file = BytesIO(b'This is a text file')
            
            response = client.post(
                '/api/v1/social-security/upload',
                data={
                    'employee_id': employee.id,
                    'document_type': 'cargas_sociales',
                    'period_month': 1,
                    'period_year': 2026,
                    'file': (txt_file, 'test_document.txt')
                },
                headers={'Authorization': f'Bearer {token}'},
                content_type='multipart/form-data'
            )
            
            assert response.status_code == 400
            assert 'PDF' in response.json.get('error', '') or 'PDF' in str(response.json.get('details', []))
    
    def test_get_employee_documents(self, client, admin_user, employee_user, app):
        """Test retrieving documents for an employee"""
        with app.app_context():
            token = get_auth_token(client, 'admin@test.com', 'admin123')
            employee = Employee.query.filter_by(user_id=employee_user.id).first()
            
            # Create a test document
            doc = SocialSecurityDocument(
                employee_id=employee.id,
                document_type='cargas_sociales',
                period_month=1,
                period_year=2026,
                file_name='test.pdf',
                file_path='social-security-documents/test.pdf',
                file_size=1024,
                mime_type='application/pdf',
                uploaded_by_id=admin_user.id
            )
            db.session.add(doc)
            db.session.commit()
            
            response = client.get(
                f'/api/v1/social-security/employee/{employee.id}',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            assert response.status_code == 200
            assert len(response.json) == 1
            assert response.json[0]['document_type'] == 'cargas_sociales'
    
    def test_employee_can_view_own_documents(self, client, employee_user, app):
        """Test that employee can view their own documents"""
        with app.app_context():
            token = get_auth_token(client, 'employee@test.com', 'employee123')
            employee = Employee.query.filter_by(user_id=employee_user.id).first()
            
            # Create a test document
            doc = SocialSecurityDocument(
                employee_id=employee.id,
                document_type='cargas_sociales',
                period_month=1,
                period_year=2026,
                file_name='test.pdf',
                file_path='social-security-documents/test.pdf',
                file_size=1024,
                mime_type='application/pdf',
                uploaded_by_id=employee_user.id
            )
            db.session.add(doc)
            db.session.commit()
            
            response = client.get(
                f'/api/v1/social-security/employee/{employee.id}',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            assert response.status_code == 200
            assert len(response.json) == 1
    
    def test_employee_cannot_view_other_documents(self, client, employee_user, admin_user, app):
        """Test that employee cannot view other employees' documents"""
        with app.app_context():
            # Create another employee
            job_position = JobPosition.query.first()
            other_user = User(
                email='other@test.com',
                role='employee',
                is_active=True
            )
            other_user.set_password('other123')
            db.session.add(other_user)
            db.session.commit()
            
            other_employee = Employee(
                user_id=other_user.id,
                first_name='Maria',
                last_name='Garcia',
                dni='87654321',
                cuil='27-87654321-3',
                hire_date=date(2024, 1, 1),
                current_job_position_id=job_position.id,
                status='activo'
            )
            db.session.add(other_employee)
            db.session.commit()
            
            token = get_auth_token(client, 'employee@test.com', 'employee123')
            
            response = client.get(
                f'/api/v1/social-security/employee/{other_employee.id}',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            assert response.status_code == 403
    
    def test_delete_document_as_admin(self, client, admin_user, employee_user, app, monkeypatch):
        """Test that admin can delete documents"""
        with app.app_context():
            token = get_auth_token(client, 'admin@test.com', 'admin123')
            employee = Employee.query.filter_by(user_id=employee_user.id).first()
            
            # Mock S3 delete
            class MockS3Service:
                def delete_file(self, s3_key):
                    return True
            
            from app.services import document_service
            monkeypatch.setattr(document_service, 's3_service', MockS3Service())
            
            # Create a test document
            doc = SocialSecurityDocument(
                employee_id=employee.id,
                document_type='cargas_sociales',
                period_month=1,
                period_year=2026,
                file_name='test.pdf',
                file_path='social-security-documents/test.pdf',
                file_size=1024,
                mime_type='application/pdf',
                uploaded_by_id=admin_user.id
            )
            db.session.add(doc)
            db.session.commit()
            doc_id = doc.id
            
            response = client.delete(
                f'/api/v1/social-security/{doc_id}',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            assert response.status_code == 200
            assert SocialSecurityDocument.query.get(doc_id) is None
    
    def test_delete_document_as_employee_forbidden(self, client, employee_user, admin_user, app):
        """Test that employee cannot delete documents"""
        with app.app_context():
            token = get_auth_token(client, 'employee@test.com', 'employee123')
            employee = Employee.query.filter_by(user_id=employee_user.id).first()
            
            # Create a test document
            doc = SocialSecurityDocument(
                employee_id=employee.id,
                document_type='cargas_sociales',
                period_month=1,
                period_year=2026,
                file_name='test.pdf',
                file_path='social-security-documents/test.pdf',
                file_size=1024,
                mime_type='application/pdf',
                uploaded_by_id=admin_user.id
            )
            db.session.add(doc)
            db.session.commit()
            doc_id = doc.id
            
            response = client.delete(
                f'/api/v1/social-security/{doc_id}',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            assert response.status_code == 403
    
    def test_get_document_types(self, client, employee_user, app):
        """Test retrieving available document types"""
        with app.app_context():
            token = get_auth_token(client, 'employee@test.com', 'employee123')
            
            response = client.get(
                '/api/v1/social-security/types',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            assert response.status_code == 200
            assert 'document_types' in response.json
            assert len(response.json['document_types']) > 0
    
    def test_filter_documents_by_period(self, client, admin_user, employee_user, app):
        """Test filtering documents by period"""
        with app.app_context():
            token = get_auth_token(client, 'admin@test.com', 'admin123')
            employee = Employee.query.filter_by(user_id=employee_user.id).first()
            
            # Create documents for different periods
            doc1 = SocialSecurityDocument(
                employee_id=employee.id,
                document_type='cargas_sociales',
                period_month=1,
                period_year=2026,
                file_name='test1.pdf',
                file_path='social-security-documents/test1.pdf',
                file_size=1024,
                mime_type='application/pdf',
                uploaded_by_id=admin_user.id
            )
            doc2 = SocialSecurityDocument(
                employee_id=employee.id,
                document_type='aportes',
                period_month=2,
                period_year=2026,
                file_name='test2.pdf',
                file_path='social-security-documents/test2.pdf',
                file_size=1024,
                mime_type='application/pdf',
                uploaded_by_id=admin_user.id
            )
            db.session.add_all([doc1, doc2])
            db.session.commit()
            
            # Filter by month
            response = client.get(
                f'/api/v1/social-security/employee/{employee.id}?period_month=1',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            assert response.status_code == 200
            assert len(response.json) == 1
            assert response.json[0]['period_month'] == 1
    
    def test_document_validation(self, app):
        """Test document model validation"""
        with app.app_context():
            doc = SocialSecurityDocument(
                employee_id=1,
                document_type='invalid_type',
                period_month=13,
                period_year=2026,
                file_name='test.pdf',
                file_path='test.pdf',
                file_size=1024,
                mime_type='application/pdf',
                uploaded_by_id=1
            )
            
            errors = doc.validate()
            assert len(errors) > 0
            assert any('tipo de documento' in err.lower() for err in errors)
            assert any('mes' in err.lower() for err in errors)
