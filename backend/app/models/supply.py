from datetime import datetime
from app.extensions import db

class Supply(db.Model):
    __tablename__ = 'supplies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    unit = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    prices = db.relationship('SupplyPrice', backref='supply', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'unit': self.unit,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }

class SupplyPrice(db.Model):
    __tablename__ = 'supply_prices'
    
    id = db.Column(db.Integer, primary_key=True)
    supply_id = db.Column(db.Integer, db.ForeignKey('supplies.id'), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    recorded_at = db.Column(db.Date, nullable=False, index=True)
    supplier = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    creator = db.relationship('User', backref='supply_prices_created')
    
    def to_dict(self):
        return {
            'id': self.id,
            'supply_id': self.supply_id,
            'supply_name': self.supply.name if self.supply else None,
            'price': float(self.price),
            'recorded_at': self.recorded_at.isoformat(),
            'supplier': self.supplier,
            'notes': self.notes
        }
