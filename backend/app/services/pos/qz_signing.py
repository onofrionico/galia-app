"""Firma de los pedidos a QZ Tray y script para preparar una PC de impresión.

QZ Tray imprime sin preguntar cuando los pedidos vienen firmados con una clave cuyo certificado tiene instalado
como `override.crt`. Galia genera ese par sola la primera vez y lo guarda en la base (un solo par para todas las
PCs). Si están definidas QZ_CERTIFICATE y QZ_PRIVATE_KEY, se usan esas en su lugar.
"""
import base64
import os
from datetime import datetime, timedelta

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.pos import QzSigningKey
from app.services.pos.common import now
from app.services.pos.errors import bad_request

KEY_ID = 1
VALID_DAYS = 3650
SETUP_FILENAME = 'preparar-impresion-galia.bat'


def _env_pem(name):
    value = os.getenv(name)
    return value.replace('\\n', '\n') if value else None


def _generate_pair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Galia POS'),
                      x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'Galia')])
    start = datetime.utcnow() - timedelta(days=1)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(start)
            .not_valid_after(start + timedelta(days=VALID_DAYS)).sign(key, hashes.SHA256()))
    key_pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption()).decode()
    return cert.public_bytes(serialization.Encoding.PEM).decode(), key_pem


def _pair():
    """(certificado, clave privada) en PEM: los del entorno, o los de la base (generados la primera vez)."""
    cert_pem, key_pem = _env_pem('QZ_CERTIFICATE'), _env_pem('QZ_PRIVATE_KEY')
    if cert_pem and key_pem:
        return cert_pem, key_pem
    row = db.session.get(QzSigningKey, KEY_ID)
    if row is None:
        cert_pem, key_pem = _generate_pair()
        db.session.add(QzSigningKey(id=KEY_ID, certificate=cert_pem, private_key=key_pem, created_at=now()))
        try:
            db.session.commit()
        except IntegrityError:
            # Otro pedido lo generó al mismo tiempo: vale el que quedó guardado.
            db.session.rollback()
        row = db.session.get(QzSigningKey, KEY_ID)
    return row.certificate, row.private_key


def qz_certificate():
    return _pair()[0]


def sign_qz(message):
    """Firma el pedido de QZ Tray con RSA y SHA-512 (lo que espera qz.security con setSignatureAlgorithm('SHA512'))."""
    if not isinstance(message, str) or not message:
        raise bad_request('Falta el texto a firmar')
    key = serialization.load_pem_private_key(_pair()[1].encode(), password=None)
    return base64.b64encode(key.sign(message.encode(), padding.PKCS1v15(), hashes.SHA512())).decode()


def qz_setup_script():
    """Script .bat para Windows: con permiso de administrador instala el certificado en QZ Tray y lo reinicia."""
    cert_lines = [line for line in qz_certificate().strip().splitlines() if line]
    lines = [
        '@echo off',
        'rem Galia: prepara esta PC para imprimir con QZ Tray sin confirmaciones.',
        'net session >nul 2>&1',
        'if %errorlevel% neq 0 (',
        '  echo Pidiendo permiso de administrador...',
        '  powershell -NoProfile -Command "Start-Process -FilePath \'%~f0\' -Verb RunAs"',
        '  exit /b',
        ')',
        'set "QZDIR="',
        'if exist "%ProgramFiles%\\QZ Tray\\qz-tray.exe" set "QZDIR=%ProgramFiles%\\QZ Tray"',
        'if not defined QZDIR if exist "%ProgramFiles(x86)%\\QZ Tray\\qz-tray.exe" set "QZDIR=%ProgramFiles(x86)%\\QZ Tray"',
        'if not defined QZDIR (',
        '  echo No se encontro QZ Tray. Instalalo desde https://qz.io/download/ y volve a ejecutar este archivo.',
        '  pause',
        '  exit /b 1',
        ')',
        '(',
        *[f'echo {line}' for line in cert_lines],
        ') > "%QZDIR%\\override.crt"',
        'echo Certificado de Galia instalado en "%QZDIR%".',
        'echo Reiniciando QZ Tray...',
        'powershell -NoProfile -Command "Get-Process | Where-Object { $_.Path -like \'*QZ Tray*\' } | Stop-Process -Force"',
        'timeout /t 3 /nobreak >nul',
        'start "" "%QZDIR%\\qz-tray.exe"',
        'echo Listo. Volve a Galia, pagina Impresion: se conecta sola en unos segundos.',
        'pause',
    ]
    return '\r\n'.join(lines) + '\r\n'
