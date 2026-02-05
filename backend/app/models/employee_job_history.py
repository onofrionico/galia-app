from datetime import datetime
from app.extensions import db

class EmployeeJobHistory(db.Model):
    __tablename__ = 'employee_job_history'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    job_position_id = db.Column(db.Integer, db.ForeignKey('job_positions.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    employee = db.relationship('Employee', back_populates='job_history')
    job_position = db.relationship('JobPosition', back_populates='job_history')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'job_position': self.job_position.to_dict() if self.job_position else None,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'is_current': self.end_date is None
        }
