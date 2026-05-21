"""
Tests for configuration API endpoints
Tests the branding configuration endpoint
"""
import pytest
from app import create_app
from app.extensions import db
from app.models.site_config import SiteConfig


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
