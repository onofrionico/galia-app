from flask import Blueprint, request, jsonify
from app.services.employee_schedule_service import EmployeeScheduleService
from app.models.employee import Employee
from datetime import datetime
from app.utils.jwt_utils import token_required

bp = Blueprint('employee_schedule', __name__, url_prefix='/api/v1/employee/schedule')

@bp.route('/my-schedule/weekly', methods=['GET'])
@token_required
def get_my_weekly_schedule(current_user):
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    
    if not employee:
        return jsonify({'error': 'No se encontró el perfil de empleado'}), 404
    
    start_date = request.args.get('start_date')
    
    if start_date:
        try:
            start_date = datetime.fromisoformat(start_date).date()
        except (ValueError, AttributeError):
            return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    schedule = EmployeeScheduleService.get_employee_weekly_schedule(employee.id, start_date)
    
    return jsonify(schedule), 200

@bp.route('/my-schedule/monthly', methods=['GET'])
@token_required
def get_my_monthly_schedule(current_user):
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    
    if not employee:
        return jsonify({'error': 'No se encontró el perfil de empleado'}), 404
    
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    if month and (month < 1 or month > 12):
        return jsonify({'error': 'Mes inválido. Debe estar entre 1 y 12'}), 400
    
    schedule = EmployeeScheduleService.get_employee_monthly_schedule(employee.id, year, month)
    
    return jsonify(schedule), 200

@bp.route('/my-schedule/upcoming', methods=['GET'])
@token_required
def get_my_upcoming_shifts(current_user):
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    
    if not employee:
        return jsonify({'error': 'No se encontró el perfil de empleado'}), 404
    
    days_ahead = request.args.get('days', type=int, default=30)
    
    if days_ahead < 1 or days_ahead > 90:
        return jsonify({'error': 'Los días deben estar entre 1 y 90'}), 400
    
    schedule = EmployeeScheduleService.get_employee_upcoming_shifts(employee.id, days_ahead)
    
    return jsonify(schedule), 200

@bp.route('/my-schedule/current-week', methods=['GET'])
@token_required
def get_my_current_week(current_user):
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    
    if not employee:
        return jsonify({'error': 'No se encontró el perfil de empleado'}), 404
    
    schedule = EmployeeScheduleService.get_current_week_schedule(employee.id)
    
    return jsonify(schedule), 200

@bp.route('/my-schedule/next-week', methods=['GET'])
@token_required
def get_my_next_week(current_user):
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    
    if not employee:
        return jsonify({'error': 'No se encontró el perfil de empleado'}), 404
    
    schedule = EmployeeScheduleService.get_next_week_schedule(employee.id)
    
    return jsonify(schedule), 200

@bp.route('/my-schedule/summary', methods=['GET'])
@token_required
def get_my_schedule_summary(current_user):
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    
    if not employee:
        return jsonify({'error': 'No se encontró el perfil de empleado'}), 404
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date:
        try:
            start_date = datetime.fromisoformat(start_date).date()
        except (ValueError, AttributeError):
            return jsonify({'error': 'Formato de start_date inválido'}), 400
    
    if end_date:
        try:
            end_date = datetime.fromisoformat(end_date).date()
        except (ValueError, AttributeError):
            return jsonify({'error': 'Formato de end_date inválido'}), 400
    
    summary = EmployeeScheduleService.get_employee_schedule_summary(employee.id, start_date, end_date)
    
    return jsonify(summary), 200
