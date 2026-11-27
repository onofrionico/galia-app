"""Apertura de caja con hora anterior: toma los pagos y anulaciones sin caja del período."""
from datetime import datetime, timedelta

import pytest

from app.extensions import db
from app.models.pos import CashEvent, PosPayment
from app.services.pos import cash_service, payment_service, sale_service
from app.services.pos.common import now
from app.services.pos.errors import PosError
from cash_helpers import make_register
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401


@pytest.fixture
def ctx(pos_app):
    user = make_user('caja@test.com', modules=('POS', 'Anular'))
    cat = make_catalog()
    _salon, t1, t2 = make_floor()
    return user, cat, (t1, t2)


def _billed_sale(user, cat, table):
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=1)
    sale_service.add_item(user, sale.id, cat.unidad.id)  # $900
    sale_service.confirm_batch(user, sale.id)
    sale_service.request_bill(user, sale.id)
    return sale


def _paid_at(user, cat, table, when, method=None):
    """Cobra una venta de $900 y le fecha el pago en `when` (UTC naive)."""
    sale = payment_service.add_payment(user, _billed_sale(user, cat, table).id, (method or cat.efectivo).id, 900)
    payment = sale.payments[0]
    payment.created_at = when
    db.session.commit()
    return payment


def _close(session, when):
    session.status = 'closed'
    session.closed_at = when
    db.session.commit()


def test_backdated_open_takes_unassigned_payments(ctx):
    user, cat, (t1, t2) = ctx
    start = now() - timedelta(hours=3)
    first = _paid_at(user, cat, t1, start + timedelta(minutes=5))
    second = _paid_at(user, cat, t2, start + timedelta(hours=1))
    session = cash_service.open_session(user, make_register().id, 0, opened_at=start.isoformat() + '+00:00')
    assert db.session.get(PosPayment, first.id).cash_session_id == session.id
    assert db.session.get(PosPayment, second.id).cash_session_id == session.id
    assert session.opened_at == start
    assert session.registered_at is not None
    assert session.movements[0].created_at == session.opened_at
    assert cash_service.session_summary(session)['cash']['sales'] == 1800.0


def test_payment_before_opening_is_not_taken(ctx):
    user, cat, (t1, t2) = ctx
    start = (now() - timedelta(hours=3)).replace(microsecond=0)
    before = _paid_at(user, cat, t1, start - timedelta(seconds=1))
    exact = _paid_at(user, cat, t2, start)
    session = cash_service.open_session(user, make_register().id, 0, opened_at=start.isoformat() + '+00:00')
    assert db.session.get(PosPayment, before.id).cash_session_id is None
    assert db.session.get(PosPayment, exact.id).cash_session_id == session.id


def test_takes_unassigned_cancellations(ctx):
    user, cat, (t1, _t2) = ctx
    register = make_register()
    old = cash_service.open_session(user, register.id, 0)
    sale = payment_service.add_payment(user, _billed_sale(user, cat, t1).id, cat.debito.id, 900)
    payment_id = sale.payments[0].id
    _close(old, now() - timedelta(hours=2))
    payment_service.cancel_payment(user, payment_id, 'Error')
    assert db.session.get(PosPayment, payment_id).cancel_cash_session_id is None
    session = cash_service.open_session(user, register.id, 0,
                                        opened_at=(now() - timedelta(hours=1)).isoformat() + '+00:00')
    payment = db.session.get(PosPayment, payment_id)
    assert payment.cancel_cash_session_id == session.id and payment.cash_session_id == old.id
    debit = next(m for m in cash_service.session_summary(session)['methods'] if m['method_name'] == 'Débito')
    assert debit['cancelled'] == 900.0


def test_does_not_take_payments_of_other_sessions(ctx):
    user, cat, (t1, _t2) = ctx
    other = cash_service.open_session(user, make_register('Barra').id, 0)
    payment = _paid_at(user, cat, t1, now() - timedelta(minutes=30))
    assert payment.cash_session_id == other.id
    _close(other, now() - timedelta(hours=2))  # cierre forzado antes, para que no limite la apertura
    cash_service.open_session(user, make_register().id, 0,
                              opened_at=(now() - timedelta(hours=1)).isoformat() + '+00:00')
    assert db.session.get(PosPayment, payment.id).cash_session_id == other.id


def test_practice_payments_not_taken(ctx):
    user, cat, (t1, _t2) = ctx
    payment = _paid_at(user, cat, t1, now() - timedelta(minutes=30))
    payment.sale.is_practice = True
    db.session.commit()
    cash_service.open_session(user, make_register().id, 0,
                              opened_at=(now() - timedelta(hours=1)).isoformat() + '+00:00')
    assert db.session.get(PosPayment, payment.id).cash_session_id is None


def test_future_opening_rejected(ctx):
    user, _cat, _tables = ctx
    register = make_register()
    with pytest.raises(PosError) as error:
        cash_service.open_session(user, register.id, 0,
                                  opened_at=(now() + timedelta(minutes=5)).isoformat() + '+00:00')
    assert error.value.status == 400 and str(error.value) == 'La apertura no puede ser futura'
    session = cash_service.open_session(user, register.id, 0,
                                        opened_at=(now() + timedelta(seconds=30)).isoformat() + '+00:00')
    assert session.registered_at is None


def test_before_last_close_rejected(ctx):
    user, _cat, _tables = ctx
    register, barra = make_register(), make_register('Barra')
    closed_at = now() - timedelta(hours=1)
    _close(cash_service.open_session(user, register.id, 0), closed_at)
    _close(cash_service.open_session(user, barra.id, 0), closed_at)
    with pytest.raises(PosError) as error:
        cash_service.open_session(user, register.id, 0,
                                  opened_at=(closed_at - timedelta(hours=1)).isoformat() + '+00:00')
    assert error.value.status == 400 and 'anterior al último cierre' in str(error.value)
    db.session.rollback()
    session = cash_service.open_session(user, register.id, 0,
                                        opened_at=(closed_at + timedelta(minutes=10)).isoformat() + '+00:00')
    assert session.registered_at is not None


def test_naive_value_is_argentina_time(pos_app):
    assert cash_service.parse_opened_at('2026-11-26T08:00') == datetime(2026, 11, 26, 11, 0)
    assert cash_service.parse_opened_at('2026-11-26T08:00:00-03:00') == datetime(2026, 11, 26, 11, 0)
    assert cash_service.parse_opened_at(None) is None and cash_service.parse_opened_at('') is None
    with pytest.raises(PosError) as error:
        cash_service.parse_opened_at('x')
    assert error.value.status == 400 and str(error.value) == 'La hora de apertura es inválida'


def test_backdated_event_payload(ctx):
    user, cat, (t1, t2) = ctx
    start = now() - timedelta(hours=3)
    _paid_at(user, cat, t1, start + timedelta(minutes=5))
    _paid_at(user, cat, t2, start + timedelta(minutes=10))
    cash_service.open_session(user, make_register().id, 0, opened_at=start.isoformat() + '+00:00')
    payload = CashEvent.query.filter_by(kind='opened').one().payload
    assert payload['backdated'] is True and payload['payments_taken'] == 2
    assert payload['payments_total'] == '1800.00' and payload['cancellations_taken'] == 0


def test_api_open_with_opened_at(pos_app):
    client = pos_app.test_client()
    headers = auth_headers(client, make_user('caja@test.com', modules=('POS',)))
    register = make_register()
    opened_at = (now() - timedelta(hours=2)).isoformat() + '+00:00'
    response = client.post('/api/v1/pos/cash/sessions',
                           json={'register_id': register.id, 'opening_float': 0, 'opened_at': opened_at},
                           headers=headers)
    assert response.status_code == 200
    assert response.get_json()['backdated'] is True


def _category():
    from app.models import ExpenseCategory
    category = ExpenseCategory(name='Insumos')
    db.session.add(category)
    db.session.commit()
    return category


def _open_days_ago(user, days):
    return cash_service.open_session(user, make_register().id, 0,
                                     opened_at=(now() - timedelta(days=days)).isoformat() + '+00:00')


def test_expense_with_past_date(ctx):
    from app.models import Expense
    from app.utils.timezone_utils import get_current_date_argentina
    user, _cat, _tables = ctx
    session = _open_days_ago(user, 2)
    yesterday = get_current_date_argentina() - timedelta(days=1)
    cash_service.add_movement(user, session.id, 'expense', 100, 'Hielo', category_id=_category().id,
                              expense_date=yesterday.isoformat())
    assert Expense.query.one().fecha == yesterday


def test_expense_date_out_of_range(ctx):
    from app.utils.timezone_utils import get_current_date_argentina
    user, _cat, _tables = ctx
    session = _open_days_ago(user, 2)
    category = _category()
    today = get_current_date_argentina()
    for day in (today - timedelta(days=5), today + timedelta(days=1)):
        with pytest.raises(PosError) as error:
            cash_service.add_movement(user, session.id, 'expense', 100, 'Hielo', category_id=category.id,
                                      expense_date=day.isoformat())
        assert error.value.status == 400
        assert str(error.value) == 'La fecha del gasto debe estar entre la apertura y hoy'
        db.session.rollback()


def test_expense_date_defaults_to_today(ctx):
    from app.models import Expense
    from app.utils.timezone_utils import get_current_date_argentina
    user, _cat, _tables = ctx
    category = _category()
    session = _open_days_ago(user, 2)
    cash_service.add_movement(user, session.id, 'expense', 100, 'Hielo', category_id=category.id)
    assert Expense.query.one().fecha == get_current_date_argentina()
    _close(session, now())
    today_session = cash_service.open_session(user, session.register_id, 0)
    cash_service.add_movement(user, today_session.id, 'expense', 50, 'Pan', category_id=category.id,
                              expense_date=get_current_date_argentina().isoformat())
    assert Expense.query.count() == 2


def test_expense_date_invalid(ctx):
    user, _cat, _tables = ctx
    session = _open_days_ago(user, 1)
    with pytest.raises(PosError) as error:
        cash_service.add_movement(user, session.id, 'expense', 100, 'Hielo', category_id=_category().id,
                                  expense_date='x')
    assert error.value.status == 400


def test_last_close_of_any_register_bounds_backdate(ctx):
    user, _cat, _tables = ctx
    barra, nueva = make_register('Barra'), make_register('Nueva')
    closed_at = now() - timedelta(hours=1)
    _close(cash_service.open_session(user, barra.id, 0), closed_at)
    with pytest.raises(PosError) as error:
        cash_service.open_session(user, nueva.id, 0,
                                  opened_at=(closed_at - timedelta(minutes=30)).isoformat() + '+00:00')
    assert error.value.status == 400 and 'anterior al último cierre' in str(error.value)


def test_backdate_rejected_while_other_register_open(ctx):
    user, _cat, _tables = ctx
    cash_service.open_session(user, make_register('Barra').id, 0)
    with pytest.raises(PosError) as error:
        cash_service.open_session(user, make_register().id, 0,
                                  opened_at=(now() - timedelta(hours=1)).isoformat() + '+00:00')
    assert error.value.status == 400
    assert str(error.value) == 'Hay otra caja abierta: cerrala antes de abrir con hora anterior'
