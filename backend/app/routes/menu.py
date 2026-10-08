import logging
import re
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models.menu import FudoProduct, MenuCategory, MenuGroup, MenuItem, MenuItemVariant, MenuSetting, MenuTag
from app.services import menu_publish_service, menu_sync_service
from app.services.menu_image_service import MAX_UPLOAD_BYTES, InvalidImageError, process_image
from app.utils.decorators import admin_required
from app.utils.fudo_client import FudoClient
from app.utils.jwt_utils import token_required
from app.utils.menu_storage import get_menu_storage
from app.utils.slug import unique_slug

bp = Blueprint('menu', __name__, url_prefix='/api/v1/menu')
logger = logging.getLogger(__name__)

SETTING_KEYS = ('footer_text', 'instagram')
COLOR_PATTERN = re.compile(r'#[0-9A-Fa-f]{6}')
UPLOAD_OVERHEAD_BYTES = 1024 * 1024  # overhead multipart
MAX_PRICE = Decimal('99999999.99')  # Numeric(10, 2)


def _error(message, status=400):
    return jsonify({'error': message}), status


def _status():
    return {
        'has_unpublished_changes': menu_publish_service.has_unpublished_changes(),
        'last_published_at': MenuSetting.get('last_published_at'),
        'unassigned_count': len(menu_sync_service.unassigned_products()),
        'alerts_count': len(menu_sync_service.alert_variants()),
    }


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_int_list(value):
    return isinstance(value, list) and all(_is_int(v) for v in value)


def _clean_text(value, max_len, field='El nombre'):
    """Normaliza un texto opcional. Devuelve (valor, error); valor es None si queda vacío."""
    if value is not None and not isinstance(value, str):
        return None, f'{field} debe ser texto'
    value = (value or '').strip()
    if len(value) > max_len:
        return None, f'{field} es demasiado largo (máximo {max_len} caracteres)'
    return value or None, None


def _required_text(value, max_len):
    text, error = _clean_text(value, max_len)
    if error is None and text is None:
        return None, 'El nombre es obligatorio'
    return text, error


def _apply_order(model, ids, scope=None):
    """Asigna sort_order según `ids`. Devuelve False si no son exactamente todos los registros."""
    if not _is_int_list(ids) or len(set(ids)) != len(ids):
        return False
    query = model.query if scope is None else model.query.filter(scope)
    records = {record.id: record for record in query.all()}
    if set(records) != set(ids):
        return False
    for position, record_id in enumerate(ids):
        records[record_id].sort_order = position
    db.session.commit()
    return True


def _next_order(column, *filters):
    current = db.session.query(db.func.max(column)).filter(*filters).scalar()
    return 0 if current is None else current + 1


def _parse_price(value):
    try:
        price = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    if not price.is_finite() or price < 0 or price > MAX_PRICE:
        return None
    return price


# ---------- Árbol ----------

@bp.route('', methods=['GET'])
@token_required
@admin_required
def get_menu(current_user):
    categories = MenuCategory.query.order_by(MenuCategory.sort_order, MenuCategory.id).all()
    return jsonify({
        'groups': [group.to_dict() for group in MenuGroup.query.order_by(MenuGroup.sort_order, MenuGroup.id)],
        'categories': [category.to_dict(include_items=True) for category in categories],
        'tags': [tag.to_dict() for tag in MenuTag.query.order_by(MenuTag.name).all()],
        'status': _status(),
    }), 200


# ---------- Grupos ----------

@bp.route('/groups', methods=['POST'])
@token_required
@admin_required
def create_group(current_user):
    name, error = _required_text((request.get_json() or {}).get('name'), 100)
    if error:
        return _error(error)
    group = MenuGroup(name=name, slug=unique_slug(MenuGroup, name), sort_order=_next_order(MenuGroup.sort_order))
    db.session.add(group)
    db.session.commit()
    return jsonify(group.to_dict()), 201


@bp.route('/groups/reorder', methods=['PUT'])
@token_required
@admin_required
def reorder_groups(current_user):
    if not _apply_order(MenuGroup, (request.get_json() or {}).get('ids')):
        return _error('La lista de grupos no es válida')
    return jsonify({'message': 'Orden actualizado'}), 200


@bp.route('/groups/<int:group_id>', methods=['PUT'])
@token_required
@admin_required
def update_group(current_user, group_id):
    group = db.get_or_404(MenuGroup, group_id)
    name, error = _required_text((request.get_json() or {}).get('name'), 100)
    if error:
        return _error(error)
    group.name = name
    group.slug = unique_slug(MenuGroup, name, exclude_id=group.id)
    db.session.commit()
    return jsonify(group.to_dict()), 200


@bp.route('/groups/<int:group_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_group(current_user, group_id):
    group = db.get_or_404(MenuGroup, group_id)
    start = _next_order(MenuCategory.sort_order, MenuCategory.group_id.is_(None))
    for offset, category in enumerate(sorted(group.categories, key=lambda c: (c.sort_order, c.id))):
        category.group_id = None
        category.sort_order = start + offset
    db.session.delete(group)
    db.session.commit()
    return jsonify({'message': 'Grupo eliminado'}), 200


# ---------- Categorías ----------

@bp.route('/categories/reorder', methods=['PUT'])
@token_required
@admin_required
def reorder_categories(current_user):
    data = request.get_json() or {}
    group_id = data.get('group_id')
    if group_id is not None and not _is_int(group_id):
        return _error('Grupo inexistente')
    scope = MenuCategory.group_id.is_(None) if group_id is None else MenuCategory.group_id == group_id
    if not _apply_order(MenuCategory, data.get('ids'), scope):
        return _error('La lista de categorías no es válida')
    return jsonify({'message': 'Orden actualizado'}), 200


@bp.route('/categories/<int:category_id>', methods=['PUT'])
@token_required
@admin_required
def update_category(current_user, category_id):
    category = db.get_or_404(MenuCategory, category_id)
    data = request.get_json() or {}
    if 'name' in data:
        if category.fudo_category_id:
            return _error('El nombre de la categoría viene de Fudo')
        name, error = _required_text(data.get('name'), 100)
        if error:
            return _error(error)
        category.name = name
        category.slug = unique_slug(MenuCategory, name, exclude_id=category.id)
    if 'description' in data:
        description, error = _clean_text(data.get('description'), 10_000, 'La descripción')
        if error:
            return _error(error)
        category.description = description
    if 'is_visible' in data:
        category.is_visible = bool(data['is_visible'])
    if 'show_title' in data:
        category.show_title = bool(data['show_title'])
    if 'group_id' in data:
        group_id = data['group_id']
        if group_id is not None and (not _is_int(group_id) or db.session.get(MenuGroup, group_id) is None):
            return _error('Grupo inexistente')
        if category.group_id != group_id:
            scope = MenuCategory.group_id.is_(None) if group_id is None else MenuCategory.group_id == group_id
            category.sort_order = _next_order(MenuCategory.sort_order, scope)
            category.group_id = group_id
    db.session.commit()
    return jsonify(category.to_dict(include_items=True)), 200


@bp.route('/categories/<int:category_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_category(current_user, category_id):
    category = db.get_or_404(MenuCategory, category_id)
    if category.fudo_category_id:
        return _error('Las categorías de Fudo no se borran: ocultala', 409)
    if category.items:
        return _error('La categoría tiene ítems: movelos o borralos primero', 409)
    db.session.delete(category)
    db.session.commit()
    return jsonify({'message': 'Categoría eliminada'}), 200


@bp.route('/categories/<int:category_id>/items/reorder', methods=['PUT'])
@token_required
@admin_required
def reorder_items(current_user, category_id):
    db.get_or_404(MenuCategory, category_id)
    ids = (request.get_json() or {}).get('ids')
    if not _apply_order(MenuItem, ids, MenuItem.category_id == category_id):
        return _error('La lista de ítems no es válida')
    return jsonify({'message': 'Orden actualizado'}), 200


# ---------- Ítems ----------

def _build_variants(item, variants_data):
    """Valida y construye las variantes. Devuelve (variantes, error)."""
    if not isinstance(variants_data, list) or not variants_data:
        return None, 'El ítem necesita al menos un precio'
    variants = []
    seen_fudo_ids = set()
    if not all(isinstance(raw, dict) for raw in variants_data):
        return None, 'Las variantes no son válidas'
    for position, raw in enumerate(variants_data):
        label, error = _clean_text(raw.get('label'), 100, 'La etiqueta')
        if error:
            return None, error
        fudo_id = str(raw['fudo_product_id']) if raw.get('fudo_product_id') else None
        if fudo_id is not None and not isinstance(raw['fudo_product_id'], (str, int)):
            return None, 'Producto de Fudo inválido'
        if fudo_id:
            if fudo_id in seen_fudo_ids:
                return None, 'Un producto de Fudo no puede repetirse en el mismo ítem'
            seen_fudo_ids.add(fudo_id)
            product = db.session.get(FudoProduct, fudo_id)
            if product is None:
                # Producto desaparecido de Fudo: se conserva solo si este ítem ya lo tenía vinculado.
                existing = None
                if item.id is not None:
                    existing = next((v for v in item.variants if v.fudo_product_id == fudo_id), None)
                if existing is None:
                    return None, f'Producto de Fudo {fudo_id} no encontrado: sincronizá con Fudo primero'
                variants.append(MenuItemVariant(
                    label=label, fudo_product_id=fudo_id, price=existing.price,
                    fudo_status='missing', sort_order=position,
                ))
                continue
            taken = MenuItemVariant.query.filter(MenuItemVariant.fudo_product_id == fudo_id)
            if item.id is not None:
                taken = taken.filter(MenuItemVariant.item_id != item.id)
            if taken.first() is not None:
                return None, f'El producto de Fudo "{product.name}" ya está en otro ítem'
            price = product.price
            status = 'ok' if product.is_active else 'inactive'
        else:
            price = _parse_price(raw.get('price'))
            if price is None:
                return None, 'Precio inválido'
            status = None
        variants.append(MenuItemVariant(
            label=label, fudo_product_id=fudo_id, price=price, fudo_status=status, sort_order=position,
        ))
    return variants, None


def _apply_item_payload(item, data):
    """Aplica los campos presentes en `data`. Devuelve un mensaje de error o None."""
    if 'name' in data:
        name, error = _required_text(data.get('name'), 200)
        if error:
            return error
        item.name = name
    if 'description' in data:
        description, error = _clean_text(data.get('description'), 10_000, 'La descripción')
        if error:
            return error
        item.description = description
    if 'category_id' in data:
        category_id = data['category_id']
        category = db.session.get(MenuCategory, category_id) if _is_int(category_id) else None
        if category is None:
            return 'Categoría inexistente'
        if item.category_id != category.id:
            item.sort_order = _next_order(MenuItem.sort_order, MenuItem.category_id == category.id)
            item.category_id = category.id
    if 'is_visible' in data:
        item.is_visible = bool(data['is_visible'])
    if 'is_featured' in data:
        item.is_featured = bool(data['is_featured'])
    if 'tag_ids' in data:
        if not _is_int_list(data.get('tag_ids') or []):
            return 'Etiquetas inválidas'
        tag_ids = set(data.get('tag_ids') or [])
        tags = MenuTag.query.filter(MenuTag.id.in_(tag_ids)).all() if tag_ids else []
        if len(tags) != len(tag_ids):
            return 'Etiqueta inexistente'
        item.tags = tags
    if 'variants' in data:
        variants, error = _build_variants(item, data['variants'])
        if error:
            return error
        if item.id is not None:
            # Borrar primero para no chocar con el unique de fudo_product_id al re-vincular.
            item.variants.clear()
            db.session.flush()
        item.variants = variants
    return None


@bp.route('/items', methods=['POST'])
@token_required
@admin_required
def create_item(current_user):
    data = request.get_json() or {}
    if 'variants' not in data:
        return _error('El ítem necesita al menos un precio')
    category_id = data.get('category_id')
    category = db.session.get(MenuCategory, category_id) if _is_int(category_id) else None
    if category is None:
        return _error('Categoría inexistente')
    item = MenuItem(
        category_id=category.id,
        name='',
        sort_order=_next_order(MenuItem.sort_order, MenuItem.category_id == category.id),
    )
    payload = {key: value for key, value in data.items() if key != 'category_id'}
    payload.setdefault('name', '')
    error = _apply_item_payload(item, payload)
    if error:
        db.session.rollback()
        return _error(error)
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@bp.route('/items/<int:item_id>', methods=['PUT'])
@token_required
@admin_required
def update_item(current_user, item_id):
    item = db.get_or_404(MenuItem, item_id)
    error = _apply_item_payload(item, request.get_json() or {})
    if error:
        db.session.rollback()
        return _error(error)
    db.session.commit()
    return jsonify(item.to_dict()), 200


@bp.route('/items/<int:item_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_item(current_user, item_id):
    item = db.get_or_404(MenuItem, item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Ítem eliminado'}), 200


# ---------- Tags ----------

def _apply_tag_payload(tag, data):
    if 'name' in data:
        name, error = _required_text(data.get('name'), 50)
        if error:
            return error
        tag.name = name
        tag.slug = unique_slug(MenuTag, name, exclude_id=tag.id)
    if 'color' in data:
        color = data.get('color')
        if not isinstance(color, str) or not COLOR_PATTERN.fullmatch(color):
            return 'Color inválido (formato #RRGGBB)'
        tag.color = color
    return None


@bp.route('/tags', methods=['POST'])
@token_required
@admin_required
def create_tag(current_user):
    data = request.get_json() or {}
    tag = MenuTag(color='#5C2E46')
    error = _apply_tag_payload(tag, {'name': data.get('name'), **({'color': data['color']} if 'color' in data else {})})
    if error:
        return _error(error)
    db.session.add(tag)
    db.session.commit()
    return jsonify(tag.to_dict()), 201


@bp.route('/tags/<int:tag_id>', methods=['PUT'])
@token_required
@admin_required
def update_tag(current_user, tag_id):
    tag = db.get_or_404(MenuTag, tag_id)
    error = _apply_tag_payload(tag, request.get_json() or {})
    if error:
        db.session.rollback()
        return _error(error)
    db.session.commit()
    return jsonify(tag.to_dict()), 200


@bp.route('/tags/<int:tag_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_tag(current_user, tag_id):
    tag = db.get_or_404(MenuTag, tag_id)
    db.session.delete(tag)
    db.session.commit()
    return jsonify({'message': 'Etiqueta eliminada'}), 200


# ---------- Configuración ----------

SETTING_MAX_LENGTH = {'footer_text': 2000, 'instagram': 100}
SETTING_LABELS = {'footer_text': 'El texto del pie', 'instagram': 'El usuario de Instagram'}


def _normalize_instagram(value):
    value = value.strip()
    marker = 'instagram.com/'
    index = value.lower().find(marker)
    if index != -1:
        value = re.split(r'[/?#]', value[index + len(marker):], maxsplit=1)[0]
    return value.strip().lstrip('@').strip()


def _settings():
    return {key: MenuSetting.get(key, '') or '' for key in SETTING_KEYS}


@bp.route('/settings', methods=['GET'])
@token_required
@admin_required
def get_settings(current_user):
    return jsonify(_settings()), 200


@bp.route('/settings', methods=['PUT'])
@token_required
@admin_required
def update_settings(current_user):
    data = request.get_json() or {}
    values = {}
    for key in SETTING_KEYS:
        if key not in data:
            continue
        value = data[key]
        if value is None:
            value = ''
        if not isinstance(value, str):
            return _error(f'{SETTING_LABELS[key]} debe ser texto')
        value = value.strip()
        if key == 'instagram':
            value = _normalize_instagram(value)
        if len(value) > SETTING_MAX_LENGTH[key]:
            return _error(f'{SETTING_LABELS[key]} es demasiado largo (máximo {SETTING_MAX_LENGTH[key]} caracteres)')
        values[key] = value
    for key, value in values.items():
        MenuSetting.set(key, value)
    db.session.commit()
    return jsonify(_settings()), 200


# ---------- Fotos ----------

@bp.route('/items/<int:item_id>/image', methods=['POST'])
@token_required
@admin_required
def upload_item_image(current_user, item_id):
    item = db.get_or_404(MenuItem, item_id)
    if request.content_length is not None and request.content_length > MAX_UPLOAD_BYTES + UPLOAD_OVERHEAD_BYTES:
        return _error('La imagen supera los 10 MB')
    upload = request.files.get('image')
    if upload is None:
        return _error('Falta el archivo "image"')
    try:
        body, key = process_image(upload.read(MAX_UPLOAD_BYTES + 1))
    except InvalidImageError as exc:
        return _error(str(exc))
    try:
        get_menu_storage().put(key, body, 'image/webp', 'public, max-age=31536000, immutable')
    except Exception:
        db.session.rollback()
        logger.exception('Error subiendo la foto del ítem %s', item_id)
        return _error('No se pudo subir la foto, probá de nuevo', 502)
    item.image_key = key
    db.session.commit()
    return jsonify(item.to_dict()), 200


@bp.route('/items/<int:item_id>/image', methods=['DELETE'])
@token_required
@admin_required
def delete_item_image(current_user, item_id):
    item = db.get_or_404(MenuItem, item_id)
    item.image_key = None  # el archivo se borra de S3 al publicar si nadie lo usa
    db.session.commit()
    return jsonify(item.to_dict()), 200


# ---------- Productos de Fudo y bandeja ----------

@bp.route('/fudo-products', methods=['GET'])
@token_required
@admin_required
def list_fudo_products(current_user):
    if request.args.get('unassigned') == 'true':
        products = menu_sync_service.unassigned_products()
    else:
        products = FudoProduct.query.filter_by(is_active=True).order_by(FudoProduct.name).all()
    query = (request.args.get('q') or '').strip().lower()
    if query:
        products = [p for p in products if query in p.name.lower()]
    linked = menu_sync_service.linked_fudo_ids()
    return jsonify([{**p.to_dict(), 'linked': p.fudo_id in linked} for p in products]), 200


@bp.route('/fudo-products/<fudo_id>/ignore', methods=['POST'])
@token_required
@admin_required
def ignore_fudo_product(current_user, fudo_id):
    product = db.get_or_404(FudoProduct, fudo_id)
    product.ignored = True
    db.session.commit()
    return jsonify(product.to_dict()), 200


@bp.route('/inbox', methods=['GET'])
@token_required
@admin_required
def get_inbox(current_user):
    alerts = []
    for variant in menu_sync_service.alert_variants():
        product = db.session.get(FudoProduct, variant.fudo_product_id)
        alerts.append({
            **variant.to_dict(),
            'item_id': variant.item_id,
            'item_name': variant.item.name,
            'fudo_name': product.name if product else None,
        })
    return jsonify({
        'unassigned': [p.to_dict() for p in menu_sync_service.unassigned_products()],
        'alerts': alerts,
    }), 200


# ---------- Sync y publicación ----------

@bp.route('/sync', methods=['POST'])
@token_required
@admin_required
def sync_fudo(current_user):
    try:
        stats = menu_sync_service.sync_fudo_products(FudoClient())
    except Exception:
        db.session.rollback()
        logger.exception('Error sincronizando la carta con Fudo')
        return _error('Error sincronizando con Fudo. Revisá las credenciales o probá más tarde.', 502)
    return jsonify({**stats, 'status': _status()}), 200


@bp.route('/publish', methods=['POST'])
@token_required
@admin_required
def publish_menu(current_user):
    try:
        result = menu_publish_service.publish(get_menu_storage())
    except Exception:
        db.session.rollback()
        logger.exception('Error publicando la carta')
        return _error('Error publicando la carta. Probá de nuevo en unos minutos.', 502)
    return jsonify({**result, 'status': _status()}), 200
