"""Configuración de MercadoPago: tokens y secreto cifrados con una clave derivada de SECRET_KEY."""
import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from flask import current_app

from app.extensions import db
from app.models import MpSettings, PaymentMethod
from app.models.mercadopago import SETTINGS_ID
from app.services.pos.errors import PosError

UNREADABLE = 'El token de MercadoPago no se puede leer: cargalo de nuevo'


def get_settings(lock=False):
    query = MpSettings.query.filter_by(id=SETTINGS_ID)
    if lock:
        query = query.with_for_update().populate_existing()
    return query.first()


def get_or_create_settings():
    settings = get_settings()
    if settings is None:
        settings = MpSettings(id=SETTINGS_ID, environment='test')
        db.session.add(settings)
        db.session.flush()
    return settings


def _fernet():
    key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b'galia-mp-token').derive(
        current_app.config['SECRET_KEY'].encode())
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt(text):
    return _fernet().encrypt(text.encode()).decode()


def decrypt(token):
    try:
        return _fernet().decrypt(token.encode()).decode()
    except (InvalidToken, ValueError, AttributeError):
        raise PosError(UNREADABLE)


def access_token(settings):
    token = settings.token(settings.environment) if settings else None
    if not token:
        raise PosError('Falta configurar MercadoPago: token')
    return decrypt(token)


def webhook_secret(settings):
    if settings is None or not settings.webhook_secret:
        return None
    try:
        return decrypt(settings.webhook_secret)
    except PosError:
        return None


def missing(settings):
    if settings is None:
        return ['token de prueba', 'terminal', 'medio de pago del Point']
    items = []
    token = settings.token(settings.environment)
    if not token:
        items.append('token de prueba' if settings.environment == 'test' else 'token de producción')
    else:
        try:
            decrypt(token)
        except PosError:
            items.append('el token no se puede leer: cargalo de nuevo')
    if not settings.terminal_id:
        items.append('terminal')
    method = db.session.get(PaymentMethod, settings.point_payment_method_id) if settings.point_payment_method_id \
        else None
    if method is None or not method.is_active:
        items.append('medio de pago del Point')
    return items


def require_ready(settings):
    items = missing(settings)
    if items:
        raise PosError(f'Falta configurar MercadoPago: {", ".join(items)}')


def settings_to_dict(settings):
    return {'environment': settings.environment, 'has_test_token': bool(settings.test_access_token),
            'has_prod_token': bool(settings.prod_access_token), 'terminal_id': settings.terminal_id,
            'has_webhook_secret': bool(settings.webhook_secret),
            'point_payment_method_id': settings.point_payment_method_id, 'user_id': settings.user_id,
            'missing': missing(settings)}
