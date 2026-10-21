"""Copia de las ventas cerradas del POS en `sales`, la tabla que leen los reportes."""
from app.extensions import db
from app.models import ProductVariant, Sale, SaleItem
from app.services.pos.common import active_payments, display_name
from app.utils.timezone_utils import business_date


def _fit(column, value, model=Sale):
    """Recorta `value` al largo de la columna de `model` (si tiene)."""
    length = getattr(model.__table__.c[column].type, 'length', None)
    if value is None or length is None:
        return value
    return value[:length]


def project(sale):
    """Crea la fila de `sales` de una venta recién cerrada (mismo criterio de fechas que fudo_sync:
    timestamps en UTC y fecha = día comercial del cierre). Las ventas de práctica no se proyectan."""
    if sale.is_practice:
        return
    methods =sorted({p.method_name for p in active_payments(sale)})
    table = sale.table
    row = Sale(
        source='galia',
        external_id=None,
        fecha=business_date(sale.closed_at),
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
    for item in sale.items:
        if item.status == 'cancelled':
            continue
        variant = db.session.get(ProductVariant, item.product_variant_id)
        product = variant.product if variant else None
        row.items.append(SaleItem(
            product_variant_id=item.product_variant_id,
            product_name=_fit('product_name', item.product_name, SaleItem),
            variant_name=_fit('variant_name', item.variant_name, SaleItem),
            category_name=_fit('category_name', product.category.name if product and product.category else None,
                               SaleItem),
            quantity=item.quantity,
            unit_price=item.unit_price + item.modifiers_total,
            total=item.line_total,
        ))
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
