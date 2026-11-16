from datetime import timedelta

from app.utils.timezone_utils import get_current_date_argentina
from voucher_helpers import auth_headers, make_batch, make_catalog, make_user, open_sale, pos_app  # noqa: F401

BASE = '/api/v1/vouchers'


def _tomorrow():
    return (get_current_date_argentina() + timedelta(days=1)).isoformat()


def _body(**overrides):
    body = {'name': 'Sorteo', 'amount': '5000', 'quantity': 5, 'expires_at': _tomorrow(), 'terms': 'Consumo en el local'}
    body.update(overrides)
    return body


def _admin(client):
    return auth_headers(client, make_user('admin@test.com', role='admin'))


def _cashier(client, modules=('POS',)):
    user = make_user('caja@test.com', modules=modules)
    return user, auth_headers(client, user)


def test_admin_creates_and_lists_batch(pos_app):
    client = pos_app.test_client()
    headers = _admin(client)
    response = client.post(f'{BASE}/batches', json=_body(), headers=headers)
    assert response.status_code == 201
    created = response.get_json()
    assert created['issued'] == 5 and all(v['code'].startswith('GAL-') for v in created['vouchers'])
    listing = client.get(f'{BASE}/batches', headers=headers).get_json()
    assert [b['name'] for b in listing] == ['Sorteo'] and listing[0]['available'] == 5


def test_create_batch_invalid_returns_400(pos_app):
    client = pos_app.test_client()
    response = client.post(f'{BASE}/batches', json=_body(quantity=0), headers=_admin(client))
    assert response.status_code == 400 and 'cantidad' in response.get_json()['error']


def test_employee_without_module_gets_403(pos_app):
    client = pos_app.test_client()
    _, headers = _cashier(client, modules=())
    assert client.get(f'{BASE}/batches', headers=headers).status_code == 403


def test_cashier_with_pos_can_redeem_but_not_manage(pos_app):
    client = pos_app.test_client()
    cashier, headers = _cashier(client)
    sale = open_sale(cashier, make_catalog())
    voucher = make_batch(created_by=cashier.id).vouchers[0]
    assert client.get(f'{BASE}/batches', headers=headers).status_code == 403
    assert client.post(f'{BASE}/batches', json=_body(), headers=headers).status_code == 403
    assert client.post(f'{BASE}/{voucher.id}/void', json={'reason': 'x'}, headers=headers).status_code == 403
    response = client.post(f'{BASE}/pos-sales/{sale.id}/redeem', json={'code': voucher.code.lower()}, headers=headers)
    assert response.status_code == 200


def test_redeem_returns_sale_with_voucher_discount(pos_app):
    client = pos_app.test_client()
    cashier, headers = _cashier(client)
    sale = open_sale(cashier, make_catalog())
    voucher = make_batch(amount='1000', created_by=cashier.id).vouchers[0]
    data = client.post(f'{BASE}/pos-sales/{sale.id}/redeem', json={'code': voucher.code}, headers=headers).get_json()
    assert data['total'] == 1700 and data['discount_total'] == 1000
    assert data['discounts'][0]['voucher_code'] == f'GAL-{voucher.code[:5]}-{voucher.code[5:]}'


def test_second_redeem_returns_409(pos_app):
    client = pos_app.test_client()
    cashier, headers = _cashier(client)
    cat = make_catalog()
    first, second = open_sale(cashier, cat), open_sale(cashier, cat)
    voucher = make_batch(created_by=cashier.id).vouchers[0]
    assert client.post(f'{BASE}/pos-sales/{first.id}/redeem', json={'code': voucher.code}, headers=headers).status_code == 200
    response = client.post(f'{BASE}/pos-sales/{second.id}/redeem', json={'code': voucher.code}, headers=headers)
    assert response.status_code == 409 and 'ya está aplicado' in response.get_json()['error']
    missing = client.post(f'{BASE}/pos-sales/{second.id}/redeem', json={'code': 'nada'}, headers=headers)
    assert missing.status_code == 404


def test_void_and_extend_endpoints(pos_app):
    client = pos_app.test_client()
    headers = _admin(client)
    batch = client.post(f'{BASE}/batches', json=_body(), headers=headers).get_json()
    voucher_id = batch['vouchers'][0]['id']
    voided = client.post(f'{BASE}/{voucher_id}/void', json={'reason': 'Impreso con error'}, headers=headers)
    assert voided.status_code == 200 and voided.get_json()['voided'] == 1
    assert client.post(f'{BASE}/{voucher_id}/void', json={}, headers=headers).status_code == 400
    new_date = (get_current_date_argentina() + timedelta(days=40)).isoformat()
    extended = client.put(f"{BASE}/batches/{batch['id']}", json={'expires_at': new_date}, headers=headers)
    assert extended.status_code == 200 and extended.get_json()['expires_at'] == new_date


def test_cancel_discount_endpoint_accepts_reason(pos_app):
    client = pos_app.test_client()
    cashier, headers = _cashier(client, modules=('POS', 'Cobrar'))
    sale = open_sale(cashier, make_catalog())
    voucher = make_batch(created_by=cashier.id).vouchers[0]
    data = client.post(f'{BASE}/pos-sales/{sale.id}/redeem', json={'code': voucher.code}, headers=headers).get_json()
    discount_id = data['discounts'][0]['id']
    url = f'/api/v1/pos/discounts/{discount_id}/cancel'
    assert client.post(url, headers=headers).status_code == 400
    response = client.post(url, json={'reason': 'Lo pidió el cliente'}, headers=headers)
    assert response.status_code == 200 and response.get_json()['total'] == 2700


def test_batch_detail_exposes_codes_for_printing(pos_app):
    client = pos_app.test_client()
    headers = _admin(client)
    batch = client.post(f'{BASE}/batches', json=_body(terms='Válido de lunes a viernes'), headers=headers).get_json()
    detail = client.get(f"{BASE}/batches/{batch['id']}", headers=headers).get_json()
    assert detail['terms'] == 'Válido de lunes a viernes' and detail['amount'] == 5000
    assert all(len(v['code_raw']) == 10 and v['status'] == 'available' for v in detail['vouchers'])
    assert client.get(f'{BASE}/batches/9999', headers=headers).status_code == 404
