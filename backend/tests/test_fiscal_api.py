from datetime import datetime, timedelta

import pytest

from app.extensions import db
from app.models import Invoice
from app.services.fiscal import arca
from app.services.fiscal.arca.fake import FakeArca
from fiscal_helpers import closed_sale, configure_fiscal, make_key_and_cert
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401
from print_helpers import make_printer

BASE = '/api/v1/fiscal'


@pytest.fixture
def ctx(pos_app, monkeypatch):
    FakeArca.reset()
    monkeypatch.setattr(arca, 'get_gateway', lambda settings: FakeArca())
    client = pos_app.test_client()
    user = make_user('caja@test.com', modules=('POS', 'Anular'))
    headers = auth_headers(client, user)
    cat = make_catalog()
    _salon, t1, t2 = make_floor()
    make_printer('Térmica caja', cashier=True)
    return client, headers, user, cat, t1, t2


def test_invoice_flow_through_the_api(ctx):
    client, headers, user, cat, t1, _t2 = ctx
    configure_fiscal()
    sale = closed_sale(user, cat, t1)
    preview = client.get(f'{BASE}/sales/{sale.id}/preview', headers=headers).get_json()
    assert preview['amount'] == '1800.00' and preview['ready'] is True
    issued = client.post(f'{BASE}/sales/{sale.id}/invoice', json={'customer': {
        'doc_type': 'CUIT', 'doc_number': '20123456786', 'name': 'Cliente SA',
        'iva_condition': 'responsable_inscripto'}}, headers=headers)
    assert issued.status_code == 201 and issued.get_json()['label'] == 'Factura C 00005-00000001'
    invoice_id = issued.get_json()['id']
    sale_data = client.get(f'/api/v1/pos/sales/{sale.id}', headers=headers).get_json()
    assert sale_data['invoice']['label'] == 'Factura C 00005-00000001'
    customers = client.get(f'{BASE}/customers?q=2012', headers=headers).get_json()['customers']
    assert customers[0]['name'] == 'Cliente SA'
    assert client.get(f'{BASE}/customers?q=clie', headers=headers).get_json()['customers'][0]['doc_type'] == 'CUIT'
    assert client.post(f'{BASE}/invoices/{invoice_id}/reprint', headers=headers).status_code == 200
    listed = client.get(f'{BASE}/invoices', headers=headers).get_json()
    assert listed['total'] == 1 and listed['environment'] == 'homologacion'
    detail = client.get(f'{BASE}/invoices/{invoice_id}', headers=headers).get_json()
    assert detail['cae'] and detail['sale_link'] == f'/pos/salon/{t1.salon_id}?sale={sale.id}'
    cancelled = client.post(f'{BASE}/invoices/{invoice_id}/cancel', headers=headers)
    assert cancelled.status_code == 201 and cancelled.get_json()['kind'] == 'credit_note'
    filtered = client.get(f'{BASE}/invoices?kind=credit_note', headers=headers).get_json()
    assert [i['kind'] for i in filtered['invoices']] == ['credit_note']
    assert len(client.get(f'{BASE}/sales/{sale.id}/invoices', headers=headers).get_json()['invoices']) == 2
    assert client.get(f'{BASE}/invoices?from=xx', headers=headers).status_code == 400


def test_pending_and_rejected_status_codes(ctx):
    client, headers, user, cat, t1, t2 = ctx
    configure_fiscal()
    FakeArca.reset('reject')
    rejected = client.post(f'{BASE}/sales/{closed_sale(user, cat, t1).id}/invoice', json={}, headers=headers)
    assert rejected.status_code == 409 and 'ARCA rechazó' in rejected.get_json()['error']
    assert rejected.get_json()['invoice']['status'] == 'rejected'
    FakeArca.reset('timeout')
    pending = client.post(f'{BASE}/sales/{closed_sale(user, cat, t2).id}/invoice', json={}, headers=headers)
    assert pending.status_code == 202 and pending.get_json()['status'] == 'pending'
    FakeArca.mode = 'approve'
    recent = client.post(f"{BASE}/invoices/{pending.get_json()['id']}/verify", headers=headers)
    assert recent.status_code == 200 and recent.get_json()['status'] == 'pending'
    invoice = db.session.get(Invoice, pending.get_json()['id'])
    invoice.created_at = datetime.utcnow() - timedelta(seconds=121)
    db.session.commit()
    verified = client.post(f"{BASE}/invoices/{pending.get_json()['id']}/verify", headers=headers)
    assert verified.status_code == 200 and verified.get_json()['status'] == 'rejected'


def test_unconfigured_and_validation_errors(ctx):
    client, headers, user, cat, t1, _t2 = ctx
    sale = closed_sale(user, cat, t1)
    response = client.post(f'{BASE}/sales/{sale.id}/invoice', json={}, headers=headers)
    assert response.status_code == 409 and response.get_json()['error'].startswith('Falta configurar')
    configure_fiscal()
    bad = client.post(f'{BASE}/sales/{sale.id}/invoice', json={'customer': {'doc_type': 'DNI',
                                                                          'doc_number': '1'}}, headers=headers)
    assert bad.status_code == 400


def test_permissions(ctx):
    client, _headers, user, cat, t1, _t2 = ctx
    configure_fiscal()
    waiter = auth_headers(client, make_user('mozo@test.com', modules=('Camarero', 'Cobrar')))
    sale = closed_sale(user, cat, t1)
    assert client.get(f'{BASE}/sales/{sale.id}/preview', headers=waiter).status_code == 403
    assert client.get(f'{BASE}/settings', headers=waiter).status_code == 403
    pos_only = auth_headers(client, make_user('caja2@test.com', modules=('POS',)))
    invoice_id = client.post(f'{BASE}/sales/{sale.id}/invoice', json={}, headers=pos_only).get_json()['id']
    assert client.post(f'{BASE}/invoices/{invoice_id}/cancel', headers=pos_only).status_code == 403
    assert client.get(f'{BASE}/settings', headers=pos_only).status_code == 403


def test_settings_admin_flow(ctx):
    client, *_rest = ctx
    admin = auth_headers(client, make_user('admin@test.com', role='admin'))
    empty = client.get(f'{BASE}/settings', headers=admin).get_json()
    assert empty['missing'] and empty['environment'] == 'homologacion'
    bad = client.put(f'{BASE}/settings', json={'cuit': '20123456780'}, headers=admin)
    assert bad.status_code == 400
    saved = client.put(f'{BASE}/settings', json={
        'cuit': '20123456786', 'business_name': 'Galia Café', 'address': 'Calle 1', 'gross_income': 'Exento',
        'activity_start': '2020-01-01', 'iva_condition': 'monotributo', 'point_of_sale': 5,
        'cf_id_threshold': '10000000', 'default_iva_rate': '21'}, headers=admin)
    assert saved.status_code == 200 and saved.get_json()['missing'] == ['certificado de homologación']
    csr = client.post(f'{BASE}/settings/homologacion/csr', headers=admin).get_json()['csr']
    assert csr.startswith('-----BEGIN CERTIFICATE REQUEST-----')
    _key, other_cert = make_key_and_cert()
    wrong = client.put(f'{BASE}/settings/homologacion/certificate', json={'certificate': other_cert}, headers=admin)
    assert wrong.status_code == 400 and 'no corresponde' in wrong.get_json()['error']
    assert client.post(f'{BASE}/settings/staging/csr', headers=admin).status_code == 400
    assert client.put(f'{BASE}/settings', json={'environment': 'produccion'}, headers=admin).status_code == 200
    assert client.put(f'{BASE}/settings', json={'point_of_sale': 0}, headers=admin).status_code == 400
    assert client.put(f'{BASE}/settings', json={'default_iva_rate': '19'}, headers=admin).status_code == 400


def test_connection_test_endpoint(ctx):
    client, *_rest = ctx
    configure_fiscal()
    admin = auth_headers(client, make_user('admin@test.com', role='admin'))
    result = client.post(f'{BASE}/settings/test', headers=admin).get_json()
    assert result == {'ok': True, 'last_number': 0, 'label': 'Último comprobante: C 00005-00000000'}
