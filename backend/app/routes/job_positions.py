from flask import Blueprint, request, jsonify
from datetime import datetime
from app.extensions import db
from app.models.job_position import JobPosition
from app.models.employee import Employee
from app.utils.decorators import admin_required
from app.utils.jwt_utils import token_required

bp = Blueprint('job_positions', __name__, url_prefix='/api/v1/job-positions')

@bp.route('', methods=['GET'])
@token_required
def get_job_positions(current_user):
    is_active = request.args.get('is_active', '')
    contract_type = request.args.get('contract_type', '')
    
    query = JobPosition.query
    
    if is_active:
        query = query.filter(JobPosition.is_active == (is_active.lower() == 'true'))
    
    if contract_type:
        query = query.filter(JobPosition.contract_type == contract_type)
    
    positions = query.order_by(JobPosition.name).all()
    
    return jsonify([pos.to_dict(include_employees=False) for pos in positions]), 200

@bp.route('/<int:position_id>', methods=['GET'])
@token_required
def get_job_position(current_user, position_id):
    position = JobPosition.query.get_or_404(position_id)
    return jsonify(position.to_dict(include_employees=False)), 200

@bp.route('', methods=['POST'])
@token_required
@admin_required
def create_job_position(current_user):
    data = request.get_json()
    
    required_fields = ['name', 'contract_type']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo requerido: {field}'}), 400
    
    if JobPosition.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Ya existe un puesto con ese nombre'}), 400
    
    position = JobPosition(
        name=data['name'],
        description=data.get('description'),
        contract_type=data['contract_type'],
        base_salary=data.get('base_salary'),
        hourly_rate=data.get('hourly_rate'),
        standard_hours_per_week=data.get('standard_hours_per_week'),
        standard_hours_per_month=data.get('standard_hours_per_month'),
        overtime_rate_multiplier=data.get('overtime_rate_multiplier', 1.5),
        weekend_rate_multiplier=data.get('weekend_rate_multiplier', 1.0),
        sunday_rate_multiplier=data.get('sunday_rate_multiplier', 1.0),
        holiday_rate_multiplier=data.get('holiday_rate_multiplier', 1.0),
        is_active=True,
        created_by_id=current_user.id
    )
    
    validation_errors = position.validate()
    if validation_errors:
        return jsonify({'error': ', '.join(validation_errors)}), 400
    
    db.session.add(position)
    db.session.commit()
    
    return jsonify(position.to_dict()), 201

@bp.route('/<int:position_id>', methods=['PUT'])
@token_required
@admin_required
def update_job_position(current_user, position_id):
    position = JobPosition.query.get_or_404(position_id)
    data = request.get_json()
    
    if 'name' in data and data['name'] != position.name:
        if JobPosition.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Ya existe un puesto con ese nombre'}), 400
        position.name = data['name']
    
    if 'description' in data:
        position.description = data['description']
    if 'contract_type' in data:
        position.contract_type = data['contract_type']
    if 'base_salary' in data:
        position.base_salary = data['base_salary']
    if 'hourly_rate' in data:
        position.hourly_rate = data['hourly_rate']
    if 'standard_hours_per_week' in data:
        position.standard_hours_per_week = data['standard_hours_per_week']
    if 'standard_hours_per_month' in data:
        position.standard_hours_per_month = data['standard_hours_per_month']
    if 'overtime_rate_multiplier' in data:
        position.overtime_rate_multiplier = data['overtime_rate_multiplier']
    if 'weekend_rate_multiplier' in data:
        position.weekend_rate_multiplier = data['weekend_rate_multiplier']
    if 'sunday_rate_multiplier' in data:
        position.sunday_rate_multiplier = data['sunday_rate_multiplier']
    if 'holiday_rate_multiplier' in data:
        position.holiday_rate_multiplier = data['holiday_rate_multiplier']
    
    position.updated_at = datetime.utcnow()
    
    validation_errors = position.validate()
    if validation_errors:
        db.session.rollback()
        return jsonify({'error': ', '.join(validation_errors)}), 400
    
    db.session.commit()
    
    return jsonify(position.to_dict()), 200

@bp.route('/<int:position_id>/deactivate', methods=['PATCH'])
@token_required
@admin_required
def deactivate_job_position(current_user, position_id):
    position = JobPosition.query.get_or_404(position_id)
    
    if not position.is_active:
        return jsonify({'error': 'El puesto ya está inactivo'}), 400
    
    active_employees = Employee.query.filter_by(
        current_job_position_id=position_id,
        status='activo'
    ).count()
    
    if active_employees > 0:
        return jsonify({
            'error': f'No se puede desactivar el puesto. Tiene {active_employees} empleado(s) activo(s) asignado(s)'
        }), 400
    
    position.is_active = False
    position.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'message': 'Puesto desactivado exitosamente',
        'position': position.to_dict()
    }), 200

@bp.route('/<int:position_id>/activate', methods=['PATCH'])
@token_required
@admin_required
def activate_job_position(current_user, position_id):
    position = JobPosition.query.get_or_404(position_id)
    
    if position.is_active:
        return jsonify({'error': 'El puesto ya está activo'}), 400
    
    position.is_active = True
    position.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'message': 'Puesto activado exitosamente',
        'position': position.to_dict()
    }), 200
