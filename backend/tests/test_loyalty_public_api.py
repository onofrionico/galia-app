from datetime import datetime

import pytest

from app.extensions import db
from app.models.loyalty import Customer, LoyaltyMovement
from app.services.loyalty import customer_auth
from app.services.loyalty.customer_auth import issue_customer_token
from app.services.loyalty.errors import LoyaltyError
from loyalty_helpers import auth_headers, make_catalog, make_customer, make_reward, make_user, pos_app  # noqa: F401

GOOGLE = {'sub': 'g-123', 'email': 'lucia@gmail.com', 'given_name': 'Lucía', 'family_name': 'Pérez'}


@pytest.fixture
def fake_google(monkeypatch):
    def verify(credential):
        if credential != 'good':
            raise LoyaltyError('Credencial de Google inválida', 401)
        return dict(GOOGLE)
    monkeypatch.setattr(customer_auth, 'verify_google_credential', verify)


def _bearer(token):
    return {'Authorization': f'Bearer {token}'}


def test_new_customer_needs_terms_then_registers(pos_app, fake_google):
    client = pos_app.test_client()
    first = client.post('/api/public/loyalty/auth/google', json={'credential': 'good'})
    assert first.status_code == 409 and first.get_json() == {'needs_terms': True, 'first_name': 'Lucía'}
    assert Customer.query.count() == 0
    created = client.post('/api/public/loyalty/auth/google', json={'credential': 'good', 'accept_terms': True})
    body = created.get_json()
    assert created.status_code == 201 and body['token']
    assert body['customer']['first_name'] == 'Lucía' and body['customer']['promo_opt_in'] is False
    customer = Customer.query.one()
    assert customer.google_sub == 'g-123' and customer.terms_accepted_at is not None


def test_bad_credential_is_401(pos_app, fake_google):
    client = pos_app.test_client()
    assert client.post('/api/public/loyalty/auth/google', json={'credential': 'bad'}).status_code == 401


def test_existing_customer_logs_in(pos_app, fake_google):
    client = pos_app.test_client()
    make_customer(google_sub='g-123')
    resp = client.post('/api/public/loyalty/auth/google', json={'credential': 'good'})
    assert resp.status_code == 200 and resp.get_json()['token']


def test_promo_opt_in_defaults_false_and_can_change(pos_app, fake_google):
    client = pos_app.test_client()
    body = client.post('/api/public/loyalty/auth/google',
                       json={'credential': 'good', 'accept_terms': True, 'promo_opt_in': True}).get_json()
    assert body['customer']['promo_opt_in'] is True
    headers = _bearer(body['token'])
    updated = client.patch('/api/public/loyalty/me', headers=headers,
                           json={'promo_opt_in': False, 'phone': ' 11 5555 0032 '}).get_json()
    assert updated['promo_opt_in'] is False and updated['phone'] == '11 5555 0032'


def test_me_returns_balance_and_qr(pos_app):
    client = pos_app.test_client()
    customer = make_customer()
    db.session.add(LoyaltyMovement(customer_id=customer.id, kind='adjustment', amount=14, reason='x'))
    db.session.commit()
    me = client.get('/api/public/loyalty/me', headers=_bearer(issue_customer_token(customer))).get_json()
    assert me['balance'] == 14 and me['qr_token'] == customer.qr_token and me['first_name'] == 'Lucía'


def test_movements_labels(pos_app):
    client = pos_app.test_client()
    cat = make_catalog()
    customer = make_customer()
    reward = make_reward(cat.taza, 8, name='Café gratis')
    rows = [('earn', 3, None), ('earn_reversal', -3, None), ('redeem', -8, reward.id),
            ('redeem_reversal', 8, reward.id), ('adjustment', 6, None)]
    for i, (kind, amount, reward_id) in enumerate(rows):
        db.session.add(LoyaltyMovement(customer_id=customer.id, kind=kind, amount=amount, reward_id=reward_id,
                                       created_at=datetime(2026, 11, 1 + i)))
    db.session.commit()
    movements = client.get('/api/public/loyalty/me/movements',
                           headers=_bearer(issue_customer_token(customer))).get_json()
    assert [m['label'] for m in movements] == ['ajuste', 'canje anulado', 'canje Café gratis', 'compra anulada',
                                               'compra']
    assert movements[0] == {'date': '2026-11-05', 'kind': 'adjustment', 'amount': 6, 'label': 'ajuste'}


def test_public_rewards_without_auth(pos_app):
    client = pos_app.test_client()
    cat = make_catalog()
    make_reward(cat.taza, 8, name='Café gratis')
    assert client.get('/api/public/loyalty/rewards').get_json() == [{'name': 'Café gratis', 'cost': 8}]


def test_customer_token_rejected_by_staff_endpoint(pos_app):
    client = pos_app.test_client()
    customer = make_customer()
    resp = client.get('/api/v1/loyalty/rewards', headers=_bearer(issue_customer_token(customer)))
    assert resp.status_code == 401


def test_staff_token_rejected_by_customer_endpoint(pos_app):
    client = pos_app.test_client()
    cashier = make_user('caja@test.com', modules=('POS',))
    assert client.get('/api/public/loyalty/me', headers=auth_headers(client, cashier)).status_code == 401
    assert client.get('/api/public/loyalty/me').status_code == 401
