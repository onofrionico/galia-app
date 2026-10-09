import json

import pytest

from app.services import menu_publish_service
from app.utils.menu_storage import MenuStorage, public_url

CARTA_ORIGIN = 'https://galia-carta.onrender.com'
IMAGE_NAME = '0123456789abcdef.webp'


def test_menu_json_404_before_publish(menu_client):
    response = menu_client.get('/api/public/menu.json')
    assert response.status_code == 404
    assert response.get_json() == {'error': 'La carta todavía no se publicó'}


def test_menu_json_returns_published_snapshot(menu_client, storage):
    menu_publish_service.publish(storage)
    response = menu_client.get('/api/public/menu.json')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/json; charset=utf-8'
    assert response.headers['Cache-Control'] == 'public, max-age=60'
    assert json.loads(response.get_data(as_text=True)) == json.loads(storage.objects['menu.json']['body'])
    assert 'published_at' in response.get_json()


def test_published_snapshot_helper(menu_app, storage):
    assert menu_publish_service.published_snapshot() is None
    menu_publish_service.publish(storage)
    assert menu_publish_service.published_snapshot() == storage.objects['menu.json']['body'].decode('utf-8')


def test_image_served_from_storage(menu_client, storage):
    storage.put(f'images/{IMAGE_NAME}', b'RIFFdata', 'image/webp', 'x')
    response = menu_client.get(f'/api/public/menu/images/{IMAGE_NAME}')
    assert response.status_code == 200
    assert response.data == b'RIFFdata'
    assert response.headers['Content-Type'] == 'image/webp'
    assert response.headers['Cache-Control'] == 'public, max-age=31536000, immutable'


@pytest.mark.parametrize('name', ['abc.png', 'ABCDEF0123456789.webp', '0123456789abcdef.webp.png', 'x.webp', '..%2Fx'])
def test_bad_image_names_404_without_storage(menu_client, storage, name):
    def boom(*a, **k):
        raise AssertionError('storage tocado')
    storage.get = boom
    assert menu_client.get(f'/api/public/menu/images/{name}').status_code == 404


def test_missing_image_404(menu_client):
    assert menu_client.get(f'/api/public/menu/images/{IMAGE_NAME}').status_code == 404


def test_storage_error_502(menu_client, storage):
    def boom(rel_key):
        raise RuntimeError('s3 down')
    storage.get = boom
    assert menu_client.get(f'/api/public/menu/images/{IMAGE_NAME}').status_code == 502


def test_cors_header_for_carta_origin(menu_client, storage):
    menu_publish_service.publish(storage)
    response = menu_client.get('/api/public/menu.json', headers={'Origin': CARTA_ORIGIN})
    assert response.headers.getlist('Access-Control-Allow-Origin') == ['*']
    storage.put(f'images/{IMAGE_NAME}', b'x', 'image/webp', 'x')
    response = menu_client.get(f'/api/public/menu/images/{IMAGE_NAME}', headers={'Origin': CARTA_ORIGIN})
    assert response.headers.getlist('Access-Control-Allow-Origin') == ['*']


def test_image_url_composition(menu_app):
    assert public_url(f'images/{IMAGE_NAME}') == f'https://cdn.test/menu/images/{IMAGE_NAME}'


def test_image_url_composition_backend_base(menu_app, monkeypatch):
    monkeypatch.setenv('MENU_PUBLIC_BASE_URL', 'https://galia-backend.onrender.com/api/public/menu')
    assert public_url(f'images/{IMAGE_NAME}') == f'https://galia-backend.onrender.com/api/public/menu/images/{IMAGE_NAME}'


class _Client:
    def __init__(self, error=None):
        self.error = error

    def get_object(self, Bucket, Key):
        if self.error:
            raise self.error
        assert Key == 'menu/images/a.webp'

        class Body:
            def read(self_inner):
                return b'bytes'
        return {'Body': Body(), 'ContentType': 'image/webp'}


def test_menu_storage_get():
    assert MenuStorage(client=_Client(), bucket='b').get('images/a.webp') == (b'bytes', 'image/webp')


def test_menu_storage_get_missing_raises_keyerror():
    from botocore.exceptions import ClientError
    err = ClientError({'Error': {'Code': 'NoSuchKey', 'Message': 'x'}}, 'GetObject')
    with pytest.raises(KeyError):
        MenuStorage(client=_Client(err), bucket='b').get('images/a.webp')


def test_menu_storage_get_other_error_propagates():
    from botocore.exceptions import ClientError
    err = ClientError({'Error': {'Code': 'AccessDenied', 'Message': 'x'}}, 'GetObject')
    with pytest.raises(ClientError):
        MenuStorage(client=_Client(err), bucket='b').get('images/a.webp')
