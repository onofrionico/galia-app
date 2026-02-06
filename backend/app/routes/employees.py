from flask import Blueprint, request, jsonify
from datetime import datetime, date
from app.extensions import db
from app.models.employee import Employee
from app.models.user import User
from app.models.job_position import JobPosition
from app.models.employee_job_history import EmployeeJobHistory
from app.models.shift import Shift
from app.utils.decorators import admin_required
from app.utils.jwt_utils import token_required

bp = Blueprint('employees', __name__, url_prefix='/api/v1/employees')

@bp.route('', methods=['GET'])
@token_required
def get_employees(current_user):
    if current_user.role != 'admin':
        employee = Employee.query.filter_by(user_id=current_user.id).first()
        if not employee:
            return jsonify({'error': 'Empleado no encontrado'}), 404
        return jsonify([employee.to_dict(include_sensitive=True)]), 200
    
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    job_position_id = request.args.get('job_position_id', '')
    hire_date_from = request.args.get('hire_date_from', '')
    hire_date_to = request.args.get('hire_date_to', '')
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    query = Employee.query.join(User, Employee.user_id == User.id)
    
    if search:
        search_filter = f'%{search}%'
        query = query.filter(
            db.or_(
                Employee.first_name.ilike(search_filter),
                Employee.last_name.ilike(search_filter),
                Employee.dni.ilike(search_filter),
                User.email.ilike(search_filter)
            )
        )
    
    if status:
        query = query.filter(Employee.status == status)
    
    if job_position_id:
        query = query.filter(Employee.current_job_position_id == int(job_position_id))
    
    if hire_date_from:
        query = query.filter(Employee.hire_date >= datetime.strptime(hire_date_from, '%Y-%m-%d').date())
    
    if hire_date_to:
        query = query.filter(Employee.hire_date <= datetime.strptime(hire_date_to, '%Y-%m-%d').date())
    
    total = query.count()
    employees = query.order_by(Employee.created_at.desc()).paginate(page=page, per_page=limit, error_out=False)
    
    return jsonify({
        'employees': [emp.to_dict() for emp in employees.items],
        'total': total,
        'page': page,
        'limit': limit,
        'pages': employees.pages
    }), 200

@bp.route('/<int:employee_id>', methods=['GET'])
@token_required
def get_employee(current_user, employee_id):
    if current_user.role != 'admin':
        employee = Employee.query.filter_by(user_id=current_user.id).first()
        if not employee or employee.id != employee_id:
            return jsonify({'error': 'No autorizado'}), 403
    
    employee = Employee.query.get_or_404(employee_id)
    is_own_profile = current_user.employee and current_user.employee.id == employee_id
    include_sensitive = current_user.role == 'admin' or is_own_profile
    
    return jsonify(employee.to_dict(include_sensitive=include_sensitive, include_history=True)), 200

@bp.route('', methods=['POST'])
@token_required
@admin_required
def create_employee(current_user):
    data = request.get_json()
    
    required_fields = [
        'first_name', 'last_name', 'dni', 'cuil', 'birth_date', 
        'phone', 'address', 'email', 'employment_relationship',
        'emergency_contact_name', 'emergency_contact_phone', 
        'emergency_contact_relationship', 'hire_date', 'job_position_id', 'password'
    ]
    
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo requerido: {field}'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'El email ya está registrado'}), 400
    
    if Employee.query.filter_by(dni=data['dni']).first():
        return jsonify({'error': 'El DNI ya está registrado'}), 400
    
    if Employee.query.filter_by(cuil=data['cuil']).first():
        return jsonify({'error': 'El CUIL ya está registrado'}), 400
    
    try:
        birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
        hire_date = datetime.strptime(data['hire_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    age = date.today().year - birth_date.year - ((date.today().month, date.today().day) < (birth_date.month, birth_date.day))
    if age < 18:
        return jsonify({'error': 'El empleado debe tener al menos 18 años'}), 400
    
    job_position = JobPosition.query.get(data['job_position_id'])
    if not job_position:
        return jsonify({'error': 'Puesto de trabajo no encontrado'}), 404
    
    user = User(
        email=data['email'],
        role='employee',
        is_active=True
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.flush()
    
    employee = Employee(
        user_id=user.id,
        first_name=data['first_name'],
        last_name=data['last_name'],
        dni=data['dni'],
        cuil=data['cuil'],
        birth_date=birth_date,
        phone=data['phone'],
        address=data['address'],
        profile_photo_url=data.get('profile_photo_url'),
        employment_relationship=data['employment_relationship'],
        emergency_contact_name=data['emergency_contact_name'],
        emergency_contact_phone=data['emergency_contact_phone'],
        emergency_contact_relationship=data['emergency_contact_relationship'],
        hire_date=hire_date,
        status='activo',
        current_job_position_id=data['job_position_id'],
        created_by_id=current_user.id
    )
    
    validation_errors = employee.validate()
    if validation_errors:
        db.session.rollback()
        return jsonify({'error': ', '.join(validation_errors)}), 400
    
    db.session.add(employee)
    db.session.flush()
    
    job_history = EmployeeJobHistory(
        employee_id=employee.id,
        job_position_id=data['job_position_id'],
        start_date=hire_date,
        notes=data.get('notes', 'Ingreso inicial'),
        created_by_id=current_user.id
    )
    db.session.add(job_history)
    
    db.session.commit()
    
    return jsonify(employee.to_dict(include_sensitive=True)), 201

@bp.route('/<int:employee_id>', methods=['PUT'])
@token_required
def update_employee(current_user, employee_id):
    employee = Employee.query.get_or_404(employee_id)
    
    is_admin = current_user.role == 'admin'
    is_own_profile = current_user.employee and current_user.employee.id == employee_id
    
    if not is_admin and not is_own_profile:
        return jsonify({'error': 'No autorizado'}), 403
    
    data = request.get_json()
    
    if is_own_profile and not is_admin:
        allowed_fields = ['phone', 'address', 'emergency_contact_name', 
                         'emergency_contact_phone', 'emergency_contact_relationship',
                         'profile_photo_url']
        for key in data.keys():
            if key not in allowed_fields:
                return jsonify({'error': f'No autorizado para modificar el campo: {key}'}), 403
    
    if 'email' in data and data['email'] != employee.user.email:
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'El email ya está registrado'}), 400
        employee.user.email = data['email']
    
    if 'first_name' in data:
        employee.first_name = data['first_name']
    if 'last_name' in data:
        employee.last_name = data['last_name']
    if 'phone' in data:
        employee.phone = data['phone']
    if 'address' in data:
        employee.address = data['address']
    if 'profile_photo_url' in data:
        employee.profile_photo_url = data['profile_photo_url']
    if 'emergency_contact_name' in data:
        employee.emergency_contact_name = data['emergency_contact_name']
    if 'emergency_contact_phone' in data:
        employee.emergency_contact_phone = data['emergency_contact_phone']
    if 'emergency_contact_relationship' in data:
        employee.emergency_contact_relationship = data['emergency_contact_relationship']
    
    if is_admin:
        if 'birth_date' in data:
            employee.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
        if 'employment_relationship' in data:
            employee.employment_relationship = data['employment_relationship']
        if 'status' in data:
            old_status = employee.status
            employee.status = data['status']
            
            if old_status != 'inactivo' and data['status'] == 'inactivo':
                Shift.query.filter(
                    Shift.employee_id == employee_id,
                    Shift.date >= date.today()
                ).delete()
                employee.user.is_active = False
        
        if 'job_position_id' in data and data['job_position_id'] != employee.current_job_position_id:
            current_history = EmployeeJobHistory.query.filter_by(
                employee_id=employee_id,
                end_date=None
            ).first()
            
            if current_history:
                current_history.end_date = date.today()
            
            new_history = EmployeeJobHistory(
                employee_id=employee_id,
                job_position_id=data['job_position_id'],
                start_date=date.today(),
                notes=data.get('job_change_notes', 'Cambio de puesto'),
                created_by_id=current_user.id
            )
            db.session.add(new_history)
            employee.current_job_position_id = data['job_position_id']
    
    employee.updated_by_id = current_user.id
    employee.updated_at = datetime.utcnow()
    
    validation_errors = employee.validate()
    if validation_errors:
        db.session.rollback()
        return jsonify({'error': ', '.join(validation_errors)}), 400
    
    db.session.commit()
    
    return jsonify(employee.to_dict(include_sensitive=True, include_history=True)), 200

@bp.route('/<int:employee_id>/deactivate', methods=['PATCH'])
@token_required
@admin_required
def deactivate_employee(current_user, employee_id):
    employee = Employee.query.get_or_404(employee_id)
    
    if employee.status == 'inactivo':
        return jsonify({'error': 'El empleado ya está inactivo'}), 400
    
    employee.status = 'inactivo'
    employee.user.is_active = False
    employee.updated_by_id = current_user.id
    employee.updated_at = datetime.utcnow()
    
    Shift.query.filter(
        Shift.employee_id == employee_id,
        Shift.date >= date.today()
    ).delete()
    
    db.session.commit()
    
    return jsonify({
        'message': 'Empleado desactivado exitosamente',
        'employee': employee.to_dict()
    }), 200

@bp.route('/<int:employee_id>/change-status', methods=['PATCH'])
@token_required
@admin_required
def change_employee_status(current_user, employee_id):
    employee = Employee.query.get_or_404(employee_id)
    data = request.get_json()
    
    if 'status' not in data:
        return jsonify({'error': 'Campo status requerido'}), 400
    
    valid_statuses = ['activo', 'inactivo', 'suspendido', 'vacaciones', 'licencia']
    if data['status'] not in valid_statuses:
        return jsonify({'error': 'Estado inválido'}), 400
    
    old_status = employee.status
    employee.status = data['status']
    
    if old_status != 'inactivo' and data['status'] == 'inactivo':
        Shift.query.filter(
            Shift.employee_id == employee_id,
            Shift.date >= date.today()
        ).delete()
        employee.user.is_active = False
    elif old_status == 'inactivo' and data['status'] != 'inactivo':
        employee.user.is_active = True
    
    employee.updated_by_id = current_user.id
    employee.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'message': f'Estado cambiado de {old_status} a {data["status"]}',
        'employee': employee.to_dict()
    }), 200

@bp.route('/<int:employee_id>/job-history', methods=['GET'])
@token_required
def get_employee_job_history(current_user, employee_id):
    if current_user.role != 'admin':
        employee = Employee.query.filter_by(user_id=current_user.id).first()
        if not employee or employee.id != employee_id:
            return jsonify({'error': 'No autorizado'}), 403
    
    history = EmployeeJobHistory.query.filter_by(employee_id=employee_id).order_by(
        EmployeeJobHistory.start_date.desc()
    ).all()
    
    return jsonify([h.to_dict() for h in history]), 200
