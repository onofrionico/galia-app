"""WSAA: acceso a los web services de ARCA. El ticket (token + sign) dura 12 h y se guarda en arca_tokens."""
import base64
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import pytz
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs7

from app.extensions import db
from app.models import ArcaToken
from app.services.fiscal import settings as fiscal_settings
from app.services.fiscal.arca import ArcaRejected, ArcaUnavailable
from app.utils.timezone_utils import ARGENTINA_TZ

SERVICE = 'wsfe'
RENEW_BEFORE = timedelta(minutes=10)
STILL_USABLE = timedelta(seconds=30)
ALREADY_AUTHENTICATED = 'already_authenticated'
URLS = {'homologacion': 'https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl',
        'produccion': 'https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl'}


def build_tra(service, moment):
    """Ticket de requerimiento de acceso. `moment` en UTC naive."""
    local = pytz.utc.localize(moment).astimezone(ARGENTINA_TZ)
    return ('<?xml version="1.0" encoding="UTF-8"?><loginTicketRequest version="1.0"><header>'
            f'<uniqueId>{int(moment.replace(tzinfo=timezone.utc).timestamp())}</uniqueId>'
            f'<generationTime>{(local - timedelta(minutes=10)).isoformat(timespec="seconds")}</generationTime>'
            f'<expirationTime>{(local + timedelta(minutes=10)).isoformat(timespec="seconds")}</expirationTime>'
            f'</header><service>{service}</service></loginTicketRequest>')


def sign_tra(tra, cert_pem, key_pem):
    """CMS (PKCS#7) con el TRA adentro, firmado con SHA-256, en base64."""
    cert = x509.load_pem_x509_certificate(cert_pem.encode())
    key = serialization.load_pem_private_key(key_pem.encode(), password=None)
    der = (pkcs7.PKCS7SignatureBuilder().set_data(tra.encode()).add_signer(cert, key, hashes.SHA256())
           .sign(serialization.Encoding.DER, []))
    return base64.b64encode(der).decode()


def parse_login(xml):
    root = ET.fromstring(xml)
    token = root.findtext('credentials/token')
    sign = root.findtext('credentials/sign')
    expiration = root.findtext('header/expirationTime')
    if not token or not sign or not expiration:
        raise ArcaRejected([{'code': 'wsaa', 'msg': 'Respuesta del WSAA incompleta'}])
    expires = datetime.fromisoformat(expiration).astimezone(timezone.utc).replace(tzinfo=None)
    return token, sign, expires


def _soap_login(environment):
    def login(cms):
        from zeep import Client
        from zeep.exceptions import Fault
        from zeep.transports import Transport
        try:
            client = Client(URLS[environment], transport=Transport(timeout=10, operation_timeout=30))
            return client.service.loginCms(in0=cms)
        except Fault as fault:
            message = str(fault.message or fault)
            if 'alreadyAuthenticated' in message or 'ya posee un TA valido' in message:
                raise ArcaRejected([{'code': ALREADY_AUTHENTICATED, 'msg': message}])
            raise ArcaRejected([{'code': 'wsaa', 'msg': message}])
        except Exception as exc:  # red, timeout, WSDL
            raise ArcaUnavailable(str(exc))
    return login


def credentials(settings, login=None):
    """(token, sign) vigentes para wsfe en el entorno activo. Guarda el ticket apenas llega (commit propio)."""
    environment = settings.environment
    row = ArcaToken.query.filter_by(service=SERVICE, environment=environment).first()
    if row is not None and row.expires_at - RENEW_BEFORE > datetime.utcnow():
        return row.token, row.sign
    cert_pem, key_pem = fiscal_settings.active_credentials(settings)
    cms = sign_tra(build_tra(SERVICE, datetime.utcnow()), cert_pem, key_pem)
    try:
        response = (login or _soap_login(environment))(cms)
    except ArcaRejected as exc:
        if exc.errors and exc.errors[0]['code'] == ALREADY_AUTHENTICATED:
            # ARCA no entrega otro ticket mientras el anterior siga vigente (renovación anticipada, u otro
            # proceso que lo pidió al mismo tiempo): se usa el guardado mientras sirva.
            db.session.rollback()
            row = ArcaToken.query.filter_by(service=SERVICE, environment=environment).first()
            if row is not None and row.expires_at - STILL_USABLE > datetime.utcnow():
                return row.token, row.sign
            raise ArcaRejected([{'code': ALREADY_AUTHENTICATED, 'msg': (
                'ARCA ya entregó un acceso a este certificado que Galia no tiene guardado: '
                'se libera solo cuando vence (como máximo 12 h)')}])
        raise
    token, sign, expires = parse_login(response)
    if row is None:
        row = ArcaToken(service=SERVICE, environment=environment, token=token, sign=sign, expires_at=expires)
        db.session.add(row)
    else:
        row.token, row.sign, row.expires_at = token, sign, expires
    db.session.commit()
    return token, sign
