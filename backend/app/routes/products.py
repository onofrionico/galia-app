from decimal import Decimal

from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.product_recipe_item import ProductRecipeItem
from app.models.product_category import ProductCategory
from app.models.supply import Supply
from app.models.menu import FudoProduct
from app.services import menu_sync_service
from app.utils.fudo_client import FudoClient
from app.utils.jwt_utils import token_required
from app.utils.decorators import module_required, authenticated_only
from app.utils.validation import clean_str, json_object, parse_decimal
from app.services.menu_image_service import MAX_UPLOAD_BYTES, InvalidImageError, process_image
from app.utils.menu_storage import get_menu_storage, public_url
from app.services.product_fudo_info import (
    FUDO_LOCKED_ERROR, LOCKED_VARIANT_FIELDS, changes_locked, fudo_info, fudo_payload,
    locked_product_fields, product_detail,
)

UPLOAD_OVERHEAD_BYTES = 1024 * 1024  # overhead multipart

# Límites según la capacidad de las columnas Numeric (exclusivos)
MAX_PRICE = Decimal('100000000')      # Numeric(10, 2)
MAX_STOCK = Decimal('10000000')       # Numeric(10, 3)
MAX_RECIPE_QTY = Decimal('1000000')   # Numeric(10, 4)

bp = Blueprint('products', __name__, url_prefix='/api/v1/products')

_BAD_BODY = ({'error': 'El cuerpo de la petición debe ser un objeto JSON'}, 400)


def _bad_body():
    return jsonify(_BAD_BODY[0]), _BAD_BODY[1]


def _fudo_locked():
    return jsonify({'error': FUDO_LOCKED_ERROR}), 409


def _valid_id(value):
    return isinstance(value, int) and not isinstance(value, bool)


@bp.route('', methods=['GET'])
@token_required
@authenticated_only
def list_products(current_user):
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '').strip()
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    page = request.args.get('page', 1, type=int)
    per_page = max(1, min(request.args.get('per_page', 50, type=int), 200))

    fudo_alerts = request.args.get('fudo_alerts', 'false').lower() == 'true'

    query = Product.query
    if fudo_alerts:
        alert_ids = db.session.query(ProductVariant.product_id).filter(
            ProductVariant.fudo_status.in_(['missing', 'inactive']))
        query = query.filter(Product.id.in_(alert_ids))
    elif not include_inactive:
        query = query.filter(Product.is_active == True)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    paginated = query.order_by(Product.name).paginate(page=page, per_page=per_page, error_out=False)
    products = [p.to_dict() for p in paginated.items]

    for p in products:
        variants = ProductVariant.query.filter_by(product_id=p['id'], is_active=True).all()
        p['variants'] = [v.to_dict() for v in variants]

    info = fudo_info([p['id'] for p in products])
    for p in products:
        p.update(fudo_payload(info.get(p['id'])))

    return jsonify({
        'products': products,
        'total': paginated.total,
        'page': page,
        'per_page': per_page,
        'pages': paginated.pages
    }), 200


@bp.route('', methods=['POST'])
@token_required
@module_required('Products')
def create_product(current_user):
    data = json_object()
    if data is None:
        return _bad_body()

    try:
        name = clean_str(data.get('name'), 200)
        description = clean_str(data.get('description'))
        image_url = clean_str(data.get('image_url'), 500)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    if not name:
        return jsonify({'error': 'El nombre del producto es requerido'}), 400
    if not data.get('category_id'):
        return jsonify({'error': 'El category_id es requerido'}), 400
    if not _valid_id(data['category_id']):
        return jsonify({'error': 'category_id inválido'}), 400

    if not db.session.get(ProductCategory, data['category_id']):
        return jsonify({'error': 'Categoría no encontrada'}), 404

    product = Product(
        name=name,
        description=description,
        category_id=data['category_id'],
        image_url=image_url,
        has_recipe=bool(data.get('has_recipe', False)),
        track_stock=bool(data.get('track_stock', False)),
    )

    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201


@bp.route('/<int:product_id>', methods=['GET'])
@token_required
@authenticated_only
def get_product(current_user, product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product_detail(product)), 200


@bp.route('/<int:product_id>', methods=['PUT'])
@token_required
@module_required('Products')
def update_product(current_user, product_id):
    product = Product.query.get_or_404(product_id)
    data = json_object()
    if data is None:
        return _bad_body()

    locked = locked_product_fields(fudo_info([product.id]).get(product.id))
    if changes_locked(data, locked, product):
        return _fudo_locked()

    try:
        if 'name' in data:
            name = clean_str(data['name'], 200)
            if not name:
                return jsonify({'error': 'El nombre no puede estar vacío'}), 400
            product.name = name

        if 'category_id' in data:
            if not _valid_id(data['category_id']):
                return jsonify({'error': 'category_id inválido'}), 400
            if not db.session.get(ProductCategory, data['category_id']):
                return jsonify({'error': 'Categoría no encontrada'}), 404
            product.category_id = data['category_id']

        if 'description' in data:
            product.description = clean_str(data['description'])
        if 'image_url' in data:
            product.image_url = clean_str(data['image_url'], 500)
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 400

    if 'has_recipe' in data:
        product.has_recipe = bool(data['has_recipe'])

    if 'track_stock' in data:
        product.track_stock = bool(data['track_stock'])

    if 'is_active' in data:
        product.is_active = bool(data['is_active'])

    db.session.commit()
    return jsonify(product_detail(product)), 200


@bp.route('/<int:product_id>', methods=['DELETE'])
@token_required
@module_required('Products')
def delete_product(current_user, product_id):
    product = Product.query.get_or_404(product_id)
    if fudo_info([product.id]):
        return _fudo_locked()
    product.is_active = False
    db.session.commit()
    return jsonify({'message': 'Producto desactivado correctamente'}), 200


@bp.route('/<int:product_id>/variants', methods=['GET'])
@token_required
@authenticated_only
def get_variants(current_user, product_id):
    Product.query.get_or_404(product_id)
    variants = ProductVariant.query.filter_by(product_id=product_id, is_active=True).order_by(ProductVariant.name).all()
    return jsonify({'variants': [v.to_dict() for v in variants], 'total': len(variants)}), 200


@bp.route('/<int:product_id>/variants', methods=['POST'])
@token_required
@module_required('Products')
def create_variant(current_user, product_id):
    Product.query.get_or_404(product_id)
    data = json_object()
    if data is None:
        return _bad_body()

    try:
        name = clean_str(data.get('name'), 100)
        if not name:
            return jsonify({'error': 'El nombre de la variante es requerido'}), 400
        if 'price' not in data:
            return jsonify({'error': 'El precio es requerido'}), 400
        price = parse_decimal(data['price'], 'El precio', maximum=MAX_PRICE)
        stock = parse_decimal(data.get('stock_quantity', 0), 'stock_quantity', maximum=MAX_STOCK)
        min_stock = parse_decimal(data.get('min_stock', 0), 'min_stock', maximum=MAX_STOCK)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    variant = ProductVariant(
        product_id=product_id,
        name=name,
        price=price,
        stock_quantity=stock,
        min_stock=min_stock,
    )

    db.session.add(variant)
    db.session.commit()
    return jsonify(variant.to_dict()), 201


@bp.route('/<int:product_id>/variants/<int:variant_id>', methods=['PUT'])
@token_required
@module_required('Products')
def update_variant(current_user, product_id, variant_id):
    variant = ProductVariant.query.filter_by(id=variant_id, product_id=product_id).first_or_404()
    data = json_object()
    if data is None:
        return _bad_body()
    if variant.fudo_product_id and changes_locked(data, LOCKED_VARIANT_FIELDS, variant):
        return _fudo_locked()

    try:
        updates = {}
        if 'name' in data:
            name = clean_str(data['name'], 100)
            if not name:
                return jsonify({'error': 'El nombre no puede estar vacío'}), 400
            updates['name'] = name
        if 'price' in data:
            updates['price'] = parse_decimal(data['price'], 'El precio', maximum=MAX_PRICE)
        if 'stock_quantity' in data:
            updates['stock_quantity'] = parse_decimal(data['stock_quantity'], 'stock_quantity', maximum=MAX_STOCK)
        if 'min_stock' in data:
            updates['min_stock'] = parse_decimal(data['min_stock'], 'min_stock', maximum=MAX_STOCK)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    for field, value in updates.items():
        setattr(variant, field, value)

    if 'is_active' in data:
        variant.is_active = bool(data['is_active'])

    db.session.commit()
    return jsonify(variant.to_dict()), 200


@bp.route('/<int:product_id>/variants/<int:variant_id>', methods=['DELETE'])
@token_required
@module_required('Products')
def delete_variant(current_user, product_id, variant_id):
    variant = ProductVariant.query.filter_by(id=variant_id, product_id=product_id).first_or_404()
    if variant.fudo_product_id:
        return _fudo_locked()
    variant.is_active = False
    db.session.commit()
    return jsonify({'message': 'Variante desactivada correctamente'}), 200


@bp.route('/<int:product_id>/recipe', methods=['GET'])
@token_required
@authenticated_only
def get_recipe(current_user, product_id):
    product = Product.query.get_or_404(product_id)
    if not product.has_recipe:
        return jsonify({'recipe': []}), 200

    items = ProductRecipeItem.query.filter_by(product_id=product_id).all()
    return jsonify({'recipe': [i.to_dict() for i in items], 'total': len(items)}), 200


@bp.route('/<int:product_id>/recipe', methods=['PUT'])
@token_required
@module_required('Products')
def update_recipe(current_user, product_id):
    Product.query.get_or_404(product_id)
    data = json_object()
    if data is None:
        return _bad_body()
    items = data.get('items', [])
    if not isinstance(items, list):
        return jsonify({'error': 'items debe ser una lista'}), 400

    # Validar todo el payload antes de tocar la receta existente
    validated = []
    seen = set()
    try:
        for item in items:
            if not isinstance(item, dict):
                return jsonify({'error': 'Cada ítem de la receta debe ser un objeto'}), 400
            supply_id = item.get('supply_id')
            if not _valid_id(supply_id):
                return jsonify({'error': 'supply_id inválido'}), 400
            if supply_id in seen:
                return jsonify({'error': f'Insumo {supply_id} repetido en la receta'}), 400
            seen.add(supply_id)
            supply = db.session.get(Supply, supply_id)
            if not supply or not supply.is_active:
                return jsonify({'error': f'Insumo {supply_id} no encontrado o inactivo'}), 400
            quantity = parse_decimal(item.get('quantity'), 'La cantidad', maximum=MAX_RECIPE_QTY)
            if quantity <= 0:
                return jsonify({'error': 'La cantidad debe ser mayor a 0'}), 400
            unit = clean_str(item.get('unit'), 50) or supply.unit
            validated.append((supply_id, quantity, unit))
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    ProductRecipeItem.query.filter_by(product_id=product_id).delete()
    for supply_id, quantity, unit in validated:
        db.session.add(ProductRecipeItem(
            product_id=product_id,
            supply_id=supply_id,
            quantity=quantity,
            unit=unit,
        ))

    db.session.commit()
    items = ProductRecipeItem.query.filter_by(product_id=product_id).all()
    return jsonify({'recipe': [i.to_dict() for i in items]}), 200


@bp.route('/low-stock', methods=['GET'])
@token_required
@authenticated_only
def get_low_stock(current_user):
    low_variants = db.session.query(ProductVariant).filter(
        ProductVariant.stock_quantity <= ProductVariant.min_stock,
        ProductVariant.is_active == True
    ).all()

    low_supplies = db.session.query(Supply).filter(
        Supply.stock_quantity <= Supply.min_stock,
        Supply.is_active == True
    ).all()

    return jsonify({
        'variants': [v.to_dict() for v in low_variants],
        'supplies': [s.to_dict() for s in low_supplies],
        'total_variants': len(low_variants),
        'total_supplies': len(low_supplies),
    }), 200


@bp.route('/<int:product_id>/variants/<int:variant_id>/stock', methods=['PUT'])
@token_required
@module_required('Stock')
def adjust_stock(current_user, product_id, variant_id):
    variant = ProductVariant.query.filter_by(id=variant_id, product_id=product_id).first_or_404()
    data = json_object()
    if data is None:
        return _bad_body()

    if 'stock_quantity' not in data:
        return jsonify({'error': 'stock_quantity es requerido'}), 400

    try:
        variant.stock_quantity = parse_decimal(data['stock_quantity'], 'stock_quantity', maximum=MAX_STOCK)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    db.session.commit()
    return jsonify(variant.to_dict()), 200


@bp.route('/upload-image', methods=['POST'])
@token_required
@module_required('Products')
def upload_image_endpoint(current_user):
    """Sube la imagen de un producto al prefijo público `products/` y devuelve su URL."""
    if request.content_length is not None and request.content_length > MAX_UPLOAD_BYTES + UPLOAD_OVERHEAD_BYTES:
        return jsonify({'error': 'La imagen supera los 10 MB'}), 413
    upload = request.files.get('file')
    if upload is None or upload.filename == '':
        return jsonify({'error': 'No se envió ningún archivo'}), 400
    try:
        body, key = process_image(upload.read(MAX_UPLOAD_BYTES + 1), key_prefix='products/')
    except InvalidImageError as exc:
        return jsonify({'error': str(exc)}), 400
    try:
        get_menu_storage().put(key, body, 'image/webp', 'public, max-age=31536000, immutable')
    except Exception:
        current_app.logger.exception('Error subiendo la imagen del producto')
        return jsonify({'error': 'No se pudo subir la imagen, probá de nuevo'}), 502
    return jsonify({'image_url': public_url(key)}), 200


@bp.route('/sync', methods=['POST'])
@token_required
@module_required('Products')
def sync_fudo(current_user):
    try:
        stats = menu_sync_service.sync_fudo_products(FudoClient())
    except Exception:
        db.session.rollback()
        current_app.logger.exception('Error sincronizando productos con Fudo')
        return jsonify({'error': 'Error sincronizando con Fudo. Revisá las credenciales o probá más tarde.'}), 502
    return jsonify(stats), 200


@bp.route('/fudo-candidates', methods=['GET'])
@token_required
@authenticated_only
def fudo_candidates(current_user):
    rows = (
        db.session.query(FudoProduct, Product.id, Product.name)
        .outerjoin(ProductVariant, ProductVariant.fudo_product_id == FudoProduct.fudo_id)
        .outerjoin(Product, Product.id == ProductVariant.product_id)
        .order_by(FudoProduct.name)
        .all()
    )
    return jsonify({'products': [
        {**fudo.to_dict(), 'product_id': product_id, 'product_name': product_name}
        for fudo, product_id, product_name in rows
    ]}), 200


def _deactivate_if_empty(product):
    db.session.flush()
    if product.variants.filter_by(is_active=True).count() == 0:
        product.is_active = False


@bp.route('/<int:product_id>/variants/attach', methods=['POST'])
@token_required
@module_required('Products')
def attach_fudo_variant(current_user, product_id):
    product = Product.query.get_or_404(product_id)
    data = json_object()
    if data is None:
        return _bad_body()
    fudo_id = data.get('fudo_product_id')
    if not isinstance(fudo_id, str) or not fudo_id.strip():
        return jsonify({'error': 'fudo_product_id es requerido'}), 400
    fudo = db.session.get(FudoProduct, fudo_id.strip())
    if fudo is None:
        return jsonify({'error': 'Producto de Fudo no encontrado'}), 404

    variant = ProductVariant.query.filter_by(fudo_product_id=fudo.fudo_id).first()
    if variant is not None and variant.product_id == product.id:
        return jsonify({'error': 'Ese producto de Fudo ya está en este producto'}), 409
    if variant is None:
        db.session.add(ProductVariant(
            product_id=product.id, name=(fudo.name or 'Sin nombre')[:100], price=fudo.price,
            fudo_product_id=fudo.fudo_id, is_active=bool(fudo.is_active),
            fudo_status='ok' if fudo.is_active else 'inactive',
        ))
    else:
        source = db.session.get(Product, variant.product_id)
        variant.product_id = product.id
        _deactivate_if_empty(source)
    db.session.commit()
    return jsonify(product_detail(product)), 200


@bp.route('/<int:product_id>/variants/<int:variant_id>/detach', methods=['POST'])
@token_required
@module_required('Products')
def detach_variant(current_user, product_id, variant_id):
    product = Product.query.get_or_404(product_id)
    variant = ProductVariant.query.filter_by(id=variant_id, product_id=product_id).first_or_404()
    if not variant.fudo_product_id:
        return jsonify({'error': 'Solo se pueden separar variantes vinculadas a Fudo'}), 409
    if product.variants.count() == 1:
        return jsonify({'error': 'Es la única variante del producto'}), 409

    new_product = Product(name=variant.name[:200], category_id=product.category_id, is_active=variant.is_active)
    db.session.add(new_product)
    db.session.flush()
    variant.product_id = new_product.id
    _deactivate_if_empty(product)
    db.session.commit()
    return jsonify(product_detail(new_product)), 201
