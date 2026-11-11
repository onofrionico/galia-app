"""Wallet de cafecitos: el libro `loyalty_movements` es la única fuente de verdad del saldo.

Ninguna función hace commit salvo `adjust`; las llama el POS dentro de su propia transacción.
"""
import math
from decimal import Decimal

from sqlalchemy import func

from app.extensions import db
from app.models.loyalty import Customer, LoyaltyChangeLog, LoyaltyMovement
from app.services.loyalty.errors import LoyaltyError


def balance(customer_id):
    total = db.session.query(func.coalesce(func.sum(LoyaltyMovement.amount), 0)).filter(
        LoyaltyMovement.customer_id == customer_id).scalar()
    return int(total or 0)


def lock_customer(customer_id):
    """Bloquea la fila del cliente (Postgres) para que dos canjes simultáneos no gasten el mismo saldo."""
    customer = db.session.query(Customer).filter(Customer.id == customer_id).with_for_update().first()
    if customer is None:
        raise LoyaltyError('El cliente no existe', 404)
    return customer


def _earning_items(sale):
    return [i for i in sale.items if i.status != 'cancelled' and not i.is_redemption]


def _item_cafecitos(item):
    per_unit = (item.variant.cafecitos if item.variant is not None else 0) or 0
    return math.floor(Decimal(item.quantity or 0)) * per_unit


def earn_preview(sale):
    return sum(_item_cafecitos(i) for i in _earning_items(sale))


def credit_sale(sale, user):
    if not sale.customer_id or sale.is_practice:
        return 0
    total = 0
    for item in _earning_items(sale):
        if item.status != 'confirmed':
            continue
        amount = _item_cafecitos(item)
        if amount <= 0:
            continue
        db.session.add(LoyaltyMovement(customer_id=sale.customer_id, kind='earn', amount=amount,
                                       pos_sale_id=sale.id, pos_sale_item_id=item.id, user_id=user.id))
        total += amount
    db.session.flush()
    return total


def _unreversed(kind, **filters):
    reversed_ids = db.session.query(LoyaltyMovement.reversal_of_id).filter(
        LoyaltyMovement.reversal_of_id.isnot(None))
    return LoyaltyMovement.query.filter_by(kind=kind, **filters).filter(
        ~LoyaltyMovement.id.in_(reversed_ids)).order_by(LoyaltyMovement.id).all()


def _reverse(movement, kind, user):
    reversal = LoyaltyMovement(customer_id=movement.customer_id, kind=kind, amount=-movement.amount,
                               pos_sale_id=movement.pos_sale_id, pos_sale_item_id=movement.pos_sale_item_id,
                               reward_id=movement.reward_id, reward_cost=movement.reward_cost,
                               pesos_value=movement.pesos_value, reversal_of_id=movement.id,
                               user_id=user.id if user else None)
    db.session.add(reversal)
    return reversal


def reverse_sale_credits(sale, user):
    total = 0
    for earn in _unreversed('earn', pos_sale_id=sale.id):
        total += _reverse(earn, 'earn_reversal', user).amount
    db.session.flush()
    return total


def redeem(sale, item, reward, user):
    lock_customer(sale.customer_id)
    available = balance(sale.customer_id)
    if available < reward.cost:
        raise LoyaltyError(f'Le faltan {reward.cost - available} cafecitos')
    pesos = Decimal(reward.variant.price) + sum((Decimal(m.price_delta or 0) for m in item.modifiers), Decimal('0'))
    movement = LoyaltyMovement(customer_id=sale.customer_id, kind='redeem', amount=-reward.cost,
                               pos_sale_id=sale.id, pos_sale_item=item, reward_id=reward.id,
                               reward_cost=reward.cost, pesos_value=pesos, user_id=user.id)
    db.session.add(movement)
    db.session.flush()
    return movement


def reverse_redemption(item, user):
    if item.id is None:
        return None
    pending = _unreversed('redeem', pos_sale_item_id=item.id)
    if not pending:
        return None
    reversal = _reverse(pending[0], 'redeem_reversal', user)
    db.session.flush()
    return reversal


def adjust(user, customer_id, amount, reason):
    reason = (reason or '').strip()
    if not reason:
        raise LoyaltyError('El ajuste necesita un motivo')
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        raise LoyaltyError('La cantidad tiene que ser un número entero')
    if amount == 0:
        raise LoyaltyError('La cantidad no puede ser cero')
    lock_customer(customer_id)
    before = balance(customer_id)
    after = before + amount
    if after < 0:
        raise LoyaltyError(f'El ajuste dejaría el saldo negativo (tiene {before})')
    movement = LoyaltyMovement(customer_id=customer_id, kind='adjustment', amount=amount, reason=reason[:255],
                               user_id=user.id)
    db.session.add(movement)
    db.session.add(LoyaltyChangeLog(entity='adjustment', entity_id=customer_id, field='balance',
                                    old_value=str(before), new_value=str(after), reason=reason[:255],
                                    user_id=user.id))
    db.session.commit()
    return movement
