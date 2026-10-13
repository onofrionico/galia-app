from decimal import Decimal

import pytest

from app.extensions import db
from app.models import Expense, ExpenseCategory, Supplier
from app.models.pos import CashEvent, CashMovement
from app.services.pos import cash_service
from app.services.pos.errors import PosError
from cash_helpers import make_methods, make_register
from pos_helpers import make_user, pos_app  # noqa: F401


@pytest.fixture
def cashier(pos_app):
    return make_user('caja@test.com', modules=('POS',))


def _category(name='Insumos'):
    category = ExpenseCategory(name=name)
    db.session.add(category)
    db.session.commit()
    return category


def test_open_session_records_float_movement_and_event(cashier):
    register = make_register()
    session = cash_service.open_session(cashier, register.id, '1500')
    assert session.status == 'open' and session.opening_float == Decimal('1500.00')
    assert [(m.kind, m.amount) for m in session.movements] == [('opening_float', Decimal('1500.00'))]
    assert [e.kind for e in CashEvent.query.all()] == ['opened']
    assert cash_service.current_session_id() == session.id


def test_open_twice_is_conflict(cashier):
    register = make_register()
    cash_service.open_session(cashier, register.id, 0)
    with pytest.raises(PosError) as error:
        cash_service.open_session(cashier, register.id, 0)
    assert error.value.status == 409


@pytest.mark.parametrize('value', ['-1', 'abc', None])
def test_open_rejects_invalid_float(cashier, value):
    register = make_register()
    with pytest.raises(ValueError):
        cash_service.open_session(cashier, register.id, value)


def test_open_inactive_register_is_bad_request(cashier):
    register = make_register()
    register.is_active = False
    db.session.commit()
    with pytest.raises(PosError) as error:
        cash_service.open_session(cashier, register.id, 0)
    assert error.value.status == 400


def test_current_session_needs_exactly_one_open(cashier):
    assert cash_service.current_session_id() is None
    first = cash_service.open_session(cashier, make_register().id, 0)
    assert cash_service.current_session_id() == first.id
    cash_service.open_session(cashier, make_register('Barra').id, 0)
    assert cash_service.current_session_id() is None


def test_movements_feed_the_cash_breakdown(cashier):
    methods = make_methods()
    category = _category()
    session = cash_service.open_session(cashier, make_register().id, '1000')
    cash_service.add_movement(cashier, session.id, 'deposit', '500', 'Cambio')
    cash_service.add_movement(cashier, session.id, 'withdrawal', '300', 'Depósito al banco')
    cash_service.add_movement(cashier, session.id, 'expense', '200', 'Hielo', category_id=category.id)
    summary = cash_service.session_summary(session)
    assert summary['cash'] == {'payment_method_id': methods.efectivo.id, 'opening_float': 1000.0, 'sales': 0.0,
                               'cancelled': 0.0, 'expenses': 200.0, 'withdrawals': 300.0, 'deposits': 500.0,
                               'expected': 1000.0}
    cash_line = next(m for m in summary['methods'] if m['kind'] == 'cash')
    assert cash_line['expected'] == 1000.0
    assert summary['collected_net'] == 0.0 and summary['open_sales'] == 0


def test_expense_movement_creates_a_cash_expense(cashier):
    category = _category()
    supplier = Supplier(name='Lácteos SA')
    db.session.add(supplier)
    db.session.commit()
    session = cash_service.open_session(cashier, make_register().id, 0)
    cash_service.add_movement(cashier, session.id, 'expense', '250.5', 'Leche', category_id=category.id,
                              supplier_id=supplier.id)
    expense = Expense.query.one()
    assert (expense.importe, expense.de_caja, expense.caja, expense.medio_pago, expense.estado_pago,
            expense.category_id, expense.supplier_id, expense.proveedor, expense.comentario, expense.creado_por,
            expense.cancelado) == (Decimal('250.50'), True, 'Caja principal', 'Efectivo', 'Pagado', category.id,
                                   supplier.id, 'Lácteos SA', 'Leche', 'caja@test.com', False)
    assert CashMovement.query.filter_by(kind='expense').one().expense_id == expense.id


@pytest.mark.parametrize('kwargs, status', [
    ({'kind': 'gift', 'amount': '10', 'reason': 'x'}, 400),
    ({'kind': 'deposit', 'amount': '10', 'reason': '  '}, 400),
    ({'kind': 'expense', 'amount': '10', 'reason': 'x', 'category_id': 999}, 400),
])
def test_movement_validation(cashier, kwargs, status):
    session = cash_service.open_session(cashier, make_register().id, 0)
    with pytest.raises(PosError) as error:
        cash_service.add_movement(cashier, session.id, **kwargs)
    assert error.value.status == status


def test_movement_amount_must_be_positive(cashier):
    session = cash_service.open_session(cashier, make_register().id, 0)
    with pytest.raises(ValueError):
        cash_service.add_movement(cashier, session.id, 'deposit', '0', 'Cambio')


def test_movement_on_closed_session_is_conflict(cashier):
    session = cash_service.open_session(cashier, make_register().id, 0)
    session.status = 'closed'
    db.session.commit()
    with pytest.raises(PosError) as error:
        cash_service.add_movement(cashier, session.id, 'deposit', '10', 'Cambio')
    assert error.value.status == 409


def test_cancel_movement_is_admin_only_and_cancels_the_expense(cashier):
    admin = make_user('admin@test.com', role='admin')
    make_methods()
    category = _category()
    session = cash_service.open_session(cashier, make_register().id, '100')
    session = cash_service.add_movement(cashier, session.id, 'expense', '40', 'Hielo', category_id=category.id)
    movement = session.movements[-1]
    with pytest.raises(PosError) as error:
        cash_service.cancel_movement(cashier, movement.id, 'Error')
    assert error.value.status == 403
    session = cash_service.cancel_movement(admin, movement.id, 'Error de carga')
    assert movement.cancelled_at is not None and movement.cancel_reason == 'Error de carga'
    assert Expense.query.one().cancelado is True
    assert cash_service.session_summary(session)['cash']['expected'] == 100.0
    assert [e.kind for e in CashEvent.query.order_by(CashEvent.id)] == ['opened', 'movement_added',
                                                                        'movement_cancelled']


def test_cancel_movement_rules(cashier):
    admin = make_user('admin@test.com', role='admin')
    session = cash_service.open_session(cashier, make_register().id, '100')
    opening = session.movements[0]
    with pytest.raises(PosError) as error:
        cash_service.cancel_movement(admin, opening.id, 'x')
    assert error.value.status == 409
    session = cash_service.add_movement(cashier, session.id, 'deposit', '10', 'Cambio')
    deposit = session.movements[-1]
    session.status = 'closed'
    db.session.commit()
    with pytest.raises(PosError) as error:
        cash_service.cancel_movement(admin, deposit.id, 'x')
    assert error.value.status == 409
