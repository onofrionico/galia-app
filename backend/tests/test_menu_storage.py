import pytest
from app.utils.menu_storage import MenuStorage, public_url


class FakeS3Client:
    def __init__(self, keys=None):
        self.calls = []
        self.keys = keys or []

    def put_object(self, **kwargs):
        self.calls.append(('put', kwargs))

    def delete_object(self, **kwargs):
        self.calls.append(('delete', kwargs))

    def get_paginator(self, name):
        assert name == 'list_objects_v2'
        keys = self.keys

        class Paginator:
            def paginate(self, Bucket, Prefix):
                yield {'Contents': [{'Key': k} for k in keys if k.startswith(Prefix)]}

        return Paginator()


def test_put_prefixes_key_with_menu():
    client = FakeS3Client()
    storage = MenuStorage(client=client, bucket='bucket')
    storage.put('menu.json', b'{}', 'application/json', 'public, max-age=60')
    op, kwargs = client.calls[0]
    assert op == 'put'
    assert kwargs == {
        'Bucket': 'bucket', 'Key': 'menu/menu.json', 'Body': b'{}',
        'ContentType': 'application/json', 'CacheControl': 'public, max-age=60',
    }


@pytest.mark.parametrize('bad_key', ['', '../secret.pdf', 'images/../../x', '/'])
def test_rejects_keys_outside_prefix(bad_key):
    storage = MenuStorage(client=FakeS3Client(), bucket='bucket')
    with pytest.raises(ValueError):
        storage.put(bad_key, b'x', 'text/plain', 'no-cache')


def test_delete_prefixes_key():
    client = FakeS3Client()
    MenuStorage(client=client, bucket='bucket').delete('images/a.webp')
    assert client.calls == [('delete', {'Bucket': 'bucket', 'Key': 'menu/images/a.webp'})]


def test_list_returns_relative_keys():
    client = FakeS3Client(keys=['menu/images/a.webp', 'menu/menu.json', 'absence-attachments/x.pdf'])
    assert MenuStorage(client=client, bucket='bucket').list('images/') == ['images/a.webp']


def test_requires_bucket(monkeypatch):
    monkeypatch.delenv('AWS_S3_BUCKET_NAME', raising=False)
    with pytest.raises(ValueError):
        MenuStorage(client=FakeS3Client())


def test_public_url(monkeypatch):
    monkeypatch.setenv('MENU_PUBLIC_BASE_URL', 'https://cdn.test/menu/')
    assert public_url('images/a.webp') == 'https://cdn.test/menu/images/a.webp'
    assert public_url(None) is None
