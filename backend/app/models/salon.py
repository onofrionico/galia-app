from app.extensions import db
from datetime import datetime

class Salon(db.Model):
    __tablename__ = 'salons'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    mesas = db.relationship('Mesa', backref='salon', lazy=True, cascade='all, delete-orphan')

    def to_dict(self, include_mesas=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        if include_mesas:
            data['mesas'] = [m.to_dict() for m in self.mesas]
        return data


class Mesa(db.Model):
    __tablename__ = 'mesas'

    id = db.Column(db.Integer, primary_key=True)
    salon_id = db.Column(db.Integer, db.ForeignKey('salons.id'), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100))
    capacity = db.Column(db.Integer, default=4)
    pos_x = db.Column(db.Float, default=0)
    pos_y = db.Column(db.Float, default=0)
    width = db.Column(db.Float, default=10)
    height = db.Column(db.Float, default=10)
    status = db.Column(db.String(50), default='libre')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sales = db.relationship('Sale', backref='mesa', lazy=True)

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
            'updated_at': self.updated_at.isoformat()
        }
