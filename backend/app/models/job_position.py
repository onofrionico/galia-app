from datetime import datetime
from app.extensions import db

class JobPosition(db.Model):
    __tablename__ = 'job_positions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    contract_type = db.Column(db.String(20), nullable=False)
    base_salary = db.Column(db.Numeric(10, 2))
    hourly_rate = db.Column(db.Numeric(10, 2))
    standard_hours_per_week = db.Column(db.Integer)
    standard_hours_per_month = db.Column(db.Integer)
    overtime_rate_multiplier = db.Column(db.Numeric(3, 2), default=1.5)
    weekend_rate_multiplier = db.Column(db.Numeric(3, 2), default=1.0)
    holiday_rate_multiplier = db.Column(db.Numeric(3, 2), default=1.0)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    employees = db.relationship('Employee', back_populates='job_position', lazy='dynamic', foreign_keys='[Employee.current_job_position_id]')
    job_history = db.relationship('EmployeeJobHistory', back_populates='job_position', lazy='dynamic')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    
    def validate(self):
        errors = []
        
        if self.contract_type not in ['por_hora', 'part_time', 'full_time']:
            errors.append('Tipo de contrato inválido')
        
        if self.contract_type == 'por_hora' and not self.hourly_rate:
            errors.append('Tarifa horaria es obligatoria para contratos por hora')
        
        if self.contract_type in ['part_time', 'full_time']:
            if not self.base_salary:
                errors.append('Salario base es obligatorio para contratos part-time/full-time')
            if not self.standard_hours_per_week:
                errors.append('Horas semanales estándar son obligatorias')
        
        if self.overtime_rate_multiplier and self.overtime_rate_multiplier < 1.0:
            errors.append('Multiplicador de horas extras debe ser >= 1.0')
        
        if self.weekend_rate_multiplier and self.weekend_rate_multiplier < 1.0:
            errors.append('Multiplicador de fin de semana debe ser >= 1.0')
        
        if self.holiday_rate_multiplier and self.holiday_rate_multiplier < 1.0:
            errors.append('Multiplicador de feriados debe ser >= 1.0')
        
        return errors
    
    def to_dict(self, include_employees=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'contract_type': self.contract_type,
            'base_salary': float(self.base_salary) if self.base_salary else None,
            'hourly_rate': float(self.hourly_rate) if self.hourly_rate else None,
            'standard_hours_per_week': self.standard_hours_per_week,
            'standard_hours_per_month': self.standard_hours_per_month,
            'overtime_rate_multiplier': float(self.overtime_rate_multiplier) if self.overtime_rate_multiplier else None,
            'weekend_rate_multiplier': float(self.weekend_rate_multiplier) if self.weekend_rate_multiplier else None,
            'holiday_rate_multiplier': float(self.holiday_rate_multiplier) if self.holiday_rate_multiplier else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_employees:
            data['employee_count'] = self.employees.filter_by(status='activo').count()
        
        return data
