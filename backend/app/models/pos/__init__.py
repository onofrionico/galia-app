from app.models.pos.floor import PosTable, Salon
from app.models.pos.modifiers import ModifierGroup, ModifierOption, ProductModifierGroup
from app.models.pos.payments import PAYMENT_KINDS, PaymentMethod
from app.models.pos.discounts import DISCOUNT_KINDS, DISCOUNT_SCOPES, DiscountTemplate

__all__ = [
    'Salon', 'PosTable', 'ModifierGroup', 'ModifierOption', 'ProductModifierGroup',
    'PaymentMethod', 'PAYMENT_KINDS', 'DiscountTemplate', 'DISCOUNT_KINDS', 'DISCOUNT_SCOPES',
]
