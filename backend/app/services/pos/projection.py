"""Copia de las ventas cerradas del POS en `sales`, la tabla que leen los reportes."""
from app.extensions import db
from app.models import Sale
from app.services.pos.common import active_payments, display_name


def _fit(column, value):
    """Recorta `value` al largo de la columna de `sales` (si tiene)."""
    length = getattr(Sale.__table__.c[column].type, 'length', None)
    if value is None or length is None:
        return value
    return value[:length]


def project(sale):
    """Crea la fila de `sales` de una venta recién cerrada (mismo criterio de fechas que fudo_sync:
    timestamps en UTC y fecha = día de cierre)."""
    methods = sorted({p.method_name for p in active_payments(sale)})
    table = sale.table
    row = Sale(
        source='galia',
        external_id=None,
        fecha=sale.closed_at.date(),
        creacion=sale.opened_at,
        cerrada=sale.closed_at,
        caja=None,
        estado='Cerrada',
        cliente=_fit('cliente', sale.customer_name),
        mesa=_fit('mesa', table.label if table else None),
        sala=_fit('sala', table.salon.name if table else None),
        personas=sale.people,
        camarero=_fit('camarero', display_name(sale.waiter)),
        medio_pago=_fit('medio_pago', (methods[0] if len(methods) == 1 else 'Mixto') if methods else None),
        total=sale.total,
        fiscal=False,
        tipo_venta=_fit('tipo_venta', 'Local' if sale.sale_type == 'salon' else 'Mostrador'),
        comentario=_fit('comentario', sale.comment),
        origen=_fit('origen', 'Galia POS'),
        id_origen=_fit('id_origen', str(sale.id)),
    )
    db.session.add(row)
    db.session.flush()
    sale.sale_id = row.id


def unproject(sale):
    """Borra la fila proyectada (al reabrir o anular una venta cerrada)."""
    if sale.sale_id is not None:
        row = db.session.get(Sale, sale.sale_id)
        if row is not None:
            db.session.delete(row)
        sale.sale_id = None
