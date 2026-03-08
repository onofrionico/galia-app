from datetime import datetime
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.social_security_document import SocialSecurityDocument
from app.models.employee import Employee
from app.utils.s3_utils import s3_service
import os

class DocumentService:
    
    ALLOWED_EXTENSIONS = {'pdf'}
    MAX_FILE_SIZE = 10 * 1024 * 1024
    FOLDER_PREFIX = 'social-security-documents/'
    
    DOCUMENT_TYPES = {
        'cargas_sociales': 'Cargas Sociales',
        'aportes': 'Aportes',
        'obra_social': 'Obra Social',
        'art': 'ART',
        'otros': 'Otros'
    }
    
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in DocumentService.ALLOWED_EXTENSIONS
    
    @staticmethod
    def validate_file(file, file_size=None):
        errors = []
        
        if not file:
            errors.append('No se proporcionó ningún archivo')
            return errors
        
        if file.filename == '':
            errors.append('El archivo no tiene nombre')
            return errors
        
        if not DocumentService.allowed_file(file.filename):
            errors.append('Solo se permiten archivos PDF')
        
        if file_size and file_size > DocumentService.MAX_FILE_SIZE:
            errors.append(f'El archivo no puede superar los {DocumentService.MAX_FILE_SIZE / (1024 * 1024):.0f}MB')
        
        return errors
    
    @staticmethod
    def upload_document(file, employee_id, document_type, period_month, period_year, uploaded_by_id, notes=None):
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        validation_errors = DocumentService.validate_file(file, file_size)
        if validation_errors:
            return None, validation_errors
        
        employee = Employee.query.get(employee_id)
        if not employee:
            return None, ['Empleado no encontrado']
        
        if document_type not in DocumentService.DOCUMENT_TYPES:
            return None, ['Tipo de documento inválido']
        
        if not (1 <= period_month <= 12):
            return None, ['Mes del período debe estar entre 1 y 12']
        
        if not (2000 <= period_year <= 2100):
            return None, ['Año del período inválido']
        
        try:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            s3_key = f"{DocumentService.FOLDER_PREFIX}{employee_id}/{period_year}/{period_month:02d}/{timestamp}_{filename}"
            
            s3_service.s3_client.upload_fileobj(
                file,
                s3_service.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': 'application/pdf',
                    'ServerSideEncryption': 'AES256',
                    'Metadata': {
                        'employee_id': str(employee_id),
                        'document_type': document_type,
                        'period': f"{period_year}-{period_month:02d}",
                        'original_filename': filename,
                        'uploaded_at': datetime.utcnow().isoformat()
                    }
                }
            )
            
            document = SocialSecurityDocument(
                employee_id=employee_id,
                document_type=document_type,
                period_month=period_month,
                period_year=period_year,
                file_name=filename,
                file_path=s3_key,
                file_size=file_size,
                mime_type='application/pdf',
                uploaded_by_id=uploaded_by_id,
                notes=notes
            )
            
            validation_errors = document.validate()
            if validation_errors:
                s3_service.delete_file(s3_key)
                return None, validation_errors
            
            db.session.add(document)
            db.session.commit()
            
            return document, None
        
        except Exception as e:
            db.session.rollback()
            return None, [f'Error al subir el documento: {str(e)}']
    
    @staticmethod
    def get_employee_documents(employee_id, document_type=None, period_year=None, period_month=None):
        query = SocialSecurityDocument.query.filter_by(employee_id=employee_id)
        
        if document_type:
            query = query.filter_by(document_type=document_type)
        
        if period_year:
            query = query.filter_by(period_year=period_year)
        
        if period_month:
            query = query.filter_by(period_month=period_month)
        
        return query.order_by(
            SocialSecurityDocument.period_year.desc(),
            SocialSecurityDocument.period_month.desc(),
            SocialSecurityDocument.uploaded_at.desc()
        ).all()
    
    @staticmethod
    def get_document_by_id(document_id):
        return SocialSecurityDocument.query.get(document_id)
    
    @staticmethod
    def download_document(document_id):
        document = SocialSecurityDocument.query.get(document_id)
        if not document:
            return None, None, 'Documento no encontrado'
        
        try:
            file_content, content_type, _ = s3_service.download_file(document.file_path)
            return file_content, document.file_name, None
        except FileNotFoundError:
            return None, None, 'Archivo no encontrado en el almacenamiento'
        except Exception as e:
            return None, None, f'Error al descargar el documento: {str(e)}'
    
    @staticmethod
    def delete_document(document_id):
        document = SocialSecurityDocument.query.get(document_id)
        if not document:
            return False, 'Documento no encontrado'
        
        try:
            s3_service.delete_file(document.file_path)
            db.session.delete(document)
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            return False, f'Error al eliminar el documento: {str(e)}'
    
    @staticmethod
    def generate_download_url(document_id, expiration=3600):
        document = SocialSecurityDocument.query.get(document_id)
        if not document:
            return None, 'Documento no encontrado'
        
        try:
            url = s3_service.generate_presigned_url(document.file_path, expiration)
            return url, None
        except Exception as e:
            return None, f'Error al generar URL de descarga: {str(e)}'

document_service = DocumentService()
