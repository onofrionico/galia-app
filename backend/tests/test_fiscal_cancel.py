import pytest

from app.extensions import db
from app.models.pos import PrintJob
from app.services.fiscal import arca, invoice_service
from app.services.fiscal.arca.fake import FakeArca
from app.services.pos import payment_service, sale_service
from app.services.pos.errors import PosError
from app.services.pos.serializers import sale_to_dict
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
    configure_fiscal()
    make_printer('Térmica caja', cashier=True)
    return user, cat, t1, t2


def test_credit_note_cancels_invoice_and_allows_reinvoicing(ctx):
    user, cat, t1, _t2 = ctx
    sale = closed_sale(user, cat, t1)
    invoice = invoice_service.issue(user, sale.id, None)
    credit = invoice_service.cancel(user, invoice.id)
    assert credit.status == 'authorized' and credit.voucher_type == 13 and credit.number == 1
    assert credit.related_invoice_id == invoice.id and credit.total == invoice.total
    assert credit.request['CbtesAsoc']['CbteAsoc'][0]['Nro'] == invoice.number
    assert invoice_service.active_invoice(sale.id) is None
    docs = [j.document['title'] for j in PrintJob.query.filter_by(kind='invoice').order_by(PrintJob.id)]
    assert docs == ['FACTURA C', 'NOTA DE CRÉDITO C']
    with pytest.raises(PosError):
        invoice_service.cancel(user, invoice.id)
    db.session.rollback()
    again = invoice_service.issue(user, sale.id, None)
    assert again.status == 'authorized' and again.number == 2


def test_credit_note_requires_anular(ctx):
    user, cat, t1, _t2 = ctx
    invoice = invoice_service.issue(user, closed_sale(user, cat, t1).id, None)
    cashier = make_user('caja2@test.com', modules=('POS',))
    with pytest.raises(PosError) as error:
        invoice_service.cancel(cashier, invoice.id)
    assert error.value.status == 403


def test_invoiced_sale_and_covered_payments_cannot_be_cancelled(ctx):
    user, cat, t1, _t2 = ctx
    sale = closed_sale(user, cat, t1, amount_cash=1000, amount_card=800)
    invoice = invoice_service.issue(user, sale.id, None)
    cash_payment = next(p for p in sale.payments if p.payment_method_id == cat.efectivo.id)
    card_payment = next(p for p in sale.payments if p.payment_method_id == cat.debito.id)
    with pytest.raises(PosError) as error:
        payment_service.cancel_payment(user, cash_payment.id, 'Error')
    assert error.value.status == 409 and invoice.label in error.value.message
    db.session.rollback()
    with pytest.raises(PosError) as error:
        sale_service.cancel_sale(user, sale.id, 'Error')
    assert invoice.label in error.value.message
    db.session.rollback()
    payment_service.cancel_payment(user, card_payment.id, 'Se cobró mal')
    invoice_service.cancel(user, invoice.id)
    payment_service.cancel_payment(user, cash_payment.id, 'Ahora sí')


def test_pending_invoice_blocks_cancellation(ctx):
    user, cat, t1, _t2 = ctx
    FakeArca.reset('timeout')
    sale = closed_sale(user, cat, t1)
    invoice_service.issue(user, sale.id, None)
    with pytest.raises(PosError) as error:
        sale_service.cancel_sale(user, sale.id, 'Error')
    assert 'sin confirmar' in error.value.message


def test_sale_dict_carries_invoice_summary(ctx):
    user, cat, t1, _t2 = ctx
    sale = closed_sale(user, cat, t1)
    assert sale_to_dict(sale)['invoice'] is None
    invoice = invoice_service.issue(user, sale.id, None)
    summary = sale_to_dict(sale)['invoice']
    assert summary == {'id': invoice.id, 'label': invoice.label, 'status': 'authorized', 'is_active': True}
    assert 'invoice' not in sale_to_dict(sale, include_items=False)
