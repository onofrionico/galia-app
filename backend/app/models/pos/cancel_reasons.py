from datetime import datetime

from app.extensions import db


class CancelReason(db.Model):
    """Motivo predefinido para anular ítems, pagos y ventas."""
    __tablename__ = 'cancel_reasons'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'position': self.position, 'is_active': self.is_active}
