from flask import Blueprint, request, jsonify
from functools import wraps
from app.extensions import db
from app.models.ml_tracking import Holiday
from app.utils.jwt_utils import token_required
from datetime import datetime

holidays_bp = Blueprint('holidays', __name__, url_prefix='/api/v1/holidays')

def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if not current_user.is_admin:
            return jsonify({'error': 'Se requieren permisos de administrador'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

@holidays_bp.route('/', methods=['GET'])
@token_required
def get_holidays(current_user):
    """
    Obtiene la lista de feriados.
    Parámetros opcionales:
    - year: filtrar por año
    """
    year = request.args.get('year', type=int)
    
    query = Holiday.query
    
    if year:
        start_date = datetime(year, 1, 1).date()
        end_date = datetime(year, 12, 31).date()
        query = query.filter(Holiday.date >= start_date, Holiday.date <= end_date)
    
    holidays = query.order_by(Holiday.date).all()
    
    return jsonify([h.to_dict() for h in holidays]), 200

@holidays_bp.route('/', methods=['POST'])
@token_required
@admin_required
def create_holiday(current_user):
    """
    Crea un nuevo feriado.
    Body:
    - date: fecha del feriado (YYYY-MM-DD)
    - name: nombre del feriado
    - type: tipo (national, local, special_event)
    - impact_multiplier: multiplicador de impacto (opcional, default 1.0)
    - notes: notas adicionales (opcional)
    """
    data = request.get_json()
    
    if not data.get('date') or not data.get('name'):
        return jsonify({'error': 'Fecha y nombre son requeridos'}), 400
    
    try:
        holiday_date = datetime.fromisoformat(data['date']).date()
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400
    
    existing = Holiday.query.filter_by(date=holiday_date).first()
    if existing:
        return jsonify({'error': 'Ya existe un feriado en esta fecha'}), 400
    
    holiday = Holiday(
        date=holiday_date,
        name=data['name'],
        type=data.get('type', 'national'),
        impact_multiplier=data.get('impact_multiplier', 1.0),
        notes=data.get('notes', '')
    )
    
    db.session.add(holiday)
    db.session.commit()
    
    return jsonify(holiday.to_dict()), 201

@holidays_bp.route('/<int:holiday_id>', methods=['GET'])
@token_required
def get_holiday(current_user, holiday_id):
    """Obtiene un feriado específico por ID"""
    holiday = Holiday.query.get_or_404(holiday_id)
    return jsonify(holiday.to_dict()), 200

@holidays_bp.route('/<int:holiday_id>', methods=['PUT'])
@token_required
@admin_required
def update_holiday(current_user, holiday_id):
    """
    Actualiza un feriado existente.
    Body: campos a actualizar (date, name, type, impact_multiplier, notes)
    """
    holiday = Holiday.query.get_or_404(holiday_id)
    data = request.get_json()
    
    if 'date' in data:
        try:
            new_date = datetime.fromisoformat(data['date']).date()
            if new_date != holiday.date:
                existing = Holiday.query.filter_by(date=new_date).first()
                if existing:
                    return jsonify({'error': 'Ya existe un feriado en esta fecha'}), 400
                holiday.date = new_date
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400
    
    if 'name' in data:
        holiday.name = data['name']
    if 'type' in data:
        holiday.type = data['type']
    if 'impact_multiplier' in data:
        holiday.impact_multiplier = data['impact_multiplier']
    if 'notes' in data:
        holiday.notes = data['notes']
    
    db.session.commit()
    
    return jsonify(holiday.to_dict()), 200

@holidays_bp.route('/<int:holiday_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_holiday(current_user, holiday_id):
    """Elimina un feriado"""
    holiday = Holiday.query.get_or_404(holiday_id)
    
    db.session.delete(holiday)
    db.session.commit()
    
    return jsonify({'message': 'Feriado eliminado exitosamente'}), 200

@holidays_bp.route('/check/<date_str>', methods=['GET'])
@token_required
def check_holiday(current_user, date_str):
    """
    Verifica si una fecha específica es feriado.
    Parámetro: date_str en formato YYYY-MM-DD
    """
    try:
        check_date = datetime.fromisoformat(date_str).date()
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400
    
    holiday = Holiday.query.filter_by(date=check_date).first()
    
    if holiday:
        return jsonify({
            'is_holiday': True,
            'holiday': holiday.to_dict()
        }), 200
    else:
        return jsonify({
            'is_holiday': False,
            'holiday': None
        }), 200
