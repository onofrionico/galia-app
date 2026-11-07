import pytest
import requests

from app.services.loyalty import customer_auth
from app.services.loyalty.errors import LoyaltyError
from loyalty_helpers import pos_app  # noqa: F401

GOOD = {'aud': 'client-123', 'iss': 'https://accounts.google.com', 'email_verified': 'true', 'sub': 'g-1',
        'email': 'lu@gmail.com', 'given_name': 'Lucía', 'family_name': 'Pérez'}


class _Resp:
    def __init__(self, status, body):
        self.status_code = status
        self._body = body

    def json(self):
        return self._body


@pytest.fixture
def google(pos_app, monkeypatch):
    pos_app.config['GOOGLE_CLIENT_ID'] = 'client-123'
    state = {'resp': _Resp(200, dict(GOOD))}

    def fake_get(url, params=None, timeout=None):
        if isinstance(state['resp'], Exception):
            raise state['resp']
        return state['resp']
    monkeypatch.setattr(customer_auth.requests, 'get', fake_get)
    return state


def test_valid_token_returns_identity(google):
    assert customer_auth.verify_google_credential('tok') == {
        'sub': 'g-1', 'email': 'lu@gmail.com', 'given_name': 'Lucía', 'family_name': 'Pérez'}


@pytest.mark.parametrize('change', [{'aud': 'otro'}, {'email_verified': 'false'}, {'iss': 'https://evil.example'},
                                    {'sub': ''}])
def test_invalid_claims_are_401(google, change):
    google['resp'] = _Resp(200, {**GOOD, **change})
    with pytest.raises(LoyaltyError) as exc:
        customer_auth.verify_google_credential('tok')
    assert exc.value.status == 401


def test_google_rejects_token_is_401(google):
    google['resp'] = _Resp(400, {'error': 'invalid_token'})
    with pytest.raises(LoyaltyError) as exc:
        customer_auth.verify_google_credential('tok')
    assert exc.value.status == 401


def test_network_error_is_503(google):
    google['resp'] = requests.Timeout()
    with pytest.raises(LoyaltyError) as exc:
        customer_auth.verify_google_credential('tok')
    assert exc.value.status == 503


def test_missing_client_id_is_503(google, pos_app):
    pos_app.config['GOOGLE_CLIENT_ID'] = None
    with pytest.raises(LoyaltyError) as exc:
        customer_auth.verify_google_credential('tok')
    assert exc.value.status == 503
