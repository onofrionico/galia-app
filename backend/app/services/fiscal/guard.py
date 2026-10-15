"""Bloqueos de la venta por facturas: no se anula lo que tiene una factura vigente o sin confirmar.

Solo importa modelos y errores: lo usan sale_service, payment_service y serializers sin ciclos de imports.
"""
from app.models import Invoice, InvoicePayment
from app.services.pos.errors import PosError

PENDING_MESSAGE = 'Hay una factura sin confirmar en esta venta: verificala antes'


def _active(sale_id):
    for invoice in Invoice.query.filter_by(sale_id=sale_id, kind='invoice', status='authorized') \
            .order_by(Invoice.id.desc()):
        if Invoice.query.filter_by(related_invoice_id=invoice.id, status='authorized').first() is None:
            return invoice
    return None


def _pending(sale_id):
    return Invoice.query.filter_by(sale_id=sale_id, status='pending').first()


def ensure_sale_can_be_cancelled(sale):
    if _pending(sale.id) is not None:
        raise PosError(PENDING_MESSAGE)
    active = _active(sale.id)
    if active is not None:
        raise PosError(f'La venta tiene la {active.label}: anulala con una nota de crédito antes')


def ensure_payment_can_be_cancelled(payment):
    if _pending(payment.sale_id) is not None:
        raise PosError(PENDING_MESSAGE)
    active = _active(payment.sale_id)
    if active is not None and InvoicePayment.query.filter_by(invoice_id=active.id,
                                                             payment_id=payment.id).first():
        raise PosError(f'La venta tiene la {active.label}: anulala con una nota de crédito antes')


def sale_invoice_summary(sale_id):
    invoice = _pending(sale_id) or _active(sale_id)
    if invoice is None:
        return None
    return {'id': invoice.id, 'label': invoice.label, 'status': invoice.status,
            'is_active': invoice.status == 'authorized'}
