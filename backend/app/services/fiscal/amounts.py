"""Montos de una factura: qué pagos cubre, cuánto se factura y con qué renglones. Funciones puras."""
from decimal import Decimal

from app.services.pos.pricing import ZERO, money


def _qty(value):
    value = Decimal(value)
    return str(int(value)) if value == value.to_integral_value() else format(value.normalize(), 'f')


def invoiceable_payments(sale, external_method_ids):
    """Pagos activos cuyo medio no factura otro sistema."""
    return [p for p in sale.payments
            if p.cancelled_at is None and p.payment_method_id not in external_method_ids]


def invoiceable_amount(sale, external_method_ids):
    return money(sum((p.amount for p in invoiceable_payments(sale, external_method_ids)), ZERO))


def _line(qty, description, amount):
    qty = Decimal(qty)
    unit = money(Decimal(amount) / qty) if qty else money(amount)
    return {'qty': _qty(qty), 'description': description, 'unit_price': f'{unit:.2f}',
            'amount': f'{money(amount):.2f}'}


def _effective_amounts(sale):
    """Importe de cada ítem confirmado con sus descuentos de ítem y su parte de los descuentos de venta.

    La suma da exactamente sale.total: el redondeo del reparto queda en el último renglón.
    """
    items = [i for i in sale.items if i.status == 'confirmed']
    active = [d for d in sale.discounts if d.cancelled_at is None]
    effective = [money(item.line_total - sum((d.amount for d in active if d.item_id == item.id), ZERO))
                 for item in items]
    sale_disc = money(sum((d.amount for d in active if d.item_id is None), ZERO))
    base = sum(effective, ZERO)
    amounts = []
    for index, value in enumerate(effective):
        if index == len(effective) - 1:
            amounts.append(money(Decimal(sale.total) - sum(amounts, ZERO)))
        else:
            share = money(sale_disc * value / base) if base else ZERO
            amounts.append(money(value - share))
    return list(zip(items, amounts))


def build_lines(sale, amount, describe):
    """('items', renglones) si se factura el total de la venta; ('generic', [Consumo – Venta #N]) si es parcial."""
    amount = money(amount)
    if amount == money(sale.total) and any(i.status == 'confirmed' for i in sale.items):
        return 'items', [_line(item.quantity, describe(item), value) for item, value in _effective_amounts(sale)]
    return 'generic', [_line(1, f'Consumo – Venta #{sale.number}', amount)]


def split_iva(total, rate, discriminated):
    """(neto, IVA). Sin discriminar (Factura C): todo es neto."""
    total = money(total)
    if not discriminated:
        return total, ZERO
    net = money(total / (1 + Decimal(rate) / 100))
    return net, money(total - net)
