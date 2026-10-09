import pytest

from app.utils.menu_storage import public_url

HASH = '0123456789abcdef'


@pytest.mark.parametrize('key', [
    f'products/{HASH}.webp',
    f'branding/logo-{HASH}.webp',
    f'branding/banner-{HASH}.webp',
])
def test_asset_served_at_public_url_path(menu_client, storage, monkeypatch, key):
    # En producción MENU_PUBLIC_BASE_URL apunta al backend: la URL que guardamos debe resolverse acá.
    monkeypatch.setenv('MENU_PUBLIC_BASE_URL', 'https://galia-backend.onrender.com/api/public/menu')
    storage.put(key, b'RIFFdata', 'image/webp', 'x')
    path = public_url(key).replace('https://galia-backend.onrender.com', '')
    response = menu_client.get(path)
    assert response.status_code == 200
    assert response.data == b'RIFFdata'
    assert response.headers['Content-Type'] == 'image/webp'
    assert response.headers['Cache-Control'] == 'public, max-age=31536000, immutable'
    assert response.headers['Access-Control-Allow-Origin'] == '*'


@pytest.mark.parametrize('path', [
    f'/api/public/menu/products/logo-{HASH}.webp',
    f'/api/public/menu/branding/{HASH}.webp',
    f'/api/public/menu/branding/other-{HASH}.webp',
    '/api/public/menu/products/..%2Fmenu.json',
    f'/api/public/menu/secrets/{HASH}.webp',
])
def test_invalid_asset_names_are_404(menu_client, path):
    assert menu_client.get(path).status_code == 404


def test_missing_asset_is_404(menu_client):
    assert menu_client.get(f'/api/public/menu/products/{HASH}.webp').status_code == 404


def test_storage_error_is_502(menu_client, storage, monkeypatch):
    def boom(_key):
        raise RuntimeError('s3 down')
    monkeypatch.setattr(storage, 'get', boom)
    assert menu_client.get(f'/api/public/menu/products/{HASH}.webp').status_code == 502
