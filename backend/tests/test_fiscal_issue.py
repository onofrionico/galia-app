import base64
import json
from datetime import datetime, timedelta

import pytest

from app.extensions import db
from app.models import FiscalCustomer
from app.models.pos import PrintJob
from app.services.fiscal import arca, invoice_service
from app.services.fiscal.arca.fake import FakeArca
from app.services.fiscal.invoice_documents import qr_url
from app.services.pos import sale_service
from app.services.pos.errors import PosError
from fiscal_helpers import closed_sale, configure_fiscal
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401
from print_helpers import make_printer


@pytest.fixture
def ctx(pos_app, monkeypatch):
    FakeArca.reset()
    monkeypatch.setattr(arca, 'get_gateway', lambda settings: FakeArca())
    user = make_user('caja@test.com', modules=('POS', 'Anular'))
    cat = make_catalog()
    _salon, t1, t2 = make_floor()
    settings = configure_fiscal()
    printer = make_printer('Térmica caja', cashier=True)
    return user, cat, t1, t2, settings, printer


def test_preview_full_and_partial(ctx):
    user, cat, t1, t2, _s, _p = ctx
    full = closed_sale(user, cat, t1)
    data = invoice_service.preview(full.id)
    assert data['amount'] == '1800.00' and data['detail_mode'] == 'items' and data['letter'] == 'C'
    assert data['ready'] is True and data['active_invoice'] is None
    partial = closed_sale(user, cat, t2, amount_cash=1000, amount_card=800)
    data = invoice_service.preview(partial.id)
    assert data['amount'] == '1000.00' and data['detail_mode'] == 'generic'
    assert data['lines'][0]['description'] == f'Consumo – Venta #{partial.number}'


def test_issue_authorized_prints_and_saves_customer(ctx):
    user, cat, t1, _t2, _settings, printer = ctx
    sale = closed_sale(user, cat, t1)
    invoice = invoice_service.issue(user, sale.id, {'doc_type': 'DNI', 'doc_number': '30123456', 'name': 'Ana',
                                                    'iva_condition': 'consumidor_final'})
    assert invoice.status == 'authorized' and invoice.number == 1 and invoice.cae
    assert invoice.label == 'Factura C 00005-00000001' and invoice.voucher_type == 11
    assert [p.amount for p in invoice.payments] == [invoice.total]
    assert FiscalCustomer.query.one().name == 'Ana'
    job = PrintJob.query.filter_by(kind='invoice').one()
    assert job.printer_id == printer.id and job.document['title'] == 'FACTURA C'
    assert 'CAE ' + invoice.cae in job.document['footer']
    assert job.document['qr'].startswith('https://www.afip.gob.ar/fe/qr/?p=')
    assert 'SIN VALIDEZ FISCAL – PRUEBA' in job.document['footer']
    assert 'DNI 30123456' in job.document['header'] and 'Cliente: Ana' in job.document['header']
    assert invoice_service.active_invoice(sale.id).id == invoice.id
    with pytest.raises(PosError) as error:
        invoice_service.issue(user, sale.id, None)
    assert 'ya tiene la Factura C 00005-00000001' in error.value.message


def test_rejected_frees_the_number(ctx):
    user, cat, t1, _t2, _s, _p = ctx
    FakeArca.reset('reject')
    sale = closed_sale(user, cat, t1)
    invoice = invoice_service.issue(user, sale.id, None)
    assert invoice.status == 'rejected' and 'Documento del receptor inválido' in invoice.error
    FakeArca.mode = 'approve'
    again = invoice_service.issue(user, sale.id, None)
    assert again.status == 'authorized' and again.number == 1


def test_timeout_leaves_pending_and_verify_rejects_when_arca_never_got_it(ctx):
    user, cat, t1, t2, _s, _p = ctx
    FakeArca.reset('timeout')
    sale = closed_sale(user, cat, t1)
    invoice = invoice_service.issue(user, sale.id, None)
    assert invoice.status == 'pending'
    other = closed_sale(user, cat, t2)
    with pytest.raises(PosError) as error:
        invoice_service.issue(user, other.id, None)
    assert 'emitiéndose' in error.value.message
    db.session.rollback()
    FakeArca.mode = 'approve'
    resolved = invoice_service.verify(user, invoice.id)
    assert resolved.status == 'rejected' and resolved.error == 'No llegó a ARCA'


def test_timeout_after_arca_issued_resolves_to_authorized(ctx):
    user, cat, t1, t2, _s, _p = ctx
    FakeArca.reset('timeout_after_issue')
    sale = closed_sale(user, cat, t1)
    invoice = invoice_service.issue(user, sale.id, None)
    assert invoice.status == 'pending'
    FakeArca.mode = 'approve'
    invoice.created_at = datetime.utcnow() - timedelta(seconds=121)
    db.session.commit()
    # La próxima emisión resuelve el pending viejo antes de reservar: queda autorizado con el CAE de ARCA.
    nxt = invoice_service.issue(user, closed_sale(user, cat, t2).id, None)
    db.session.refresh(invoice)
    assert invoice.status == 'authorized' and invoice.cae == FakeArca.issued[(5, 11)][1]['cae']
    assert nxt.number == 2 and nxt.status == 'authorized'
    assert PrintJob.query.filter_by(kind='invoice').count() == 2


def test_cannot_invoice_open_sale_external_only_or_unconfigured(ctx):
    user, cat, t1, t2, settings, _p = ctx
    open_sale = sale_service.open_sale(user, 'salon', table_id=t1.id, people=1)
    with pytest.raises(PosError) as error:
        invoice_service.issue(user, open_sale.id, None)
    assert error.value.message == 'Solo se factura una venta cerrada'
    db.session.rollback()
    card_only = closed_sale(user, cat, t2, amount_card=1800)
    with pytest.raises(PosError) as error:
        invoice_service.issue(user, card_only.id, None)
    assert error.value.message == 'Todo lo cobrado en esta venta lo factura otro sistema'
    db.session.rollback()
    settings.point_of_sale = None
    db.session.commit()
    assert invoice_service.preview(card_only.id)['ready'] is False


def test_invoice_without_cashier_printer_still_authorizes(ctx):
    user, cat, t1, _t2, _s, printer = ctx
    printer.is_active = False
    db.session.commit()
    invoice = invoice_service.issue(user, closed_sale(user, cat, t1).id, None)
    data = invoice_service.invoice_to_dict(invoice)
    assert invoice.status == 'authorized' and data['print_warning'] == 'No hay impresora de caja configurada'


def test_qr_url_payload(ctx):
    user, cat, t1, _t2, _s, _p = ctx
    invoice = invoice_service.issue(user, closed_sale(user, cat, t1).id, None)
    payload = json.loads(base64.b64decode(qr_url(invoice, '20123456786').split('?p=')[1]))
    assert payload == {'ver': 1, 'fecha': invoice.voucher_date.isoformat(), 'cuit': 20123456786, 'ptoVta': 5,
                       'tipoCmp': 11, 'nroCmp': 1, 'importe': 1800.0, 'moneda': 'PES', 'ctz': 1,
                       'tipoDocRec': 99, 'nroDocRec': 0, 'tipoCodAut': 'E', 'codAut': int(invoice.cae)}
