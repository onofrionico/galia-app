from datetime import datetime
from app.extensions import db

class AbsenceRequest(db.Model):
    __tablename__ = 'absence_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False, index=True)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False, index=True)
    justification = db.Column(db.Text, nullable=False)
    attachment_path = db.Column(db.Text, nullable=True)
    attachment_filename = db.Column(db.String(255), nullable=True)
    attachment_mimetype = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending', index=True)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    review_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    employee = db.relationship('Employee', backref='absence_requests', foreign_keys=[employee_id])
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])
    
    __table_args__ = (
        db.Index('idx_absence_employee_dates', 'employee_id', 'start_date', 'end_date'),
        db.Index('idx_absence_status', 'status'),
    )
    
    def validate(self):
        errors = []
        
        if self.start_date > self.end_date:
            errors.append('La fecha de inicio no puede ser posterior a la fecha de fin')
        
        if self.status not in ['pending', 'approved', 'rejected']:
            errors.append('Estado inválido')
        
        if not self.justification or len(self.justification.strip()) < 10:
            errors.append('La justificación debe tener al menos 10 caracteres')
        
        return errors
    
    def to_dict(self, include_employee=True, include_reviewer=True):
        data = {
            'id': self.id,
            'employee_id': self.employee_id,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'justification': self.justification,
            'has_attachment': self.attachment_path is not None,
            'attachment_filename': self.attachment_filename,
            'attachment_mimetype': self.attachment_mimetype,
            'status': self.status,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'review_notes': self.review_notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_employee and self.employee:
            data['employee'] = {
                'id': self.employee.id,
                'full_name': self.employee.full_name,
                'dni': self.employee.dni,
                'job_position': self.employee.job_position.name if self.employee.job_position else None
            }
        
        if include_reviewer and self.reviewed_by:
            data['reviewed_by'] = {
                'id': self.reviewed_by.id,
                'email': self.reviewed_by.email,
                'role': self.reviewed_by.role
            }
        
        return data
