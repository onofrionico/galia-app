"""Stock de los ítems del POS: se descuenta al confirmar y se devuelve al anular."""
from collections import defaultdict
from decimal import Decimal

from app.services.stock_service import move_stock, stock_requirements


def _requirements(items):
    variants = defaultdict(Decimal)
    extra_supplies = defaultdict(Decimal)
    for item in items:
        quantity = Decimal(item.quantity)
        variants[item.product_variant_id] += quantity
        for modifier in item.modifiers:
            if modifier.supply_id and modifier.supply_quantity:
                extra_supplies[modifier.supply_id] += Decimal(modifier.supply_quantity) * quantity
    return stock_requirements(dict(variants), dict(extra_supplies))


def consume(items):
    """Descuenta el stock de ítems recién confirmados. Puede quedar negativo: la venta no se frena."""
    if items:
        variants, supplies = _requirements(items)
        move_stock(variants, supplies, sign=-1, allow_negative=True)


def restore(items):
    """Devuelve el stock de ítems confirmados que se anulan."""
    if items:
        variants, supplies = _requirements(items)
        move_stock(variants, supplies, sign=1)
