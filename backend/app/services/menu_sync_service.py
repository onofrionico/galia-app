from datetime import datetime
from decimal import Decimal

from app.extensions import db
from app.models.menu import FudoProduct, MenuItemVariant


def _category_id(product):
    relationship = (product.get('relationships') or {}).get('productCategory') or {}
    return (relationship.get('data') or {}).get('id')


def sync_fudo_products(client):
    """Actualiza la caché de productos de Fudo y los precios/estados de las variantes vinculadas.

    Nunca crea, borra ni mueve ítems de la carta.
    """
    raw_products = client.get_all_products()
    if not raw_products:
        raise ValueError('Fudo no devolvió productos; no se sincronizó nada')

    category_names = {
        str(c['id']): (c.get('attributes') or {}).get('name')
        for c in client.get_all_product_categories()
    }
    existing = {p.fudo_id: p for p in FudoProduct.query.all()}
    now = datetime.utcnow()
    by_id = {}

    for raw in raw_products:
        fudo_id = str(raw['id'])
        attrs = raw.get('attributes') or {}
        product = by_id.get(fudo_id) or existing.get(fudo_id)
        if product is None:
            product = FudoProduct(fudo_id=fudo_id, ignored=False)
            db.session.add(product)
        product.name = (attrs.get('name') or '')[:100]
        product.price = Decimal(str(attrs.get('price') or 0)).quantize(Decimal('0.01'))
        product.is_active = bool(attrs.get('active', True))
        product.category_name = category_names.get(str(_category_id(raw)))
        product.synced_at = now
        by_id[fudo_id] = product

    for fudo_id, product in existing.items():
        if fudo_id not in by_id:
            db.session.delete(product)

    price_changes = 0
    alerts = 0
    linked = MenuItemVariant.query.filter(MenuItemVariant.fudo_product_id.isnot(None)).all()
    for variant in linked:
        product = by_id.get(variant.fudo_product_id)
        if product is None:
            variant.fudo_status = 'missing'
        elif not product.is_active:
            variant.fudo_status = 'inactive'
        else:
            variant.fudo_status = 'ok'
            if Decimal(variant.price) != product.price:
                variant.price = product.price
                price_changes += 1
        if variant.fudo_status != 'ok':
            alerts += 1

    db.session.commit()
    return {'products': len(by_id), 'price_changes': price_changes, 'alerts': alerts}


def linked_fudo_ids():
    rows = db.session.query(MenuItemVariant.fudo_product_id).filter(MenuItemVariant.fudo_product_id.isnot(None))
    return {fudo_id for (fudo_id,) in rows}


def unassigned_products():
    linked = linked_fudo_ids()
    products = (
        FudoProduct.query
        .filter(FudoProduct.is_active.is_(True), FudoProduct.ignored.is_(False))
        .order_by(FudoProduct.category_name, FudoProduct.name)
        .all()
    )
    return [p for p in products if p.fudo_id not in linked]


def alert_variants():
    return MenuItemVariant.query.filter(MenuItemVariant.fudo_status.in_(['inactive', 'missing'])).all()
