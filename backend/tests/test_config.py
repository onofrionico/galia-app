"""
Tests for configuration API endpoints
Tests the branding configuration endpoint
"""
import pytest
import json
from app import create_app
from app.extensions import db
from app.models.site_config import SiteConfig
from app.models.user import User


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
def regular_user(app):
    """Create regular (non-admin) user"""
    with app.app_context():
        user = User(
            email='user@test.com',
            role='employee',
            is_active=True
        )
        user.set_password('user123')
        db.session.add(user)
        db.session.commit()
        return user


def get_auth_token(client, email, password):
    """Helper to get JWT token"""
    response = client.post('/api/v1/auth/login',
                          json={'email': email, 'password': password})
    data = json.loads(response.data)
    return data.get('token')


def test_get_branding_config_returns_empty_by_default(client):
    """Test GET /api/v1/config/branding returns empty config when none exists"""
    response = client.get('/api/v1/config/branding')

    assert response.status_code == 200
    data = response.get_json()
    assert data['logo_path'] is None
    assert data['banner_background_path'] is None


def test_get_branding_config_returns_stored_paths(client, app):
    """Test GET returns stored config"""
    with app.app_context():
        config = SiteConfig(
            logo_path='/uploads/logo-123.png',
            banner_background_path='/uploads/banner-456.png'
        )
        db.session.add(config)
        db.session.commit()

    response = client.get('/api/v1/config/branding')

    assert response.status_code == 200
    data = response.get_json()
    assert data['logo_path'] == '/uploads/logo-123.png'
    assert data['banner_background_path'] == '/uploads/banner-456.png'


def test_post_branding_config_requires_admin(client, regular_user):
    """Test POST /api/v1/admin/config/branding requires admin role"""
    token = get_auth_token(client, 'user@test.com', 'user123')
    response = client.post(
        '/api/v1/admin/config/branding',
        headers={'Authorization': f'Bearer {token}'},
        data={}
    )

    assert response.status_code == 403


def test_post_branding_config_requires_auth(client):
    """Test POST /api/v1/admin/config/branding requires authentication"""
    response = client.post(
        '/api/v1/admin/config/branding',
        data={}
    )

    assert response.status_code == 401


def test_post_branding_config_requires_file(client, admin_user):
    """Test POST requires at least one file"""
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    response = client.post(
        '/api/v1/admin/config/branding',
        headers={'Authorization': f'Bearer {token}'},
        data={}
    )

    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_post_branding_config_updates_logo(client, admin_user, tmp_path):
    """Test POST updates logo in config"""
    # Create a fake image file
    fake_image = tmp_path / "logo.png"
    fake_image.write_bytes(b'fake png data')

    token = get_auth_token(client, 'admin@test.com', 'admin123')
    with open(fake_image, 'rb') as f:
        response = client.post(
            '/api/v1/admin/config/branding',
            headers={'Authorization': f'Bearer {token}'},
            data={'logo': (f, 'logo.png')},
            content_type='multipart/form-data'
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data['logo_path'] is not None
    assert data['logo_path'].startswith('/uploads/logo-')
    assert data['logo_path'].endswith('.png')


def test_post_branding_config_updates_background(client, admin_user, tmp_path):
    """Test POST updates background in config"""
    # Create a fake image file
    fake_image = tmp_path / "banner.jpg"
    fake_image.write_bytes(b'fake jpg data')

    token = get_auth_token(client, 'admin@test.com', 'admin123')
    with open(fake_image, 'rb') as f:
        response = client.post(
            '/api/v1/admin/config/branding',
            headers={'Authorization': f'Bearer {token}'},
            data={'background': (f, 'banner.jpg')},
            content_type='multipart/form-data'
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data['banner_background_path'] is not None
    assert data['banner_background_path'].startswith('/uploads/banner-')
    assert data['banner_background_path'].endswith('.jpg')


def test_post_branding_config_updates_both_files(client, admin_user, tmp_path):
    """Test POST updates both logo and background"""
    # Create fake image files
    logo_file = tmp_path / "logo.png"
    logo_file.write_bytes(b'fake png data')
    bg_file = tmp_path / "banner.jpg"
    bg_file.write_bytes(b'fake jpg data')

    token = get_auth_token(client, 'admin@test.com', 'admin123')
    with open(logo_file, 'rb') as lf, open(bg_file, 'rb') as bf:
        response = client.post(
            '/api/v1/admin/config/branding',
            headers={'Authorization': f'Bearer {token}'},
            data={'logo': (lf, 'logo.png'), 'background': (bf, 'banner.jpg')},
            content_type='multipart/form-data'
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data['logo_path'] is not None
    assert data['banner_background_path'] is not None
    assert data['logo_path'].startswith('/uploads/logo-')
    assert data['banner_background_path'].startswith('/uploads/banner-')


def test_post_branding_config_rejects_invalid_file_type(client, admin_user, tmp_path):
    """Test POST rejects invalid file types"""
    # Create a file with invalid extension
    invalid_file = tmp_path / "file.txt"
    invalid_file.write_bytes(b'invalid file content')

    token = get_auth_token(client, 'admin@test.com', 'admin123')
    with open(invalid_file, 'rb') as f:
        response = client.post(
            '/api/v1/admin/config/branding',
            headers={'Authorization': f'Bearer {token}'},
            data={'logo': (f, 'file.txt')},
            content_type='multipart/form-data'
        )

    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
