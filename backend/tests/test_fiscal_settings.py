from datetime import datetime, timedelta

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import serialization

from app.services.fiscal import settings as fs
from app.services.pos.errors import PosError
from fiscal_helpers import configure_fiscal, make_key_and_cert
from pos_helpers import pos_app  # noqa: F401


def test_key_encryption_round_trip_and_is_not_plaintext(pos_app):
    key_pem, _ = make_key_and_cert()
    token = fs.encrypt_key(key_pem)
    assert 'PRIVATE KEY' not in token and fs.decrypt_key(token) == key_pem


def test_undecryptable_key_reports_clear_error(pos_app):
    settings = configure_fiscal()
    pos_app.config['SECRET_KEY'] = 'otra-clave'
    with pytest.raises(PosError) as error:
        fs.active_credentials(settings)
    assert 'no se puede leer' in error.value.message
    assert any('no se puede leer' in item for item in fs.missing(settings))


def test_generate_csr_and_save_matching_certificate(pos_app):
    settings = configure_fiscal()
    csr_pem = fs.generate_csr(settings, 'produccion')
    csr = x509.load_pem_x509_csr(csr_pem.encode())
    assert csr.is_signature_valid
    assert 'CUIT 20123456786' in csr.subject.rfc4514_string()
    assert settings.prod_certificate is None and settings.prod_private_key
    _other_key, other_cert = make_key_and_cert()
    with pytest.raises(PosError) as error:
        fs.save_certificate(settings, 'produccion', other_cert)
    assert 'no corresponde' in error.value.message
    key = serialization.load_pem_private_key(fs.decrypt_key(settings.prod_private_key).encode(), None)
    _same_key_pem, cert_pem = make_key_and_cert(key=key, days=30)
    expires = fs.save_certificate(settings, 'produccion', cert_pem)
    assert expires > datetime.utcnow() + timedelta(days=28)
    with pytest.raises(PosError):
        fs.save_certificate(settings, 'produccion', 'no es un certificado')


def test_missing_lists_what_is_not_configured(pos_app):
    settings = fs.get_or_create_settings()
    missing = fs.missing(settings)
    assert any('CUIT' in item for item in missing) and any('punto de venta' in item for item in missing)
    assert any('certificado' in item for item in missing)
    with pytest.raises(PosError) as error:
        fs.require_ready(settings)
    assert error.value.message.startswith('Falta configurar la facturación')
    ready = configure_fiscal()
    assert fs.missing(ready) == []
    ready.homo_cert_expires_at = datetime.utcnow() - timedelta(days=1)
    assert any('venció' in item for item in fs.missing(ready))


def test_settings_to_dict_hides_secrets(pos_app):
    data = fs.settings_to_dict(configure_fiscal())
    assert data['cuit'] == '20123456786' and data['credentials']['homologacion']['has_certificate'] is True
    assert 'PRIVATE' not in str(data) and data['missing'] == []
