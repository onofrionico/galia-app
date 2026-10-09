from decimal import Decimal

from app.extensions import db

SALE_TYPES = ('salon', 'counter')
SALE_STATUSES = ('open', 'billing', 'closed', 'cancelled')
ACTIVE_SALE_STATUSES = ('open', 'billing')
ITEM_STATUSES = ('pending', 'confirmed', 'cancelled')


class PosSale(db.Model):
    __tablename__ = 'pos_sales'
    __table_args__ = (db.UniqueConstraint('business_date', 'number', name='uq_pos_sales_day_number'),)

    id = db.Column(db.Integer, primary_key=True)
    business_date = db.Column(db.Date, nullable=False)
    number = db.Column(db.Integer, nullable=False)
    sale_type = db.Column(db.String(10), nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey('pos_tables.id'), nullable=True, index=True)
    people = db.Column(db.Integer, nullable=True)
    customer_name = db.Column(db.String(100), nullable=True)
    comment = db.Column(db.String(500), nullable=True)
    waiter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(10), nullable=False, default='open', index=True)
    opened_at = db.Column(db.DateTime, nullable=False, index=True)
    opened_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    billing_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    closed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancelled_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    cancel_reason = db.Column(db.String(255), nullable=True)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    discount_total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    paid_total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    split_from_id = db.Column(db.Integer, db.ForeignKey('pos_sales.id'), nullable=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id', ondelete='SET NULL'), nullable=True)

    table = db.relationship('PosTable')
    waiter = db.relationship('User', foreign_keys=[waiter_id])
    items = db.relationship('PosSaleItem', back_populates='sale', order_by='PosSaleItem.id',
                            cascade='all, delete-orphan')
    discounts = db.relationship('PosDiscount', back_populates='sale', order_by='PosDiscount.id',
                                cascade='all, delete-orphan')
    payments = db.relationship('PosPayment', back_populates='sale', order_by='PosPayment.id',
                               cascade='all, delete-orphan')

    @property
    def balance(self):
        return Decimal(self.total or 0) - Decimal(self.paid_total or 0)


class PosSaleItem(db.Model):
    __tablename__ = 'pos_sale_items'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('pos_sales.id'), nullable=False, index=True)
    product_variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    variant_name = db.Column(db.String(100), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Numeric(10, 3), nullable=False)
    modifiers_total = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    note = db.Column(db.String(255), nullable=True)
    line_total = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(10), nullable=False, default='pending')
    batch = db.Column(db.Integer, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    confirmed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    cancelled_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancel_reason = db.Column(db.String(255), nullable=True)

    sale = db.relationship('PosSale', back_populates='items')
    modifiers = db.relationship('PosSaleItemModifier', back_populates='item', order_by='PosSaleItemModifier.id',
                                cascade='all, delete-orphan')
    discounts = db.relationship('PosDiscount', back_populates='item', order_by='PosDiscount.id',
                               passive_deletes='all')


class PosSaleItemModifier(db.Model):
    __tablename__ = 'pos_sale_item_modifiers'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('pos_sale_items.id'), nullable=False, index=True)
    option_id = db.Column(db.Integer, db.ForeignKey('modifier_options.id'), nullable=False)
    group_name = db.Column(db.String(100), nullable=False)
    option_name = db.Column(db.String(100), nullable=False)
    price_delta = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    supply_id = db.Column(db.Integer, db.ForeignKey('supplies.id'), nullable=True)
    supply_quantity = db.Column(db.Numeric(10, 4), nullable=True)

    item = db.relationship('PosSaleItem', back_populates='modifiers')
