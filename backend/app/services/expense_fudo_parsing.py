"""Traduce un gasto de Fudo (JSON:API) a los campos de `Expense`. Puro: no toca la base."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

# Nombres de Fudo (confirmados en la Tarea 1 del plan con scripts/inspect_fudo_expenses.py).
ATTR = {
    'date': 'date',
    'due_date': 'dueDate',
    'amount': 'amount',
    'description': 'description',
    'status': 'status',
    'receipt_number': 'receiptNumber',
    'from_cash': 'useInCashCount',
}
REL = {
    'provider': 'provider',
    'category': 'expenseCategory',
    'payment_method': 'paymentMethod',
    'receipt_type': 'receiptType',
    'cash_register': 'cashRegister',
}
PROVIDER_ATTR = {'name': 'name', 'cuit': 'fiscalNumber'}
STATUS_MAP = {'PENDING': 'Pendiente', 'PAID': 'Pagado', 'CANCELLED': 'Cancelado', 'CANCELED': 'Cancelado'}
CANCELLED_STATUSES = {'CANCELLED', 'CANCELED'}

FUDO_FIELDS = (
    'fecha', 'fecha_vencimiento', 'importe', 'comentario', 'estado_pago', 'cancelado', 'de_caja', 'caja',
    'medio_pago', 'tipo_comprobante', 'numero_comprobante', 'numero_fiscal', 'proveedor',
)

CENT = Decimal('0.01')


class ParseError(ValueError):
    pass


@dataclass(frozen=True)
class ProviderRef:
    fudo_id: str
    name: str | None
    cuit: str | None


@dataclass(frozen=True)
class CategoryRef:
    fudo_id: str
    name: str | None


@dataclass
class ParsedExpense:
    external_id: int
    fields: dict
    provider: ProviderRef | None
    category: CategoryRef | None


def index_included(included):
    return {(item.get('type'), str(item.get('id'))): item.get('attributes') or {} for item in included or []}


def _related(raw, rel_key, index):
    """(id, atributos) del recurso relacionado, o (None, {}) si no hay relación."""
    data = ((raw.get('relationships') or {}).get(REL[rel_key]) or {}).get('data')
    if not data or data.get('id') is None:
        return None, {}
    rel_id = str(data['id'])
    return rel_id, index.get((data.get('type'), rel_id), {})


def _text(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _date(value, field, required):
    if value in (None, ''):
        if required:
            raise ParseError(f'{field} vacía')
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        raise ParseError(f'{field} inválida: {value!r}')


def _amount(value):
    if value is None or str(value).strip() == '':
        raise ParseError('importe vacío')
    try:
        return Decimal(str(value)).quantize(CENT)
    except InvalidOperation:
        raise ParseError(f'importe inválido: {value!r}')


def parse_expense(raw, index):
    try:
        external_id = int(raw.get('id'))
    except (TypeError, ValueError):
        raise ParseError(f'id inválido: {raw.get("id")!r}')

    attrs = raw.get('attributes') or {}
    status = (attrs.get(ATTR['status']) or '').upper()

    provider_id, provider_attrs = _related(raw, 'provider', index)
    provider = None
    if provider_id:
        provider = ProviderRef(provider_id, _text(provider_attrs.get(PROVIDER_ATTR['name'])),
                               _text(provider_attrs.get(PROVIDER_ATTR['cuit'])))

    category_id, category_attrs = _related(raw, 'category', index)
    category = CategoryRef(category_id, _text(category_attrs.get('name'))) if category_id else None

    _, method_attrs = _related(raw, 'payment_method', index)
    _, receipt_attrs = _related(raw, 'receipt_type', index)
    _, cash_attrs = _related(raw, 'cash_register', index)

    fields = {
        'fecha': _date(attrs.get(ATTR['date']), 'fecha', required=True),
        'fecha_vencimiento': _date(attrs.get(ATTR['due_date']), 'fecha de vencimiento', required=False),
        'importe': _amount(attrs.get(ATTR['amount'])),
        'comentario': _text(attrs.get(ATTR['description'])),
        'estado_pago': STATUS_MAP.get(status, 'Pendiente'),
        'cancelado': status in CANCELLED_STATUSES,
        'de_caja': bool(attrs.get(ATTR['from_cash'])),
        'caja': _text(cash_attrs.get('name')),
        'medio_pago': _text(method_attrs.get('name')),
        'tipo_comprobante': _text(receipt_attrs.get('name')),
        'numero_comprobante': _text(attrs.get(ATTR['receipt_number'])),
        'numero_fiscal': provider.cuit if provider else None,
        'proveedor': provider.name if provider else None,
    }
    return ParsedExpense(external_id, fields, provider, category)
