from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.menu import FudoProduct, MenuCategory, MenuItem, MenuItemVariant
from app.utils.slug import unique_slug

NO_CATEGORY_ID = '__none__'
NO_CATEGORY_NAME = 'Sin categoría'


def _category_id(product):
    relationship = (product.get('relationships') or {}).get('productCategory') or {}
    data = relationship.get('data') or {}
    return str(data['id']) if data.get('id') is not None else None


def _next_category_order():
    current = db.session.query(db.func.max(MenuCategory.sort_order)).filter(MenuCategory.group_id.is_(None)).scalar()
    return 0 if current is None else current + 1


def _next_item_order(category_id):
    current = db.session.query(db.func.max(MenuItem.sort_order)).filter(MenuItem.category_id == category_id).scalar()
    return 0 if current is None else current + 1


def _upsert_category(by_fudo_id, fudo_category_id, name, stats):
    category = by_fudo_id.get(fudo_category_id)
    if category is None:
        name = name[:100]
        category = MenuCategory(
            fudo_category_id=fudo_category_id, name=name, slug=unique_slug(MenuCategory, name),
            is_visible=True, show_title=True, sort_order=_next_category_order(),
        )
        db.session.add(category)
        db.session.flush()
        by_fudo_id[fudo_category_id] = category
        stats['categories_created'] += 1
    else:
        name = name[:100]
        if category.name != name:
            category.name = name
            category.slug = unique_slug(MenuCategory, name, exclude_id=category.id)
        if category.fudo_status == 'missing':
            category.is_visible = True
        category.fudo_status = None
    return category


def _sync_categories(raw_categories, stats):
    by_fudo_id = {c.fudo_category_id: c for c in MenuCategory.query.filter(MenuCategory.fudo_category_id.isnot(None))}
    if not raw_categories:
        return by_fudo_id
    seen = set()
    for raw in raw_categories:
        fudo_category_id = str(raw['id'])
        seen.add(fudo_category_id)
        _upsert_category(by_fudo_id, fudo_category_id, (raw.get('attributes') or {}).get('name') or 'Sin nombre', stats)
    for fudo_category_id, category in by_fudo_id.items():
        if fudo_category_id not in seen and fudo_category_id != NO_CATEGORY_ID:
            category.is_visible = False
            category.fudo_status = 'missing'
    return by_fudo_id


def _category_for_product(product, categories, stats):
    """Categoría de la carta para un FudoProduct; crea 'Sin categoría' si hace falta."""
    category = categories.get(product.fudo_category_id) if product.fudo_category_id else None
    if category is None:
        category = _upsert_category(categories, NO_CATEGORY_ID, NO_CATEGORY_NAME, stats)
    return category


def assign_fudo_category(item, products_by_id=None, categories=None):
    """Pone al ítem en la categoría de Fudo de su primer precio vinculado con producto existente."""
    categories = categories if categories is not None else {
        c.fudo_category_id: c for c in MenuCategory.query.filter(MenuCategory.fudo_category_id.isnot(None))
    }
    for variant in sorted(item.variants, key=lambda v: (v.sort_order, v.id or 0)):
        if not variant.fudo_product_id:
            continue
        product = (products_by_id or {}).get(variant.fudo_product_id) or db.session.get(FudoProduct, variant.fudo_product_id)
        if product is None:
            continue
        if product.fudo_category_id and product.fudo_category_id not in categories:
            return False  # categoría desconocida (p. ej. Fudo no devolvió categorías): no mover
        stats = {'categories_created': 0}
        category = _category_for_product(product, categories, stats)
        if item.category_id != category.id:
            item.sort_order = _next_item_order(category.id)
            item.category_id = category.id
        return True
    return False


def sync_fudo_products(client):
    """Sincroniza categorías, productos, precios y crea ítems ocultos para productos nuevos."""
    raw_products = client.get_all_products()
    if not raw_products:
        raise ValueError('Fudo no devolvió productos; no se sincronizó nada')

    stats = {'categories_created': 0, 'items_created': 0}
    categories = _sync_categories(client.get_all_product_categories(), stats)
    category_names = {fid: c.name for fid, c in categories.items()}

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
        product.fudo_category_id = _category_id(raw)
        product.category_name = category_names.get(product.fudo_category_id)
        product.synced_at = now
        by_id[fudo_id] = product
    for fudo_id, product in existing.items():
        if fudo_id not in by_id:
            db.session.delete(product)

    price_changes = 0
    alerts = 0
    for variant in MenuItemVariant.query.filter(MenuItemVariant.fudo_product_id.isnot(None)).all():
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

    linked_items = (
        MenuItem.query.join(MenuItemVariant).filter(MenuItemVariant.fudo_product_id.isnot(None))
        .options(selectinload(MenuItem.variants)).distinct().all()
    )
    for item in linked_items:
        assign_fudo_category(item, by_id, categories)

    linked = linked_fudo_ids()
    for product in by_id.values():
        if not product.is_active or product.ignored or product.fudo_id in linked:
            continue
        category = _category_for_product(product, categories, stats)
        item = MenuItem(
            category_id=category.id, name=product.name[:200] or 'Sin nombre', is_visible=False,
            sort_order=_next_item_order(category.id),
        )
        item.variants = [MenuItemVariant(fudo_product_id=product.fudo_id, price=product.price, fudo_status='ok', sort_order=0)]
        db.session.add(item)
        db.session.flush()
        linked.add(product.fudo_id)
        stats['items_created'] += 1

    db.session.commit()
    return {'products': len(by_id), 'price_changes': price_changes, 'alerts': alerts, **stats}


def linked_fudo_ids():
    rows = db.session.query(MenuItemVariant.fudo_product_id).filter(MenuItemVariant.fudo_product_id.isnot(None))
    return {fudo_id for (fudo_id,) in rows}


def new_items():
    return MenuItem.query.filter(MenuItem.reviewed_at.is_(None)).order_by(MenuItem.category_id, MenuItem.name).all()


def alert_variants():
    return MenuItemVariant.query.filter(MenuItemVariant.fudo_status.in_(['inactive', 'missing'])).all()


def alert_categories():
    return MenuCategory.query.filter(MenuCategory.fudo_status == 'missing').all()
