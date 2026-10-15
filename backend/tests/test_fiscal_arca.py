import base64
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs7

from app.models import ArcaToken
from app.services.fiscal import arca
from app.services.fiscal.arca import ArcaRejected, wsaa, wsfe
from app.services.fiscal.arca.fake import FakeArca
from fiscal_helpers import configure_fiscal, make_key_and_cert
from pos_helpers import pos_app  # noqa: F401


def test_tra_and_signed_cms_contains_tra_and_certificate():
    tra = wsaa.build_tra('wsfe', datetime(2026, 10, 14, 15, 0, 0))
    assert '<service>wsfe</service>' in tra and '<uniqueId>' in tra
    assert '2026-10-14T11:50:00-03:00' in tra and '2026-10-14T12:10:00-03:00' in tra
    key_pem, cert_pem = make_key_and_cert()
    der = base64.b64decode(wsaa.sign_tra(tra, cert_pem, key_pem))
    assert tra.encode() in der
    certs = pkcs7.load_der_pkcs7_certificates(der)
    assert certs[0].public_bytes(serialization.Encoding.PEM).decode() == cert_pem


def test_parse_login_response():
    xml = ('<?xml version="1.0"?><loginTicketResponse version="1.0"><header>'
           '<expirationTime>2026-10-15T03:00:00.123-03:00</expirationTime></header>'
           '<credentials><token>TOK</token><sign>SIG</sign></credentials></loginTicketResponse>')
    token, sign, expires = wsaa.parse_login(xml)
    assert (token, sign) == ('TOK', 'SIG') and expires == datetime(2026, 10, 15, 6, 0, 0, 123000)


def test_credentials_are_cached_until_near_expiry(pos_app):
    settings = configure_fiscal()
    calls = []

    def login(cms):
        calls.append(cms)
        expiry = (datetime.utcnow() + timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M:%S') + '+00:00'
        return (f'<loginTicketResponse><header><expirationTime>{expiry}</expirationTime></header>'
                f'<credentials><token>T{len(calls)}</token><sign>S</sign></credentials></loginTicketResponse>')

    assert wsaa.credentials(settings, login=login) == ('T1', 'S')
    assert wsaa.credentials(settings, login=login) == ('T1', 'S')
    assert len(calls) == 1 and ArcaToken.query.count() == 1
    token = ArcaToken.query.one()
    token.expires_at = datetime.utcnow() + timedelta(minutes=5)
    assert wsaa.credentials(settings, login=login) == ('T2', 'S')
    assert ArcaToken.query.count() == 1


def test_already_authenticated_reuses_the_stored_ticket(pos_app):
    settings = configure_fiscal()
    db_token = ArcaToken(service='wsfe', environment='homologacion', token='VIGENTE', sign='S',
                         expires_at=datetime.utcnow() + timedelta(minutes=5))
    from app.extensions import db
    db.session.add(db_token)
    db.session.commit()

    def login(cms):
        raise ArcaRejected([{'code': wsaa.ALREADY_AUTHENTICATED, 'msg': 'ya posee un TA valido'}])

    # Faltan 5 minutos (ventana de renovación): ARCA no da otro, se sigue usando el guardado.
    assert wsaa.credentials(settings, login=login) == ('VIGENTE', 'S')
    db_token.expires_at = datetime.utcnow() - timedelta(minutes=1)
    db.session.commit()
    with pytest.raises(ArcaRejected):
        wsaa.credentials(settings, login=login)


def test_build_detail_for_invoice_and_credit_note():
    fields = {'number': 42, 'voucher_date': date(2026, 10, 14), 'doc_type_code': 99,
              'doc_number': '0', 'total': Decimal('1800.00'), 'net': Decimal('1800.00'), 'iva': Decimal('0.00'),
              'iva_rate': Decimal('0'), 'discriminated': False, 'receiver_iva_id': 5, 'associated': None}
    detail = wsfe.build_detail(fields)
    assert detail == {'Concepto': 1, 'DocTipo': 99, 'DocNro': 0, 'CbteDesde': 42, 'CbteHasta': 42,
                      'CbteFch': '20261014', 'ImpTotal': 1800.0, 'ImpTotConc': 0, 'ImpNeto': 1800.0,
                      'ImpOpEx': 0, 'ImpIVA': 0.0, 'ImpTrib': 0, 'MonId': 'PES', 'MonCotiz': 1,
                      'CondicionIVAReceptorId': 5}
    fields.update({'discriminated': True, 'iva_rate': Decimal('21.00'), 'net': Decimal('1487.60'),
                   'iva': Decimal('312.40'),
                   'associated': {'type': 6, 'pos': 5, 'number': 41, 'cuit': '20123456786',
                                  'date': date(2026, 10, 13)}})
    detail = wsfe.build_detail(fields)
    assert detail['Iva'] == {'AlicIva': [{'Id': 5, 'BaseImp': 1487.6, 'Importe': 312.4}]}
    assert detail['CbtesAsoc'] == {'CbteAsoc': [{'Tipo': 6, 'PtoVta': 5, 'Nro': 41, 'Cuit': '20123456786',
                                                 'CbteFch': '20261013'}]}


def test_parse_cae_response_approved_rejected_and_errors():
    approved = {'FeCabResp': {'Resultado': 'A'}, 'FeDetResp': {'FECAEDetResponse': [
        {'Resultado': 'A', 'CAE': '75123456789012', 'CAEFchVto': '20261024',
         'Observaciones': {'Obs': [{'Code': 10217, 'Msg': 'Aviso'}]}}]}, 'Errors': None}
    result = wsfe.parse_cae_response(approved)
    assert result.result == 'A' and result.cae == '75123456789012'
    assert result.cae_due == date(2026, 10, 24) and result.observations == [{'code': 10217, 'msg': 'Aviso'}]
    rejected = {'FeCabResp': {'Resultado': 'R'}, 'FeDetResp': {'FECAEDetResponse': [
        {'Resultado': 'R', 'CAE': '', 'CAEFchVto': '',
         'Observaciones': {'Obs': [{'Code': 10015, 'Msg': 'Documento inválido'}]}}]}, 'Errors': None}
    result = wsfe.parse_cae_response(rejected)
    assert result.result == 'R' and result.observations[0]['msg'] == 'Documento inválido'
    with pytest.raises(ArcaRejected) as error:
        wsfe.parse_cae_response({'FeCabResp': None, 'FeDetResp': None,
                                 'Errors': {'Err': [{'Code': 600, 'Msg': 'Token inválido'}]}})
    assert error.value.errors == [{'code': 600, 'msg': 'Token inválido'}]


def test_parse_query_response():
    found = {'ResultGet': {'CodAutorizacion': '751', 'FchVto': '20261024', 'ImpTotal': 1800.0, 'DocTipo': 99,
                           'DocNro': 0, 'Resultado': 'A'}, 'Errors': None}
    assert wsfe.parse_query_response(found) == {'cae': '751', 'cae_due': date(2026, 10, 24),
                                                'total': Decimal('1800.00'), 'doc_type': 99, 'doc_number': '0'}
    assert wsfe.parse_query_response({'ResultGet': None, 'Errors': {'Err': [{'Code': 602, 'Msg': 'No existen'}]}}) \
        is None


def test_fake_gateway_only_with_sqlite_and_flag(pos_app, monkeypatch):
    settings = configure_fiscal()
    monkeypatch.setenv('FISCAL_FAKE_ARCA', '1')
    assert isinstance(arca.get_gateway(settings), FakeArca)
    FakeArca.reset()
    fake = FakeArca()
    assert fake.last_authorized(5, 11) == 0
    result = fake.request_cae(5, 11, {'CbteDesde': 1, 'ImpTotal': 10.0, 'DocTipo': 99, 'DocNro': 0})
    assert result.result == 'A' and fake.last_authorized(5, 11) == 1
    assert fake.query(11, 5, 1)['cae'] == result.cae and fake.query(11, 5, 2) is None
