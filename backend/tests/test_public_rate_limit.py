"""Regresiones del bug bash 2026-11: rate limit, cache y ETag de los endpoints publicos."""
import pytest

from app.services import menu_publish_service
from app.utils import rate_limit as rl

IMAGE_NAME = '0123456789abcdef.webp'


@pytest.fixture
def limited(menu_app):
    menu_app.config['RATE_LIMIT_ENABLED'] = True
    rl.reset()
    yield menu_app
    rl.reset()


def test_google_login_is_rate_limited_per_ip(limited, menu_client):
    statuses = [menu_client.post('/api/public/loyalty/auth/google', json={}).status_code for _ in range(12)]
    assert 429 not in statuses[:10]
    assert statuses[10] == 429 and statuses[11] == 429
    blocked = menu_client.post('/api/public/loyalty/auth/google', json={})
    assert blocked.headers['Retry-After'].isdigit()
    # otra IP no queda bloqueada
    other = menu_client.post('/api/public/loyalty/auth/google', json={}, headers={'X-Forwarded-For': '9.9.9.9'})
    assert other.status_code != 429


def test_limit_is_off_in_testing_by_default(menu_app, menu_client):
    rl.reset()
    statuses = {menu_client.post('/api/public/loyalty/auth/google', json={}).status_code for _ in range(15)}
    assert 429 not in statuses


def test_menu_json_supports_etag_304(menu_client, storage):
    menu_publish_service.publish(storage)
    first = menu_client.get('/api/public/menu.json')
    etag = first.headers['ETag']
    assert first.status_code == 200 and etag
    second = menu_client.get('/api/public/menu.json', headers={'If-None-Match': etag})
    assert second.status_code == 304 and second.data == b''


def test_image_conditional_request_skips_storage(menu_client, storage):
    storage.put(f'images/{IMAGE_NAME}', b'RIFFdata', 'image/webp', 'x')
    first = menu_client.get(f'/api/public/menu/images/{IMAGE_NAME}')
    etag = first.headers['ETag']
    storage.objects.clear()  # si tocara el storage devolveria 404
    second = menu_client.get(f'/api/public/menu/images/{IMAGE_NAME}', headers={'If-None-Match': etag})
    assert second.status_code == 304


def test_etag_matches_after_compress_rewrites_it(menu_client, storage):
    """flask-compress devuelve el ETag como W/"hash:gzip"; el cliente lo reenvia asi y tiene que dar 304."""
    menu_publish_service.publish(storage)
    etag = menu_client.get('/api/public/menu.json').headers['ETag']
    core = etag.strip('"')
    for sent in (f'W/"{core}:gzip"', f'W/"{core}"', f'"x", "{core}"', '*'):
        response = menu_client.get('/api/public/menu.json', headers={'If-None-Match': sent})
        assert response.status_code == 304, sent
    assert menu_client.get('/api/public/menu.json', headers={'If-None-Match': 'W/"otro:gzip"'}).status_code == 200
