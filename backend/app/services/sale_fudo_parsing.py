"""Traduce una venta de Fudo (JSON:API, con `included`) a los campos de `Sale` y sus ítems. Puro: no toca la base.

Nombres según https://api.fu.do/v1alpha1/openapi.yml (listSales); verificar con scripts/inspect_fudo_sales.py.
"""
from datetime import datetime
from decimal import Decimal, InvalidOperation

from app.utils.timezone_utils import business_date, get_current_date_argentina

SALE_FIELDS = ('closedAt', 'comment', 'createdAt', 'people', 'customerName', 'total', 'saleType', 'saleState')
SALE_RELATIONS = ('items', 'waiter', 'table', 'cashRegister', 'payments')
INCLUDE = ('items', 'items.product', 'items.product.productCategory', 'waiter', 'table', 'table.room',
           'cashRegister', 'payments', 'payments.paymentMethod')
# Sin fields[...] Fudo puede devolver recursos sin atributos (pasó en /expenses).
# listSales rechaza con 400 cualquier fields[tipo] fuera de su lista (no acepta item, payment ni paymentMethod).
FIELDS = {
    'sale': SALE_FIELDS + SALE_RELATIONS,
    'product': ('name', 'productCategory'),
    'productCategory': ('name',),
    'user': ('name',),
    'table': ('number', 'room'),
    'room': ('name',),
    'cashRegister': ('name',),
}

STATE_MAP = {'CLOSED': 'Cerrada', 'CANCELED': 'Cancelada', 'CANCELLED': 'Cancelada'}
TYPE_MAP = {'EAT-IN': 'Local', 'TAKEAWAY': 'Para llevar', 'DELIVERY': 'Delivery'}

CENT = Decimal('0.01')


def request_params():
    """Parámetros de include y fields para GET /sales."""
    return {'include': ','.join(INCLUDE), **{f'fields[{k}]': ','.join(v) for k, v in FIELDS.items()}}


def index_included(included):
    """Recursos de `included` (completos, con relaciones) por (type, id)."""
    return {(item.get('type'), str(item.get('id'))): item for item in included or []}


def _rel_data(resource, name):
    return ((resource or {}).get('relationships') or {}).get(name, {}).get('data')


def _related(resource, name, index):
    """Recurso relacionado (de `included`) o None."""
    data = _rel_data(resource, name)
    if not data or isinstance(data, list) or data.get('id') is None:
        return None
    return index.get((data.get('type'), str(data['id'])))


def _related_many(resource, name, index):
    data = _rel_data(resource, name) or []
    found = (index.get((d.get('type'), str(d.get('id')))) for d in data if isinstance(d, dict))
    return [r for r in found if r is not None]


def _attr(resource, name):
    return ((resource or {}).get('attributes') or {}).get(name)


def _text(value, length=None):
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    return value[:length] if length else value


def _decimal(value):
    if value is None or value == '':
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def _datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except ValueError:
        return None


def _payment_method(raw, index):
    names = set()
    for payment in _related_many(raw, 'payments', index):
        if _attr(payment, 'canceled'):
            continue
        name = _text(_attr(_related(payment, 'paymentMethod', index), 'name'))
        if name:
            names.add(name)
    if not names:
        return None
    return names.pop() if len(names) == 1 else 'Mixto'


def parse_fudo_sale(raw, index=None):
    """Campos de `Sale` para una venta de Fudo."""
    index = index or {}
    attributes = raw.get('attributes') or {}
    creacion = _datetime(attributes.get('createdAt')) or datetime.now()
    cerrada = _datetime(attributes.get('closedAt'))
    total = _decimal(attributes.get('total'))
    table = _related(raw, 'table', index)
    room = _related(table, 'room', index)
    table_number = _attr(table, 'number')
    people = attributes.get('people')
    return {
        'external_id': int(raw.get('id')),
        'fecha': business_date(cerrada or creacion) if (cerrada or creacion) else get_current_date_argentina(),
        'creacion': creacion,
        'cerrada': cerrada,
        'caja': _text(_attr(_related(raw, 'cashRegister', index), 'name'), 100),
        'estado': STATE_MAP.get(attributes.get('saleState'), 'Cerrada'),
        'cliente': _text(attributes.get('customerName'), 200),
        'mesa': _text(table_number, 20),
        'sala': _text(_attr(room, 'name'), 100),
        'personas': int(people) if isinstance(people, (int, float)) else None,
        'camarero': _text(_attr(_related(raw, 'waiter', index), 'name'), 200),
        'medio_pago': _text(_payment_method(raw, index), 100),
        'total': float(total) if total is not None else 0,
        'fiscal': False,
        'tipo_venta': TYPE_MAP.get(attributes.get('saleType'), 'Local'),
        'comentario': _text(attributes.get('comment')),
        'origen': 'Fudo',
        'id_origen': str(raw.get('id')),
    }


def parse_fudo_items(raw, index):
    """Ítems no cancelados de una venta de Fudo, como dicts para `SaleItem` (+ `fudo_product_id`)."""
    items = []
    for item in _related_many(raw, 'items', index):
        if _attr(item, 'canceled'):
            continue
        quantity = _decimal(_attr(item, 'quantity'))
        price = _decimal(_attr(item, 'price'))
        if quantity is None or price is None or quantity <= 0:
            continue
        product = _related(item, 'product', index)
        product_ref = _rel_data(item, 'product')
        category = _related(product, 'productCategory', index)
        cost = _decimal(_attr(item, 'cost'))
        items.append({
            'external_id': str(item.get('id')),
            'fudo_product_id': str(product_ref['id']) if isinstance(product_ref, dict) and product_ref.get('id') else None,
            'product_name': _text(_attr(product, 'name'), 200) or 'Producto sin nombre',
            'variant_name': None,
            'category_name': _text(_attr(category, 'name'), 100),
            'quantity': quantity,
            # `price` de Fudo es el total de la línea, no el unitario: verificado contra producción el 2026-10-24
            # (en octubre 750 de 762 ventas cierran con la suma de price; con price x cantidad el reporte daba +25 %).
            'unit_price': (price / quantity).quantize(CENT),
            'total': price.quantize(CENT),
            'unit_cost': cost.quantize(CENT) if cost is not None else None,
        })
    return items
