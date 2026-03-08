from flask import Blueprint, request, jsonify, send_file
from functools import wraps
from app.extensions import db
from app.models.social_security_document import SocialSecurityDocument
from app.models.employee import Employee
from app.models.user import User
from app.utils.jwt_utils import token_required
from app.services.document_service import document_service, DocumentService
from datetime import datetime
from io import BytesIO

social_security_bp = Blueprint('social_security', __name__, url_prefix='/api/v1/social-security')

def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({'error': 'Se requieren permisos de administrador'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

@social_security_bp.route('/upload', methods=['POST'])
@token_required
@admin_required
def upload_document(current_user):
    employee_id = request.form.get('employee_id', type=int)
    document_type = request.form.get('document_type')
    period_month = request.form.get('period_month', type=int)
    period_year = request.form.get('period_year', type=int)
    notes = request.form.get('notes')
    
    if not all([employee_id, document_type, period_month, period_year]):
        return jsonify({'error': 'Faltan datos requeridos: employee_id, document_type, period_month, period_year'}), 400
    
    if 'file' not in request.files:
        return jsonify({'error': 'No se proporcionó ningún archivo'}), 400
    
    file = request.files['file']
    
    if not file or file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
    
    document, errors = document_service.upload_document(
        file=file,
        employee_id=employee_id,
        document_type=document_type,
        period_month=period_month,
        period_year=period_year,
        uploaded_by_id=current_user.id,
        notes=notes
    )
    
    if errors:
        return jsonify({'error': 'Error al subir documento', 'details': errors}), 400
    
    return jsonify({
        'message': 'Documento subido exitosamente',
        'document': document.to_dict()
    }), 201

@social_security_bp.route('/employee/<int:employee_id>', methods=['GET'])
@token_required
def get_employee_documents(current_user, employee_id):
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    
    if current_user.role not in ['admin', 'supervisor']:
        if not employee or employee.id != employee_id:
            return jsonify({'error': 'No tiene permiso para ver estos documentos'}), 403
    
    target_employee = Employee.query.get(employee_id)
    if not target_employee:
        return jsonify({'error': 'Empleado no encontrado'}), 404
    
    document_type = request.args.get('document_type')
    period_year = request.args.get('period_year', type=int)
    period_month = request.args.get('period_month', type=int)
    
    documents = document_service.get_employee_documents(
        employee_id=employee_id,
        document_type=document_type,
        period_year=period_year,
        period_month=period_month
    )
    
    return jsonify([doc.to_dict() for doc in documents])

@social_security_bp.route('/download/<int:document_id>', methods=['GET'])
@token_required
def download_document(current_user, document_id):
    document = document_service.get_document_by_id(document_id)
    
    if not document:
        return jsonify({'error': 'Documento no encontrado'}), 404
    
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    
    if current_user.role not in ['admin', 'supervisor']:
        if not employee or document.employee_id != employee.id:
            return jsonify({'error': 'No tiene permiso para descargar este documento'}), 403
    
    file_content, filename, error = document_service.download_document(document_id)
    
    if error:
        return jsonify({'error': error}), 404 if 'no encontrado' in error.lower() else 500
    
    return send_file(
        BytesIO(file_content),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

@social_security_bp.route('/download-url/<int:document_id>', methods=['GET'])
@token_required
def get_download_url(current_user, document_id):
    document = document_service.get_document_by_id(document_id)
    
    if not document:
        return jsonify({'error': 'Documento no encontrado'}), 404
    
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    
    if current_user.role not in ['admin', 'supervisor']:
        if not employee or document.employee_id != employee.id:
            return jsonify({'error': 'No tiene permiso para acceder a este documento'}), 403
    
    expiration = request.args.get('expiration', default=3600, type=int)
    
    url, error = document_service.generate_download_url(document_id, expiration)
    
    if error:
        return jsonify({'error': error}), 404 if 'no encontrado' in error.lower() else 500
    
    return jsonify({
        'url': url,
        'expires_in': expiration
    })

@social_security_bp.route('/<int:document_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_document(current_user, document_id):
    success, error = document_service.delete_document(document_id)
    
    if not success:
        return jsonify({'error': error}), 404 if 'no encontrado' in error.lower() else 500
    
    return jsonify({'message': 'Documento eliminado exitosamente'}), 200

@social_security_bp.route('/<int:document_id>', methods=['GET'])
@token_required
def get_document_detail(current_user, document_id):
    document = document_service.get_document_by_id(document_id)
    
    if not document:
        return jsonify({'error': 'Documento no encontrado'}), 404
    
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    
    if current_user.role not in ['admin', 'supervisor']:
        if not employee or document.employee_id != employee.id:
            return jsonify({'error': 'No tiene permiso para ver este documento'}), 403
    
    return jsonify(document.to_dict())

@social_security_bp.route('/types', methods=['GET'])
@token_required
def get_document_types(current_user):
    return jsonify({
        'document_types': [
            {'value': key, 'label': value}
            for key, value in DocumentService.DOCUMENT_TYPES.items()
        ]
    })

@social_security_bp.route('/all', methods=['GET'])
@token_required
@admin_required
def get_all_documents(current_user):
    employee_id = request.args.get('employee_id', type=int)
    document_type = request.args.get('document_type')
    period_year = request.args.get('period_year', type=int)
    period_month = request.args.get('period_month', type=int)
    
    query = SocialSecurityDocument.query
    
    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    if document_type:
        query = query.filter_by(document_type=document_type)
    if period_year:
        query = query.filter_by(period_year=period_year)
    if period_month:
        query = query.filter_by(period_month=period_month)
    
    documents = query.order_by(
        SocialSecurityDocument.period_year.desc(),
        SocialSecurityDocument.period_month.desc(),
        SocialSecurityDocument.uploaded_at.desc()
    ).all()
    
    return jsonify([doc.to_dict() for doc in documents])
