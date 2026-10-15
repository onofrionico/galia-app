"""Documentos de impresión del POS: comanda, anulación, precuenta, ticket y prueba.

Un documento es JSON: {title, header: [str], lines: [{qty, text, amount, details: [str], strike}],
totals: [{label, amount}], footer: [str]}. Los montos van como string con 2 decimales, calculados acá;
el frontend solo los imprime. El mismo documento le sirve a una futura pantalla de cocina.
"""
import copy
from decimal import Decimal

import pytz

from app.extensions import db
from app.models import ProductVariant
from app.services.pos.common import display_name, now
from app.utils.timezone_utils import ARGENTINA_TZ

NOT_FISCAL = 'No válido como factura'
REPRINT = 'REIMPRESIÓN'


def _when(moment=None):
    return pytz.utc.localize(moment or now()).astimezone(ARGENTINA_TZ).strftime('%d/%m/%Y %H:%M')


def _money(value):
    return f'{Decimal(value):.2f}'


def _qty(value):
    value = Decimal(value)
    return str(int(value)) if value == value.to_integral_value() else format(value.normalize(), 'f')


def _place(sale):
    return sale.table.label if sale.table is not None else f'Mostrador #{sale.number}'


def _waiter(sale):
    return f'Mozo: {display_name(sale.waiter) or "—"}'


def _text(item):
    variant = db.session.get(ProductVariant, item.product_variant_id)
    several = variant is not None and variant.product.variants.filter_by(is_active=True).count() > 1
    return f'{item.product_name} ({item.variant_name})' if several else item.product_name


def _details(item):
    details = [modifier.option_name for modifier in item.modifiers]
    if item.note:
        details.append(f'Nota: {item.note}')
    return details


def _line(item, amount=None, strike=False):
    return {'qty': _qty(item.quantity), 'text': _text(item), 'amount': amount, 'details': _details(item),
            'strike': strike}


def _document(title, header, lines, totals=None, footer=None):
    return {'title': title, 'header': header, 'lines': lines, 'totals': totals or [], 'footer': footer or []}


def order_document(sale, station, batch, items):
    return _document(station.name.upper(), [_place(sale), _waiter(sale), f'Tanda {batch}', _when()],
                     [_line(item) for item in items])


def void_document(sale, station, items, reason):
    return _document(f'ANULACIÓN · {station.name.upper()}', [_place(sale), _waiter(sale), _when()],
                     [_line(item, strike=True) for item in items], footer=[f'Motivo: {reason}'])


def _sale_header(sale):
    header = [_place(sale)]
    if sale.people:
        header.append(f'Personas: {sale.people}')
    header += [_waiter(sale), f'Venta #{sale.number}', _when()]
    return header


def _sale_lines(sale):
    return [_line(item, amount=_money(item.line_total)) for item in sale.items if item.status == 'confirmed']


def _sale_totals(sale):
    totals = [{'label': 'Subtotal', 'amount': _money(sale.subtotal)}]
    for discount in sale.discounts:
        if discount.cancelled_at is None:
            label = f'Descuento · {discount.reason}' if discount.reason else 'Descuento'
            totals.append({'label': label, 'amount': _money(-discount.amount)})
    totals.append({'label': 'TOTAL', 'amount': _money(sale.total)})
    return totals


def bill_document(sale):
    return _document('PRECUENTA', _sale_header(sale), _sale_lines(sale), _sale_totals(sale), [NOT_FISCAL])


def receipt_document(sale):
    totals = _sale_totals(sale)
    for payment in sale.payments:
        if payment.cancelled_at is None:
            totals.append({'label': payment.method_name, 'amount': _money(payment.amount)})
            if payment.change:
                totals.append({'label': 'Vuelto', 'amount': _money(payment.change)})
    return _document('TICKET', _sale_header(sale), _sale_lines(sale), totals, [NOT_FISCAL, '¡Gracias!'])


def test_document(printer):
    return _document('PRUEBA', [printer.name, f'Papel {printer.paper_width} mm', _when()],
                     [{'qty': '1', 'text': 'Café con leche y medialuna de manteca (ñandú)', 'amount': '1234.50',
                       'details': ['Acentos: áéíóú ÁÉÍÓÚ ü ñ Ñ ¿? ¡!'], 'strike': False}],
                     [{'label': 'TOTAL', 'amount': '1234.50'}], ['Si los acentos y la ñ se ven bien, está OK'])


def mark_reprint(document):
    copied = copy.deepcopy(document)
    copied['header'] = list(copied.get('header', [])) + [REPRINT]
    return copied
