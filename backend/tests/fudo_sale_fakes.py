"""Ventas de Fudo de mentira (JSON:API con `included`) para los tests de la importación de la historia."""
from datetime import date


def fudo_category(category_id, name):
    return {'type': 'ProductCategory', 'id': str(category_id), 'attributes': {'name': name}}


def fudo_product(product_id, name, category_id=None):
    product = {'type': 'Product', 'id': str(product_id), 'attributes': {'name': name}}
    if category_id is not None:
        product['relationships'] = {'productCategory': {'data': {'type': 'ProductCategory', 'id': str(category_id)}}}
    return product


def fudo_item(item_id, product_id, quantity, price, canceled=False):
    return {'type': 'Item', 'id': str(item_id),
            'attributes': {'quantity': quantity, 'price': price, 'canceled': canceled},
            'relationships': {'product': {'data': {'type': 'Product', 'id': str(product_id)}}}}


def fudo_sale(sale_id, closed_at, total, state='CLOSED', items=()):
    return {
        'type': 'Sale', 'id': str(sale_id),
        'attributes': {'createdAt': closed_at, 'closedAt': closed_at, 'total': total, 'saleState': state,
                       'saleType': 'EAT-IN'},
        'relationships': {'items': {'data': [{'type': 'Item', 'id': item['id']} for item in items]}},
        '_items': list(items),
    }


def payload(sales, extra_included=()):
    """{'data', 'included'} con los ítems de cada venta y los recursos extra (productos, categorías)."""
    data, included = [], list(extra_included)
    for sale in sales:
        sale = dict(sale)
        included.extend(sale.pop('_items', []))
        data.append(sale)
    return {'data': data, 'included': included}


class FakeSalesClient:
    """`sales_by_month`: {'2026-09': [fudo_sale(...)]}. Las ventas cuyo estado no está en `states` se filtran."""

    def __init__(self, sales_by_month, first=None, included=()):
        self.sales_by_month = sales_by_month
        self.first = first
        self.included = list(included)
        self.requested = []

    def get_all_sales_with_included(self, start_date=None, end_date=None, states=('CLOSED',)):
        month = start_date[:7]
        self.requested.append(month)
        sales = [s for s in self.sales_by_month.get(month, []) if s['attributes']['saleState'] in states]
        return payload(sales, self.included)

    def first_sale_date(self):
        return self.first


def first_of(year, month):
    return date(year, month, 1)
