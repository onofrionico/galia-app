import gzip
import json

from app.extensions import db
from app.models.pos import CancelReason
from pos_helpers import auth_headers, make_user, pos_app  # noqa: F401


def test_large_json_responses_are_gzipped(pos_app):
    client = pos_app.test_client()
    admin = make_user('admin@test.com', role='admin')
    db.session.add_all([CancelReason(name=f'Motivo de prueba número {i}', position=i) for i in range(40)])
    db.session.commit()
    headers = {**auth_headers(client, admin), 'Accept-Encoding': 'gzip'}
    response = client.get('/api/v1/pos/config/cancel-reasons', headers=headers)
    assert response.status_code == 200
    assert response.headers.get('Content-Encoding') == 'gzip'
    body = json.loads(gzip.decompress(response.data))
    assert body['cancel_reasons'][0]['name'] == 'Motivo de prueba número 0'


def test_responses_are_plain_without_accept_encoding(pos_app):
    client = pos_app.test_client()
    admin = make_user('admin@test.com', role='admin')
    response = client.get('/api/v1/pos/config/cancel-reasons', headers=auth_headers(client, admin))
    assert response.headers.get('Content-Encoding') is None and response.get_json() == {'cancel_reasons': []}
