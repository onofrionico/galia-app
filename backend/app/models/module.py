from datetime import datetime
from app.extensions import db

class Module(db.Model):
    __tablename__ = 'modules'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)  # 'POS', 'Payroll'
    display_name = db.Column(db.String(100), nullable=False)  # 'Caja/POS', 'Nóminas'
    description = db.Column(db.Text)
    icon = db.Column(db.String(20))  # emoji or icon name
    category = db.Column(db.String(50))  # 'Operations', 'Finance', 'HR'
    route = db.Column(db.String(100))  # '/pos', '/payroll'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    role_permissions = db.relationship('RolePermission', backref='module', cascade='all, delete-orphan')
    user_permissions = db.relationship('UserPermission', backref='module', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'icon': self.icon,
            'category': self.category,
            'route': self.route,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }
