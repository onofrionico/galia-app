from datetime import datetime
from app.extensions import db

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(20), nullable=False)
    field_name = db.Column(db.String(100), nullable=True)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip_address = db.Column(db.String(50), nullable=True)
    
    user = db.relationship('User', foreign_keys=[user_id])
    
    __table_args__ = (
        db.Index('idx_audit_logs_entity', 'entity_type', 'entity_id'),
        db.Index('idx_audit_logs_timestamp', 'timestamp'),
        db.Index('idx_audit_logs_user_id', 'user_id'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'action': self.action,
            'field_name': self.field_name,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'ip_address': self.ip_address,
            'user_email': self.user.email if self.user else None
        }
    
    @staticmethod
    def log_change(entity_type, entity_id, action, user_id=None, field_name=None, old_value=None, new_value=None, ip_address=None):
        """Create an audit log entry"""
        log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            field_name=field_name,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            ip_address=ip_address
        )
        db.session.add(log)
        return log
    
    def __repr__(self):
        return f'<AuditLog {self.action} on {self.entity_type}#{self.entity_id}>'
