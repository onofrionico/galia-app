"""Builders de payloads JSON:API de gastos de Fudo y cliente fake para los tests de sync."""


def _rel(kind, rel_id):
    return {'data': {'id': str(rel_id), 'type': kind}} if rel_id is not None else {'data': None}


def fudo_expense(expense_id, amount='1000.00', date='2026-10-01', provider_id=None, category_id=None,
                 payment_method_id=None, receipt_type_id=None, status='PAID', **attributes):
    attrs = {'amount': amount, 'date': date, 'status': status, 'description': None}
    attrs.update(attributes)
    return {
        'id': str(expense_id),
        'type': 'Expense',
        'attributes': attrs,
        'relationships': {
            'provider': _rel('Provider', provider_id),
            'expenseCategory': _rel('ExpenseCategory', category_id),
            'paymentMethod': _rel('PaymentMethod', payment_method_id),
            'receiptType': _rel('ReceiptType', receipt_type_id),
        },
    }


def fudo_provider(provider_id, name, cuit=None):
    return {'id': str(provider_id), 'type': 'Provider', 'attributes': {'name': name, 'fiscalNumber': cuit}}


def fudo_expense_category(category_id, name):
    return {'id': str(category_id), 'type': 'ExpenseCategory', 'attributes': {'name': name}}


def fudo_payment_method(method_id, name):
    return {'id': str(method_id), 'type': 'PaymentMethod', 'attributes': {'name': name}}


def fudo_receipt_type(type_id, name):
    return {'id': str(type_id), 'type': 'ReceiptType', 'attributes': {'name': name}}


class FakeExpensesClient:
    def __init__(self, data=None, included=None, error=None):
        self.data = data or []
        self.included = included or []
        self.error = error
        self.calls = []

    def get_all_expenses_with_included(self, start_date=None, end_date=None):
        self.calls.append((start_date, end_date))
        if self.error:
            raise self.error
        return {'data': self.data, 'included': self.included}
