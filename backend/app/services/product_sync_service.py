"""Sincroniza el catálogo de Productos (POS) desde la caché de Fudo que actualiza la carta.

Durante la transición Fudo es la fuente de verdad de nombre, categoría, precio y estado.
No hace commit: lo hace quien lo llama (menu_sync_service.sync_fudo_products).
"""
from decimal import Decimal

from sqlalchemy import func

from app.extensions import db
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_variant import ProductVariant

NO_CATEGORY_ID = '__none__'
NO_CATEGORY_NAME = 'Sin categoría'


def _name_taken(name, exclude_id=None):
    query = ProductCategory.query.filter(func.lower(ProductCategory.name) == name.lower())
    if exclude_id is not None:
        query = query.filter(ProductCategory.id != exclude_id)
    return db.session.query(query.exists()).scalar()


def _free_name(base, exclude_id=None):
    """El nombre de Fudo, o con sufijo ' (Fudo)', ' (Fudo 2)'... si ya lo usa otra categoría."""
    base = base.strip()[:100] or 'Sin nombre'
    if not _name_taken(base, exclude_id):
        return base
    n = 1
    while True:
        suffix = ' (Fudo)' if n == 1 else f' (Fudo {n})'
        candidate = base[:100 - len(suffix)] + suffix
        if not _name_taken(candidate, exclude_id):
            return candidate
        n += 1


def upsert_category(by_fudo_id, fudo_category_id, name, stats):
    category = by_fudo_id.get(fudo_category_id)
    if category is None:
        clean = name.strip()[:100] or 'Sin nombre'
        category = ProductCategory.query.filter(
            func.lower(ProductCategory.name) == clean.lower(),
            ProductCategory.fudo_category_id.is_(None),
        ).first()
        if category is None:
            category = ProductCategory(name=_free_name(clean))
            db.session.add(category)
            stats['categories_created'] += 1
        category.fudo_category_id = fudo_category_id
        by_fudo_id[fudo_category_id] = category
    else:
        new_name = _free_name(name, exclude_id=category.id)
        if category.name != new_name:
            category.name = new_name
    category.is_active = True
    category.fudo_status = None
    db.session.flush()
    return category


def sync_product_categories(raw_categories, stats):
    """Upsert de las categorías de Fudo. Devuelve {fudo_category_id: ProductCategory}."""
    by_fudo_id = {
        c.fudo_category_id: c
        for c in ProductCategory.query.filter(ProductCategory.fudo_category_id.isnot(None))
    }
    if not raw_categories:
        return by_fudo_id
    seen = set()
    for raw in raw_categories:
        fudo_category_id = str(raw['id'])
        seen.add(fudo_category_id)
        name = (raw.get('attributes') or {}).get('name') or 'Sin nombre'
        upsert_category(by_fudo_id, fudo_category_id, name, stats)
    for fudo_category_id, category in by_fudo_id.items():
        if fudo_category_id not in seen and fudo_category_id != NO_CATEGORY_ID:
            category.is_active = False
            category.fudo_status = 'missing'
    return by_fudo_id


def _category_for(fudo_product, categories, stats, existing=False):
    """Categoría para un producto de Fudo. None = categoría desconocida en un producto existente: no mover."""
    if fudo_product.fudo_category_id and fudo_product.fudo_category_id in categories:
        return categories[fudo_product.fudo_category_id]
    if fudo_product.fudo_category_id and existing:
        return None
    return upsert_category(categories, NO_CATEGORY_ID, NO_CATEGORY_NAME, stats)


def _sync_linked_variants(linked, by_id, stats):
    for variant in linked:
        fudo = by_id.get(variant.fudo_product_id)
        if fudo is None:
            variant.is_active = False
            variant.fudo_status = 'missing'
        else:
            name = fudo.name[:100] or 'Sin nombre'
            if variant.name != name or Decimal(str(variant.price)) != Decimal(str(fudo.price)):
                stats['variants_updated'] += 1
            variant.name = name
            variant.price = fudo.price
            variant.is_active = bool(fudo.is_active)
            variant.fudo_status = 'ok' if fudo.is_active else 'inactive'
        if variant.fudo_status != 'ok':
            stats['alerts'] += 1


def _sync_linked_products(linked, by_id, categories, stats):
    variants_by_product = {}
    for variant in linked:
        variants_by_product.setdefault(variant.product_id, []).append(variant)
    for product_id, variants in variants_by_product.items():
        product = db.session.get(Product, product_id)
        in_cache = [by_id[v.fudo_product_id] for v in variants if v.fudo_product_id in by_id]
        if in_cache:
            if len(variants) == 1:
                product.name = in_cache[0].name[:200] or 'Sin nombre'
            category = _category_for(in_cache[0], categories, stats, existing=True)
            if category is not None:
                product.category_id = category.id
        db.session.flush()
        product.is_active = product.variants.filter_by(is_active=True).count() > 0


def _create_new_products(fudo_products, linked_ids, categories, stats):
    for fudo in fudo_products:
        if not fudo.is_active or fudo.fudo_id in linked_ids:
            continue
        name = fudo.name or 'Sin nombre'
        category = _category_for(fudo, categories, stats)
        product = Product(name=name[:200], category_id=category.id, is_active=True)
        db.session.add(product)
        db.session.flush()
        db.session.add(ProductVariant(
            product_id=product.id, name=name[:100], price=fudo.price,
            fudo_product_id=fudo.fudo_id, fudo_status='ok', is_active=True,
        ))
        linked_ids.add(fudo.fudo_id)
        stats['products_created'] += 1


def sync_products_from_cache(fudo_products, raw_categories):
    """Actualiza categorías, Productos y variantes desde la caché de Fudo. No hace commit."""
    stats = {'categories_created': 0, 'products_created': 0, 'variants_updated': 0, 'alerts': 0}
    categories = sync_product_categories(raw_categories, stats)
    by_id = {p.fudo_id: p for p in fudo_products}

    linked = (
        ProductVariant.query.filter(ProductVariant.fudo_product_id.isnot(None))
        .order_by(ProductVariant.id).all()
    )
    _sync_linked_variants(linked, by_id, stats)
    _sync_linked_products(linked, by_id, categories, stats)
    _create_new_products(fudo_products, {v.fudo_product_id for v in linked}, categories, stats)
    db.session.flush()
    return stats
