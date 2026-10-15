"""Receptor de la factura y tipo de comprobante."""
import re
from decimal import Decimal

from app.models.fiscal import RECEIVER_CONDITIONS
from app.services.pos.errors import bad_request
from app.utils.validation import clean_str

DOC_TYPES = {'CUIT': 80, 'CUIL': 86, 'DNI': 96}
ANONYMOUS_DOC_TYPE = 99
RECEIVER_IVA_IDS = {'responsable_inscripto': 1, 'exento': 4, 'consumidor_final': 5, 'monotributo': 6}
CUIT_WEIGHTS = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)


def valid_cuit(number):
    if not isinstance(number, str) or not re.fullmatch(r'\d{11}', number):
        return False
    remainder = 11 - sum(int(d) * w for d, w in zip(number[:10], CUIT_WEIGHTS)) % 11
    check = 0 if remainder == 11 else remainder
    return check != 10 and check == int(number[10])


def _pesos(value):
    return f'${Decimal(value):,.0f}'.replace(',', '.')


def normalize_receiver(data, total, threshold, emitter_condition):
    """Receptor validado. `data` None = consumidor final sin identificar (solo debajo del umbral)."""
    if data is None:
        if threshold is not None and Decimal(total) >= Decimal(threshold):
            raise bad_request(f'Para facturas desde {_pesos(threshold)} hay que identificar al cliente')
        return {'doc_type_code': ANONYMOUS_DOC_TYPE, 'doc_type': None, 'doc_number': '0',
                'name': 'Consumidor final', 'iva_condition': 'consumidor_final', 'address': None}
    if not isinstance(data, dict):
        raise bad_request('Los datos del cliente son inválidos')
    doc_type = data.get('doc_type')
    if doc_type not in DOC_TYPES:
        raise bad_request('El tipo de documento tiene que ser DNI, CUIT o CUIL')
    number = re.sub(r'\D', '', str(data.get('doc_number') or ''))
    if doc_type == 'DNI' and not 7 <= len(number) <= 8:
        raise bad_request('El DNI tiene que tener 7 u 8 dígitos')
    if doc_type in ('CUIT', 'CUIL') and not valid_cuit(number):
        raise bad_request(f'El {doc_type} es inválido')
    condition = data.get('iva_condition')
    if condition not in RECEIVER_CONDITIONS:
        raise bad_request('Elegí la condición frente al IVA del cliente')
    if condition in ('responsable_inscripto', 'monotributo') and doc_type != 'CUIT':
        raise bad_request('Para esa condición frente al IVA hace falta el CUIT')
    name = clean_str(data.get('name'), 120)
    if not name:
        raise bad_request('Indicá el nombre o la razón social del cliente')
    address = clean_str(data.get('address'), 200)
    return {'doc_type_code': DOC_TYPES[doc_type], 'doc_type': doc_type, 'doc_number': number, 'name': name,
            'iva_condition': condition, 'address': address}


CREDIT_NOTE_FOR = {11: 13, 1: 3, 6: 8}


def voucher_type_for(emitter_condition, receiver_condition, credit_note=False):
    if emitter_condition == 'monotributo':
        return 13 if credit_note else 11
    # Responsable inscripto: Factura A a responsables inscriptos y monotributistas (RG 5003), B al resto.
    if receiver_condition in ('responsable_inscripto', 'monotributo'):
        return 3 if credit_note else 1
    return 8 if credit_note else 6


def credit_note_type_for(invoice_type):
    """La nota de crédito sigue a la factura que anula (aunque después haya cambiado la condición del emisor)."""
    return CREDIT_NOTE_FOR[invoice_type]
