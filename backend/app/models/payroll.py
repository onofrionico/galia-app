from datetime import datetime
from app.extensions import db

class Payroll(db.Model):
    __tablename__ = 'payrolls'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    hours_worked = db.Column(db.Numeric(10, 2), nullable=False)
    hourly_rate = db.Column(db.Numeric(10, 2), nullable=False)
    gross_salary = db.Column(db.Numeric(10, 2), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    generator = db.relationship('User', backref='payrolls_generated')
    
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'month', 'year', name='unique_employee_month_year'),
        db.Index('idx_payroll_period', 'year', 'month'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.full_name if self.employee else None,
            'month': self.month,
            'year': self.year,
            'hours_worked': float(self.hours_worked),
            'hourly_rate': float(self.hourly_rate),
            'gross_salary': float(self.gross_salary),
            'generated_at': self.generated_at.isoformat()
        }
