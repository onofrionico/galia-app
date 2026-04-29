from datetime import datetime
from app.extensions import db

class Mesa(db.Model):
    __tablename__ = 'mesas'

    id = db.Column(db.Integer, primary_key=True)
    salon_id = db.Column(db.Integer, db.ForeignKey('salones.id'), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    capacity = db.Column(db.Integer, nullable=True)
    pos_x = db.Column(db.Float, nullable=False, default=10.0)
    pos_y = db.Column(db.Float, nullable=False, default=10.0)
    width = db.Column(db.Float, nullable=False, default=10.0)
    height = db.Column(db.Float, nullable=False, default=10.0)
    status = db.Column(db.String(20), nullable=False, default='libre')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'salon_id': self.salon_id,
            'number': self.number,
            'name': self.name,
            'capacity': self.capacity,
            'pos_x': self.pos_x,
            'pos_y': self.pos_y,
            'width': self.width,
            'height': self.height,
            'status': self.status,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
