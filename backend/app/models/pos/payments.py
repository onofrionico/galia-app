from app.extensions import db

PAYMENT_KINDS = ('cash', 'card', 'transfer', 'other')


class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    kind = db.Column(db.String(20), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'kind': self.kind, 'position': self.position,
                'is_active': self.is_active}


class PosPayment(db.Model):
    __tablename__ = 'pos_payments'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('pos_sales.id'), nullable=False, index=True)
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_methods.id'), nullable=False)
    method_name = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    tendered = db.Column(db.Numeric(12, 2), nullable=True)
    change = db.Column(db.Numeric(12, 2), nullable=True)
    client_request_id = db.Column(db.String(64), nullable=True, unique=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    cancelled_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancel_reason = db.Column(db.String(255), nullable=True)

    sale = db.relationship('PosSale', back_populates='payments')

    @property
    def is_active(self):
        return self.cancelled_at is None
