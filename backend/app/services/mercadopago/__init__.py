"""MercadoPago: cliente REST propio o FakeMercadoPago (desarrollo y tests)."""
import os

from app.extensions import db


class MpUnavailable(Exception):
    """MercadoPago no respondió (red, timeout, 5xx)."""


class MpRejected(Exception):
    """MercadoPago respondió con un error (4xx)."""

    def __init__(self, status, code, message):
        super().__init__(f'{status} {code}: {message}')
        self.status = status
        self.code = code
        self.message = message


def fake_enabled():
    return os.getenv('MP_FAKE') == '1' and db.engine.dialect.name == 'sqlite'


def get_client(settings):
    if fake_enabled():
        from app.services.mercadopago.fake import FakeMercadoPago
        return FakeMercadoPago()
    from app.services.mercadopago import settings as mp_settings
    from app.services.mercadopago.client import MpClient
    return MpClient(mp_settings.access_token(settings))
