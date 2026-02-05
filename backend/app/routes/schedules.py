from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.schedule import Schedule
from app.models.shift import Shift
from app.utils.decorators import admin_required

bp = Blueprint('schedules', __name__, url_prefix='/api/v1/schedules')

@bp.route('', methods=['GET'])
@login_required
def get_schedules():
    schedules = Schedule.query.order_by(Schedule.start_date.desc()).all()
    return jsonify([schedule.to_dict() for schedule in schedules]), 200

@bp.route('', methods=['POST'])
@login_required
@admin_required
def create_schedule():
    from app.services.schedule_service import ScheduleService
    from app.utils.validators import validate_date_range
    from datetime import datetime
    
    data = request.get_json()
    
    if not data or not data.get('start_date') or not data.get('end_date'):
        return jsonify({'error': 'start_date y end_date son requeridos'}), 400
    
    try:
        start_date = datetime.fromisoformat(data['start_date']).date()
        end_date = datetime.fromisoformat(data['end_date']).date()
    except (ValueError, AttributeError):
        return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    if not validate_date_range(start_date, end_date):
        return jsonify({'error': 'La fecha de fin debe ser posterior a la fecha de inicio'}), 400
    
    schedule = ScheduleService.create_schedule(start_date, end_date, current_user.id)
    
    return jsonify({
        'message': 'Grilla creada exitosamente',
        'schedule': schedule.to_dict(include_shifts=True)
    }), 201

@bp.route('/<int:schedule_id>', methods=['GET'])
@login_required
def get_schedule(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    return jsonify(schedule.to_dict(include_shifts=True)), 200

@bp.route('/<int:schedule_id>', methods=['PUT'])
@login_required
@admin_required
def update_schedule(schedule_id):
    from app.services.schedule_service import ScheduleService
    from datetime import datetime
    
    data = request.get_json()
    
    update_data = {}
    if 'start_date' in data:
        try:
            update_data['start_date'] = datetime.fromisoformat(data['start_date']).date()
        except (ValueError, AttributeError):
            return jsonify({'error': 'Formato de start_date inválido'}), 400
    
    if 'end_date' in data:
        try:
            update_data['end_date'] = datetime.fromisoformat(data['end_date']).date()
        except (ValueError, AttributeError):
            return jsonify({'error': 'Formato de end_date inválido'}), 400
    
    if 'status' in data:
        if data['status'] not in ['draft', 'published']:
            return jsonify({'error': 'Status inválido'}), 400
        update_data['status'] = data['status']
    
    schedule = ScheduleService.update_schedule(schedule_id, **update_data)
    
    if not schedule:
        return jsonify({'error': 'Grilla no encontrada'}), 404
    
    return jsonify({
        'message': 'Grilla actualizada exitosamente',
        'schedule': schedule.to_dict(include_shifts=True)
    }), 200

@bp.route('/<int:schedule_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_schedule(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    db.session.delete(schedule)
    db.session.commit()
    
    return jsonify({'message': 'Grilla eliminada exitosamente'}), 200
