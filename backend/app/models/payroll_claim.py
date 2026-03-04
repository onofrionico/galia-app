from datetime import datetime
from app.extensions import db

class PayrollClaim(db.Model):
    __tablename__ = 'payroll_claims'
    
    id = db.Column(db.Integer, primary_key=True)
    payroll_id = db.Column(db.Integer, db.ForeignKey('payrolls.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    claim_reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    admin_response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    payroll = db.relationship('Payroll', backref='claims')
    employee = db.relationship('Employee', backref='payroll_claims')
    creator = db.relationship('User', foreign_keys=[created_by], backref='claims_created')
    resolver = db.relationship('User', foreign_keys=[resolved_by], backref='claims_resolved')
    
    __table_args__ = (
        db.Index('idx_claim_status', 'status'),
        db.Index('idx_claim_payroll', 'payroll_id'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'payroll_id': self.payroll_id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.full_name if self.employee else None,
            'claim_reason': self.claim_reason,
            'status': self.status,
            'admin_response': self.admin_response,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'payroll': {
                'month': self.payroll.month,
                'year': self.payroll.year,
                'gross_salary': float(self.payroll.gross_salary),
                'hours_worked': float(self.payroll.hours_worked)
            } if self.payroll else None
        }
