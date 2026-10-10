"""Cierre de ventas del POS (compartido por cobros, anulaciones y descuentos)."""
from app.services.pos import audit, projection
from app.services.pos.common import now


def close_sale_rows(sale, user):
    """Cierra la venta y la proyecta en `sales`. No hace commit."""
    sale.status = 'closed'
    sale.closed_at = now()
    sale.closed_by = user.id
    projection.project(sale)
    audit.record(sale, user, 'closed', total=sale.total, paid_total=sale.paid_total)


def close_if_settled(sale, user):
    """Cierra una venta en cobro que ya tiene pagos y no debe nada. No hace commit."""
    if sale.status == 'billing' and sale.paid_total > 0 and sale.balance <= 0:
        close_sale_rows(sale, user)
        return True
    return False
