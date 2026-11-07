"""Fidelización: clientes, premios, libro de movimientos de cafecitos, configuración e historial."""
import secrets
import unicodedata
from datetime import datetime

from sqlalchemy import event

from app.extensions import db

MOVEMENT_KINDS = ('earn', 'earn_reversal', 'redeem', 'redeem_reversal', 'adjustment')


def normalize_search(text):
    """Minúsculas y sin acentos, para buscar 'lucia' y encontrar 'Lucía'."""
    decomposed = unicodedata.normalize('NFKD', text or '')
    return ''.join(c for c in decomposed if not unicodedata.combining(c)).lower().strip()


def new_qr_token():
    return secrets.token_urlsafe(24)


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    google_sub = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), nullable=True, index=True)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(30), nullable=True, index=True)
    search_text = db.Column(db.String(600), nullable=False, default='', index=True)
    qr_token = db.Column(db.String(64), unique=True, nullable=False, default=new_qr_token)
    terms_accepted_at = db.Column(db.DateTime, nullable=False)
    promo_opt_in_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def full_name(self):
        return ' '.join(p for p in (self.first_name, self.last_name) if p) or (self.email or '')

    def refresh_search_text(self):
        parts = [self.first_name, self.last_name, self.email, self.phone]
        self.search_text = normalize_search(' '.join(p for p in parts if p))


@event.listens_for(Customer, 'before_insert')
@event.listens_for(Customer, 'before_update')
def _customer_search_text(_mapper, _connection, target):
    target.refresh_search_text()
    if not target.qr_token:
        target.qr_token = new_qr_token()


class Reward(db.Model):
    __tablename__ = 'loyalty_rewards'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    product_variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=False)
    cost = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    variant = db.relationship('ProductVariant')


class LoyaltyMovement(db.Model):
    __tablename__ = 'loyalty_movements'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False, index=True)
    kind = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    pos_sale_id = db.Column(db.Integer, db.ForeignKey('pos_sales.id'), nullable=True, index=True)
    pos_sale_item_id = db.Column(db.Integer, db.ForeignKey('pos_sale_items.id'), nullable=True, index=True)
    reward_id = db.Column(db.Integer, db.ForeignKey('loyalty_rewards.id'), nullable=True)
    reward_cost = db.Column(db.Integer, nullable=True)
    pesos_value = db.Column(db.Numeric(12, 2), nullable=True)
    reversal_of_id = db.Column(db.Integer, db.ForeignKey('loyalty_movements.id'), nullable=True, index=True)
    reason = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    customer = db.relationship('Customer')
    reward = db.relationship('Reward')
    pos_sale_item = db.relationship('PosSaleItem')


class LoyaltySettings(db.Model):
    __tablename__ = 'loyalty_settings'

    id = db.Column(db.Integer, primary_key=True)
    active_days = db.Column(db.Integer, nullable=False, default=30)
    updated_at = db.Column(db.DateTime, nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    @classmethod
    def get(cls):
        row = cls.query.order_by(cls.id).first()
        if row is None:
            row = cls(active_days=30)
            db.session.add(row)
            db.session.commit()
        return row


class LoyaltyChangeLog(db.Model):
    __tablename__ = 'loyalty_change_log'

    id = db.Column(db.Integer, primary_key=True)
    entity = db.Column(db.String(30), nullable=False, index=True)
    entity_id = db.Column(db.Integer, nullable=True)
    field = db.Column(db.String(50), nullable=True)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    reason = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = db.relationship('User')
