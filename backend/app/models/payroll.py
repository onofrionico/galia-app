from datetime import datetime
from app.extensions import db

class Payroll(db.Model):
    __tablename__ = 'payrolls'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    hours_worked = db.Column(db.Numeric(10, 2), nullable=False)
    scheduled_hours = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    hourly_rate = db.Column(db.Numeric(10, 2), nullable=False)
    gross_salary = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='draft')
    validated_at = db.Column(db.DateTime)
    validated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    pdf_generated = db.Column(db.Boolean, default=False, nullable=False)
    pdf_path = db.Column(db.Text)
    notes = db.Column(db.Text)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Employee validation fields
    employee_validated_at = db.Column(db.DateTime)
    employee_validated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    generator = db.relationship('User', foreign_keys=[generated_by], backref='payrolls_generated')
    validator = db.relationship('User', foreign_keys=[validated_by], backref='payrolls_validated')
    employee_validator = db.relationship('User', foreign_keys=[employee_validated_by], backref='payrolls_employee_validated')
    
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'month', 'year', name='unique_employee_month_year'),
        db.Index('idx_payroll_period', 'year', 'month'),
        db.Index('idx_payroll_status', 'status'),
    )
    
    def to_dict(self, include_details=False):
        hours_diff = float(self.hours_worked) - float(self.scheduled_hours)
        
        data = {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.full_name if self.employee else None,
            'month': self.month,
            'year': self.year,
            'hours_worked': float(self.hours_worked),
            'scheduled_hours': float(self.scheduled_hours),
            'hours_difference': hours_diff,
            'hourly_rate': float(self.hourly_rate),
            'gross_salary': float(self.gross_salary),
            'status': self.status,
            'validated_at': self.validated_at.isoformat() if self.validated_at else None,
            'validated_by': self.validated_by,
            'employee_validated_at': self.employee_validated_at.isoformat() if self.employee_validated_at else None,
            'employee_validated_by': self.employee_validated_by,
            'pdf_generated': self.pdf_generated,
            'pdf_path': self.pdf_path,
            'notes': self.notes,
            'generated_at': self.generated_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_details and self.employee:
            data['employee_details'] = {
                'dni': self.employee.dni,
                'cuil': self.employee.cuil,
                'job_position': self.employee.job_position.name if self.employee.job_position else None,
                'employment_relationship': self.employee.employment_relationship
            }
        
        return data
