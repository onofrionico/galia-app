"""Ventas del POS que todavía no cerraron, para mostrarlas en la pestaña Ventas.

Es solo lectura: estas ventas no están en `sales` (esa tabla la leen los reportes y solo recibe las
cerradas), así que no se mezclan con reportes, estadísticas ni exportación.
"""
from app.models.pos import ACTIVE_SALE_STATUSES, PosSale
from app.services.pos.common import display_name


def _place(sale):
    if sale.table is None:
        return 'Mostrador'
    return f'{sale.table.label} - {sale.table.salon.name}'


def in_progress_sales():
    """Ventas abiertas o con la cuenta pedida (sin las de práctica), de la más reciente a la más vieja."""
    sales = (PosSale.query.filter(PosSale.status.in_(ACTIVE_SALE_STATUSES), PosSale.is_practice.is_(False))
             .order_by(PosSale.opened_at.desc()).all())
    rows = [{
        'id': sale.id,
        'number': sale.number,
        'status': sale.status,
        'place': _place(sale),
        'people': sale.people,
        'waiter': display_name(sale.waiter),
        'customer': sale.customer_name,
        'opened_at': sale.opened_at.isoformat() + 'Z',  # se guarda en UTC sin zona; la Z evita que el navegador la lea como local
        'total': float(sale.total or 0),
    } for sale in sales]
    return {'sales': rows, 'total': round(sum(row['total'] for row in rows), 2)}
