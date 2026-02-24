from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.time_tracking import TimeTracking
from app.models.work_block import WorkBlock
from app.models.employee import Employee
from app.models.shift import Shift
from datetime import datetime, date, timedelta
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from calendar import monthrange
import logging
from app.utils.jwt_utils import token_required
from app.utils.payroll_utils import calculate_employee_cost, calculate_total_hours_from_dict

logger = logging.getLogger(__name__)
bp = Blueprint('time_tracking', __name__, url_prefix='/api/v1/time-tracking')

def blocks_overlap(start1, end1, start2, end2):
    """Verifica si dos bloques de tiempo se superponen"""
    return start1 < end2 and start2 < end1

@bp.route('/check-in', methods=['POST'])
@token_required
def check_in(current_user):
    data = request.get_json()
    
    if not current_user.employee:
        return jsonify({'error': 'Usuario no es un empleado'}), 403
    
    try:
        tracking_date = datetime.fromisoformat(data.get('date')).date() if data.get('date') else date.today()
    except (ValueError, AttributeError):
        return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    if tracking_date > date.today():
        return jsonify({'error': 'No se pueden registrar horarios futuros'}), 400
    
    try:
        record = TimeTracking.query.filter_by(
            employee_id=current_user.employee.id,
            tracking_date=tracking_date
        ).first()
        
        if not record:
            record = TimeTracking(
                employee_id=current_user.employee.id,
                tracking_date=tracking_date
            )
            db.session.add(record)
            db.session.flush()
        
        current_time = datetime.now().time()
        
        for existing_block in record.work_blocks:
            if blocks_overlap(existing_block.start_time, existing_block.end_time, current_time, current_time):
                return jsonify({'error': 'Ya existe un bloque de trabajo en este horario'}), 409
        
        work_block = WorkBlock(
            time_tracking_id=record.id,
            start_time=current_time,
            end_time=current_time
        )
        db.session.add(work_block)
        db.session.commit()
        
        return jsonify({
            'message': 'Entrada registrada exitosamente',
            'record': record.to_dict()
        }), 201
    
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"IntegrityError en check_in: {str(e)}")
        return jsonify({'error': 'Error al registrar entrada'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error en check_in: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp.route('/check-out', methods=['POST'])
@token_required
def check_out(current_user):
    data = request.get_json()
    
    if not current_user.employee:
        return jsonify({'error': 'Usuario no es un empleado'}), 403
    
    try:
        tracking_date = datetime.fromisoformat(data.get('date')).date() if data.get('date') else date.today()
    except (ValueError, AttributeError):
        return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    if tracking_date > date.today():
        return jsonify({'error': 'No se pueden registrar horarios futuros'}), 400
    
    try:
        record = TimeTracking.query.filter_by(
            employee_id=current_user.employee.id,
            tracking_date=tracking_date
        ).first()
        
        if not record or not record.work_blocks:
            return jsonify({'error': 'No hay registro de entrada para hoy'}), 404
        
        last_block = record.work_blocks[-1]
        
        if last_block.end_time != last_block.start_time:
            return jsonify({'error': 'Ya has registrado salida para el último bloque'}), 409
        
        last_block.end_time = datetime.now().time()
        db.session.commit()
        
        return jsonify({
            'message': 'Salida registrada exitosamente',
            'record': record.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error en check_out: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp.route('/today', methods=['GET'])
@token_required
def get_today_record(current_user):
    if not current_user.employee:
        return jsonify({'error': 'Usuario no es un empleado'}), 403
    
    today = date.today()
    record = TimeTracking.query.filter_by(
        employee_id=current_user.employee.id,
        tracking_date=today
    ).first()
    
    if not record:
        return jsonify({
            'id': None,
            'employee_id': current_user.employee.id,
            'tracking_date': today.isoformat(),
            'work_blocks': [],
            'total_hours': 0,
            'total_minutes': 0,
            'created_at': None,
            'updated_at': None
        }), 200
    
    return jsonify(record.to_dict()), 200

@bp.route('/records', methods=['GET'])
@token_required
def get_records(current_user):
    if not current_user.employee:
        return jsonify({'error': 'Usuario no es un empleado'}), 403
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        start = datetime.fromisoformat(start_date).date() if start_date else None
        end = datetime.fromisoformat(end_date).date() if end_date else None
    except (ValueError, AttributeError):
        return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    query = TimeTracking.query.filter_by(employee_id=current_user.employee.id)
    
    if start:
        query = query.filter(TimeTracking.tracking_date >= start)
    if end:
        query = query.filter(TimeTracking.tracking_date <= end)
    
    records = query.order_by(TimeTracking.tracking_date.desc()).all()
    
    return jsonify([record.to_dict() for record in records]), 200

@bp.route('/monthly', methods=['GET'])
@token_required
def get_monthly_records(current_user):
    if not current_user.employee:
        return jsonify({'error': 'Usuario no es un empleado'}), 403
    
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    if not year or not month:
        return jsonify({'error': 'Año y mes son requeridos'}), 400
    
    if month < 1 or month > 12:
        return jsonify({'error': 'Mes inválido'}), 400
    
    from datetime import date as date_class
    from calendar import monthrange
    
    start_date = date_class(year, month, 1)
    last_day = monthrange(year, month)[1]
    end_date = date_class(year, month, last_day)
    
    records = TimeTracking.query.filter_by(
        employee_id=current_user.employee.id
    ).filter(
        TimeTracking.tracking_date >= start_date,
        TimeTracking.tracking_date <= end_date
    ).order_by(TimeTracking.tracking_date.asc()).all()
    
    return jsonify([record.to_dict() for record in records]), 200

@bp.route('/record-hours', methods=['POST'])
@token_required
def record_hours(current_user):
    data = request.get_json()
    
    if not current_user.employee:
        return jsonify({'error': 'Usuario no es un empleado'}), 403
    
    required_fields = ['date', 'check_in', 'check_out']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Todos los campos son requeridos'}), 400
    
    try:
        tracking_date = datetime.fromisoformat(data['date']).date()
        check_in_time = datetime.strptime(data['check_in'], '%H:%M').time()
        check_out_time = datetime.strptime(data['check_out'], '%H:%M').time()
    except (ValueError, AttributeError):
        return jsonify({'error': 'Formato de fecha u hora inválido'}), 400
    
    if tracking_date > date.today():
        return jsonify({'error': 'No se pueden registrar horarios futuros'}), 400
    
    if check_in_time >= check_out_time:
        return jsonify({'error': 'La hora de salida debe ser posterior a la hora de entrada'}), 400
    
    try:
        record = TimeTracking.query.filter_by(
            employee_id=current_user.employee.id,
            tracking_date=tracking_date
        ).first()
        
        if not record:
            record = TimeTracking(
                employee_id=current_user.employee.id,
                tracking_date=tracking_date
            )
            db.session.add(record)
            db.session.flush()
        
        for existing_block in record.work_blocks:
            if blocks_overlap(existing_block.start_time, existing_block.end_time, check_in_time, check_out_time):
                return jsonify({'error': 'Este bloque se superpone con otro bloque existente'}), 409
        
        work_block = WorkBlock(
            time_tracking_id=record.id,
            start_time=check_in_time,
            end_time=check_out_time
        )
        db.session.add(work_block)
        db.session.commit()
        
        return jsonify({
            'message': 'Horas registradas exitosamente',
            'record': record.to_dict()
        }), 201
    
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"IntegrityError en record_hours: {str(e)}")
        return jsonify({'error': 'Error al registrar horas'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error en record_hours: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/calendar', methods=['GET'])
@token_required
def get_calendar_data(current_user):
    """
    Obtiene datos de horas trabajadas para el calendario.
    Parámetros:
    - year: año (requerido)
    - month: mes (requerido)
    - employee_id: filtrar por empleado (opcional)
    - shift_id: filtrar por turno programado (opcional)
    """
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    employee_id = request.args.get('employee_id', type=int)
    shift_schedule_id = request.args.get('shift_schedule_id', type=int)
    
    if not year or not month:
        return jsonify({'error': 'Año y mes son requeridos'}), 400
    
    if month < 1 or month > 12:
        return jsonify({'error': 'Mes inválido'}), 400
    
    start_date = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    end_date = date(year, month, last_day)
    
    query = db.session.query(TimeTracking).join(Employee)
    
    if employee_id:
        query = query.filter(TimeTracking.employee_id == employee_id)
    
    if shift_schedule_id:
        employee_ids_in_shift = db.session.query(Shift.employee_id).filter(
            Shift.schedule_id == shift_schedule_id
        ).distinct().subquery()
        query = query.filter(TimeTracking.employee_id.in_(employee_ids_in_shift))
    
    query = query.filter(
        TimeTracking.tracking_date >= start_date,
        TimeTracking.tracking_date <= end_date
    )
    
    records = query.all()
    
    calendar_data = {}
    for day in range(1, last_day + 1):
        day_date = date(year, month, day)
        calendar_data[day_date.isoformat()] = {
            'date': day_date.isoformat(),
            'total_hours': 0,
            'total_minutes': 0,
            'employee_count': 0,
            'employees': [],
            'daily_cost': 0.0
        }
    
    total_cost = 0.0
    
    for record in records:
        day_key = record.tracking_date.isoformat()
        if day_key in calendar_data:
            record_data = record.to_dict()
            calendar_data[day_key]['total_hours'] += record_data['total_hours']
            calendar_data[day_key]['total_minutes'] += record_data['total_minutes']
            calendar_data[day_key]['employee_count'] += 1
            calendar_data[day_key]['employees'].append({
                'employee_id': record.employee_id,
                'employee_name': record.employee.full_name,
                'hours': record_data['total_hours'],
                'minutes': record_data['total_minutes']
            })
            
            if record.employee.job_position and record.employee.job_position.hourly_rate:
                employee_total_hours = calculate_total_hours_from_dict(record_data['total_hours'], record_data['total_minutes'])
                hourly_rate = record.employee.job_position.hourly_rate
                employee_cost = calculate_employee_cost(
                    employee_total_hours, 
                    hourly_rate,
                    work_date=record.tracking_date,
                    job_position=record.employee.job_position
                )
                calendar_data[day_key]['daily_cost'] += employee_cost
                total_cost += employee_cost
                logger.info(f"Added cost for {record.employee.full_name} on {day_key}: ${employee_cost:.2f} (total now: ${total_cost:.2f})")
            else:
                logger.warning(f"Employee {record.employee.full_name} (ID: {record.employee_id}) missing job_position or hourly_rate")
    
    for day_key in calendar_data:
        extra_hours = calendar_data[day_key]['total_minutes'] // 60
        calendar_data[day_key]['total_hours'] += extra_hours
        calendar_data[day_key]['total_minutes'] = calendar_data[day_key]['total_minutes'] % 60
    
    return jsonify({
        'year': year,
        'month': month,
        'days': list(calendar_data.values()),
        'total_cost': round(total_cost, 2)
    }), 200


@bp.route('/calendar/day-detail', methods=['GET'])
@token_required
def get_day_detail(current_user):
    """
    Obtiene el detalle de horas trabajadas para un día específico.
    Muestra empleados y sus bloques de trabajo por hora.
    """
    date_str = request.args.get('date')
    employee_id = request.args.get('employee_id', type=int)
    shift_schedule_id = request.args.get('shift_schedule_id', type=int)
    
    if not date_str:
        return jsonify({'error': 'Fecha requerida'}), 400
    
    try:
        target_date = datetime.fromisoformat(date_str).date()
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    query = db.session.query(TimeTracking).join(Employee)
    
    if employee_id:
        query = query.filter(TimeTracking.employee_id == employee_id)
    
    if shift_schedule_id:
        employee_ids_in_shift = db.session.query(Shift.employee_id).filter(
            Shift.schedule_id == shift_schedule_id
        ).distinct().subquery()
        query = query.filter(TimeTracking.employee_id.in_(employee_ids_in_shift))
    
    query = query.filter(TimeTracking.tracking_date == target_date)
    records = query.all()
    
    hours_breakdown = {hour: [] for hour in range(24)}
    employees_summary = []
    
    for record in records:
        employee_data = {
            'employee_id': record.employee_id,
            'employee_name': record.employee.full_name,
            'work_blocks': [],
            'total_hours': 0,
            'total_minutes': 0
        }
        
        for block in record.work_blocks:
            start_hour = block.start_time.hour
            end_hour = block.end_time.hour if block.end_time.minute > 0 else block.end_time.hour
            
            block_data = {
                'start_time': block.start_time.strftime('%H:%M'),
                'end_time': block.end_time.strftime('%H:%M')
            }
            employee_data['work_blocks'].append(block_data)
            
            for hour in range(start_hour, min(end_hour + 1, 24)):
                if not any(e['employee_id'] == record.employee_id for e in hours_breakdown[hour]):
                    hours_breakdown[hour].append({
                        'employee_id': record.employee_id,
                        'employee_name': record.employee.full_name,
                        'start_time': block.start_time.strftime('%H:%M'),
                        'end_time': block.end_time.strftime('%H:%M')
                    })
        
        record_dict = record.to_dict()
        employee_data['total_hours'] = record_dict['total_hours']
        employee_data['total_minutes'] = record_dict['total_minutes']
        employees_summary.append(employee_data)
    
    hours_with_work = {
        hour: employees 
        for hour, employees in hours_breakdown.items() 
        if employees
    }
    
    return jsonify({
        'date': target_date.isoformat(),
        'employees_summary': employees_summary,
        'hours_breakdown': hours_with_work,
        'total_employees': len(employees_summary)
    }), 200
