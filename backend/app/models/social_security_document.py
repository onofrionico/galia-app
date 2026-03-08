from datetime import datetime
from app.extensions import db

class SocialSecurityDocument(db.Model):
    __tablename__ = 'social_security_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False, index=True)
    document_type = db.Column(db.String(50), nullable=False)
    period_month = db.Column(db.Integer, nullable=False)
    period_year = db.Column(db.Integer, nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.Text, nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False, default='application/pdf')
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    
    employee = db.relationship('Employee', backref=db.backref('social_security_documents', lazy='dynamic', cascade='all, delete-orphan'))
    uploaded_by = db.relationship('User', foreign_keys=[uploaded_by_id])
    
    def validate(self):
        errors = []
        
        if self.document_type not in ['cargas_sociales', 'aportes', 'obra_social', 'art', 'otros']:
            errors.append('Tipo de documento inválido')
        
        if not (1 <= self.period_month <= 12):
            errors.append('Mes del período debe estar entre 1 y 12')
        
        if not (2000 <= self.period_year <= 2100):
            errors.append('Año del período inválido')
        
        if self.file_size > 10 * 1024 * 1024:
            errors.append('El archivo no puede superar los 10MB')
        
        if self.mime_type != 'application/pdf':
            errors.append('Solo se permiten archivos PDF')
        
        return errors
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.full_name if self.employee else None,
            'document_type': self.document_type,
            'period_month': self.period_month,
            'period_year': self.period_year,
            'period': f"{self.period_year}-{self.period_month:02d}",
            'file_name': self.file_name,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'uploaded_by_id': self.uploaded_by_id,
            'uploaded_by_name': f"{self.uploaded_by.employee.full_name}" if self.uploaded_by and hasattr(self.uploaded_by, 'employee') else None,
            'notes': self.notes
        }
