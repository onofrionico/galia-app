"""Ventas por producto, un mes contra otro (ítems de Fudo y del POS en `sale_items`).

Monto = total de la línea (cantidad × precio), sin descontar los descuentos de la venta.
"""
import calendar
from datetime import date
from decimal import Decimal

from sqlalchemy import func

from app.extensions import db
from app.models import ProductVariant, Sale, SaleItem

ZERO_Q, ZERO_A = Decimal('0'), Decimal('0')


def _month_end(month):
    return month.replace(day=calendar.monthrange(month.year, month.month)[1])


def _values(quantity=ZERO_Q, amount=ZERO_A):
    return {'quantity': f'{Decimal(quantity):.3f}', 'amount': f'{Decimal(amount):.2f}'}


def _rows(month):
    """(producto, nombre, variante, categoría, día, cantidad, monto, id del último ítem) agregados del mes."""
    return (db.session.query(
        ProductVariant.product_id, SaleItem.product_name, SaleItem.variant_name, SaleItem.category_name,
        Sale.fecha, func.sum(SaleItem.quantity), func.sum(SaleItem.total), func.max(SaleItem.id))
        .join(Sale, SaleItem.sale_id == Sale.id)
        .outerjoin(ProductVariant, SaleItem.product_variant_id == ProductVariant.id)
        .filter(Sale.estado == 'Cerrada', Sale.fecha >= month, Sale.fecha <= _month_end(month))
        .group_by(ProductVariant.product_id, SaleItem.product_name, SaleItem.variant_name, SaleItem.category_name,
                  Sale.fecha)
        .all())


def _key(product_id, product_name):
    return f'p:{product_id}' if product_id is not None else f'n:{product_name}'


def compare(month_a, month_b):
    months = {'a': month_a.replace(day=1), 'b': month_b.replace(day=1)}
    products = {}
    latest = {}
    totals = {'a': [ZERO_Q, ZERO_A], 'b': [ZERO_Q, ZERO_A]}
    for side, month in months.items():
        for product_id, name, variant, category, _day, quantity, amount, last_id in _rows(month):
            key = _key(product_id, name)
            entry = products.setdefault(key, {'key': key, 'name': name, 'category': category,
                                              'sums': {'a': [ZERO_Q, ZERO_A], 'b': [ZERO_Q, ZERO_A]},
                                              'variants': {}})
            if last_id > latest.get(key, 0):  # nombre y categoría del ítem más reciente
                latest[key] = last_id
                entry['name'], entry['category'] = name, category
            variant_name = variant or name
            variant_sums = entry['variants'].setdefault(variant_name, {'a': [ZERO_Q, ZERO_A], 'b': [ZERO_Q, ZERO_A]})
            for target in (entry['sums'][side], variant_sums[side], totals[side]):
                target[0] += quantity or ZERO_Q
                target[1] += amount or ZERO_A
    result = []
    for entry in products.values():
        result.append({
            'key': entry['key'], 'name': entry['name'], 'category': entry['category'],
            'a': _values(*entry['sums']['a']), 'b': _values(*entry['sums']['b']),
            'variants': [{'name': name, 'a': _values(*sums['a']), 'b': _values(*sums['b'])}
                         for name, sums in sorted(entry['variants'].items())],
        })
    result.sort(key=lambda p: (-Decimal(p['b']['amount']), p['name']))
    return {'months': [months['a'].strftime('%Y-%m'), months['b'].strftime('%Y-%m')], 'products': result,
            'totals': {'a': _values(*totals['a']), 'b': _values(*totals['b'])}}


def daily(key, month_a, month_b):
    months = {'a': month_a.replace(day=1), 'b': month_b.replace(day=1)}
    by_day = {'a': {}, 'b': {}}
    for side, month in months.items():
        for product_id, name, _variant, _category, day, quantity, amount, _last in _rows(month):
            if _key(product_id, name) != key:
                continue
            sums = by_day[side].setdefault(day.day, [ZERO_Q, ZERO_A])
            sums[0] += quantity or ZERO_Q
            sums[1] += amount or ZERO_A
    lengths = {side: calendar.monthrange(m.year, m.month)[1] for side, m in months.items()}
    days = []
    for number in range(1, 32):
        days.append({'day': number, **{
            side: (_values(*by_day[side].get(number, (ZERO_Q, ZERO_A))) if number <= lengths[side] else None)
            for side in ('a', 'b')}})
    return {'days': days}


def parse_month(value):
    """'YYYY-MM' → date (día 1). ValueError si no es válido."""
    if not isinstance(value, str) or len(value) != 7:
        raise ValueError('Mes inválido, usá YYYY-MM')
    return date.fromisoformat(f'{value}-01')
