from datetime import datetime
from app.extensions import db

class RolePermission(db.Model):
    __tablename__ = 'role_permissions'

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False, index=True)  # 'admin', 'employee', 'supervisor'
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    is_granted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('role', 'module_id', name='uq_role_module'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'module_id': self.module_id,
            'is_granted': self.is_granted,
            'created_at': self.created_at.isoformat()
        }
