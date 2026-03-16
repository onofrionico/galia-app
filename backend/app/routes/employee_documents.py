from flask import Blueprint, request, jsonify, send_file
from functools import wraps
from app.extensions import db
from app.models.employee_document import EmployeeDocument
from app.models.employee import Employee
from app.models.payroll import Payroll
from app.models.social_security_document import SocialSecurityDocument
from app.models.absence_request import AbsenceRequest
from app.models.user import User
from app.utils.jwt_utils import token_required
from datetime import datetime
from sqlalchemy import or_, and_
from io import BytesIO
import os

employee_documents_bp = Blueprint('employee_documents', __name__, url_prefix='/api/v1')

def employee_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if not hasattr(current_user, 'employee') or not current_user.employee:
            return jsonify({'error': 'Usuario no tiene un empleado asociado'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

@employee_documents_bp.route('/my-documents', methods=['GET'])
@token_required
@employee_required
def get_my_documents(current_user):
    """
    Obtiene todos los documentos del empleado autenticado
    """
    employee = current_user.employee
    
    document_type = request.args.get('type')
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    documents = []
    
    if not document_type or document_type == 'payroll':
        payrolls_query = Payroll.query.filter_by(employee_id=employee.id)
        
        if year:
            payrolls_query = payrolls_query.filter_by(year=year)
        if month:
            payrolls_query = payrolls_query.filter_by(month=month)
        
        payrolls = payrolls_query.order_by(Payroll.year.desc(), Payroll.month.desc()).all()
        
        for payroll in payrolls:
            if payroll.pdf_generated and payroll.pdf_path:
                documents.append({
                    'id': f'payroll_{payroll.id}',
                    'type': 'payroll',
                    'reference_id': payroll.id,
                    'title': f'Recibo de Sueldo - {payroll.month:02d}/{payroll.year}',
                    'period_month': payroll.month,
                    'period_year': payroll.year,
                    'period': f'{payroll.year}-{payroll.month:02d}',
                    'file_name': f'nomina_{employee.dni}_{payroll.year}_{payroll.month:02d}.pdf',
                    'file_path': payroll.pdf_path,
                    'created_at': payroll.generated_at.isoformat() if payroll.generated_at else None,
                    'status': payroll.status,
                    'gross_salary': float(payroll.gross_salary)
                })
    
    if not document_type or document_type == 'social_security':
        ss_docs_query = SocialSecurityDocument.query.filter_by(employee_id=employee.id)
        
        if year:
            ss_docs_query = ss_docs_query.filter_by(period_year=year)
        if month:
            ss_docs_query = ss_docs_query.filter_by(period_month=month)
        
        ss_docs = ss_docs_query.order_by(
            SocialSecurityDocument.period_year.desc(),
            SocialSecurityDocument.period_month.desc()
        ).all()
        
        for doc in ss_docs:
            documents.append({
                'id': f'social_security_{doc.id}',
                'type': 'social_security',
                'reference_id': doc.id,
                'title': f'Cargas Sociales - {doc.period_month:02d}/{doc.period_year}',
                'period_month': doc.period_month,
                'period_year': doc.period_year,
                'period': f'{doc.period_year}-{doc.period_month:02d}',
                'file_name': doc.file_name,
                'file_path': doc.file_path,
                'file_size': doc.file_size,
                'created_at': doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                'document_subtype': doc.document_type,
                'notes': doc.notes
            })
    
    if not document_type or document_type == 'absence':
        absences_query = AbsenceRequest.query.filter_by(employee_id=employee.id)
        
        if year:
            absences_query = absences_query.filter(
                or_(
                    and_(
                        db.extract('year', AbsenceRequest.start_date) == year
                    ),
                    and_(
                        db.extract('year', AbsenceRequest.end_date) == year
                    )
                )
            )
        
        absences = absences_query.filter(
            AbsenceRequest.attachment_path.isnot(None)
        ).order_by(AbsenceRequest.start_date.desc()).all()
        
        for absence in absences:
            documents.append({
                'id': f'absence_{absence.id}',
                'type': 'absence',
                'reference_id': absence.id,
                'title': f'Justificativo de Ausencia - {absence.start_date.strftime("%d/%m/%Y")}',
                'period_month': absence.start_date.month,
                'period_year': absence.start_date.year,
                'period': f'{absence.start_date.year}-{absence.start_date.month:02d}',
                'file_name': absence.attachment_filename,
                'file_path': absence.attachment_path,
                'created_at': absence.created_at.isoformat() if absence.created_at else None,
                'status': absence.status,
                'start_date': absence.start_date.isoformat(),
                'end_date': absence.end_date.isoformat(),
                'justification': absence.justification
            })
    
    documents.sort(key=lambda x: (x.get('period_year', 0), x.get('period_month', 0)), reverse=True)
    
    return jsonify({
        'documents': documents,
        'total': len(documents),
        'employee': {
            'id': employee.id,
            'full_name': employee.full_name,
            'dni': employee.dni
        }
    }), 200

@employee_documents_bp.route('/my-documents/payrolls', methods=['GET'])
@token_required
@employee_required
def get_my_payrolls(current_user):
    """
    Obtiene solo los recibos de sueldo del empleado autenticado
    """
    employee = current_user.employee
    
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    status = request.args.get('status')
    
    payrolls_query = Payroll.query.filter_by(employee_id=employee.id)
    
    if year:
        payrolls_query = payrolls_query.filter_by(year=year)
    if month:
        payrolls_query = payrolls_query.filter_by(month=month)
    if status:
        payrolls_query = payrolls_query.filter_by(status=status)
    
    payrolls_query = payrolls_query.filter(
        Payroll.pdf_generated == True,
        Payroll.pdf_path.isnot(None)
    )
    
    payrolls = payrolls_query.order_by(Payroll.year.desc(), Payroll.month.desc()).all()
    
    documents = []
    for payroll in payrolls:
        documents.append({
            'id': payroll.id,
            'title': f'Recibo de Sueldo - {payroll.month:02d}/{payroll.year}',
            'period_month': payroll.month,
            'period_year': payroll.year,
            'period': f'{payroll.year}-{payroll.month:02d}',
            'file_name': f'nomina_{employee.dni}_{payroll.year}_{payroll.month:02d}.pdf',
            'file_path': payroll.pdf_path,
            'hours_worked': float(payroll.hours_worked),
            'scheduled_hours': float(payroll.scheduled_hours),
            'hourly_rate': float(payroll.hourly_rate),
            'gross_salary': float(payroll.gross_salary),
            'status': payroll.status,
            'generated_at': payroll.generated_at.isoformat() if payroll.generated_at else None,
            'validated_at': payroll.validated_at.isoformat() if payroll.validated_at else None,
            'employee_validated_at': payroll.employee_validated_at.isoformat() if payroll.employee_validated_at else None
        })
    
    return jsonify({
        'payrolls': documents,
        'total': len(documents),
        'employee': {
            'id': employee.id,
            'full_name': employee.full_name,
            'dni': employee.dni
        }
    }), 200

@employee_documents_bp.route('/my-documents/social-security', methods=['GET'])
@token_required
@employee_required
def get_my_social_security(current_user):
    """
    Obtiene solo los documentos de cargas sociales del empleado autenticado
    """
    employee = current_user.employee
    
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    doc_type = request.args.get('doc_type')
    
    ss_docs_query = SocialSecurityDocument.query.filter_by(employee_id=employee.id)
    
    if year:
        ss_docs_query = ss_docs_query.filter_by(period_year=year)
    if month:
        ss_docs_query = ss_docs_query.filter_by(period_month=month)
    if doc_type:
        ss_docs_query = ss_docs_query.filter_by(document_type=doc_type)
    
    ss_docs = ss_docs_query.order_by(
        SocialSecurityDocument.period_year.desc(),
        SocialSecurityDocument.period_month.desc()
    ).all()
    
    documents = []
    for doc in ss_docs:
        documents.append({
            'id': doc.id,
            'title': f'Cargas Sociales - {doc.period_month:02d}/{doc.period_year}',
            'period_month': doc.period_month,
            'period_year': doc.period_year,
            'period': f'{doc.period_year}-{doc.period_month:02d}',
            'file_name': doc.file_name,
            'file_path': doc.file_path,
            'file_size': doc.file_size,
            'mime_type': doc.mime_type,
            'document_type': doc.document_type,
            'uploaded_at': doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            'notes': doc.notes
        })
    
    return jsonify({
        'social_security_documents': documents,
        'total': len(documents),
        'employee': {
            'id': employee.id,
            'full_name': employee.full_name,
            'dni': employee.dni
        }
    }), 200

@employee_documents_bp.route('/my-documents/absences', methods=['GET'])
@token_required
@employee_required
def get_my_absences(current_user):
    """
    Obtiene solo los documentos de ausencias del empleado autenticado
    """
    employee = current_user.employee
    
    year = request.args.get('year', type=int)
    status = request.args.get('status')
    
    absences_query = AbsenceRequest.query.filter_by(employee_id=employee.id)
    
    if year:
        absences_query = absences_query.filter(
            or_(
                db.extract('year', AbsenceRequest.start_date) == year,
                db.extract('year', AbsenceRequest.end_date) == year
            )
        )
    
    if status:
        absences_query = absences_query.filter_by(status=status)
    
    absences_query = absences_query.filter(
        AbsenceRequest.attachment_path.isnot(None)
    )
    
    absences = absences_query.order_by(AbsenceRequest.start_date.desc()).all()
    
    documents = []
    for absence in absences:
        documents.append({
            'id': absence.id,
            'title': f'Justificativo de Ausencia - {absence.start_date.strftime("%d/%m/%Y")}',
            'start_date': absence.start_date.isoformat(),
            'end_date': absence.end_date.isoformat(),
            'period_month': absence.start_date.month,
            'period_year': absence.start_date.year,
            'file_name': absence.attachment_filename,
            'file_path': absence.attachment_path,
            'mime_type': absence.attachment_mimetype,
            'status': absence.status,
            'justification': absence.justification,
            'created_at': absence.created_at.isoformat() if absence.created_at else None,
            'reviewed_at': absence.reviewed_at.isoformat() if absence.reviewed_at else None,
            'review_notes': absence.review_notes
        })
    
    return jsonify({
        'absence_documents': documents,
        'total': len(documents),
        'employee': {
            'id': employee.id,
            'full_name': employee.full_name,
            'dni': employee.dni
        }
    }), 200

@employee_documents_bp.route('/my-documents/download/<document_type>/<int:document_id>', methods=['GET'])
@token_required
@employee_required
def download_my_document(current_user, document_type, document_id):
    """
    Descarga un documento específico del empleado autenticado
    """
    employee = current_user.employee
    
    if document_type == 'payroll':
        payroll = Payroll.query.filter_by(
            id=document_id,
            employee_id=employee.id
        ).first()
        
        if not payroll:
            return jsonify({'error': 'Recibo de sueldo no encontrado'}), 404
        
        if not payroll.pdf_generated or not payroll.pdf_path:
            return jsonify({'error': 'El PDF del recibo no está disponible'}), 404
        
        file_path = payroll.pdf_path
        file_name = f'nomina_{employee.dni}_{payroll.year}_{payroll.month:02d}.pdf'
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Archivo no encontrado en el servidor'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_name,
            mimetype='application/pdf'
        )
    
    elif document_type == 'social_security':
        ss_doc = SocialSecurityDocument.query.filter_by(
            id=document_id,
            employee_id=employee.id
        ).first()
        
        if not ss_doc:
            return jsonify({'error': 'Documento de cargas sociales no encontrado'}), 404
        
        from app.services.document_service import document_service
        file_content, file_name, error = document_service.download_document(document_id)
        
        if error:
            return jsonify({'error': error}), 404 if 'no encontrado' in error.lower() else 500
        
        return send_file(
            BytesIO(file_content),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=file_name
        )
    
    elif document_type == 'absence':
        absence = AbsenceRequest.query.filter_by(
            id=document_id,
            employee_id=employee.id
        ).first()
        
        if not absence:
            return jsonify({'error': 'Documento de ausencia no encontrado'}), 404
        
        if not absence.attachment_path:
            return jsonify({'error': 'El documento de ausencia no tiene archivo adjunto'}), 404
        
        file_path = absence.attachment_path
        file_name = absence.attachment_filename
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Archivo no encontrado en el servidor'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_name,
            mimetype='application/pdf'
        )
    
    else:
        return jsonify({'error': 'Tipo de documento inválido'}), 400
