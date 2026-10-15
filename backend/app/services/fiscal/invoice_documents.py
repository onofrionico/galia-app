"""Factura y nota de crédito impresas en la térmica de caja, con el QR de ARCA."""
import base64
import json
from decimal import Decimal

CONDITION_LABELS = {'monotributo': 'Responsable Monotributo', 'responsable_inscripto': 'IVA Responsable Inscripto',
                    'consumidor_final': 'Consumidor Final', 'exento': 'IVA Exento'}
DOC_LABELS = {80: 'CUIT', 86: 'CUIL', 96: 'DNI'}
QR_BASE = 'https://www.afip.gob.ar/fe/qr/?p='


def _money(value):
    return f'{Decimal(value):.2f}'


def qr_url(invoice, cuit):
    payload = {'ver': 1, 'fecha': invoice.voucher_date.isoformat(), 'cuit': int(cuit),
               'ptoVta': invoice.point_of_sale, 'tipoCmp': invoice.voucher_type, 'nroCmp': invoice.number,
               'importe': float(Decimal(invoice.total)), 'moneda': 'PES', 'ctz': 1,
               'tipoDocRec': invoice.receiver_doc_type, 'nroDocRec': int(invoice.receiver_doc_number or 0),
               'tipoCodAut': 'E', 'codAut': int(invoice.cae)}
    encoded = base64.b64encode(json.dumps(payload, separators=(',', ':')).encode()).decode()
    return f'{QR_BASE}{encoded}'


def invoice_document(invoice, settings):
    title = ('NOTA DE CRÉDITO ' if invoice.is_credit_note else 'FACTURA ') + invoice.letter
    header = [settings.business_name, f'CUIT {settings.cuit}', f'IIBB {settings.gross_income or "-"}',
              f'Inicio de actividades {settings.activity_start:%d/%m/%Y}' if settings.activity_start else None,
              settings.address, CONDITION_LABELS.get(settings.iva_condition), f'Cód. {invoice.voucher_type:03d}',
              f'P.V. {invoice.point_of_sale:05d} Nº {invoice.number:08d}', f'Fecha {invoice.voucher_date:%d/%m/%Y}',
              f'Cliente: {invoice.receiver_name}']
    if invoice.receiver_doc_type in DOC_LABELS:
        header.append(f'{DOC_LABELS[invoice.receiver_doc_type]} {invoice.receiver_doc_number}')
    header.append(CONDITION_LABELS[invoice.receiver_iva_condition])
    if invoice.receiver_address:
        header.append(invoice.receiver_address)
    if invoice.related is not None:
        header.append(f'Anula {invoice.related.label}')
    lines = [{'qty': line['qty'], 'text': line['description'], 'amount': line['amount'], 'details': [],
              'strike': False} for line in invoice.lines]
    totals = []
    if Decimal(invoice.iva):
        totals += [{'label': 'Neto', 'amount': _money(invoice.net)},
                   {'label': f'IVA {Decimal(invoice.iva_rate).normalize():f}%', 'amount': _money(invoice.iva)}]
    totals.append({'label': 'TOTAL', 'amount': _money(invoice.total)})
    footer = [f'CAE {invoice.cae}', f'Vto. CAE {invoice.cae_due:%d/%m/%Y}']
    if invoice.environment == 'homologacion':
        footer.append('SIN VALIDEZ FISCAL – PRUEBA')
    return {'title': title, 'header': [h for h in header if h], 'lines': lines, 'totals': totals,
            'footer': footer, 'qr': qr_url(invoice, settings.cuit)}
