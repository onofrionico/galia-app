from app.extensions import db
from datetime import datetime
from decimal import Decimal


class Supply(db.Model):
    __tablename__ = 'supplies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    unit = db.Column(db.String(50), nullable=False)
    stock_quantity = db.Column(db.Numeric(10, 3), default=0)
    min_stock = db.Column(db.Numeric(10, 3), default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    prices = db.relationship('SupplyPrice', cascade='all, delete-orphan', backref='supply')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'unit': self.unit,
            'stock_quantity': float(self.stock_quantity) if self.stock_quantity is not None else 0.0,
            'min_stock': float(self.min_stock) if self.min_stock is not None else 0.0,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class SupplyPrice(db.Model):
    __tablename__ = 'supply_prices'

    id = db.Column(db.Integer, primary_key=True)
    supply_id = db.Column(db.Integer, db.ForeignKey('supplies.id'), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    recorded_at = db.Column(db.Date, nullable=False)
    supplier = db.Column(db.String(255))
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'supply_id': self.supply_id,
            'price': float(self.price) if self.price is not None else 0.0,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'supplier': self.supplier,
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
