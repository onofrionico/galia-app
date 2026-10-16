"""Cobro de Point activo de una venta (para el aviso "Cobro en Point pendiente"). Solo modelos: sin ciclos."""
from app.models import MpPointOrder
from app.models.mercadopago import ACTIVE_STATUSES


def active_point_order(sale_id):
    order = MpPointOrder.query.filter(MpPointOrder.sale_id == sale_id,
                                      MpPointOrder.status.in_(ACTIVE_STATUSES)).order_by(MpPointOrder.id.desc()).first()
    if order is None:
        return None
    return {'id': order.id, 'status': order.status, 'amount': f'{order.amount:.2f}'}
