from datetime import datetime
from app.extensions import db

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    full_name = db.Column(db.String(200), nullable=False)
    hourly_rate = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    hire_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    shifts = db.relationship('Shift', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    sales = db.relationship('Sale', backref='employee', lazy='dynamic')
    payrolls = db.relationship('Payroll', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'full_name': self.full_name,
            'hourly_rate': float(self.hourly_rate),
            'hire_date': self.hire_date.isoformat(),
            'email': self.user.email if self.user else None
        }
