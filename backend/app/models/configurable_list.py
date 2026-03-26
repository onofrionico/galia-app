from datetime import datetime
from app.extensions import db

class ConfigurableList(db.Model):
    __tablename__ = 'configurable_lists'
    
    id = db.Column(db.Integer, primary_key=True)
    list_type = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(200), nullable=False)
    display_order = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    created_by = db.relationship('User', foreign_keys=[created_by_user_id])
    
    __table_args__ = (
        db.UniqueConstraint('list_type', 'value', name='uq_list_type_value'),
        db.Index('idx_configurable_lists_type', 'list_type'),
        db.Index('idx_configurable_lists_is_active', 'is_active'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'list_type': self.list_type,
            'value': self.value,
            'display_order': self.display_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by_user_id': self.created_by_user_id
        }
    
    @staticmethod
    def get_active_values(list_type):
        """Get all active values for a specific list type"""
        items = ConfigurableList.query.filter_by(
            list_type=list_type,
            is_active=True
        ).order_by(ConfigurableList.display_order, ConfigurableList.value).all()
        
        return [item.value for item in items]
    
    @staticmethod
    def get_all_by_type(list_type):
        """Get all items (active and inactive) for a specific list type"""
        return ConfigurableList.query.filter_by(
            list_type=list_type
        ).order_by(ConfigurableList.display_order, ConfigurableList.value).all()
    
    def __repr__(self):
        return f'<ConfigurableList {self.list_type}: {self.value}>'
