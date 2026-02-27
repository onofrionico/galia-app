from app.extensions import db
from datetime import datetime

class VacationPeriod(db.Model):
    """Períodos de vacaciones de empleados"""
    __tablename__ = 'vacation_periods'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='aprobado', nullable=False)  # solicitado, aprobado, rechazado
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relaciones
    employee = db.relationship('Employee', backref=db.backref('vacation_periods', lazy='dynamic'))
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.full_name if self.employee else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'approved_by': self.approved_by.email if self.approved_by else None
        }
    
    def is_active_on_date(self, check_date):
        """Verifica si el período de vacaciones está activo en una fecha dada"""
        return (self.status == 'aprobado' and 
                self.start_date <= check_date <= self.end_date)
    
    def __repr__(self):
        return f'<VacationPeriod {self.employee.full_name if self.employee else "N/A"} {self.start_date} - {self.end_date}>'
