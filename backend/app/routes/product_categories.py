from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.product_category import ProductCategory
from app.utils.jwt_utils import token_required
from app.utils.decorators import admin_required
from sqlalchemy.exc import IntegrityError

bp = Blueprint('product_categories', __name__, url_prefix='/api/v1/product-categories')


@bp.route('', methods=['GET'])
@token_required
def list_categories(current_user):
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'

    query = ProductCategory.query
    if not include_inactive:
        query = query.filter(ProductCategory.is_active == True)

    categories = query.order_by(ProductCategory.name).all()
    return jsonify({'categories': [c.to_dict() for c in categories], 'total': len(categories)}), 200


@bp.route('', methods=['POST'])
@token_required
@admin_required
def create_category(current_user):
    data = request.get_json() or {}

    if not data.get('name', '').strip():
        return jsonify({'error': 'El nombre de la categoría es requerido'}), 400

    category = ProductCategory(
        name=data['name'].strip(),
        description=data.get('description', '').strip() or None,
        color=data.get('color', '').strip() or None,
        icon=data.get('icon', '').strip() or None,
    )

    db.session.add(category)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Ya existe una categoría con ese nombre'}), 409

    return jsonify(category.to_dict()), 201


@bp.route('/<int:category_id>', methods=['GET'])
@token_required
def get_category(current_user, category_id):
    category = ProductCategory.query.get_or_404(category_id)
    return jsonify(category.to_dict()), 200


@bp.route('/<int:category_id>', methods=['PUT'])
@token_required
@admin_required
def update_category(current_user, category_id):
    category = ProductCategory.query.get_or_404(category_id)
    data = request.get_json() or {}

    if 'name' in data:
        if not data['name'].strip():
            return jsonify({'error': 'El nombre no puede estar vacío'}), 400
        category.name = data['name'].strip()

    for field in ('description', 'color', 'icon'):
        if field in data:
            val = data[field]
            setattr(category, field, val.strip() or None)

    if 'is_active' in data:
        category.is_active = bool(data['is_active'])

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Ya existe una categoría con ese nombre'}), 409

    return jsonify(category.to_dict()), 200


@bp.route('/<int:category_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_category(current_user, category_id):
    category = ProductCategory.query.get_or_404(category_id)
    category.is_active = False
    db.session.commit()
    return jsonify({'message': 'Categoría desactivada correctamente'}), 200
