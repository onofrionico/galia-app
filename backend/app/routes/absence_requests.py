from flask import Blueprint, request, jsonify, send_file
from functools import wraps
from app.extensions import db
from app.models.absence_request import AbsenceRequest
from app.models.employee import Employee
from app.models.user import User
from app.models.shift import Shift
from app.utils.jwt_utils import token_required
from app.utils.s3_utils import s3_service
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
from io import BytesIO

absence_bp = Blueprint('absence_requests', __name__, url_prefix='/api/v1/absence-requests')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
MAX_FILE_SIZE = 5 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_or_supervisor_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.role not in ['admin', 'supervisor']:
            return jsonify({'error': 'Se requieren permisos de administrador o supervisor'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

@absence_bp.route('/', methods=['POST'])
@token_required
def create_absence_request(current_user):
    try:
        employee = Employee.query.filter_by(user_id=current_user.id).first()
        if not employee:
            return jsonify({'error': 'No se encontró un empleado asociado a este usuario'}), 404
        
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        justification = request.form.get('justification')
        
        print(f"[ABSENCE DEBUG] Form data - start_date: {start_date_str}, end_date: {end_date_str}, justification length: {len(justification) if justification else 0}")
        print(f"[ABSENCE DEBUG] Files in request: {list(request.files.keys())}")
        
        if not all([start_date_str, end_date_str, justification]):
            return jsonify({'error': 'Faltan datos requeridos: start_date, end_date, justification'}), 400
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError as e:
            print(f"[ABSENCE DEBUG] Date parsing error: {str(e)}")
            return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400
        
        absence_request = AbsenceRequest(
            employee_id=employee.id,
            start_date=start_date,
            end_date=end_date,
            justification=justification,
            status='pending'
        )
        
        errors = absence_request.validate()
        if errors:
            print(f"[ABSENCE DEBUG] Validation errors: {errors}")
            return jsonify({'error': 'Validación fallida', 'details': errors}), 400
        
        if 'attachment' in request.files:
            file = request.files['attachment']
            print(f"[ABSENCE DEBUG] File object: {file}, filename: {file.filename if file else 'None'}")
            
            if file and file.filename and file.filename.strip():
                print(f"[ABSENCE DEBUG] Processing file: {file.filename}")
                
                if not allowed_file(file.filename):
                    return jsonify({'error': 'Tipo de archivo no permitido. Use: png, jpg, jpeg, pdf'}), 400
                
                if request.content_length and request.content_length > MAX_FILE_SIZE:
                    return jsonify({'error': 'El archivo es demasiado grande. Máximo 5MB'}), 400
                
                try:
                    s3_result = s3_service.upload_file(file, employee.id, file.filename)
                    print(f"[ABSENCE DEBUG] S3 upload successful: {s3_result['s3_key']}")
                    
                    absence_request.attachment_path = s3_result['s3_key']
                    absence_request.attachment_filename = s3_result['original_filename']
                    absence_request.attachment_mimetype = s3_result['content_type']
                except ValueError as e:
                    print(f"[ABSENCE DEBUG] ValueError during upload: {str(e)}")
                    return jsonify({'error': str(e)}), 400
                except Exception as e:
                    print(f"[ABSENCE DEBUG] Exception during upload: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return jsonify({'error': f'Error al subir archivo: {str(e)}'}), 500
            else:
                print(f"[ABSENCE DEBUG] File validation failed - file exists: {file is not None}, has filename: {file.filename if file else 'N/A'}")
        
        db.session.add(absence_request)
        db.session.commit()
        print(f"[ABSENCE DEBUG] Absence request created successfully with ID: {absence_request.id}")
        
        return jsonify({
            'message': 'Solicitud de ausencia creada exitosamente',
            'absence_request': absence_request.to_dict()
        }), 201
    
    except Exception as e:
        print(f"[ABSENCE DEBUG] Unexpected error in create_absence_request: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@absence_bp.route('/my-requests', methods=['GET'])
@token_required
def get_my_absence_requests(current_user):
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    if not employee:
        return jsonify({'error': 'No se encontró un empleado asociado a este usuario'}), 404
    
    status = request.args.get('status')
    
    query = AbsenceRequest.query.filter_by(employee_id=employee.id)
    
    if status:
        query = query.filter_by(status=status)
    
    requests = query.order_by(AbsenceRequest.created_at.desc()).all()
    
    return jsonify([r.to_dict(include_employee=False) for r in requests])

@absence_bp.route('/my-requests/<int:request_id>', methods=['GET'])
@token_required
def get_my_absence_request_detail(current_user, request_id):
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    if not employee:
        return jsonify({'error': 'No se encontró un empleado asociado a este usuario'}), 404
    
    absence_request = AbsenceRequest.query.get_or_404(request_id)
    
    if absence_request.employee_id != employee.id:
        return jsonify({'error': 'No tiene permiso para ver esta solicitud'}), 403
    
    return jsonify(absence_request.to_dict())

@absence_bp.route('/my-requests/<int:request_id>', methods=['DELETE'])
@token_required
def delete_my_absence_request(current_user, request_id):
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    if not employee:
        return jsonify({'error': 'No se encontró un empleado asociado a este usuario'}), 404
    
    absence_request = AbsenceRequest.query.get_or_404(request_id)
    
    if absence_request.employee_id != employee.id:
        return jsonify({'error': 'No tiene permiso para eliminar esta solicitud'}), 403
    
    if absence_request.status != 'pending':
        return jsonify({'error': 'Solo se pueden eliminar solicitudes pendientes'}), 400
    
    if absence_request.attachment_path:
        try:
            s3_service.delete_file(absence_request.attachment_path)
        except Exception as e:
            print(f"Error deleting S3 file: {str(e)}")
    
    db.session.delete(absence_request)
    db.session.commit()
    
    return jsonify({'message': 'Solicitud eliminada exitosamente'}), 200

@absence_bp.route('/', methods=['GET'])
@token_required
@admin_or_supervisor_required
def get_all_absence_requests(current_user):
    status = request.args.get('status')
    employee_id = request.args.get('employee_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = AbsenceRequest.query
    
    if status:
        query = query.filter_by(status=status)
    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(AbsenceRequest.start_date >= start)
        except ValueError:
            return jsonify({'error': 'Formato de start_date inválido'}), 400
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(AbsenceRequest.end_date <= end)
        except ValueError:
            return jsonify({'error': 'Formato de end_date inválido'}), 400
    
    requests = query.order_by(AbsenceRequest.created_at.desc()).all()
    
    return jsonify([r.to_dict() for r in requests])

@absence_bp.route('/<int:request_id>', methods=['GET'])
@token_required
@admin_or_supervisor_required
def get_absence_request_detail(current_user, request_id):
    absence_request = AbsenceRequest.query.get_or_404(request_id)
    return jsonify(absence_request.to_dict())

@absence_bp.route('/<int:request_id>/approve', methods=['POST'])
@token_required
@admin_or_supervisor_required
def approve_absence_request(current_user, request_id):
    absence_request = AbsenceRequest.query.get_or_404(request_id)
    
    if absence_request.status != 'pending':
        return jsonify({'error': 'Solo se pueden aprobar solicitudes pendientes'}), 400
    
    data = request.get_json() or {}
    review_notes = data.get('review_notes', '')
    
    absence_request.status = 'approved'
    absence_request.reviewed_by_id = current_user.id
    absence_request.reviewed_at = datetime.utcnow()
    absence_request.review_notes = review_notes
    
    current_date = absence_request.start_date
    while current_date <= absence_request.end_date:
        shifts = Shift.query.filter_by(
            employee_id=absence_request.employee_id,
            shift_date=current_date
        ).all()
        
        current_date += timedelta(days=1)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Solicitud aprobada exitosamente',
        'absence_request': absence_request.to_dict()
    })

@absence_bp.route('/<int:request_id>/reject', methods=['POST'])
@token_required
@admin_or_supervisor_required
def reject_absence_request(current_user, request_id):
    absence_request = AbsenceRequest.query.get_or_404(request_id)
    
    if absence_request.status != 'pending':
        return jsonify({'error': 'Solo se pueden rechazar solicitudes pendientes'}), 400
    
    data = request.get_json() or {}
    review_notes = data.get('review_notes', '')
    
    if not review_notes:
        return jsonify({'error': 'Debe proporcionar una razón para el rechazo en review_notes'}), 400
    
    absence_request.status = 'rejected'
    absence_request.reviewed_by_id = current_user.id
    absence_request.reviewed_at = datetime.utcnow()
    absence_request.review_notes = review_notes
    
    db.session.commit()
    
    return jsonify({
        'message': 'Solicitud rechazada',
        'absence_request': absence_request.to_dict()
    })

@absence_bp.route('/<int:request_id>/attachment', methods=['GET'])
@token_required
def download_attachment(current_user, request_id):
    absence_request = AbsenceRequest.query.get_or_404(request_id)
    
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    
    if current_user.role not in ['admin', 'supervisor']:
        if not employee or absence_request.employee_id != employee.id:
            return jsonify({'error': 'No tiene permiso para descargar este archivo'}), 403
    
    if not absence_request.attachment_path:
        return jsonify({'error': 'Archivo no encontrado'}), 404
    
    try:
        file_content, content_type, filename = s3_service.download_file(absence_request.attachment_path)
        
        return send_file(
            BytesIO(file_content),
            mimetype=content_type,
            as_attachment=True,
            download_name=filename
        )
    except FileNotFoundError:
        return jsonify({'error': 'Archivo no encontrado en S3'}), 404
    except Exception as e:
        return jsonify({'error': f'Error al descargar archivo: {str(e)}'}), 500

@absence_bp.route('/pending-count', methods=['GET'])
@token_required
@admin_or_supervisor_required
def get_pending_count(current_user):
    count = AbsenceRequest.query.filter_by(status='pending').count()
    return jsonify({'pending_count': count})
