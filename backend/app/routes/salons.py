from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.salon import Salon
from app.models.mesa import Mesa
from app.utils.jwt_utils import token_required
from app.utils.decorators import admin_required

bp = Blueprint('salons', __name__, url_prefix='/api/v1/salons')


@bp.route('', methods=['GET'])
@token_required
def list_salons(current_user):
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'

    query = Salon.query
    if not include_inactive:
        query = query.filter(Salon.is_active == True)

    salons = query.order_by(Salon.name).all()
    result = []
    for salon in salons:
        data = salon.to_dict()
        mesas = Mesa.query.filter_by(salon_id=salon.id, is_active=True).count()
        data['mesa_count'] = mesas
        result.append(data)

    return jsonify({'salons': result, 'total': len(result)}), 200


@bp.route('', methods=['POST'])
@token_required
@admin_required
def create_salon(current_user):
    data = request.get_json() or {}

    if not data.get('name', '').strip():
        return jsonify({'error': 'El nombre del salón es requerido'}), 400

    salon = Salon(
        name=data['name'].strip(),
        description=data.get('description', '').strip() or None,
    )

    db.session.add(salon)
    db.session.commit()

    result = salon.to_dict()
    result['mesa_count'] = 0
    return jsonify(result), 201


@bp.route('/<int:salon_id>', methods=['GET'])
@token_required
def get_salon(current_user, salon_id):
    salon = Salon.query.get_or_404(salon_id)
    data = salon.to_dict()
    mesas = Mesa.query.filter_by(salon_id=salon_id).all()
    data['mesas'] = [m.to_dict() for m in mesas]
    data['mesa_count'] = len(mesas)
    return jsonify(data), 200


@bp.route('/<int:salon_id>', methods=['PUT'])
@token_required
@admin_required
def update_salon(current_user, salon_id):
    salon = Salon.query.get_or_404(salon_id)
    data = request.get_json() or {}

    if 'name' in data:
        if not data['name'].strip():
            return jsonify({'error': 'El nombre no puede estar vacío'}), 400
        salon.name = data['name'].strip()

    if 'description' in data:
        val = data['description']
        salon.description = val.strip() if val else None

    if 'is_active' in data:
        salon.is_active = bool(data['is_active'])

    db.session.commit()

    result = salon.to_dict()
    mesas = Mesa.query.filter_by(salon_id=salon_id, is_active=True).count()
    result['mesa_count'] = mesas
    return jsonify(result), 200


@bp.route('/<int:salon_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_salon(current_user, salon_id):
    salon = Salon.query.get_or_404(salon_id)
    salon.is_active = False
    db.session.commit()
    return jsonify({'message': 'Salón desactivado correctamente'}), 200


@bp.route('/<int:salon_id>/mesas', methods=['GET'])
@token_required
def list_mesas(current_user, salon_id):
    Salon.query.get_or_404(salon_id)
    mesas = Mesa.query.filter_by(salon_id=salon_id).order_by(Mesa.number).all()
    return jsonify({'mesas': [m.to_dict() for m in mesas], 'total': len(mesas)}), 200


@bp.route('/<int:salon_id>/mesas', methods=['POST'])
@token_required
@admin_required
def create_mesa(current_user, salon_id):
    Salon.query.get_or_404(salon_id)
    data = request.get_json() or {}

    if not data.get('number'):
        return jsonify({'error': 'El número de mesa es requerido'}), 400

    mesa = Mesa(
        salon_id=salon_id,
        number=int(data['number']),
        name=data.get('name', '').strip() or None,
        capacity=int(data['capacity']) if data.get('capacity') else None,
        pos_x=float(data.get('pos_x', 10.0)),
        pos_y=float(data.get('pos_y', 10.0)),
        width=float(data.get('width', 10.0)),
        height=float(data.get('height', 10.0)),
        status=data.get('status', 'libre'),
    )

    db.session.add(mesa)
    db.session.commit()
    return jsonify(mesa.to_dict()), 201


@bp.route('/<int:salon_id>/mesas/<int:mesa_id>', methods=['GET'])
@token_required
def get_mesa(current_user, salon_id, mesa_id):
    mesa = Mesa.query.filter_by(id=mesa_id, salon_id=salon_id).first_or_404()
    return jsonify(mesa.to_dict()), 200


@bp.route('/<int:salon_id>/mesas/<int:mesa_id>', methods=['PUT'])
@token_required
@admin_required
def update_mesa(current_user, salon_id, mesa_id):
    mesa = Mesa.query.filter_by(id=mesa_id, salon_id=salon_id).first_or_404()
    data = request.get_json() or {}

    if 'number' in data:
        mesa.number = int(data['number'])

    for field in ('name', 'status'):
        if field in data:
            val = data[field]
            setattr(mesa, field, val.strip() if val else None)

    if 'capacity' in data:
        mesa.capacity = int(data['capacity']) if data['capacity'] else None

    for field in ('pos_x', 'pos_y', 'width', 'height'):
        if field in data:
            setattr(mesa, field, float(data[field]))

    if 'is_active' in data:
        mesa.is_active = bool(data['is_active'])

    db.session.commit()
    return jsonify(mesa.to_dict()), 200


@bp.route('/<int:salon_id>/mesas/<int:mesa_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_mesa(current_user, salon_id, mesa_id):
    mesa = Mesa.query.filter_by(id=mesa_id, salon_id=salon_id).first_or_404()
    mesa.is_active = False
    db.session.commit()
    return jsonify({'message': 'Mesa desactivada correctamente'}), 200
