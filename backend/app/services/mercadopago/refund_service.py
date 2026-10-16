"""Anular un pago del Point devolviendo el dinero en MercadoPago (reembolso total de la orden)."""
import logging

from app.extensions import db
from app.models import MpPointOrder, PosPayment
from app.services import mercadopago
from app.services.fiscal import guard
from app.services.mercadopago import MpRejected, MpUnavailable
from app.services.mercadopago import settings as mp_settings
from app.services.pos import payment_service
from app.services.pos.cancel_reasons import resolve_reason
from app.services.pos.common import now, parse_id, require_module
from app.services.pos.errors import PosError, not_found

logger = logging.getLogger(__name__)


def order_for_payment(payment_id):
    return MpPointOrder.query.filter_by(payment_id=payment_id).first()


def _check_cancellable(payment_id, reason, reason_id):
    """Las mismas validaciones que la anulación, antes de devolver plata que no se puede deshacer."""
    resolve_reason(reason_id, reason)
    payment = db.session.get(PosPayment, payment_id)
    if payment is None:
        raise not_found('El pago no existe')
    if payment.cancelled_at is not None:
        raise PosError('El pago ya está anulado')
    guard.ensure_payment_can_be_cancelled(payment)
    if payment.sale.status not in ('billing', 'closed'):
        raise PosError('Solo se anulan pagos de una venta en cobro o cerrada')


def cancel_with_refund(user, payment_id, reason, reason_id=None):
    """Primero la devolución en MercadoPago; si la acepta, se anula en Galia. Si no, no se anula nada."""
    require_module(user, 'Anular', 'No tenés permiso para anular pagos')
    payment_id = parse_id(payment_id, 'El pago')
    order = order_for_payment(payment_id)
    if order is None:
        raise PosError('Ese pago no vino de un cobro con el Point: anulalo solo en Galia')
    _check_cancellable(payment_id, reason, reason_id)
    if order.refunded_at is None:
        client = mercadopago.get_client(mp_settings.get_settings())
        try:
            client.refund_order(order.mp_order_id, f'refund-{order.payment_id}')
        except MpUnavailable as exc:
            logger.warning('MercadoPago sin respuesta devolviendo la orden %s: %s', order.id, exc)
            raise PosError('MercadoPago no responde: no se anuló el pago')
        except MpRejected as exc:
            logger.warning('MercadoPago rechazó la devolución de la orden %s: %s', order.id, exc)
            raise PosError(f'MercadoPago rechazó la devolución: {exc.message}')
        order.refunded_at = now()
        db.session.commit()  # la devolución ya ocurrió: queda registrada aunque la anulación falle después
    return payment_service.cancel_payment(user, payment_id, reason, reason_id=reason_id)
