"""Qué datos de un Producto vienen de Fudo y, por lo tanto, no se editan en Galia."""
from decimal import Decimal, InvalidOperation

from app.extensions import db
from app.models.product_recipe_item import ProductRecipeItem
from app.models.product_variant import ProductVariant

FUDO_LOCKED_ERROR = 'Este dato se edita en Fudo'
LOCKED_VARIANT_FIELDS = ('name', 'price', 'is_active')
LOCKED_CATEGORY_FIELDS = ('name', 'is_active')
ALERT_STATUSES = ('missing', 'inactive')


def _catalog_in_galia():
    from app.services import cutover
    return cutover.catalog_in_galia()


def fudo_info(product_ids):
    """{product_id: {'linked': n, 'alerts': n}} para los Productos con variantes vinculadas a Fudo.

    Con el catálogo en Galia, Fudo ya no manda: nada aparece como vinculado ni bloqueado.
    """
    if not product_ids or _catalog_in_galia():
        return {}
    rows = (
        db.session.query(ProductVariant.product_id, ProductVariant.fudo_status)
        .filter(ProductVariant.product_id.in_(product_ids), ProductVariant.fudo_product_id.isnot(None))
        .all()
    )
    info = {}
    for product_id, status in rows:
        entry = info.setdefault(product_id, {'linked': 0, 'alerts': 0})
        entry['linked'] += 1
        if status in ALERT_STATUSES:
            entry['alerts'] += 1
    return info


def locked_product_fields(entry):
    if not entry:
        return []
    fields = ['category_id', 'is_active']
    if entry['linked'] == 1:
        fields.insert(0, 'name')
    return fields


def fudo_payload(entry):
    return {
        'fudo_linked': bool(entry),
        'fudo_locked_fields': locked_product_fields(entry),
        'fudo_alerts': entry['alerts'] if entry else 0,
    }


def _normalize(field, value):
    if field == 'price':
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
    if field == 'is_active':
        return bool(value)
    if isinstance(value, str):
        return value.strip()
    return value


def changes_locked(data, fields, obj):
    """True si el body intenta cambiar algún campo bloqueado respecto de su valor actual."""
    if _catalog_in_galia():
        return False
    for field in fields:
        if field not in data:
            continue
        new = _normalize(field, data[field])
        if new is None or new != _normalize(field, getattr(obj, field)):
            return True
    return False


def product_detail(product):
    """Formato de GET /products/<id>: todas las variantes, receta si tiene y datos de Fudo."""
    data = product.to_dict()
    variants = ProductVariant.query.filter_by(product_id=product.id).order_by(ProductVariant.id).all()
    data['variants'] = [v.to_dict() for v in variants]
    if product.has_recipe:
        data['recipe'] = [r.to_dict() for r in ProductRecipeItem.query.filter_by(product_id=product.id).all()]
    data.update(fudo_payload(fudo_info([product.id]).get(product.id)))
    return data
