from decimal import Decimal
from types import SimpleNamespace as NS

from app.services.fiscal.amounts import build_lines, invoiceable_amount, invoiceable_payments, split_iva

D = Decimal


def _sale(items, discounts=(), payments=(), total=None):
    total = total if total is not None else sum((i.line_total for i in items if i.status != 'cancelled'),
                                                D('0')) - sum((d.amount for d in discounts), D('0'))
    return NS(total=D(total), number=7, items=list(items), discounts=list(discounts), payments=list(payments))


def _item(item_id, qty, line_total, status='confirmed'):
    return NS(id=item_id, status=status, quantity=D(qty), line_total=D(line_total))


def _pay(pay_id, method_id, amount, cancelled=False):
    return NS(id=pay_id, payment_method_id=method_id, amount=D(amount), cancelled_at='x' if cancelled else None)


def describe(item):
    return f'Producto {item.id}'


def test_only_active_payments_of_non_external_methods_count():
    sale = _sale([_item(1, 1, '18000')], payments=[_pay(1, 1, '10000'), _pay(2, 2, '8000'),
                                                   _pay(3, 1, '500', cancelled=True)])
    assert [p.id for p in invoiceable_payments(sale, {2})] == [1]
    assert invoiceable_amount(sale, {2}) == D('10000.00')
    assert invoiceable_amount(sale, {1, 2}) == D('0.00')


def test_full_amount_lists_items_partial_uses_generic_line():
    sale = _sale([_item(1, 2, '6000'), _item(2, 1, '2000'), _item(3, 1, '900', status='cancelled')])
    mode, lines = build_lines(sale, D('8000'), describe)
    assert mode == 'items'
    assert lines == [{'qty': '2', 'description': 'Producto 1', 'unit_price': '3000.00', 'amount': '6000.00'},
                     {'qty': '1', 'description': 'Producto 2', 'unit_price': '2000.00', 'amount': '2000.00'}]
    mode, lines = build_lines(sale, D('5000'), describe)
    assert mode == 'generic'
    assert lines == [{'qty': '1', 'description': 'Consumo – Venta #7', 'unit_price': '5000.00',
                      'amount': '5000.00'}]


def test_item_and_sale_discounts_are_reflected_in_lines():
    items = [_item(1, 1, '1000'), _item(2, 1, '3000')]
    discounts = [NS(item_id=1, amount=D('100'), cancelled_at=None),
                 NS(item_id=None, amount=D('390'), cancelled_at=None),
                 NS(item_id=2, amount=D('999'), cancelled_at='x')]
    sale = _sale(items, discounts[:2])
    sale.discounts = discounts
    assert sale.total == D('3510')
    mode, lines = build_lines(sale, D('3510'), describe)
    assert mode == 'items'
    # 900 y 3000 efectivos; el descuento de venta (390) se reparte 90/300.
    assert [l['amount'] for l in lines] == ['810.00', '2700.00']


def test_items_absorb_rounding_in_last_line():
    items = [_item(1, 3, '1000'), _item(2, 1, '1000'), _item(3, 1, '1000')]
    discounts = [NS(item_id=None, amount=D('100'), cancelled_at=None)]
    sale = _sale(items, discounts)
    mode, lines = build_lines(sale, sale.total, describe)
    assert sum(D(l['amount']) for l in lines) == sale.total == D('2900')
    assert lines[0]['unit_price'] == '322.22'


def test_split_iva():
    assert split_iva(D('121'), D('21'), True) == (D('100.00'), D('21.00'))
    assert split_iva(D('1000'), D('21'), True) == (D('826.45'), D('173.55'))
    assert split_iva(D('1000'), D('21'), False) == (D('1000.00'), D('0.00'))
