from datetime import datetime
from app.extensions import db

class TimeTracking(db.Model):
    __tablename__ = 'time_tracking'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    tracking_date = db.Column(db.Date, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    __table_args__ = (
        db.Index('idx_time_tracking_employee_date', 'employee_id', 'tracking_date'),
        db.UniqueConstraint('employee_id', 'tracking_date', name='uq_employee_tracking_date'),
    )
    
    employee = db.relationship('Employee', backref='time_tracking_records')
    
    def to_dict(self):
        total_hours = 0
        total_minutes = 0
        
        for block in self.work_blocks:
            start = block.start_time
            end = block.end_time
            
            hours = end.hour - start.hour
            minutes = end.minute - start.minute
            
            if minutes < 0:
                hours -= 1
                minutes += 60
            
            total_hours += hours
            total_minutes += minutes
        
        total_hours += total_minutes // 60
        total_minutes = total_minutes % 60
        
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'tracking_date': self.tracking_date.isoformat(),
            'work_blocks': [block.to_dict() for block in self.work_blocks],
            'total_hours': total_hours,
            'total_minutes': total_minutes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
