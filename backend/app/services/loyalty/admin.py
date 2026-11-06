"""Administración de fidelización. Cada cambio queda en loyalty_change_log y hace commit."""
from datetime import datetime

from app.extensions import db
from app.models import ProductVariant
from app.models.loyalty import Customer, LoyaltyChangeLog, LoyaltySettings, Reward, new_qr_token
from app.services.loyalty.errors import LoyaltyError


def _log(user, entity, entity_id, field, old, new, reason=None):
    db.session.add(LoyaltyChangeLog(entity=entity, entity_id=entity_id, field=field,
                                    old_value=None if old is None else str(old),
                                    new_value=None if new is None else str(new), reason=reason, user_id=user.id))


def _int(value, label, minimum, maximum=None):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise LoyaltyError(f'{label} tiene que ser un número entero')
    if isinstance(value, bool) or number < minimum or (maximum is not None and number > maximum):
        rango = f'entre {minimum} y {maximum}' if maximum is not None else f'mayor o igual a {minimum}'
        raise LoyaltyError(f'{label} tiene que ser {rango}')
    return number


def set_variant_cafecitos(user, variant_ids, cafecitos):
    cafecitos = _int(cafecitos, 'Los cafecitos', 0, 1000)
    if not isinstance(variant_ids, list) or not variant_ids:
        raise LoyaltyError('Elegí al menos una variante')
    variants = ProductVariant.query.filter(ProductVariant.id.in_([int(v) for v in variant_ids])).all()
    if len(variants) != len(set(variant_ids)):
        raise LoyaltyError('Alguna variante no existe', 404)
    for variant in variants:
        if variant.cafecitos != cafecitos:
            _log(user, 'variant', variant.id, 'cafecitos', variant.cafecitos, cafecitos)
            variant.cafecitos = cafecitos
    db.session.commit()
    return variants


def _reward_fields(data, partial):
    fields = {}
    if 'name' in data or not partial:
        name = (data.get('name') or '').strip()
        if not name:
            raise LoyaltyError('El premio necesita un nombre')
        fields['name'] = name[:100]
    if 'product_variant_id' in data or not partial:
        variant = db.session.get(ProductVariant, data.get('product_variant_id') or 0)
        if variant is None:
            raise LoyaltyError('Elegí el producto que entrega el premio')
        fields['product_variant_id'] = variant.id
    if 'cost' in data or not partial:
        fields['cost'] = _int(data.get('cost'), 'El costo', 1, 100000)
    if 'is_active' in data:
        fields['is_active'] = bool(data.get('is_active'))
    if 'position' in data:
        fields['position'] = _int(data.get('position'), 'La posición', 0)
    return fields


def create_reward(user, data):
    reward = Reward(**_reward_fields(data or {}, partial=False))
    db.session.add(reward)
    db.session.flush()
    _log(user, 'reward', reward.id, 'created', None, reward.name)
    db.session.commit()
    return reward


def update_reward(user, reward_id, data):
    reward = db.session.get(Reward, reward_id)
    if reward is None:
        raise LoyaltyError('El premio no existe', 404)
    for field, value in _reward_fields(data or {}, partial=True).items():
        if getattr(reward, field) != value:
            _log(user, 'reward', reward.id, field, getattr(reward, field), value)
            setattr(reward, field, value)
    db.session.commit()
    return reward


def update_settings(user, active_days):
    active_days = _int(active_days, 'El período de activos', 1, 365)
    settings = LoyaltySettings.get()
    if settings.active_days != active_days:
        _log(user, 'settings', settings.id, 'active_days', settings.active_days, active_days)
        settings.active_days = active_days
        settings.updated_at = datetime.utcnow()
        settings.updated_by = user.id
    db.session.commit()
    return settings


def regenerate_qr(user, customer_id):
    customer = db.session.get(Customer, customer_id)
    if customer is None:
        raise LoyaltyError('El cliente no existe', 404)
    customer.qr_token = new_qr_token()
    _log(user, 'customer', customer.id, 'qr_token', 'anterior', 'nuevo')
    db.session.commit()
    return customer
