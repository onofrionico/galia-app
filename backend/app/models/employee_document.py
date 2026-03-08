from datetime import datetime
from app.extensions import db

class EmployeeDocument(db.Model):
    __tablename__ = 'employee_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False, index=True)
    document_type = db.Column(db.String(50), nullable=False, index=True)
    reference_id = db.Column(db.Integer, nullable=False)
    period_month = db.Column(db.Integer, nullable=True)
    period_year = db.Column(db.Integer, nullable=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.Text, nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    mime_type = db.Column(db.String(100), nullable=False, default='application/pdf')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    employee = db.relationship('Employee', backref=db.backref('documents', lazy='dynamic', cascade='all, delete-orphan'))
    
    __table_args__ = (
        db.Index('idx_employee_doc_type', 'employee_id', 'document_type'),
        db.Index('idx_employee_doc_period', 'employee_id', 'period_year', 'period_month'),
    )
    
    def validate(self):
        errors = []
        
        if self.document_type not in ['payroll', 'social_security', 'absence', 'other']:
            errors.append('Tipo de documento inválido')
        
        if self.period_month and not (1 <= self.period_month <= 12):
            errors.append('Mes del período debe estar entre 1 y 12')
        
        if self.period_year and not (2000 <= self.period_year <= 2100):
            errors.append('Año del período inválido')
        
        if self.file_size and self.file_size > 10 * 1024 * 1024:
            errors.append('El archivo no puede superar los 10MB')
        
        return errors
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.full_name if self.employee else None,
            'document_type': self.document_type,
            'reference_id': self.reference_id,
            'period_month': self.period_month,
            'period_year': self.period_year,
            'period': f"{self.period_year}-{self.period_month:02d}" if self.period_year and self.period_month else None,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'description': self.description
        }
