"""Cobro de Point activo de una venta (para el aviso "Cobro en Point pendiente"). Solo modelos: sin ciclos."""
from app.models import MpPointOrder
from app.models.mercadopago import ACTIVE_STATUSES


def active_point_order(sale_id):
    order = MpPointOrder.query.filter(MpPointOrder.sale_id == sale_id,
                                      MpPointOrder.status.in_(ACTIVE_STATUSES)).order_by(MpPointOrder.id.desc()).first()
    if order is None:
        return None
    return {'id': order.id, 'status': order.status, 'amount': f'{order.amount:.2f}'}


def refundable(payment):
    """El pago vino de un cobro con el Point que todavía no se devolvió."""
    if payment.id is None or payment.cancelled_at is not None:
        return False
    order = MpPointOrder.query.filter_by(payment_id=payment.id).first()
    return order is not None and order.refunded_at is None
