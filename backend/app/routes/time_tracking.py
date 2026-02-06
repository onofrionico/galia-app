from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.time_tracking import TimeTracking
from app.models.work_block import WorkBlock
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('time_tracking', __name__, url_prefix='/api/v1/time-tracking')

def blocks_overlap(start1, end1, start2, end2):
    """Verifica si dos bloques de tiempo se superponen"""
    return start1 < end2 and start2 < end1

@bp.route('/check-in', methods=['POST'])
@login_required
def check_in():
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
@login_required
def check_out():
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
@login_required
def get_today_record():
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
@login_required
def get_records():
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
@login_required
def get_monthly_records():
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
@login_required
def record_hours():
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
