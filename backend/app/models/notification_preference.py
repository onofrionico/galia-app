# backend/app/models/notification_preference.py
from datetime import datetime
from app.extensions import db

class NotificationPreference(db.Model):
    __tablename__ = 'notification_preferences'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    comanda_enabled = db.Column(db.Boolean, default=True)
    venta_cerrada_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship('User', backref='notification_preferences')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'comanda_enabled': self.comanda_enabled,
            'venta_cerrada_enabled': self.venta_cerrada_enabled,
            'created_at': self.created_at.isoformat(),
        }
