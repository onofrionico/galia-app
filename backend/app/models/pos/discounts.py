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
