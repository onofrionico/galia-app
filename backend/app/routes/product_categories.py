from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.product_category import ProductCategory
from app.utils.jwt_utils import token_required
from app.utils.decorators import module_required, authenticated_only
from app.utils.validation import clean_str, json_object
from sqlalchemy.exc import IntegrityError

bp = Blueprint('product_categories', __name__, url_prefix='/api/v1/product-categories')


@bp.route('', methods=['GET'])
@token_required
@authenticated_only
def list_categories(current_user):
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'

    query = ProductCategory.query
    if not include_inactive:
        query = query.filter(ProductCategory.is_active == True)

    categories = query.order_by(ProductCategory.name).all()
    return jsonify({'categories': [c.to_dict() for c in categories], 'total': len(categories)}), 200


@bp.route('', methods=['POST'])
@token_required
@module_required('Products')
def create_category(current_user):
    data = json_object()
    if data is None:
        return jsonify({'error': 'El cuerpo de la petición debe ser un objeto JSON'}), 400

    try:
        name = clean_str(data.get('name'), 100)
        description = clean_str(data.get('description'))
        color = clean_str(data.get('color'), 20)
        icon = clean_str(data.get('icon'), 10)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    if not name:
        return jsonify({'error': 'El nombre de la categoría es requerido'}), 400

    category = ProductCategory(name=name, description=description, color=color, icon=icon)

    db.session.add(category)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Ya existe una categoría con ese nombre'}), 409

    return jsonify(category.to_dict()), 201


@bp.route('/<int:category_id>', methods=['GET'])
@token_required
@authenticated_only
def get_category(current_user, category_id):
    category = ProductCategory.query.get_or_404(category_id)
    return jsonify(category.to_dict()), 200


@bp.route('/<int:category_id>', methods=['PUT'])
@token_required
@module_required('Products')
def update_category(current_user, category_id):
    category = ProductCategory.query.get_or_404(category_id)
    data = json_object()
    if data is None:
        return jsonify({'error': 'El cuerpo de la petición debe ser un objeto JSON'}), 400

    limits = {'description': None, 'color': 20, 'icon': 10}
    try:
        updates = {}
        if 'name' in data:
            name = clean_str(data['name'], 100)
            if not name:
                return jsonify({'error': 'El nombre no puede estar vacío'}), 400
            updates['name'] = name
        for field, max_len in limits.items():
            if field in data:
                updates[field] = clean_str(data[field], max_len)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    for field, value in updates.items():
        setattr(category, field, value)

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
@module_required('Products')
def delete_category(current_user, category_id):
    category = ProductCategory.query.get_or_404(category_id)
    category.is_active = False
    db.session.commit()
    return jsonify({'message': 'Categoría desactivada correctamente'}), 200
