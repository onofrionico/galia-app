from datetime import date
from decimal import Decimal

import pytest

from app.services.expense_fudo_parsing import (
    FUDO_FIELDS, CategoryRef, ParseError, ProviderRef, index_included, parse_expense,
)
from app.utils.fudo_client import FudoClient
from fudo_expense_fakes import (
    fudo_expense, fudo_expense_category, fudo_payment_method, fudo_provider, fudo_receipt_type,
)

INCLUDED = [
    fudo_provider(7, 'Molino Sur', cuit='30-71234567-8'),
    fudo_expense_category(3, 'Insumos'),
    fudo_payment_method(1, 'Transferencia'),
    fudo_receipt_type(2, 'Factura A'),
]


def test_parse_full_expense():
    raw = fudo_expense(101, amount='15000.5', date='2026-10-01', provider_id=7, category_id=3,
                       payment_method_id=1, receipt_type_id=2, status='PAID',
                       dueDate='2026-10-15', description='Harina 000', receiptNumber='0001-00001234')

    parsed = parse_expense(raw, index_included(INCLUDED))

    assert parsed.external_id == 101
    assert parsed.provider == ProviderRef('7', 'Molino Sur', '30-71234567-8')
    assert parsed.category == CategoryRef('3', 'Insumos')
    assert set(parsed.fields) == set(FUDO_FIELDS)
    assert parsed.fields['fecha'] == date(2026, 10, 1)
    assert parsed.fields['fecha_vencimiento'] == date(2026, 10, 15)
    assert parsed.fields['importe'] == Decimal('15000.50')
    assert parsed.fields['comentario'] == 'Harina 000'
    assert parsed.fields['estado_pago'] == 'Pagado'
    assert parsed.fields['cancelado'] is False
    assert parsed.fields['medio_pago'] == 'Transferencia'
    assert parsed.fields['tipo_comprobante'] == 'Factura A'
    assert parsed.fields['numero_comprobante'] == '0001-00001234'
    assert parsed.fields['numero_fiscal'] == '30-71234567-8'
    assert parsed.fields['proveedor'] == 'Molino Sur'


def test_parse_without_relations():
    parsed = parse_expense(fudo_expense(5, status='PENDING'), index_included([]))

    assert parsed.provider is None
    assert parsed.category is None
    assert parsed.fields['proveedor'] is None
    assert parsed.fields['medio_pago'] is None
    assert parsed.fields['estado_pago'] == 'Pendiente'


def test_relation_not_in_included_keeps_id_without_name():
    parsed = parse_expense(fudo_expense(5, provider_id=99), index_included([]))
    assert parsed.provider == ProviderRef('99', None, None)


@pytest.mark.parametrize('status', ['CANCELLED', 'CANCELED'])
def test_cancelled_status(status):
    parsed = parse_expense(fudo_expense(5, status=status), {})
    assert parsed.fields['cancelado'] is True
    assert parsed.fields['estado_pago'] == 'Cancelado'


@pytest.mark.parametrize('amount, expected', [
    ('15000.5', Decimal('15000.50')), (15000.499, Decimal('15000.50')), (0, Decimal('0.00')), ('1200', Decimal('1200.00')),
])
def test_amount_is_quantized(amount, expected):
    assert parse_expense(fudo_expense(5, amount=amount), {}).fields['importe'] == expected


@pytest.mark.parametrize('amount', [None, '', 'abc'])
def test_invalid_amount_raises(amount):
    with pytest.raises(ParseError, match='importe'):
        parse_expense(fudo_expense(5, amount=amount), {})


@pytest.mark.parametrize('value', [None, '', '01/10/2026'])
def test_invalid_date_raises(value):
    with pytest.raises(ParseError, match='fecha'):
        parse_expense(fudo_expense(5, date=value), {})


def test_invalid_id_raises():
    raw = fudo_expense(5)
    raw['id'] = 'abc'
    with pytest.raises(ParseError, match='id'):
        parse_expense(raw, {})


def test_client_collects_included_across_pages(monkeypatch):
    client = FudoClient(api_key='key', api_secret='secret')
    page1 = {'data': [{'id': str(i)} for i in range(500)], 'included': [fudo_provider(7, 'Molino Sur')]}
    page2 = {'data': [{'id': '500'}], 'included': [fudo_provider(7, 'Molino Sur'), fudo_expense_category(3, 'Insumos')]}
    calls = []

    def fake_request(endpoint, params=None):
        calls.append(params)
        return [page1, page2][params['page[number]'] - 1]

    monkeypatch.setattr(client, '_make_request', fake_request)

    result = client.get_all_expenses_with_included(start_date='2026-10-01', end_date='2026-10-15')

    assert len(result['data']) == 501
    assert [(i['type'], i['id']) for i in result['included']] == [('Provider', '7'), ('ExpenseCategory', '3')]
    assert calls[0]['filter[date]'] == 'and(gte.2026-10-01,lte.2026-10-15)'
    assert len(client.get_all_expenses()) == 501  # el método viejo sigue devolviendo solo la lista


def test_missing_date_error_lists_received_attributes():
    raw = fudo_expense(5, date=None)
    del raw['attributes']['date']
    raw['attributes']['createdAt'] = '2026-10-01T12:00:00Z'

    with pytest.raises(ParseError) as exc:
        parse_expense(raw, {})

    message = str(exc.value)
    assert 'fecha vacía' in message
    assert 'createdAt' in message
    assert 'amount' in message


def test_get_expenses_requests_sparse_fieldsets(monkeypatch):
    """GET /expenses de Fudo no devuelve atributos si no se piden con fields[...] (openapi v1alpha1)."""
    client = FudoClient(api_key='key', api_secret='secret')
    calls = []
    monkeypatch.setattr(client, '_make_request', lambda endpoint, params=None: calls.append(params) or {'data': []})

    client.get_expenses(page_size=10, page_number=1)

    params = calls[0]
    expense_fields = set(params['fields[expense]'].split(','))
    assert {'date', 'dueDate', 'amount', 'description', 'status', 'canceled', 'receiptNumber',
            'useInCashCount', 'provider', 'expenseCategory', 'paymentMethod', 'receiptType',
            'cashRegister'} <= expense_fields
    for related in ('provider', 'expenseCategory', 'paymentMethod', 'receiptType', 'cashRegister'):
        assert params[f'fields[{related}]'] == 'name'
    assert set(params['include'].split(',')) >= {'provider', 'expenseCategory', 'paymentMethod', 'receiptType',
                                                 'cashRegister'}


def test_unpaid_status_is_pending():
    parsed = parse_expense(fudo_expense(5, status='UNPAID'), {})
    assert parsed.fields['estado_pago'] == 'Pendiente'
    assert parsed.fields['cancelado'] is False


def test_canceled_attribute_marks_expense_cancelled():
    parsed = parse_expense(fudo_expense(5, status='PAID', canceled=True), {})
    assert parsed.fields['cancelado'] is True
    assert parsed.fields['estado_pago'] == 'Cancelado'


def test_canceled_false_keeps_payment_status():
    parsed = parse_expense(fudo_expense(5, status='PAID', canceled=False), {})
    assert parsed.fields['cancelado'] is False
    assert parsed.fields['estado_pago'] == 'Pagado'
