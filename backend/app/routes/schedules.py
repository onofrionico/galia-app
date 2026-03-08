from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.schedule import Schedule
from app.models.shift import Shift
from app.models.employee import Employee
from app.utils.decorators import admin_required
from app.utils.jwt_utils import token_required
from datetime import datetime, timedelta
from collections import defaultdict

bp = Blueprint('schedules', __name__, url_prefix='/api/v1/schedules')

@bp.route('', methods=['GET'])
@token_required
def get_schedules(current_user):
    schedules = Schedule.query.order_by(Schedule.start_date.desc()).all()
    return jsonify([schedule.to_dict() for schedule in schedules]), 200

@bp.route('', methods=['POST'])
@token_required
@admin_required
def create_schedule(current_user):
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
@token_required
def get_schedule(current_user, schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    return jsonify(schedule.to_dict(include_shifts=True)), 200

@bp.route('/<int:schedule_id>', methods=['PUT'])
@token_required
@admin_required
def update_schedule(current_user, schedule_id):
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
@token_required
@admin_required
def delete_schedule(current_user, schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    
    if not schedule.can_be_deleted():
        return jsonify({
            'error': 'Solo se pueden eliminar grillas en estado borrador',
            'status': schedule.status
        }), 403
    
    db.session.delete(schedule)
    db.session.commit()
    
    return jsonify({'message': 'Grilla eliminada exitosamente'}), 200

@bp.route('/coverage', methods=['GET'])
@token_required
def get_daily_coverage(current_user):
    """Get daily coverage with employee details for a date range"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'error': 'start_date y end_date son requeridos'}), 400
    
    try:
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
    except (ValueError, AttributeError):
        return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    # Get all shifts in the date range with employee and job position data
    shifts = Shift.query.join(Employee).filter(
        Shift.shift_date >= start,
        Shift.shift_date <= end
    ).all()
    
    # Group shifts by date
    coverage_by_date = defaultdict(list)
    
    for shift in shifts:
        date_str = shift.shift_date.isoformat()
        employee = shift.employee
        
        coverage_by_date[date_str].append({
            'employee_id': employee.id,
            'employee_name': employee.full_name,
            'job_position': employee.job_position.name if employee.job_position else 'Sin puesto',
            'start_time': shift.start_time.strftime('%H:%M'),
            'end_time': shift.end_time.strftime('%H:%M'),
            'hours': float(shift.hours),
            'shift_id': shift.id
        })
    
    # Format response with all dates in range
    result = []
    current_date = start
    while current_date <= end:
        date_str = current_date.isoformat()
        employees = coverage_by_date.get(date_str, [])
        
        result.append({
            'date': date_str,
            'employee_count': len(employees),
            'employees': sorted(employees, key=lambda x: x['start_time'])
        })
        
        current_date += timedelta(days=1)
    
    return jsonify(result), 200
