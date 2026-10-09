import io

import pytest
from PIL import Image

from app import create_app
from app.extensions import db
from app.models import SiteConfig
from app.models.user import User
from menu_fakes import FakeStorage


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv('MENU_PUBLIC_BASE_URL', 'https://cdn.test/menu')
    app = create_app('testing')
    app.extensions['menu_storage'] = FakeStorage()
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def storage(app):
    return app.extensions['menu_storage']


def _headers(client, email, role):
    user = User(email=email, role=role, is_active=True)
    user.set_password('secret123')
    db.session.add(user)
    db.session.commit()
    token = client.post('/api/v1/auth/login', json={'email': email, 'password': 'secret123'}).get_json()['token']
    return {'Authorization': f'Bearer {token}'}


def _png(size=(2400, 1200)):
    buffer = io.BytesIO()
    Image.new('RGBA', size, color=(10, 20, 30, 255)).save(buffer, format='PNG')
    buffer.seek(0)
    return buffer


def test_get_branding_is_public_and_empty_by_default(client):
    response = client.get('/api/v1/config/branding')
    assert response.status_code == 200
    assert response.get_json() == {'logo_path': None, 'banner_background_path': None}


def test_admin_uploads_logo_and_banner(client, storage):
    headers = _headers(client, 'a@test.com', 'admin')
    response = client.post('/api/v1/admin/config/branding', headers=headers, content_type='multipart/form-data',
                           data={'logo': (_png(), 'logo.png'), 'background': (_png(), 'banner.png')})
    assert response.status_code == 200, response.get_json()
    data = response.get_json()
    assert data['logo_path'].startswith('https://cdn.test/menu/branding/logo-')
    assert data['banner_background_path'].startswith('https://cdn.test/menu/branding/banner-')
    banner_key = next(k for k in storage.objects if k.startswith('branding/banner-'))
    banner = Image.open(io.BytesIO(storage.objects[banner_key]['body']))
    assert max(banner.size) == 1920
    logo_key = next(k for k in storage.objects if k.startswith('branding/logo-'))
    assert max(Image.open(io.BytesIO(storage.objects[logo_key]['body'])).size) == 800
    assert SiteConfig.query.count() == 1


def test_upload_requires_a_file(client):
    headers = _headers(client, 'a@test.com', 'admin')
    response = client.post('/api/v1/admin/config/branding', headers=headers, content_type='multipart/form-data', data={})
    assert response.status_code == 400


def test_upload_rejects_non_images(client, storage):
    headers = _headers(client, 'a@test.com', 'admin')
    response = client.post('/api/v1/admin/config/branding', headers=headers, content_type='multipart/form-data',
                           data={'logo': (io.BytesIO(b'texto'), 'logo.png')})
    assert response.status_code == 400
    assert storage.objects == {}


def test_employee_cannot_upload(client):
    headers = _headers(client, 'e@test.com', 'employee')
    response = client.post('/api/v1/admin/config/branding', headers=headers, content_type='multipart/form-data',
                           data={'logo': (_png(), 'logo.png')})
    assert response.status_code == 403


def _upload(client, headers, **files):
    return client.post('/api/v1/admin/config/branding', headers=headers, content_type='multipart/form-data',
                       data={field: (_png(), f'{field}.png') for field in files})


def test_partial_upload_keeps_existing_banner(client):
    headers = _headers(client, 'a@test.com', 'admin')
    first = _upload(client, headers, logo=1, background=1).get_json()
    second = _upload(client, headers, logo=1)
    assert second.status_code == 200
    data = second.get_json()
    assert data['banner_background_path'] == first['banner_background_path']
    assert data['logo_path'] == first['logo_path']  # keys are content-hashed: same image, same key
    assert SiteConfig.query.count() == 1


def test_storage_failure_returns_502_and_creates_no_row(client, storage, monkeypatch):
    headers = _headers(client, 'a@test.com', 'admin')

    def boom(*args, **kwargs):
        raise RuntimeError('s3 down')

    monkeypatch.setattr(storage, 'put', boom)
    response = _upload(client, headers, logo=1)
    assert response.status_code == 502
    assert SiteConfig.query.count() == 0


def test_get_returns_populated_urls_after_upload(client):
    headers = _headers(client, 'a@test.com', 'admin')
    uploaded = _upload(client, headers, logo=1, background=1).get_json()
    data = client.get('/api/v1/config/branding').get_json()
    assert data['logo_path'] == uploaded['logo_path']
    assert data['banner_background_path'] == uploaded['banner_background_path']


def test_upload_requires_auth(client):
    response = client.post('/api/v1/admin/config/branding', content_type='multipart/form-data',
                           data={'logo': (_png(), 'logo.png')})
    assert response.status_code == 401
