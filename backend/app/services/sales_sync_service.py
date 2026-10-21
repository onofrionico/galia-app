"""Aplica en `sales`/`sale_items` las ventas traídas de Fudo. No hace commit."""
from app.extensions import db
from app.models import ProductVariant, Sale, SaleItem
from app.services.sale_fudo_parsing import index_included, parse_fudo_items, parse_fudo_sale


def _set_items(sale, parsed_items, variant_ids):
    sale.items.clear()
    db.session.flush()  # borra los ítems viejos antes de insertar (external_id es único)
    for data in parsed_items:
        data = dict(data)
        fudo_product_id = data.pop('fudo_product_id')
        sale.items.append(SaleItem(product_variant_id=variant_ids.get(fudo_product_id), **data))


def apply_fudo_sales(payload, update_existing=False):
    """`payload` = {'data': [...ventas], 'included': [...]}.

    Ventas nuevas se crean con sus ítems. Las existentes se actualizan (con ítems) si
    `update_existing`; si no, solo reciben ítems cuando todavía no tenían, así re-sincronizar
    un período rellena el detalle del historial sin pisar nada más.
    """
    index = index_included(payload.get('included'))
    variant_ids = dict(db.session.query(ProductVariant.fudo_product_id, ProductVariant.id)
                       .filter(ProductVariant.fudo_product_id.isnot(None)).all())
    results = {'total_fetched': len(payload.get('data') or []), 'imported': 0, 'updated': 0, 'skipped': 0,
               'items_backfilled': 0, 'errors': []}

    for raw in payload.get('data') or []:
        try:
            with db.session.begin_nested():
                fields = parse_fudo_sale(raw, index)
                items = parse_fudo_items(raw, index)
                sale = Sale.query.filter_by(external_id=fields['external_id']).first()
                if sale is None:
                    sale = Sale(**fields)
                    db.session.add(sale)
                    db.session.flush()
                    _set_items(sale, items, variant_ids)
                    results['imported'] += 1
                elif update_existing:
                    for key, value in fields.items():
                        if key != 'external_id':
                            setattr(sale, key, value)
                    _set_items(sale, items, variant_ids)
                    results['updated'] += 1
                else:
                    if items and not sale.items:
                        _set_items(sale, items, variant_ids)
                        results['items_backfilled'] += 1
                    results['skipped'] += 1
        except Exception as e:  # una venta rota no frena el resto
            results['errors'].append({'sale_id': raw.get('id'), 'error': str(e)})
    return results
