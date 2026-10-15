"""Configuración fiscal y credenciales de ARCA (clave cifrada con una clave derivada de SECRET_KEY)."""
import base64
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from cryptography import x509
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.x509.oid import NameOID
from flask import current_app

from app.extensions import db
from app.models.fiscal import EMITTER_CONDITIONS, ENVIRONMENTS, SETTINGS_ID, FiscalSettings
from app.services.fiscal.receivers import valid_cuit
from app.services.pos.common import now
from app.services.pos.errors import PosError, bad_request
from app.utils.validation import clean_str

UNREADABLE = 'La clave del certificado no se puede leer: generá un certificado nuevo'
EXPIRY_WARNING = timedelta(days=30)
IVA_RATES = (Decimal('0'), Decimal('10.5'), Decimal('21'), Decimal('27'))


def get_settings(lock=False):
    query = FiscalSettings.query.filter_by(id=SETTINGS_ID)
    if lock:
        query = query.with_for_update().populate_existing()
    return query.first()


def get_or_create_settings():
    settings = get_settings()
    if settings is None:
        settings = FiscalSettings(id=SETTINGS_ID, iva_condition='monotributo', environment='homologacion',
                                  default_iva_rate=21)
        db.session.add(settings)
        db.session.flush()
    return settings


def _fernet():
    secret = current_app.config['SECRET_KEY'].encode()
    key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b'galia-fiscal-key').derive(secret)
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_key(pem):
    return _fernet().encrypt(pem.encode()).decode()


def decrypt_key(token):
    try:
        return _fernet().decrypt(token.encode()).decode()
    except (InvalidToken, ValueError, AttributeError):
        raise PosError(UNREADABLE)


def _check_environment(environment):
    if environment not in ENVIRONMENTS:
        raise bad_request('El entorno tiene que ser homologación o producción')


def generate_csr(settings, environment):
    """Clave RSA 2048 nueva y pedido de certificado para subir a ARCA. Borra el certificado anterior del entorno."""
    _check_environment(environment)
    if not settings.cuit or not settings.business_name:
        raise bad_request('Completá el CUIT y la razón social antes de generar el pedido')
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COUNTRY_NAME, 'AR'),
                         x509.NameAttribute(NameOID.ORGANIZATION_NAME, settings.business_name[:64]),
                         x509.NameAttribute(NameOID.COMMON_NAME, 'galia'),
                         x509.NameAttribute(NameOID.SERIAL_NUMBER, f'CUIT {settings.cuit}')])
    csr = x509.CertificateSigningRequestBuilder().subject_name(subject).sign(key, hashes.SHA256())
    key_pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption()).decode()
    csr_pem = csr.public_bytes(serialization.Encoding.PEM).decode()
    settings.set_credential(environment, 'private_key', encrypt_key(key_pem))
    settings.set_credential(environment, 'csr', csr_pem)
    settings.set_credential(environment, 'certificate', None)
    settings.set_credential(environment, 'cert_expires_at', None)
    settings.updated_at = now()
    return csr_pem


def save_certificate(settings, environment, pem):
    """Valida que el certificado sea PEM, corresponda a la clave del entorno y no esté vencido."""
    _check_environment(environment)
    try:
        cert = x509.load_pem_x509_certificate((pem or '').strip().encode())
    except ValueError:
        raise bad_request('Eso no es un certificado válido: pegá el contenido completo, con BEGIN y END')
    encrypted = settings.credential(environment, 'private_key')
    if not encrypted:
        raise bad_request('Primero generá el pedido de certificado (CSR)')
    key = serialization.load_pem_private_key(decrypt_key(encrypted).encode(), password=None)
    if cert.public_key().public_numbers() != key.public_key().public_numbers():
        raise bad_request('El certificado no corresponde a la clave de Galia: subí el CSR que generó Galia')
    expires = cert.not_valid_after
    if expires <= datetime.utcnow():
        raise bad_request(f'El certificado venció el {expires:%d/%m/%Y}')
    settings.set_credential(environment, 'certificate', cert.public_bytes(serialization.Encoding.PEM).decode())
    settings.set_credential(environment, 'cert_expires_at', expires)
    settings.updated_at = now()
    return expires


def _credential_problem(settings):
    environment = settings.environment
    if not settings.credential(environment, 'private_key') or not settings.credential(environment, 'certificate'):
        return f'certificado de {"homologación" if environment == "homologacion" else "producción"}'
    expires = settings.credential(environment, 'cert_expires_at')
    if expires and expires <= datetime.utcnow():
        return f'el certificado venció el {expires:%d/%m/%Y}: generá uno nuevo'
    try:
        decrypt_key(settings.credential(environment, 'private_key'))
    except PosError:
        return 'la clave del certificado no se puede leer: generá un certificado nuevo'
    return None


def missing(settings):
    if settings is None:
        return ['CUIT y datos del emisor', 'punto de venta', 'certificado']
    items = []
    if not settings.cuit or not settings.business_name or not settings.address or not settings.activity_start:
        items.append('CUIT y datos del emisor')
    if not settings.point_of_sale:
        items.append('punto de venta')
    problem = _credential_problem(settings)
    if problem:
        items.append(problem)
    return items


def require_ready(settings):
    items = missing(settings)
    if items:
        raise PosError(f'Falta configurar la facturación: {", ".join(items)}')


def active_credentials(settings):
    environment = settings.environment
    cert = settings.credential(environment, 'certificate')
    encrypted = settings.credential(environment, 'private_key')
    if not cert or not encrypted:
        raise PosError('Falta configurar la facturación: certificado')
    return cert, decrypt_key(encrypted)


def settings_to_dict(settings):
    def creds(environment):
        expires = settings.credential(environment, 'cert_expires_at')
        return {'has_key': bool(settings.credential(environment, 'private_key')),
                'has_csr': bool(settings.credential(environment, 'csr')),
                'has_certificate': bool(settings.credential(environment, 'certificate')),
                'expires_at': expires.isoformat() if expires else None,
                'expires_soon': bool(expires and expires - datetime.utcnow() < EXPIRY_WARNING)}

    return {
        'cuit': settings.cuit, 'business_name': settings.business_name, 'address': settings.address,
        'gross_income': settings.gross_income,
        'activity_start': settings.activity_start.isoformat() if settings.activity_start else None,
        'iva_condition': settings.iva_condition, 'point_of_sale': settings.point_of_sale,
        'environment': settings.environment,
        'cf_id_threshold': f'{settings.cf_id_threshold:.2f}' if settings.cf_id_threshold is not None else None,
        'default_iva_rate': f'{Decimal(settings.default_iva_rate):.2f}',
        'credentials': {env: creds(env) for env in ENVIRONMENTS},
        'missing': missing(settings),
    }


def _decimal(value, label):
    if value in (None, ''):
        return None
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        raise bad_request(f'{label} es inválido')
    if not number.is_finite() or number < 0:
        raise bad_request(f'{label} es inválido')
    return number


def update_settings(data):
    """Datos del emisor, punto de venta, entorno, umbral de identificación y alícuota. No hace commit."""
    settings = get_or_create_settings()
    if 'cuit' in data:
        cuit = ''.join(ch for ch in str(data['cuit'] or '') if ch.isdigit())
        if not valid_cuit(cuit):
            raise bad_request('El CUIT es inválido')
        settings.cuit = cuit
    for field, limit in (('business_name', 120), ('address', 200), ('gross_income', 40)):
        if field in data:
            setattr(settings, field, clean_str(data[field], limit))
    if 'activity_start' in data:
        try:
            settings.activity_start = date.fromisoformat(data['activity_start']) if data['activity_start'] else None
        except (TypeError, ValueError):
            raise bad_request('La fecha de inicio de actividades es inválida')
    if 'iva_condition' in data:
        if data['iva_condition'] not in EMITTER_CONDITIONS:
            raise bad_request('La condición frente al IVA es inválida')
        settings.iva_condition = data['iva_condition']
    if 'point_of_sale' in data:
        value = data['point_of_sale']
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 99999:
            raise bad_request('El punto de venta tiene que ser un número entre 1 y 99999')
        settings.point_of_sale = value
    if 'environment' in data:
        _check_environment(data['environment'])
        settings.environment = data['environment']
    if 'cf_id_threshold' in data:
        settings.cf_id_threshold = _decimal(data['cf_id_threshold'], 'El umbral de identificación')
    if 'default_iva_rate' in data:
        rate = _decimal(data['default_iva_rate'], 'La alícuota de IVA')
        if rate not in IVA_RATES:
            raise bad_request('La alícuota tiene que ser 0, 10,5, 21 o 27')
        settings.default_iva_rate = rate
    settings.updated_at = now()
    return settings
