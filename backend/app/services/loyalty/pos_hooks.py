"""Fidelización dentro del POS: asociar el cliente a una venta y canjear premios."""
from decimal import Decimal

from app.extensions import db
from app.models import ProductVariant
from app.models.loyalty import Customer, Reward
from app.models.pos import ACTIVE_SALE_STATUSES
from app.services.loyalty import wallet
from app.services.loyalty.errors import LoyaltyError
from app.services.pos import audit, sale_service
from app.services.pos.common import load_sale, parse_id, recalc, require_status


def _active_redemptions(sale):
    return [i for i in sale.items if i.is_redemption and i.status != 'cancelled']


def set_customer(user, sale_id, customer_id):
    sale = load_sale(sale_id)
    require_status(sale, ACTIVE_SALE_STATUSES, 'Solo se asocia un cliente a una venta abierta o en cobro')
    customer = None
    if customer_id is not None:
        customer = db.session.get(Customer, parse_id(customer_id, 'El cliente'))
        if customer is None:
            raise LoyaltyError('El cliente no existe', 404)
    new_id = customer.id if customer else None
    if new_id != sale.customer_id and _active_redemptions(sale):
        raise LoyaltyError('Anulá los canjes antes de cambiar el cliente')
    sale.customer_id = new_id
    if customer and not sale.customer_name:
        sale.customer_name = customer.full_name[:100]
    audit.record(sale, user, 'customer_set', customer_id=new_id)
    db.session.commit()
    return sale


def add_redemption(user, sale_id, reward_id, modifier_option_ids):
    sale = load_sale(sale_id)
    require_status(sale, ('open',), 'Solo se canjea en una venta abierta')
    if not sale.customer_id:
        raise LoyaltyError('Asociá un cliente a la venta antes de canjear')
    if sale.is_practice:
        raise LoyaltyError('No se canjea en una venta de práctica')
    reward = db.session.get(Reward, parse_id(reward_id, 'El premio'))
    if reward is None or not reward.is_active:
        raise LoyaltyError('El premio no está disponible', 404)
    variant = db.session.get(ProductVariant, reward.product_variant_id)
    if variant is None or not variant.is_active or not variant.product.is_active:
        raise LoyaltyError('El producto del premio no está disponible')
    options = sale_service._validate_modifiers(variant.product_id, modifier_option_ids)
    item = sale_service.build_item(user, variant, Decimal('1'), options, free=True, reward_id=reward.id)
    sale.items.append(item)
    movement = wallet.redeem(sale, item, reward, user)
    recalc(sale)
    audit.record(sale, user, 'redemption_added', item=item, reward_id=reward.id, cost=reward.cost,
                 pesos_value=str(movement.pesos_value), modifiers=[o.name for o in options])
    db.session.commit()
    return sale
