"""Cálculo de totales del POS. Funciones puras: sin base de datos, todo en Decimal."""
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal('0.01')
ZERO = Decimal('0.00')


def to_decimal(value):
    """Decimal exacto: los float pasan por str para no arrastrar error binario."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        return Decimal(str(value))
    return Decimal(value)


def money(value):
    return to_decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def line_total(quantity, unit_price, modifiers_total):
    return money(to_decimal(quantity) * (to_decimal(unit_price) + to_decimal(modifiers_total)))


def discount_amount(kind, value, base, cap):
    """Monto de un descuento: porcentaje sobre `base` o monto fijo, nunca mayor que `cap`."""
    cap = money(max(to_decimal(cap), ZERO))
    raw = to_decimal(base) * to_decimal(value) / Decimal(100) if kind == 'percent' else to_decimal(value)
    return min(money(max(raw, ZERO)), cap)


def split_value(value, part, whole):
    """Parte proporcional de un monto fijo al dividir `part` de `whole` unidades."""
    return money(to_decimal(value) * to_decimal(part) / to_decimal(whole))


@dataclass(frozen=True)
class Line:
    key: object
    total: Decimal


@dataclass(frozen=True)
class Disc:
    key: object
    item_key: object  # None = descuento sobre la venta
    kind: str
    value: Decimal


@dataclass
class Totals:
    subtotal: Decimal
    discount_total: Decimal
    total: Decimal
    amounts: dict = field(default_factory=dict)


def compute(lines, discounts):
    """Totales de una venta.

    lines: renglones activos (pendientes y confirmados). discounts: descuentos activos en orden
    de creación. Primero los de ítem (porcentaje sobre el renglón, tope en lo que le queda),
    después los de venta (porcentaje sobre el subtotal ya descontado por ítems, tope en lo que
    queda). Nada queda negativo.
    """
    line_totals = {line.key: money(line.total) for line in lines}
    subtotal = money(sum(line_totals.values(), ZERO))
    remaining = dict(line_totals)
    amounts = {}
    for disc in discounts:
        if disc.item_key is None:
            continue
        base = line_totals.get(disc.item_key, ZERO)
        cap = remaining.get(disc.item_key, ZERO)
        amount = discount_amount(disc.kind, disc.value, base, cap)
        amounts[disc.key] = amount
        if disc.item_key in remaining:
            remaining[disc.item_key] = cap - amount
    sale_base = money(sum(remaining.values(), ZERO))
    sale_remaining = sale_base
    for disc in discounts:
        if disc.item_key is not None:
            continue
        amount = discount_amount(disc.kind, disc.value, sale_base, sale_remaining)
        amounts[disc.key] = amount
        sale_remaining -= amount
    discount_total = money(sum(amounts.values(), ZERO))
    return Totals(subtotal=subtotal, discount_total=discount_total, total=subtotal - discount_total, amounts=amounts)
