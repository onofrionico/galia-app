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
