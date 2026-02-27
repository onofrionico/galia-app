from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.store_hours import StoreHours
from app.utils.decorators import admin_required
from app.utils.jwt_utils import token_required
from datetime import datetime, time

bp = Blueprint('store_hours', __name__, url_prefix='/api/v1/store-hours')

@bp.route('', methods=['GET'])
@token_required
def get_store_hours(current_user):
    """Obtener horarios del local"""
    location_name = request.args.get('location_name')
    is_active = request.args.get('is_active', 'true').lower() == 'true'
    
    query = StoreHours.query
    
    if location_name:
        query = query.filter(StoreHours.location_name == location_name)
    
    if is_active:
        query = query.filter(StoreHours.is_active == True)
    
    hours = query.order_by(StoreHours.location_name, StoreHours.day_of_week).all()
    
    return jsonify([hour.to_dict() for hour in hours]), 200

@bp.route('', methods=['POST'])
@token_required
@admin_required
def create_store_hours(current_user):
    """Crear horario del local"""
    data = request.get_json()
    
    required_fields = ['location_name', 'day_of_week', 'opening_time', 'closing_time']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo requerido: {field}'}), 400
    
    try:
        opening_time = datetime.strptime(data['opening_time'], '%H:%M').time()
        closing_time = datetime.strptime(data['closing_time'], '%H:%M').time()
    except ValueError:
        return jsonify({'error': 'Formato de hora inválido. Use HH:MM'}), 400
    
    if not 0 <= data['day_of_week'] <= 6:
        return jsonify({'error': 'day_of_week debe estar entre 0 (Lunes) y 6 (Domingo)'}), 400
    
    store_hours = StoreHours(
        location_name=data['location_name'],
        day_of_week=data['day_of_week'],
        opening_time=opening_time,
        closing_time=closing_time,
        is_active=data.get('is_active', True),
        created_by_id=current_user.id
    )
    
    db.session.add(store_hours)
    db.session.commit()
    
    return jsonify(store_hours.to_dict()), 201

@bp.route('/<int:hours_id>', methods=['PUT'])
@token_required
@admin_required
def update_store_hours(current_user, hours_id):
    """Actualizar horario del local"""
    store_hours = StoreHours.query.get_or_404(hours_id)
    data = request.get_json()
    
    if 'location_name' in data:
        store_hours.location_name = data['location_name']
    
    if 'day_of_week' in data:
        if not 0 <= data['day_of_week'] <= 6:
            return jsonify({'error': 'day_of_week debe estar entre 0 y 6'}), 400
        store_hours.day_of_week = data['day_of_week']
    
    if 'opening_time' in data:
        try:
            store_hours.opening_time = datetime.strptime(data['opening_time'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Formato de hora inválido'}), 400
    
    if 'closing_time' in data:
        try:
            store_hours.closing_time = datetime.strptime(data['closing_time'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Formato de hora inválido'}), 400
    
    if 'is_active' in data:
        store_hours.is_active = data['is_active']
    
    store_hours.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(store_hours.to_dict()), 200

@bp.route('/<int:hours_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_store_hours(current_user, hours_id):
    """Eliminar horario del local"""
    store_hours = StoreHours.query.get_or_404(hours_id)
    
    db.session.delete(store_hours)
    db.session.commit()
    
    return jsonify({'message': 'Horario eliminado exitosamente'}), 200

@bp.route('/locations', methods=['GET'])
@token_required
def get_locations(current_user):
    """Obtener lista de locales únicos"""
    locations = db.session.query(StoreHours.location_name).distinct().all()
    return jsonify([loc[0] for loc in locations]), 200
