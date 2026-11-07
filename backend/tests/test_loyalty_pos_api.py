from app.extensions import db
from app.models.loyalty import LoyaltyMovement
from app.services.loyalty.search import mask_email, mask_phone
from loyalty_helpers import auth_headers, make_catalog, make_customer, make_reward, make_user, pos_app  # noqa: F401


def _client_and_cashier(pos_app):
    client = pos_app.test_client()
    cashier = make_user('caja@test.com', modules=('POS',))
    return client, auth_headers(client, cashier)


def test_search_ignores_accents_and_case(pos_app):
    client, headers = _client_and_cashier(pos_app)
    make_customer()
    found = client.get('/api/v1/loyalty/customers/search?q=LUCIA', headers=headers).get_json()
    assert [c['full_name'] for c in found] == ['Lucía Pérez']
    assert found[0]['balance'] == 0


def test_search_matches_every_word(pos_app):
    client, headers = _client_and_cashier(pos_app)
    make_customer()
    make_customer(first='Lucía', last='Gómez', email='lg@test.com')
    found = client.get('/api/v1/loyalty/customers/search?q=lucia per', headers=headers).get_json()
    assert [c['full_name'] for c in found] == ['Lucía Pérez']


def test_homonyms_show_distinct_masked_contacts(pos_app):
    client, headers = _client_and_cashier(pos_app)
    make_customer(email='lucia@gmail.com', phone='1155550032')
    make_customer(email='luperez@hotmail.com', phone='1166660099')
    found = client.get('/api/v1/loyalty/customers/search?q=lucia perez', headers=headers).get_json()
    assert len(found) == 2
    assert {c['email_masked'] for c in found} == {'lu…@gmail.com', 'lu…@hotmail.com'}
    assert {c['phone_masked'] for c in found} == {'11…0032', '11…0099'}


def test_masks():
    assert mask_email('lucia@gmail.com') == 'lu…@gmail.com'
    assert mask_email(None) is None
    assert mask_phone('1155550032') == '11…0032'
    assert mask_phone(None) is None


def test_search_by_qr_token_returns_exact_customer(pos_app):
    client, headers = _client_and_cashier(pos_app)
    customer = make_customer()
    make_customer(first='Juan', last='Gómez', email='juan@test.com')
    found = client.get(f'/api/v1/loyalty/customers/search?q={customer.qr_token}', headers=headers).get_json()
    assert [c['id'] for c in found] == [customer.id]


def test_search_requires_two_chars(pos_app):
    client, headers = _client_and_cashier(pos_app)
    make_customer()
    assert client.get('/api/v1/loyalty/customers/search?q=l', headers=headers).get_json() == []


def test_waiter_without_pos_module_gets_403(pos_app):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero', 'Cobrar'))
    headers = auth_headers(client, waiter)
    assert client.get('/api/v1/loyalty/customers/search?q=lu', headers=headers).status_code == 403
    assert client.get('/api/v1/loyalty/rewards', headers=headers).status_code == 403
    assert client.put('/api/v1/loyalty/pos-sales/1/customer', headers=headers, json={}).status_code == 403
    assert client.post('/api/v1/loyalty/pos-sales/1/redemptions', headers=headers, json={}).status_code == 403


def test_set_customer_and_redeem_via_api(pos_app):
    client, headers = _client_and_cashier(pos_app)
    cat = make_catalog()
    customer = make_customer()
    reward = make_reward(cat.taza, 8, name='Café gratis')
    db.session.add(LoyaltyMovement(customer_id=customer.id, kind='adjustment', amount=10, reason='seed'))
    db.session.commit()
    rewards = client.get('/api/v1/loyalty/rewards', headers=headers).get_json()
    assert rewards == [{'id': reward.id, 'name': 'Café gratis', 'cost': 8, 'product_variant_id': cat.taza.id,
                        'product_id': cat.cortado.id}]
    sale = client.post('/api/v1/pos/sales', headers=headers, json={'sale_type': 'counter'}).get_json()
    set_resp = client.put(f"/api/v1/loyalty/pos-sales/{sale['id']}/customer", headers=headers,
                          json={'customer_id': customer.id})
    assert set_resp.status_code == 200 and set_resp.get_json()['customer']['balance'] == 10
    redeemed = client.post(f"/api/v1/loyalty/pos-sales/{sale['id']}/redemptions", headers=headers,
                           json={'reward_id': reward.id, 'modifier_option_ids': [cat.entera.id]})
    body = redeemed.get_json()
    assert redeemed.status_code == 200 and body['customer']['balance'] == 2
    assert body['items'][0]['is_redemption'] is True and body['total'] == 0
    again = client.post(f"/api/v1/loyalty/pos-sales/{sale['id']}/redemptions", headers=headers,
                        json={'reward_id': reward.id, 'modifier_option_ids': [cat.entera.id]})
    assert again.status_code == 400 and 'Le faltan 6 cafecitos' in again.get_json()['error']
