from decimal import Decimal

import pytest

from app.services.fiscal.receivers import normalize_receiver, valid_cuit, voucher_type_for
from app.services.pos.errors import PosError


def test_cuit_check_digit():
    assert valid_cuit('20123456786') is True
    assert valid_cuit('20123456780') is False
    assert valid_cuit('2012345678') is False
    assert valid_cuit('abc') is False


def test_anonymous_consumer_below_threshold_only():
    receiver = normalize_receiver(None, Decimal('1000'), Decimal('5000'), 'monotributo')
    assert receiver == {'doc_type_code': 99, 'doc_type': None, 'doc_number': '0', 'name': 'Consumidor final',
                        'iva_condition': 'consumidor_final', 'address': None}
    assert normalize_receiver(None, Decimal('1000'), None, 'monotributo')['doc_type_code'] == 99
    with pytest.raises(PosError) as error:
        normalize_receiver(None, Decimal('5000'), Decimal('5000'), 'monotributo')
    assert error.value.status == 400 and 'identificar al cliente' in error.value.message
    assert '$5.000' in error.value.message


def test_identified_receivers_are_validated():
    dni = normalize_receiver({'doc_type': 'DNI', 'doc_number': '30.123.456', 'name': ' Ana ',
                              'iva_condition': 'consumidor_final'}, Decimal('1'), None, 'monotributo')
    assert dni['doc_type_code'] == 96 and dni['doc_number'] == '30123456' and dni['name'] == 'Ana'
    cuit = normalize_receiver({'doc_type': 'CUIT', 'doc_number': '20-12345678-6', 'name': 'Proveedor SA',
                               'iva_condition': 'responsable_inscripto', 'address': 'Calle 1'},
                              Decimal('1'), None, 'monotributo')
    assert cuit['doc_type_code'] == 80 and cuit['doc_number'] == '20123456786'
    bad_cases = [
        {'doc_type': 'DNI', 'doc_number': '123', 'name': 'X', 'iva_condition': 'consumidor_final'},
        {'doc_type': 'CUIT', 'doc_number': '20123456780', 'name': 'X', 'iva_condition': 'monotributo'},
        {'doc_type': 'DNI', 'doc_number': '30123456', 'name': 'X', 'iva_condition': 'monotributo'},
        {'doc_type': 'DNI', 'doc_number': '30123456', 'name': '', 'iva_condition': 'consumidor_final'},
        {'doc_type': 'PAS', 'doc_number': '30123456', 'name': 'X', 'iva_condition': 'consumidor_final'},
        {'doc_type': 'DNI', 'doc_number': '30123456', 'name': 'X', 'iva_condition': 'otra'},
    ]
    for data in bad_cases:
        with pytest.raises(PosError):
            normalize_receiver(data, Decimal('1'), None, 'monotributo')


def test_voucher_type_matrix():
    assert voucher_type_for('monotributo', 'responsable_inscripto') == 11
    assert voucher_type_for('monotributo', 'consumidor_final', credit_note=True) == 13
    assert voucher_type_for('responsable_inscripto', 'responsable_inscripto') == 1
    assert voucher_type_for('responsable_inscripto', 'consumidor_final') == 6
    # Desde la RG 5003, un responsable inscripto le emite Factura A a un monotributista.
    assert voucher_type_for('responsable_inscripto', 'monotributo') == 1
    assert voucher_type_for('responsable_inscripto', 'monotributo', credit_note=True) == 3
    assert voucher_type_for('responsable_inscripto', 'exento', credit_note=True) == 8


def test_credit_note_type_follows_the_original_invoice():
    from app.services.fiscal.receivers import credit_note_type_for
    assert [credit_note_type_for(t) for t in (11, 1, 6)] == [13, 3, 8]
