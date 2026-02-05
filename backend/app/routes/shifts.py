from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.shift import Shift
from app.utils.decorators import admin_required
from app.services.schedule_service import ScheduleService
from datetime import datetime, time

bp = Blueprint('shifts', __name__, url_prefix='/api/v1/shifts')

@bp.route('', methods=['POST'])
@login_required
@admin_required
def create_shift():
    data = request.get_json()
    
    required_fields = ['schedule_id', 'employee_id', 'shift_date', 'start_time', 'end_time']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Todos los campos son requeridos'}), 400
    
    try:
        shift_date = datetime.fromisoformat(data['shift_date']).date()
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
    except (ValueError, AttributeError):
        return jsonify({'error': 'Formato de fecha u hora inválido'}), 400
    
    has_conflict, conflicting_shift = ScheduleService.check_shift_conflicts(
        data['employee_id'],
        shift_date,
        start_time,
        end_time
    )
    
    if has_conflict:
        return jsonify({
            'error': 'El turno se superpone con otro turno existente',
            'conflicting_shift': conflicting_shift.to_dict()
        }), 409
    
    shift = ScheduleService.add_shift(
        data['schedule_id'],
        data['employee_id'],
        shift_date,
        start_time,
        end_time
    )
    
    return jsonify({
        'message': 'Turno creado exitosamente',
        'shift': shift.to_dict()
    }), 201

@bp.route('/<int:shift_id>', methods=['PUT'])
@login_required
@admin_required
def update_shift(shift_id):
    data = request.get_json()
    
    update_data = {}
    
    if 'shift_date' in data:
        try:
            update_data['shift_date'] = datetime.fromisoformat(data['shift_date']).date()
        except (ValueError, AttributeError):
            return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    if 'start_time' in data:
        try:
            update_data['start_time'] = datetime.strptime(data['start_time'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Formato de start_time inválido'}), 400
    
    if 'end_time' in data:
        try:
            update_data['end_time'] = datetime.strptime(data['end_time'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Formato de end_time inválido'}), 400
    
    if 'employee_id' in data:
        update_data['employee_id'] = data['employee_id']
    
    shift = Shift.query.get(shift_id)
    if not shift:
        return jsonify({'error': 'Turno no encontrado'}), 404
    
    check_date = update_data.get('shift_date', shift.shift_date)
    check_start = update_data.get('start_time', shift.start_time)
    check_end = update_data.get('end_time', shift.end_time)
    check_employee = update_data.get('employee_id', shift.employee_id)
    
    has_conflict, conflicting_shift = ScheduleService.check_shift_conflicts(
        check_employee,
        check_date,
        check_start,
        check_end,
        exclude_shift_id=shift_id
    )
    
    if has_conflict:
        return jsonify({
            'error': 'El turno se superpone con otro turno existente',
            'conflicting_shift': conflicting_shift.to_dict()
        }), 409
    
    updated_shift = ScheduleService.update_shift(shift_id, **update_data)
    
    return jsonify({
        'message': 'Turno actualizado exitosamente',
        'shift': updated_shift.to_dict()
    }), 200

@bp.route('/<int:shift_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_shift(shift_id):
    success = ScheduleService.delete_shift(shift_id)
    
    if not success:
        return jsonify({'error': 'Turno no encontrado'}), 404
    
    return jsonify({'message': 'Turno eliminado exitosamente'}), 200

@bp.route('/employee/<int:employee_id>', methods=['GET'])
@login_required
def get_employee_shifts(employee_id):
    if not current_user.is_admin() and current_user.employee.id != employee_id:
        return jsonify({'error': 'No autorizado'}), 403
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        start = datetime.fromisoformat(start_date).date() if start_date else None
        end = datetime.fromisoformat(end_date).date() if end_date else None
    except (ValueError, AttributeError):
        return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    shifts = ScheduleService.get_shifts_by_employee(employee_id, start, end)
    
    return jsonify([shift.to_dict() for shift in shifts]), 200
