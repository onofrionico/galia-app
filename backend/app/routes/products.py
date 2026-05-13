from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.product_recipe_item import ProductRecipeItem
from app.models.product_category import ProductCategory
from app.models.supply import Supply
from app.utils.jwt_utils import token_required
from app.utils.decorators import admin_required
from sqlalchemy.exc import IntegrityError

bp = Blueprint('products', __name__, url_prefix='/api/v1/products')


@bp.route('', methods=['GET'])
@token_required
def list_products(current_user):
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '').strip()
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    query = Product.query
    if not include_inactive:
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

    return jsonify({
        'products': products,
        'total': paginated.total,
        'page': page,
        'per_page': per_page,
        'pages': paginated.pages
    }), 200


@bp.route('', methods=['POST'])
@token_required
@admin_required
def create_product(current_user):
    data = request.get_json() or {}

    if not data.get('name', '').strip():
        return jsonify({'error': 'El nombre del producto es requerido'}), 400
    if not data.get('category_id'):
        return jsonify({'error': 'El category_id es requerido'}), 400

    if not ProductCategory.query.get(data['category_id']):
        return jsonify({'error': 'Categoría no encontrada'}), 404

    product = Product(
        name=data['name'].strip(),
        description=data.get('description', '').strip() or None,
        category_id=data['category_id'],
        image_url=data.get('image_url', '').strip() or None,
        has_recipe=bool(data.get('has_recipe', False)),
    )

    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201


@bp.route('/<int:product_id>', methods=['GET'])
@token_required
def get_product(current_user, product_id):
    product = Product.query.get_or_404(product_id)
    data = product.to_dict()

    variants = ProductVariant.query.filter_by(product_id=product_id).all()
    data['variants'] = [v.to_dict() for v in variants]

    if product.has_recipe:
        recipe = ProductRecipeItem.query.filter_by(product_id=product_id).all()
        data['recipe'] = [r.to_dict() for r in recipe]

    return jsonify(data), 200


@bp.route('/<int:product_id>', methods=['PUT'])
@token_required
@admin_required
def update_product(current_user, product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json() or {}

    if 'name' in data:
        if not data['name'].strip():
            return jsonify({'error': 'El nombre no puede estar vacío'}), 400
        product.name = data['name'].strip()

    if 'category_id' in data:
        if not ProductCategory.query.get(data['category_id']):
            return jsonify({'error': 'Categoría no encontrada'}), 404
        product.category_id = data['category_id']

    for field in ('description', 'image_url'):
        if field in data:
            val = data[field]
            setattr(product, field, val.strip() if val else None)

    if 'has_recipe' in data:
        product.has_recipe = bool(data['has_recipe'])

    if 'is_active' in data:
        product.is_active = bool(data['is_active'])

    db.session.commit()
    return jsonify(product.to_dict()), 200


@bp.route('/<int:product_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_product(current_user, product_id):
    product = Product.query.get_or_404(product_id)
    product.is_active = False
    db.session.commit()
    return jsonify({'message': 'Producto desactivado correctamente'}), 200


@bp.route('/<int:product_id>/variants', methods=['GET'])
@token_required
def get_variants(current_user, product_id):
    Product.query.get_or_404(product_id)
    variants = ProductVariant.query.filter_by(product_id=product_id, is_active=True).order_by(ProductVariant.name).all()
    return jsonify({'variants': [v.to_dict() for v in variants], 'total': len(variants)}), 200


@bp.route('/<int:product_id>/variants', methods=['POST'])
@token_required
@admin_required
def create_variant(current_user, product_id):
    Product.query.get_or_404(product_id)
    data = request.get_json() or {}

    if not data.get('name', '').strip():
        return jsonify({'error': 'El nombre de la variante es requerido'}), 400
    if not data.get('price'):
        return jsonify({'error': 'El precio es requerido'}), 400

    variant = ProductVariant(
        product_id=product_id,
        name=data['name'].strip(),
        price=float(data['price']),
        stock_quantity=float(data.get('stock_quantity', 0)),
        min_stock=float(data.get('min_stock', 0)),
    )

    db.session.add(variant)
    db.session.commit()
    return jsonify(variant.to_dict()), 201


@bp.route('/<int:product_id>/variants/<int:variant_id>', methods=['PUT'])
@token_required
@admin_required
def update_variant(current_user, product_id, variant_id):
    variant = ProductVariant.query.filter_by(id=variant_id, product_id=product_id).first_or_404()
    data = request.get_json() or {}

    if 'name' in data:
        if not data['name'].strip():
            return jsonify({'error': 'El nombre no puede estar vacío'}), 400
        variant.name = data['name'].strip()

    if 'price' in data:
        variant.price = float(data['price'])

    if 'stock_quantity' in data:
        variant.stock_quantity = float(data['stock_quantity'])

    if 'min_stock' in data:
        variant.min_stock = float(data['min_stock'])

    if 'is_active' in data:
        variant.is_active = bool(data['is_active'])

    db.session.commit()
    return jsonify(variant.to_dict()), 200


@bp.route('/<int:product_id>/variants/<int:variant_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_variant(current_user, product_id, variant_id):
    variant = ProductVariant.query.filter_by(id=variant_id, product_id=product_id).first_or_404()
    variant.is_active = False
    db.session.commit()
    return jsonify({'message': 'Variante desactivada correctamente'}), 200


@bp.route('/<int:product_id>/recipe', methods=['GET'])
@token_required
def get_recipe(current_user, product_id):
    product = Product.query.get_or_404(product_id)
    if not product.has_recipe:
        return jsonify({'recipe': []}), 200

    items = ProductRecipeItem.query.filter_by(product_id=product_id).all()
    return jsonify({'recipe': [i.to_dict() for i in items], 'total': len(items)}), 200


@bp.route('/<int:product_id>/recipe', methods=['PUT'])
@token_required
@admin_required
def update_recipe(current_user, product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json() or {}
    items = data.get('items', [])

    ProductRecipeItem.query.filter_by(product_id=product_id).delete()

    for item in items:
        if not item.get('supply_id') or not item.get('quantity'):
            continue

        if not Supply.query.get(item['supply_id']):
            db.session.rollback()
            return jsonify({'error': f"Supply {item['supply_id']} no encontrado"}), 404

        recipe_item = ProductRecipeItem(
            product_id=product_id,
            supply_id=item['supply_id'],
            quantity=float(item['quantity']),
            unit=item.get('unit', ''),
        )
        db.session.add(recipe_item)

    db.session.commit()
    items = ProductRecipeItem.query.filter_by(product_id=product_id).all()
    return jsonify({'recipe': [i.to_dict() for i in items]}), 200


@bp.route('/low-stock', methods=['GET'])
@token_required
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
@admin_required
def adjust_stock(current_user, product_id, variant_id):
    variant = ProductVariant.query.filter_by(id=variant_id, product_id=product_id).first_or_404()
    data = request.get_json() or {}

    if 'stock_quantity' not in data:
        return jsonify({'error': 'stock_quantity es requerido'}), 400

    variant.stock_quantity = float(data['stock_quantity'])
    db.session.commit()
    return jsonify(variant.to_dict()), 200
