"""Utilidades compartidas por los servicios del POS."""
from datetime import datetime
from decimal import Decimal

from app.models.pos import PosSale
from app.services.pos import pricing
from app.services.pos.errors import PosError, bad_request, forbidden, not_found
from app.utils.permissions import check_module_access
from app.utils.validation import clean_str

MAX_QUANTITY = Decimal('1000')
MAX_MONEY = Decimal('10000000000')  # Numeric(12, 2)


def now():
    return datetime.utcnow()


def parse_id(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise bad_request(f'{label} es inválido')
    return value


def require_reason(reason):
    reason = clean_str(reason, 255)
    if not reason:
        raise bad_request('Indicá el motivo')
    return reason


def require_module(user, module, message):
    if not check_module_access(user, module):
        raise forbidden(message)


def require_status(sale, statuses, message):
    if sale.status not in statuses:
        raise PosError(message)


def load_sale(sale_id):
    """Trae la venta bloqueando su fila (SELECT ... FOR UPDATE) y con valores frescos."""
    sale = PosSale.query.filter_by(id=sale_id).with_for_update().populate_existing().first()
    if sale is None:
        raise not_found('La venta no existe')
    return sale


def active_payments(sale):
    return [p for p in sale.payments if p.cancelled_at is None]


def recalc(sale):
    """Recalcula montos de descuentos y totales de la venta a partir de sus filas."""
    from app.extensions import db
    db.session.flush()
    lines = [pricing.Line(i.id, i.line_total) for i in sale.items if i.status != 'cancelled']
    discounts = [d for d in sale.discounts if d.cancelled_at is None]
    totals = pricing.compute(lines, [pricing.Disc(d.id, d.item_id, d.kind, d.value) for d in discounts])
    for discount in discounts:
        discount.amount = totals.amounts[discount.id]
    sale.subtotal = totals.subtotal
    sale.discount_total = totals.discount_total
    sale.total = totals.total
    sale.paid_total = pricing.money(sum((p.amount for p in active_payments(sale)), Decimal('0')))


def display_name(user):
    if user is None:
        return None
    employee = getattr(user, 'employee', None)
    return employee.full_name if employee else user.email
