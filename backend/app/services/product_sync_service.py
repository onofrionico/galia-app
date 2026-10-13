"""Sincroniza el catálogo de Productos (POS) desde la caché de Fudo que actualiza la carta.

Durante la transición Fudo es la fuente de verdad de nombre, categoría, precio y estado.
No hace commit: lo hace quien lo llama (menu_sync_service.sync_fudo_products).
"""
from sqlalchemy import func

from app.extensions import db
from app.models.product_category import ProductCategory

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
