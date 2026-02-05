from app.extensions import db
from datetime import datetime

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # schedule_change, shift_added, shift_removed, etc.
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    related_schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=True)
    related_shift_id = db.Column(db.Integer, db.ForeignKey('shifts.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    user = db.relationship('User', backref='notifications')
    schedule = db.relationship('Schedule', backref='notifications')
    shift = db.relationship('Shift', backref='notifications')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'is_read': self.is_read,
            'related_schedule_id': self.related_schedule_id,
            'related_shift_id': self.related_shift_id,
            'created_at': self.created_at.isoformat()
        }

class ScheduleChangeLog(db.Model):
    __tablename__ = 'schedule_change_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=False)
    shift_id = db.Column(db.Integer, db.ForeignKey('shifts.id'), nullable=True)
    change_type = db.Column(db.String(50), nullable=False)  # shift_added, shift_modified, shift_deleted
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    affected_employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    old_data = db.Column(db.JSON, nullable=True)
    new_data = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    schedule = db.relationship('Schedule', backref='change_logs')
    shift = db.relationship('Shift', backref='change_logs')
    changed_by_user = db.relationship('User', backref='schedule_changes')
    affected_employee = db.relationship('Employee', backref='schedule_changes')
    
    def to_dict(self):
        return {
            'id': self.id,
            'schedule_id': self.schedule_id,
            'shift_id': self.shift_id,
            'change_type': self.change_type,
            'changed_by': self.changed_by,
            'affected_employee_id': self.affected_employee_id,
            'old_data': self.old_data,
            'new_data': self.new_data,
            'created_at': self.created_at.isoformat()
        }
