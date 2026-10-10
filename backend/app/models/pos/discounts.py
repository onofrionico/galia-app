from app.extensions import db

DISCOUNT_KINDS = ('percent', 'amount')
DISCOUNT_SCOPES = ('sale', 'item')


class DiscountTemplate(db.Model):
    __tablename__ = 'discount_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    kind = db.Column(db.String(10), nullable=False)
    value = db.Column(db.Numeric(10, 2), nullable=False)
    scope = db.Column(db.String(10), nullable=False)
    restricted = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'kind': self.kind, 'value': float(self.value),
                'scope': self.scope, 'restricted': self.restricted, 'is_active': self.is_active}


class PosDiscount(db.Model):
    __tablename__ = 'pos_discounts'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('pos_sales.id'), nullable=False, index=True)
    item_id = db.Column(db.Integer, db.ForeignKey('pos_sale_items.id'), nullable=True, index=True)
    template_id = db.Column(db.Integer, db.ForeignKey('discount_templates.id'), nullable=True)
    kind = db.Column(db.String(10), nullable=False)
    value = db.Column(db.Numeric(10, 2), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    reason = db.Column(db.String(255), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    cancelled_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)

    sale = db.relationship('PosSale', back_populates='discounts')
    item = db.relationship('PosSaleItem', back_populates='discounts')
    template = db.relationship('DiscountTemplate')

    @property
    def is_active(self):
        return self.cancelled_at is None
