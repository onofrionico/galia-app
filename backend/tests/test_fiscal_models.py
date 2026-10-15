from decimal import Decimal

from app.extensions import db
from app.models import Invoice, PaymentMethod
from app.models.pos import PRINT_JOB_KINDS
from app.services.pos.common import now
from pos_helpers import auth_headers, make_catalog, make_user, pos_app  # noqa: F401


def test_invoiced_externally_defaults_by_kind(pos_app):
    cat = make_catalog()
    assert cat.efectivo.invoiced_externally is False
    assert cat.debito.invoiced_externally is True
    assert 'invoice' in PRINT_JOB_KINDS


def test_payment_method_flag_via_config_api(pos_app):
    client = pos_app.test_client()
    admin = auth_headers(client, make_user('admin@test.com', role='admin'))
    created = client.post('/api/v1/pos/config/payment-methods', json={'name': 'QR', 'kind': 'other'}, headers=admin)
    assert created.status_code == 201 and created.get_json()['invoiced_externally'] is True
    cash = client.post('/api/v1/pos/config/payment-methods', json={'name': 'Caja chica', 'kind': 'cash'},
                       headers=admin).get_json()
    assert cash['invoiced_externally'] is False
    updated = client.put(f"/api/v1/pos/config/payment-methods/{created.get_json()['id']}",
                         json={'invoiced_externally': False}, headers=admin)
    assert updated.status_code == 200 and updated.get_json()['invoiced_externally'] is False
    assert db.session.get(PaymentMethod, cash['id']).invoiced_externally is False


def test_invoice_label_and_letter(pos_app):
    user = make_user('caja@test.com', modules=('POS',))
    invoice = Invoice(kind='invoice', voucher_type=11, environment='homologacion', point_of_sale=5, number=123,
                      receiver_doc_type=99, receiver_doc_number='0', receiver_name='Consumidor final',
                      receiver_iva_condition='consumidor_final', detail_mode='generic', lines=[],
                      total=Decimal('10'), net=Decimal('10'), iva=Decimal('0'), iva_rate=Decimal('0'),
                      voucher_date=now().date(), status='pending', request={}, created_by=user.id,
                      created_at=now())
    db.session.add(invoice)
    db.session.commit()
    assert invoice.letter == 'C' and invoice.label == 'Factura C 00005-00000123'
    invoice.voucher_type = 13
    invoice.kind = 'credit_note'
    assert invoice.label == 'Nota de crédito C 00005-00000123' and invoice.is_credit_note
