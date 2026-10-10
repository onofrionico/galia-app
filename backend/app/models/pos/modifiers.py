from datetime import datetime

from app.extensions import db


class ModifierGroup(db.Model):
    __tablename__ = 'modifier_groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    min_select = db.Column(db.Integer, nullable=False, default=0)
    max_select = db.Column(db.Integer, nullable=False, default=1)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    options = db.relationship('ModifierOption', back_populates='group',
                              order_by='[ModifierOption.position, ModifierOption.id]')

    def to_dict(self, include_inactive=False):
        return {
            'id': self.id,
            'name': self.name,
            'min_select': self.min_select,
            'max_select': self.max_select,
            'is_active': self.is_active,
            'options': [o.to_dict() for o in self.options if include_inactive or o.is_active],
        }


class ModifierOption(db.Model):
    __tablename__ = 'modifier_options'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('modifier_groups.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    price_delta = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    supply_id = db.Column(db.Integer, db.ForeignKey('supplies.id'), nullable=True)
    supply_quantity = db.Column(db.Numeric(10, 4), nullable=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    group = db.relationship('ModifierGroup', back_populates='options')
    supply = db.relationship('Supply')

    def to_dict(self):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'name': self.name,
            'price_delta': float(self.price_delta),
            'supply_id': self.supply_id,
            'supply_name': self.supply.name if self.supply else None,
            'supply_quantity': float(self.supply_quantity) if self.supply_quantity is not None else None,
            'position': self.position,
            'is_active': self.is_active,
        }


class ProductModifierGroup(db.Model):
    __tablename__ = 'product_modifier_groups'

    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('modifier_groups.id'), primary_key=True)
    position = db.Column(db.Integer, nullable=False, default=0)

    group = db.relationship('ModifierGroup')
