from datetime import datetime
from app.extensions import db

class WorkBlock(db.Model):
    __tablename__ = 'work_blocks'
    
    id = db.Column(db.Integer, primary_key=True)
    time_tracking_id = db.Column(db.Integer, db.ForeignKey('time_tracking.id'), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    time_tracking = db.relationship('TimeTracking', backref='work_blocks')
    
    def to_dict(self):
        return {
            'id': self.id,
            'start_time': self.start_time.strftime('%H:%M:%S') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M:%S') if self.end_time else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
