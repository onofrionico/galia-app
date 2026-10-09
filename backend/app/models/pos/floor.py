from datetime import datetime

from app.extensions import db


class Salon(db.Model):
    __tablename__ = 'salons'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    tables = db.relationship('PosTable', back_populates='salon', order_by='PosTable.number')

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'position': self.position, 'is_active': self.is_active}


class PosTable(db.Model):
    __tablename__ = 'pos_tables'
    __table_args__ = (db.UniqueConstraint('salon_id', 'number', name='uq_pos_tables_salon_number'),)

    id = db.Column(db.Integer, primary_key=True)
    salon_id = db.Column(db.Integer, db.ForeignKey('salons.id'), nullable=False, index=True)
    number = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(50), nullable=True)
    capacity = db.Column(db.Integer, nullable=True)
    pos_x = db.Column(db.Float, nullable=False, default=10.0)
    pos_y = db.Column(db.Float, nullable=False, default=10.0)
    width = db.Column(db.Float, nullable=False, default=10.0)
    height = db.Column(db.Float, nullable=False, default=10.0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    salon = db.relationship('Salon', back_populates='tables')

    @property
    def label(self):
        return self.name or f'Mesa {self.number}'

    def to_dict(self):
        return {
            'id': self.id,
            'salon_id': self.salon_id,
            'number': self.number,
            'name': self.name,
            'label': self.label,
            'capacity': self.capacity,
            'pos_x': self.pos_x,
            'pos_y': self.pos_y,
            'width': self.width,
            'height': self.height,
            'is_active': self.is_active,
        }
