from datetime import datetime, date
from app.extensions import db
from app.models.employee_job_history import EmployeeJobHistory

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    dni = db.Column(db.String(8), unique=True, nullable=False, index=True)
    cuil = db.Column(db.String(13), unique=True, nullable=False, index=True)
    birth_date = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    profile_photo_url = db.Column(db.Text)
    employment_relationship = db.Column(db.String(20), nullable=False)
    emergency_contact_name = db.Column(db.String(100), nullable=False)
    emergency_contact_phone = db.Column(db.String(20), nullable=False)
    emergency_contact_relationship = db.Column(db.String(50), nullable=False)
    hire_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='activo', index=True)
    current_job_position_id = db.Column(db.Integer, db.ForeignKey('job_positions.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    job_position = db.relationship('JobPosition', back_populates='employees', foreign_keys=[current_job_position_id])
    job_history = db.relationship('EmployeeJobHistory', back_populates='employee', lazy='dynamic', cascade='all, delete-orphan')
    shifts = db.relationship('Shift', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    sales = db.relationship('Sale', backref='employee', lazy='dynamic')
    payrolls = db.relationship('Payroll', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    updated_by = db.relationship('User', foreign_keys=[updated_by_id])
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
    
    def validate(self):
        errors = []
        
        if not self.dni or not self.dni.isdigit() or len(self.dni) not in [7, 8]:
            errors.append('DNI debe tener 7 u 8 dígitos numéricos')
        
        if not self._validate_cuil():
            errors.append('CUIL inválido')
        
        if self.age < 18:
            errors.append('El empleado debe tener al menos 18 años')
        
        if self.employment_relationship not in ['dependencia', 'monotributo']:
            errors.append('Tipo de relación laboral inválido')
        
        if self.status not in ['activo', 'inactivo', 'suspendido', 'vacaciones', 'licencia']:
            errors.append('Estado inválido')
        
        return errors
    
    def _validate_cuil(self):
        if not self.cuil or len(self.cuil) != 13:
            return False
        
        cuil_clean = self.cuil.replace('-', '')
        if len(cuil_clean) != 11 or not cuil_clean.isdigit():
            return False
        
        multipliers = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        total = sum(int(cuil_clean[i]) * multipliers[i] for i in range(10))
        
        remainder = total % 11
        expected_verifier = 11 - remainder
        
        if expected_verifier == 11:
            expected_verifier = 0
        elif expected_verifier == 10:
            expected_verifier = 9
        
        return int(cuil_clean[10]) == expected_verifier
    
    def to_dict(self, include_sensitive=False, include_history=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'email': self.user.email if self.user else None,
            'phone': self.phone,
            'status': self.status,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
            'profile_photo_url': self.profile_photo_url,
            'job_position': self.job_position.to_dict() if self.job_position else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            data.update({
                'dni': self.dni,
                'cuil': self.cuil,
                'birth_date': self.birth_date.isoformat() if self.birth_date else None,
                'age': self.age if self.birth_date else None,
                'address': self.address,
                'employment_relationship': self.employment_relationship,
                'emergency_contact_name': self.emergency_contact_name,
                'emergency_contact_phone': self.emergency_contact_phone,
                'emergency_contact_relationship': self.emergency_contact_relationship
            })
        
        if include_history:
            job_history_records = EmployeeJobHistory.query.filter_by(employee_id=self.id).order_by(EmployeeJobHistory.start_date.desc()).all()
            data['job_history'] = [h.to_dict() for h in job_history_records]
        
        return data
