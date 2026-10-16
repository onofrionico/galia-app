from datetime import date, datetime
from decimal import Decimal

from app.extensions import db
from app.models.expense import Expense, ExpenseCategory, infer_expense_type
from app.models.fudo_sync_run import FudoSyncRun
from app.models.supplier import Supplier


def test_expense_defaults_and_to_dict(menu_app):
    category = ExpenseCategory(name='Insumos', fudo_category_id='3')
    supplier = Supplier(name='Molino Sur', fudo_provider_id='7')
    db.session.add_all([category, supplier])
    db.session.flush()
    expense = Expense(fecha=date(2026, 10, 1), importe=Decimal('10.00'),
                      category_id=category.id, supplier_id=supplier.id)
    db.session.add(expense)
    db.session.commit()

    data = expense.to_dict()
    assert data['source'] == 'galia'
    assert data['category_overridden'] is False
    assert data['supplier_overridden'] is False
    assert category.to_dict()['fudo_category_id'] == '3'
    assert supplier.to_dict()['fudo_provider_id'] == '7'


def test_infer_expense_type():
    assert infer_expense_type('Mercadería') == 'directo'
    assert infer_expense_type('Materia prima panadería') == 'directo'
    assert infer_expense_type('Alquiler') == 'indirecto'
    assert infer_expense_type('') == 'indirecto'


def test_csv_row_with_id_is_marked_fudo(menu_app):
    expense = Expense.from_csv_row({'Id': '55', 'Fecha': '01/10/2026', 'Importe': '100', 'Categoría': 'Alquiler'})
    assert expense.source == 'fudo'
    manual = Expense.from_csv_row({'Id': '', 'Fecha': '01/10/2026', 'Importe': '100', 'Categoría': 'Alquiler'})
    assert manual.source == 'galia'


def test_sync_run_to_dict(menu_app):
    run = FudoSyncRun(kind='expenses', status='running', started_at=datetime(2026, 10, 15, 12, 0),
                      params={'start_date': '2026-10-01', 'end_date': '2026-10-15'})
    db.session.add(run)
    db.session.commit()

    data = run.to_dict()
    assert data['kind'] == 'expenses'
    assert data['status'] == 'running'
    assert data['started_at'] == '2026-10-15T12:00:00'
    assert data['finished_at'] is None
    assert data['params'] == {'start_date': '2026-10-01', 'end_date': '2026-10-15'}
    assert data['stats'] is None
