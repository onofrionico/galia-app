from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import ProductCategory
from app.utils.jwt_utils import token_required

bp = Blueprint('product_categories', __name__, url_prefix='/api/v1/product-categories')

@bp.route('/', methods=['GET'])
def get_categories():
    """Lista de categorías activas"""
    categories = ProductCategory.query.filter_by(is_active=True).all()
    return jsonify([c.to_dict() for c in categories]), 200

@bp.route('/', methods=['POST'])
@token_required
def create_category(current_user):
    """Crear categoría"""
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({'error': 'Nombre es requerido'}), 400

    # Verificar que no exista
    existing = ProductCategory.query.filter_by(name=data['name']).first()
    if existing:
        return jsonify({'error': 'Categoría ya existe'}), 400

    category = ProductCategory(
        name=data['name'],
        description=data.get('description'),
        color=data.get('color'),
        icon=data.get('icon'),
        is_active=True
    )

    db.session.add(category)
    db.session.commit()

    return jsonify(category.to_dict()), 201

@bp.route('/<int:category_id>', methods=['PUT'])
@token_required
def update_category(current_user, category_id):
    """Editar categoría"""
    category = ProductCategory.query.get(category_id)
    if not category:
        return jsonify({'error': 'Categoría no encontrada'}), 404

    data = request.get_json()

    if 'name' in data:
        # Verificar que no exista otro con ese nombre
        existing = ProductCategory.query.filter(
            ProductCategory.name == data['name'],
            ProductCategory.id != category_id
        ).first()
        if existing:
            return jsonify({'error': 'Nombre ya existe'}), 400
        category.name = data['name']

    if 'description' in data:
        category.description = data['description']
    if 'color' in data:
        category.color = data['color']
    if 'icon' in data:
        category.icon = data['icon']

    db.session.commit()
    return jsonify(category.to_dict()), 200

@bp.route('/<int:category_id>', methods=['DELETE'])
@token_required
def delete_category(current_user, category_id):
    """Desactivar categoría (soft delete)"""
    category = ProductCategory.query.get(category_id)
    if not category:
        return jsonify({'error': 'Categoría no encontrada'}), 404

    category.is_active = False
    db.session.commit()

    return jsonify({'message': 'Categoría desactivada'}), 200
