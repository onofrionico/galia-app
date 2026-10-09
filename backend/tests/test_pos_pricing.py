from decimal import Decimal as D

from app.services.pos.pricing import Disc, Line, compute, discount_amount, line_total, money, split_value


def test_money_rounds_half_up():
    assert money(D('10.005')) == D('10.01')
    assert money(D('10.004')) == D('10.00')


def test_line_total_includes_modifiers():
    assert line_total(D('2'), D('2000'), D('300')) == D('4600.00')
    assert line_total(D('1.5'), D('1000'), D('0')) == D('1500.00')


def test_discount_amount_percent_and_cap():
    assert discount_amount('percent', D('10'), base=D('1000'), cap=D('1000')) == D('100.00')
    assert discount_amount('amount', D('500'), base=D('300'), cap=D('300')) == D('300.00')
    assert discount_amount('percent', D('50'), base=D('1000'), cap=D('200')) == D('200.00')
    assert discount_amount('amount', D('10'), base=D('0'), cap=D('0')) == D('0.00')


def test_compute_without_discounts():
    totals = compute([Line(1, D('2300')), Line(2, D('900'))], [])
    assert (totals.subtotal, totals.discount_total, totals.total) == (D('3200.00'), D('0.00'), D('3200.00'))


def test_item_discount_then_sale_percent_on_remaining():
    lines = [Line(1, D('2000')), Line(2, D('1000'))]
    discounts = [Disc(10, 1, 'percent', D('50')), Disc(11, None, 'percent', D('10'))]
    totals = compute(lines, discounts)
    assert totals.amounts == {10: D('1000.00'), 11: D('200.00')}
    assert totals.total == D('1800.00')


def test_discounts_never_make_total_negative():
    totals = compute([Line(1, D('500'))], [Disc(1, None, 'amount', D('400')), Disc(2, None, 'amount', D('400'))])
    assert totals.amounts == {1: D('400.00'), 2: D('100.00')}
    assert totals.total == D('0.00')


def test_discount_on_missing_item_is_zero():
    totals = compute([Line(1, D('500'))], [Disc(1, 99, 'amount', D('100'))])
    assert totals.amounts == {1: D('0.00')}
    assert totals.total == D('500.00')


def test_split_value_proportional():
    assert split_value(D('100'), D('1'), D('3')) == D('33.33')
