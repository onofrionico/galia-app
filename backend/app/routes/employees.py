from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.employee import Employee
from app.utils.decorators import admin_required

bp = Blueprint('employees', __name__, url_prefix='/api/v1/employees')

@bp.route('', methods=['GET'])
@login_required
@admin_required
def get_employees():
    employees = Employee.query.all()
    return jsonify([employee.to_dict() for employee in employees]), 200

@bp.route('/<int:employee_id>', methods=['GET'])
@login_required
def get_employee(employee_id):
    if not current_user.is_admin() and current_user.employee.id != employee_id:
        return jsonify({'error': 'No autorizado'}), 403
    
    employee = Employee.query.get_or_404(employee_id)
    return jsonify(employee.to_dict()), 200

@bp.route('/<int:employee_id>/schedule', methods=['GET'])
@login_required
def get_employee_schedule(employee_id):
    if not current_user.is_admin() and current_user.employee.id != employee_id:
        return jsonify({'error': 'No autorizado'}), 403
    
    return jsonify({'message': 'Endpoint en desarrollo'}), 501
