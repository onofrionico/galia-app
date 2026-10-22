"""Carta digital sobre el catálogo de Galia (después del corte con Fudo).

Del catálogo salen precio, categoría y estado. El nombre, la descripción, la foto, los tags y el orden de cada
ítem siguen siendo los que puso el dueño en la carta. `MenuItemVariant.fudo_status` se sigue usando como estado
del vínculo ('ok' | 'inactive' | 'missing').
"""
from decimal import Decimal

from app.extensions import db
from app.models import Product, ProductCategory, ProductVariant
from app.models.menu import MenuCategory, MenuItem, MenuItemVariant
from app.services.menu_sync_service import _next_category_order, _next_item_order
from app.utils.slug import unique_slug


def link_to_catalog():
    """Vincula (una vez, idempotente) la carta al catálogo por los ids de Fudo. No hace commit."""
    stats = {'variants_linked': 0, 'variants_unlinked': 0, 'categories_linked': 0}
    by_fudo_variant = {v.fudo_product_id: v for v in
                       ProductVariant.query.filter(ProductVariant.fudo_product_id.isnot(None))}
    for variant in MenuItemVariant.query.filter(MenuItemVariant.fudo_product_id.isnot(None)):
        target = by_fudo_variant.get(variant.fudo_product_id)
        if target is not None:
            variant.product_variant_id = target.id
            stats['variants_linked'] += 1
        elif variant.product_variant_id is None:
            variant.fudo_status = 'missing'
            stats['variants_unlinked'] += 1
    by_fudo_category = {c.fudo_category_id: c for c in
                        ProductCategory.query.filter(ProductCategory.fudo_category_id.isnot(None))}
    for category in MenuCategory.query.filter(MenuCategory.fudo_category_id.isnot(None)):
        target = by_fudo_category.get(category.fudo_category_id)
        if target is not None:
            category.product_category_id = target.id
            stats['categories_linked'] += 1
    db.session.flush()
    return stats


def _menu_category(product_category, categories, stats):
    """Categoría de la carta vinculada a la categoría del catálogo (la crea al final, sin grupo, si falta)."""
    category = categories.get(product_category.id)
    if category is None:
        name = product_category.name[:100]
        category = MenuCategory(product_category_id=product_category.id, name=name,
                                slug=unique_slug(MenuCategory, name), is_visible=True, show_title=True,
                                sort_order=_next_category_order())
        db.session.add(category)
        db.session.flush()
        categories[product_category.id] = category
        stats['categories_created'] += 1
    return category


def _status(variant):
    if variant is None:
        return 'missing'
    if not variant.is_active or not variant.product.is_active:
        return 'inactive'
    return 'ok'


def sync_from_catalog():
    """Actualiza precios, estados y categorías desde el catálogo y crea ítems ocultos para variantes nuevas."""
    stats = {'categories_created': 0, 'items_created': 0}
    categories = {c.product_category_id: c for c in
                  MenuCategory.query.filter(MenuCategory.product_category_id.isnot(None))}
    price_changes = alerts = 0
    items_by_product = {}
    for menu_variant in MenuItemVariant.query.all():
        if menu_variant.product_variant_id is None:
            if menu_variant.fudo_product_id is not None:  # venía de Fudo y no tiene par en Galia
                menu_variant.fudo_status = 'missing'
                alerts += 1
            continue
        variant = db.session.get(ProductVariant, menu_variant.product_variant_id)
        menu_variant.fudo_status = _status(variant)
        if menu_variant.fudo_status != 'ok':
            alerts += 1
            continue
        if Decimal(menu_variant.price) != Decimal(variant.price):
            menu_variant.price = variant.price
            price_changes += 1
        items_by_product.setdefault(variant.product_id, menu_variant.item_id)

    for item in MenuItem.query.all():
        linked = sorted((v for v in item.variants if v.product_variant_id is not None),
                        key=lambda v: (v.sort_order, v.id or 0))
        if not linked:
            continue
        variant = db.session.get(ProductVariant, linked[0].product_variant_id)
        if variant is None or variant.product.category is None:
            continue
        category = _menu_category(variant.product.category, categories, stats)
        if item.category_id != category.id:
            item.sort_order = _next_item_order(category.id)
            item.category_id = category.id

    linked_ids = {row[0] for row in db.session.query(MenuItemVariant.product_variant_id)
                  .filter(MenuItemVariant.product_variant_id.isnot(None))}
    candidates = (ProductVariant.query.join(Product, ProductVariant.product_id == Product.id)
                  .filter(ProductVariant.is_active.is_(True), Product.is_active.is_(True),
                          ProductVariant.menu_ignored.is_(False))
                  .order_by(Product.id, ProductVariant.id).all())
    for variant in candidates:
        if variant.id in linked_ids:
            continue
        product = variant.product
        siblings = product.variants.filter(ProductVariant.is_active.is_(True)).count()
        label = variant.name[:100] if siblings > 1 else None
        item = db.session.get(MenuItem, items_by_product[product.id]) if product.id in items_by_product else None
        if item is None:
            category = _menu_category(product.category, categories, stats)
            item = MenuItem(category_id=category.id, name=product.name[:200] or 'Sin nombre', is_visible=False,
                            sort_order=_next_item_order(category.id))
            db.session.add(item)
            db.session.flush()
            items_by_product[product.id] = item.id
            stats['items_created'] += 1
        order = max((v.sort_order for v in item.variants), default=-1) + 1
        item.variants.append(MenuItemVariant(product_variant_id=variant.id, label=label, price=variant.price,
                                             fudo_status='ok', sort_order=order))
        db.session.flush()
        linked_ids.add(variant.id)

    db.session.commit()
    return {'products': len(candidates), 'price_changes': price_changes, 'alerts': alerts, **stats}
