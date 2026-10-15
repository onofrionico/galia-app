"""Fábricas compartidas por los tests de facturación."""
from datetime import date, datetime, timedelta

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from app.extensions import db
from app.services.fiscal import settings as fiscal_settings
from app.services.pos import payment_service, sale_service

CUIT = '20123456786'


def make_key_and_cert(cuit=CUIT, days=365, key=None):
    """(clave PEM, certificado PEM) autofirmado. Con `key`, el certificado es de esa clave."""
    key = key or rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'galia'),
                      x509.NameAttribute(NameOID.SERIAL_NUMBER, f'CUIT {cuit}')])
    start = datetime.utcnow() - timedelta(days=1)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(start)
            .not_valid_after(start + timedelta(days=days)).sign(key, hashes.SHA256()))
    key_pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption()).decode()
    return key_pem, cert.public_bytes(serialization.Encoding.PEM).decode()


def configure_fiscal(environment='homologacion', **overrides):
    settings = fiscal_settings.get_or_create_settings()
    settings.cuit = CUIT
    settings.business_name = 'Galia Café'
    settings.address = 'Av. Siempreviva 742'
    settings.gross_income = 'Exento'
    settings.activity_start = date(2020, 1, 1)
    settings.iva_condition = 'monotributo'
    settings.point_of_sale = 5
    settings.environment = environment
    key_pem, cert_pem = make_key_and_cert()
    settings.set_credential(environment, 'private_key', fiscal_settings.encrypt_key(key_pem))
    fiscal_settings.save_certificate(settings, environment, cert_pem)
    for name, value in overrides.items():
        setattr(settings, name, value)
    db.session.commit()
    return settings


def closed_sale(user, cat, table, amount_cash=None, amount_card=None):
    """Mesa con 2 medialunas ($1800) cobrada; sin montos: todo en efectivo."""
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=1)
    sale_service.add_item(user, sale.id, cat.unidad.id, quantity=2)
    sale_service.confirm_batch(user, sale.id)
    sale_service.request_bill(user, sale.id)
    if amount_cash is None and amount_card is None:
        amount_cash = 1800
    if amount_card:
        payment_service.add_payment(user, sale.id, cat.debito.id, amount_card)
    if amount_cash:
        payment_service.add_payment(user, sale.id, cat.efectivo.id, amount_cash)
    return sale
