from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.vacation_period import VacationPeriod
from app.models.employee import Employee
from app.utils.decorators import admin_required
from app.utils.jwt_utils import token_required
from datetime import datetime

bp = Blueprint('vacation_periods', __name__, url_prefix='/api/v1/vacation-periods')

@bp.route('', methods=['GET'])
@token_required
def get_vacation_periods(current_user):
    """Obtener períodos de vacaciones"""
    employee_id = request.args.get('employee_id', type=int)
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = VacationPeriod.query
    
    # Empleados solo pueden ver sus propias vacaciones
    if current_user.role != 'admin':
        if not current_user.employee:
            return jsonify({'error': 'No se encontró empleado asociado'}), 404
        query = query.filter(VacationPeriod.employee_id == current_user.employee.id)
    elif employee_id:
        query = query.filter(VacationPeriod.employee_id == employee_id)
    
    if status:
        query = query.filter(VacationPeriod.status == status)
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(VacationPeriod.end_date >= start_dt)
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(VacationPeriod.start_date <= end_dt)
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    periods = query.order_by(VacationPeriod.start_date.desc()).all()
    
    return jsonify([period.to_dict() for period in periods]), 200

@bp.route('', methods=['POST'])
@token_required
@admin_required
def create_vacation_period(current_user):
    """Crear período de vacaciones"""
    data = request.get_json()
    
    required_fields = ['employee_id', 'start_date', 'end_date']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo requerido: {field}'}), 400
    
    employee = Employee.query.get(data['employee_id'])
    if not employee:
        return jsonify({'error': 'Empleado no encontrado'}), 404
    
    try:
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400
    
    if start_date > end_date:
        return jsonify({'error': 'La fecha de inicio debe ser anterior a la fecha de fin'}), 400
    
    vacation_period = VacationPeriod(
        employee_id=data['employee_id'],
        start_date=start_date,
        end_date=end_date,
        status=data.get('status', 'aprobado'),
        notes=data.get('notes'),
        created_by_id=current_user.id,
        approved_by_id=current_user.id if data.get('status') == 'aprobado' else None
    )
    
    db.session.add(vacation_period)
    db.session.commit()
    
    return jsonify(vacation_period.to_dict()), 201

@bp.route('/<int:period_id>', methods=['PUT'])
@token_required
@admin_required
def update_vacation_period(current_user, period_id):
    """Actualizar período de vacaciones"""
    period = VacationPeriod.query.get_or_404(period_id)
    data = request.get_json()
    
    if 'start_date' in data:
        try:
            period.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    if 'end_date' in data:
        try:
            period.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    if period.start_date > period.end_date:
        return jsonify({'error': 'La fecha de inicio debe ser anterior a la fecha de fin'}), 400
    
    if 'status' in data:
        period.status = data['status']
        if data['status'] == 'aprobado':
            period.approved_by_id = current_user.id
    
    if 'notes' in data:
        period.notes = data['notes']
    
    period.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(period.to_dict()), 200

@bp.route('/<int:period_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_vacation_period(current_user, period_id):
    """Eliminar período de vacaciones"""
    period = VacationPeriod.query.get_or_404(period_id)
    
    db.session.delete(period)
    db.session.commit()
    
    return jsonify({'message': 'Período de vacaciones eliminado exitosamente'}), 200

@bp.route('/check-availability/<int:employee_id>', methods=['GET'])
@token_required
def check_employee_availability(current_user, employee_id):
    """Verificar si un empleado está disponible en un rango de fechas"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'error': 'Se requieren start_date y end_date'}), 400
    
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    # Buscar vacaciones que se solapen con el rango
    overlapping_vacations = VacationPeriod.query.filter(
        VacationPeriod.employee_id == employee_id,
        VacationPeriod.status == 'aprobado',
        VacationPeriod.start_date <= end_dt,
        VacationPeriod.end_date >= start_dt
    ).all()
    
    is_available = len(overlapping_vacations) == 0
    
    return jsonify({
        'employee_id': employee_id,
        'is_available': is_available,
        'vacation_periods': [v.to_dict() for v in overlapping_vacations]
    }), 200
