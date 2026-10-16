from datetime import date
from decimal import Decimal

from app.extensions import db
from app.models.expense import Expense, ExpenseCategory
from app.models.supplier import Supplier


def _expense(source, category, supplier=None):
    expense = Expense(fecha=date(2026, 10, 1), importe=Decimal('100'), category_id=category.id,
                      supplier_id=supplier.id if supplier else None, source=source,
                      external_id=1 if source == 'fudo' else None)
    db.session.add(expense)
    db.session.commit()
    return expense


def _setup():
    first, second = ExpenseCategory(name='A'), ExpenseCategory(name='B')
    supplier_a, supplier_b = Supplier(name='S1'), Supplier(name='S2')
    db.session.add_all([first, second, supplier_a, supplier_b])
    db.session.commit()
    return first, second, supplier_a, supplier_b


def test_put_marks_overrides_on_fudo_expense(menu_client, admin_headers):
    first, second, supplier_a, supplier_b = _setup()
    expense = _expense('fudo', first, supplier_a)

    response = menu_client.put(f'/api/v1/expenses/{expense.id}', headers=admin_headers,
                               json={'category_id': second.id, 'supplier_id': supplier_b.id})

    assert response.status_code == 200
    data = response.get_json()
    assert data['category_overridden'] is True
    assert data['supplier_overridden'] is True


def test_put_with_same_values_does_not_mark(menu_client, admin_headers):
    first, _, supplier_a, _ = _setup()
    expense = _expense('fudo', first, supplier_a)

    data = menu_client.put(f'/api/v1/expenses/{expense.id}', headers=admin_headers,
                           json={'category_id': first.id, 'supplier_id': supplier_a.id, 'comentario': 'x'}).get_json()

    assert data['category_overridden'] is False
    assert data['supplier_overridden'] is False


def test_put_on_manual_expense_does_not_mark(menu_client, admin_headers):
    first, second, _, _ = _setup()
    expense = _expense('galia', first)

    data = menu_client.put(f'/api/v1/expenses/{expense.id}', headers=admin_headers,
                           json={'category_id': second.id}).get_json()

    assert data['category_overridden'] is False


def test_classify_marks_category_override(menu_client, admin_headers):
    first, second, _, _ = _setup()
    fudo_expense = _expense('fudo', first)

    response = menu_client.post('/api/v1/expenses/classify', headers=admin_headers,
                                json={'classifications': [{'expense_id': fudo_expense.id, 'category_id': second.id}]})

    assert response.status_code == 200
    db.session.refresh(fudo_expense)
    assert fudo_expense.category_overridden is True


def test_relink_fudo_category_moves_link(menu_client, admin_headers):
    old = ExpenseCategory(name='Vieja', fudo_category_id='3')
    new = ExpenseCategory(name='Nueva')
    db.session.add_all([old, new])
    db.session.commit()

    response = menu_client.put(f'/api/v1/reports/expense-categories/{new.id}', headers=admin_headers,
                               json={'fudo_category_id': 3})

    assert response.status_code == 200
    assert response.get_json()['fudo_category_id'] == '3'
    db.session.refresh(old)
    assert old.fudo_category_id is None


def test_unlink_fudo_category(menu_client, admin_headers):
    category = ExpenseCategory(name='Vieja', fudo_category_id='3')
    db.session.add(category)
    db.session.commit()

    data = menu_client.put(f'/api/v1/reports/expense-categories/{category.id}', headers=admin_headers,
                           json={'fudo_category_id': None}).get_json()

    assert data['fudo_category_id'] is None


def test_put_keeps_inactive_category_when_unchanged(menu_client, admin_headers):
    first, _, _, _ = _setup()
    expense = _expense('fudo', first)
    first.is_active = False
    db.session.commit()

    response = menu_client.put(f'/api/v1/expenses/{expense.id}', headers=admin_headers,
                               json={'category_id': str(first.id), 'comentario': 'nota'})

    assert response.status_code == 200
    assert response.get_json()['comentario'] == 'nota'
    assert response.get_json()['category_overridden'] is False


def test_put_same_category_as_string_does_not_mark(menu_client, admin_headers):
    first, _, _, _ = _setup()
    expense = _expense('fudo', first)

    data = menu_client.put(f'/api/v1/expenses/{expense.id}', headers=admin_headers,
                           json={'category_id': str(first.id)}).get_json()

    assert data['category_overridden'] is False


def test_put_changed_category_as_string_marks_and_saves_int(menu_client, admin_headers):
    first, second, _, _ = _setup()
    expense = _expense('fudo', first)

    data = menu_client.put(f'/api/v1/expenses/{expense.id}', headers=admin_headers,
                           json={'category_id': str(second.id)}).get_json()

    assert data['category_id'] == second.id
    assert data['category_overridden'] is True
