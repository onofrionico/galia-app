"""Fábricas compartidas por los tests de fidelización."""
from datetime import datetime

from app.extensions import db
from app.models.loyalty import Customer, LoyaltyMovement, Reward
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401

_seq = {'n': 0}


def make_customer(first='Lucía', last='Pérez', email='lu@test.com', phone=None, google_sub=None):
    _seq['n'] += 1
    customer = Customer(first_name=first, last_name=last, email=email, phone=phone,
                        google_sub=google_sub or f'sub-{_seq["n"]}-{email}', terms_accepted_at=datetime.utcnow())
    db.session.add(customer)
    db.session.commit()
    return customer


def make_reward(variant, cost, name=None):
    reward = Reward(name=name or variant.product.name, product_variant_id=variant.id, cost=cost, is_active=True)
    db.session.add(reward)
    db.session.commit()
    return reward


def balance_of(customer):
    return sum(m.amount for m in LoyaltyMovement.query.filter_by(customer_id=customer.id).all())
