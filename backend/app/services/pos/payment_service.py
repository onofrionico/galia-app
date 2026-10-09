"""Cobros y cierre de ventas del POS."""
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.pos import PaymentMethod, PosPayment
from app.services.pos import audit, pricing, projection
from app.services.pos.common import (MAX_MONEY, active_payments, load_sale, now, parse_id, recalc, require_reason)
from app.services.pos.errors import PosError, bad_request, not_found
from app.services.pos.sale_service import confirm_pending
from app.utils.validation import clean_str, parse_decimal


def _close(sale, user):
    sale.status = 'closed'
    sale.closed_at = now()
    sale.closed_by = user.id
    projection.project(sale)
    audit.record(sale, user, 'closed', total=sale.total, paid_total=sale.paid_total)


def _existing_payment(client_request_id, sale_id):
    payment = PosPayment.query.filter_by(client_request_id=client_request_id).first()
    if payment is not None and payment.sale_id != sale_id:
        raise PosError('Ese identificador de pago ya se usó en otra venta')
    return payment


def add_payment(user, sale_id, payment_method_id, amount, tendered=None, client_request_id=None):
    request_id = clean_str(client_request_id, 64)
    if request_id is not None and _existing_payment(request_id, sale_id) is not None:
        return load_sale(sale_id)
    sale = load_sale(sale_id)
    if sale.status == 'open' and sale.sale_type == 'counter':
        confirm_pending(sale, user)
        recalc(sale)
    elif sale.status != 'billing':
        raise PosError('Pedí la cuenta antes de cobrar')
    if not any(i.status == 'confirmed' for i in sale.items):
        raise PosError('La venta no tiene ítems para cobrar')
    method = db.session.get(PaymentMethod, parse_id(payment_method_id, 'El medio de pago'))
    if method is None or not method.is_active:
        raise bad_request('El medio de pago no existe')
    amount = pricing.money(parse_decimal(amount, 'El monto', minimum=Decimal('0.01'), maximum=MAX_MONEY))
    if amount > sale.balance:
        raise bad_request(f'El monto supera el saldo de {sale.balance}')
    change = None
    if tendered is not None:
        if method.kind != 'cash':
            raise bad_request('El vuelto solo aplica a pagos en efectivo')
        tendered = pricing.money(parse_decimal(tendered, 'El monto entregado', minimum=amount, maximum=MAX_MONEY))
        change = tendered - amount
    payment = PosPayment(payment_method_id=method.id, method_name=method.name, amount=amount, tendered=tendered,
                         change=change, client_request_id=request_id, created_by=user.id, created_at=now())
    sale.payments.append(payment)
    try:
        recalc(sale)
    except IntegrityError:
        db.session.rollback()
        if request_id is not None and _existing_payment(request_id, sale_id) is not None:
            return load_sale(sale_id)
        raise
    audit.record(sale, user, 'payment_added', payment_id=payment.id, method=method.name, amount=amount,
                 tendered=tendered, change=change)
    if sale.paid_total >= sale.total:
        _close(sale, user)
    db.session.commit()
    return sale


def close_sale(user, sale_id):
    """Cierra una venta sin saldo (por ejemplo, total 0 por descuentos)."""
    sale = load_sale(sale_id)
    if sale.status != 'billing':
        raise PosError('Pedí la cuenta antes de cerrar')
    if sale.balance > 0:
        raise PosError(f'La venta tiene saldo pendiente ({sale.balance})')
    _close(sale, user)
    db.session.commit()
    return sale


def cancel_payment(user, payment_id, reason):
    reason = require_reason(reason)
    payment = db.session.get(PosPayment, parse_id(payment_id, 'El pago'))
    if payment is None:
        raise not_found('El pago no existe')
    sale = load_sale(payment.sale_id)
    if payment.cancelled_at is not None:
        raise PosError('El pago ya está anulado')
    if sale.status not in ('billing', 'closed'):
        raise PosError('Solo se anulan pagos de una venta en cobro o cerrada')
    payment.cancelled_at = now()
    payment.cancelled_by = user.id
    payment.cancel_reason = reason
    if sale.status == 'closed':
        projection.unproject(sale)
        sale.status = 'billing'
        sale.closed_at = None
        sale.closed_by = None
    recalc(sale)
    audit.record(sale, user, 'payment_cancelled', payment_id=payment.id, amount=payment.amount, reason=reason)
    db.session.commit()
    return sale
