from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Salon, Mesa
from app.utils.jwt_utils import token_required

bp = Blueprint('salons', __name__, url_prefix='/api/v1/salons')

@bp.route('/', methods=['GET'])
def get_salons():
    """Lista de salones activos"""
    salons = Salon.query.filter_by(is_active=True).all()
    return jsonify([s.to_dict() for s in salons]), 200

@bp.route('/', methods=['POST'])
@token_required
def create_salon(current_user):
    """Crear salón"""
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({'error': 'Nombre es requerido'}), 400

    # Verificar que no exista
    existing = Salon.query.filter_by(name=data['name']).first()
    if existing:
        return jsonify({'error': 'Salón ya existe'}), 400

    salon = Salon(
        name=data['name'],
        description=data.get('description'),
        is_active=True
    )

    db.session.add(salon)
    db.session.commit()

    return jsonify(salon.to_dict()), 201

@bp.route('/<int:salon_id>', methods=['PUT'])
@token_required
def update_salon(current_user, salon_id):
    """Editar salón"""
    salon = Salon.query.get(salon_id)
    if not salon:
        return jsonify({'error': 'Salón no encontrado'}), 404

    data = request.get_json()

    if 'name' in data:
        # Verificar que no exista otro con ese nombre
        existing = Salon.query.filter(
            Salon.name == data['name'],
            Salon.id != salon_id
        ).first()
        if existing:
            return jsonify({'error': 'Nombre ya existe'}), 400
        salon.name = data['name']

    if 'description' in data:
        salon.description = data['description']

    db.session.commit()
    return jsonify(salon.to_dict()), 200

@bp.route('/<int:salon_id>', methods=['DELETE'])
@token_required
def delete_salon(current_user, salon_id):
    """Desactivar salón"""
    salon = Salon.query.get(salon_id)
    if not salon:
        return jsonify({'error': 'Salón no encontrado'}), 404

    salon.is_active = False
    db.session.commit()

    return jsonify({'message': 'Salón desactivado'}), 200

# MESAS

@bp.route('/<int:salon_id>/mesas', methods=['GET'])
def get_salon_mesas(salon_id):
    """Mesas del salón"""
    salon = Salon.query.get(salon_id)
    if not salon:
        return jsonify({'error': 'Salón no encontrado'}), 404

    return jsonify([m.to_dict() for m in salon.mesas]), 200

@bp.route('/<int:salon_id>/mesas', methods=['POST'])
@token_required
def create_mesa(current_user, salon_id):
    """Crear mesa en salón"""
    salon = Salon.query.get(salon_id)
    if not salon:
        return jsonify({'error': 'Salón no encontrado'}), 404

    data = request.get_json()

    if not data or not data.get('number'):
        return jsonify({'error': 'Número de mesa es requerido'}), 400

    # Verificar que no exista mesa con ese número en el salón
    existing = Mesa.query.filter_by(salon_id=salon_id, number=data['number']).first()
    if existing:
        return jsonify({'error': 'Mesa con ese número ya existe en el salón'}), 400

    mesa = Mesa(
        salon_id=salon_id,
        number=data['number'],
        name=data.get('name'),
        capacity=data.get('capacity', 4),
        pos_x=data.get('pos_x', 0),
        pos_y=data.get('pos_y', 0),
        width=data.get('width', 10),
        height=data.get('height', 10),
        status='libre',
        is_active=True
    )

    db.session.add(mesa)
    db.session.commit()

    return jsonify(mesa.to_dict()), 201

@bp.route('/<int:salon_id>/mesas/<int:mesa_id>', methods=['PUT'])
@token_required
def update_mesa(current_user, salon_id, mesa_id):
    """Editar mesa (incluye posición en plano)"""
    salon = Salon.query.get(salon_id)
    if not salon:
        return jsonify({'error': 'Salón no encontrado'}), 404

    mesa = Mesa.query.filter_by(id=mesa_id, salon_id=salon_id).first()
    if not mesa:
        return jsonify({'error': 'Mesa no encontrada'}), 404

    data = request.get_json()

    if 'name' in data:
        mesa.name = data['name']
    if 'capacity' in data:
        mesa.capacity = data['capacity']
    if 'pos_x' in data:
        mesa.pos_x = data['pos_x']
    if 'pos_y' in data:
        mesa.pos_y = data['pos_y']
    if 'width' in data:
        mesa.width = data['width']
    if 'height' in data:
        mesa.height = data['height']
    if 'status' in data:
        if data['status'] not in ['libre', 'ocupada', 'reservada']:
            return jsonify({'error': 'Status inválido'}), 400
        mesa.status = data['status']

    db.session.commit()
    return jsonify(mesa.to_dict()), 200

@bp.route('/<int:salon_id>/mesas/<int:mesa_id>', methods=['DELETE'])
@token_required
def delete_mesa(current_user, salon_id, mesa_id):
    """Desactivar mesa"""
    mesa = Mesa.query.filter_by(id=mesa_id, salon_id=salon_id).first()
    if not mesa:
        return jsonify({'error': 'Mesa no encontrada'}), 404

    mesa.is_active = False
    db.session.commit()

    return jsonify({'message': 'Mesa desactivada'}), 200
