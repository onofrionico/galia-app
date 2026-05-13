from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Product, ProductVariant, ProductRecipeItem, Supply
from app.utils.jwt_utils import token_required
from sqlalchemy import or_

bp = Blueprint('products', __name__, url_prefix='/api/v1/products')

@bp.route('/', methods=['GET'])
def get_products():
    """Lista de productos con filtros y paginación"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '')
    is_active = request.args.get('is_active', 'true').lower() == 'true'

    query = Product.query

    if is_active:
        query = query.filter_by(is_active=True)

    if category_id:
        query = query.filter_by(category_id=category_id)

    if search:
        query = query.filter(or_(
            Product.name.ilike(f'%{search}%'),
            Product.description.ilike(f'%{search}%')
        ))

    pagination = query.paginate(page=page, per_page=per_page)

    return jsonify({
        'items': [p.to_dict(include_variants=True) for p in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@bp.route('/', methods=['POST'])
@token_required
def create_product(current_user):
    """Crear producto"""
    data = request.get_json()

    if not data or not data.get('name') or not data.get('category_id'):
        return jsonify({'error': 'Nombre y categoría son requeridos'}), 400

    product = Product(
        name=data['name'],
        description=data.get('description'),
        category_id=data['category_id'],
        image_url=data.get('image_url'),
        has_recipe=data.get('has_recipe', False),
        is_active=True
    )

    db.session.add(product)
    db.session.commit()

    return jsonify(product.to_dict()), 201

@bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Detalle de producto"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Producto no encontrado'}), 404

    return jsonify(product.to_dict(include_variants=True, include_recipe=True)), 200

@bp.route('/<int:product_id>', methods=['PUT'])
@token_required
def update_product(current_user, product_id):
    """Editar producto"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Producto no encontrado'}), 404

    data = request.get_json()

    if 'name' in data:
        product.name = data['name']
    if 'description' in data:
        product.description = data['description']
    if 'category_id' in data:
        product.category_id = data['category_id']
    if 'image_url' in data:
        product.image_url = data['image_url']
    if 'has_recipe' in data:
        product.has_recipe = data['has_recipe']

    db.session.commit()
    return jsonify(product.to_dict()), 200

@bp.route('/<int:product_id>', methods=['DELETE'])
@token_required
def delete_product(current_user, product_id):
    """Desactivar producto"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Producto no encontrado'}), 404

    product.is_active = False
    db.session.commit()

    return jsonify({'message': 'Producto desactivado'}), 200

# VARIANTES

@bp.route('/<int:product_id>/variants', methods=['GET'])
def get_product_variants(product_id):
    """Lista de variantes del producto"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Producto no encontrado'}), 404

    return jsonify([v.to_dict() for v in product.variants]), 200

@bp.route('/<int:product_id>/variants', methods=['POST'])
@token_required
def create_variant(current_user, product_id):
    """Crear variante"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Producto no encontrado'}), 404

    data = request.get_json()

    if not data or not data.get('name') or data.get('price') is None:
        return jsonify({'error': 'Nombre y precio son requeridos'}), 400

    variant = ProductVariant(
        product_id=product_id,
        name=data['name'],
        price=data['price'],
        stock_quantity=data.get('stock_quantity', 0),
        min_stock=data.get('min_stock', 0),
        is_active=True
    )

    db.session.add(variant)
    db.session.commit()

    return jsonify(variant.to_dict()), 201

@bp.route('/<int:product_id>/variants/<int:variant_id>', methods=['PUT'])
@token_required
def update_variant(current_user, product_id, variant_id):
    """Editar variante"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Producto no encontrado'}), 404

    variant = ProductVariant.query.filter_by(id=variant_id, product_id=product_id).first()
    if not variant:
        return jsonify({'error': 'Variante no encontrada'}), 404

    data = request.get_json()

    if 'name' in data:
        variant.name = data['name']
    if 'price' in data:
        variant.price = data['price']
    if 'stock_quantity' in data:
        variant.stock_quantity = data['stock_quantity']
    if 'min_stock' in data:
        variant.min_stock = data['min_stock']

    db.session.commit()
    return jsonify(variant.to_dict()), 200

@bp.route('/<int:product_id>/variants/<int:variant_id>', methods=['DELETE'])
@token_required
def delete_variant(current_user, product_id, variant_id):
    """Desactivar variante"""
    variant = ProductVariant.query.filter_by(id=variant_id, product_id=product_id).first()
    if not variant:
        return jsonify({'error': 'Variante no encontrada'}), 404

    variant.is_active = False
    db.session.commit()

    return jsonify({'message': 'Variante desactivada'}), 200

# RECIPE

@bp.route('/<int:product_id>/recipe', methods=['GET'])
def get_recipe(product_id):
    """Receta del producto"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Producto no encontrado'}), 404

    if not product.has_recipe:
        return jsonify({'error': 'Producto no tiene receta'}), 400

    return jsonify([r.to_dict() for r in product.recipe_items]), 200

@bp.route('/<int:product_id>/recipe', methods=['PUT'])
@token_required
def update_recipe(current_user, product_id):
    """Reemplazar receta completa"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Producto no encontrado'}), 404

    data = request.get_json()

    if not isinstance(data, list):
        return jsonify({'error': 'Receta debe ser un array de items'}), 400

    # Eliminar items anteriores
    ProductRecipeItem.query.filter_by(product_id=product_id).delete()

    # Crear nuevos items
    for item_data in data:
        if not item_data.get('supply_id') or not item_data.get('quantity') or not item_data.get('unit'):
            return jsonify({'error': 'Cada item requiere supply_id, quantity, unit'}), 400

        # Verificar que el insumo existe
        supply = Supply.query.get(item_data['supply_id'])
        if not supply:
            return jsonify({'error': f'Insumo {item_data["supply_id"]} no encontrado'}), 404

        recipe_item = ProductRecipeItem(
            product_id=product_id,
            supply_id=item_data['supply_id'],
            quantity=item_data['quantity'],
            unit=item_data['unit']
        )
        db.session.add(recipe_item)

    db.session.commit()
    return jsonify([r.to_dict() for r in product.recipe_items]), 200

# STOCK

@bp.route('/low-stock', methods=['GET'])
def get_low_stock():
    """Variantes y/o insumos por debajo de min_stock"""
    low_variants = ProductVariant.query.filter(
        ProductVariant.stock_quantity <= ProductVariant.min_stock,
        ProductVariant.is_active == True
    ).all()

    low_supplies = Supply.query.filter(
        Supply.stock_quantity <= Supply.min_stock
    ).all()

    return jsonify({
        'variants': [v.to_dict() for v in low_variants],
        'supplies': [s.to_dict() for s in low_supplies]
    }), 200

@bp.route('/<int:product_id>/variants/<int:variant_id>/stock', methods=['PUT'])
@token_required
def adjust_variant_stock(current_user, product_id, variant_id):
    """Ajuste manual de stock de variante"""
    variant = ProductVariant.query.filter_by(id=variant_id, product_id=product_id).first()
    if not variant:
        return jsonify({'error': 'Variante no encontrada'}), 404

    data = request.get_json()

    if 'quantity' not in data:
        return jsonify({'error': 'Cantidad es requerida'}), 400

    variant.stock_quantity = data['quantity']
    db.session.commit()

    return jsonify(variant.to_dict()), 200
