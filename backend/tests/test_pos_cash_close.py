from datetime import date, datetime, timedelta

import pytest

from app.extensions import db
from app.models.pos import CashEvent, CashSessionCount
from app.services.pos import cash_service, payment_service, sale_service
from app.services.pos.errors import PosError
from cash_helpers import make_register
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401


@pytest.fixture
def ctx(pos_app):
    user = make_user('caja@test.com', modules=('POS',))
    admin = make_user('admin@test.com', role='admin')
    cat = make_catalog()
    _salon, t1, t2 = make_floor()
    return user, admin, cat, (t1, t2)


def _paid(user, cat, table, method, tendered=None):
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=1)
    sale_service.add_item(user, sale.id, cat.unidad.id)  # $900
    sale_service.confirm_batch(user, sale.id)
    sale_service.request_bill(user, sale.id)
    return payment_service.add_payment(user, sale.id, method.id, 900, tendered=tendered)


def test_close_is_blocked_while_sales_are_open(ctx):
    user, _admin, cat, (t1, _t2) = ctx
    session = cash_service.open_session(user, make_register().id, 0)
    sale_service.open_sale(user, 'salon', table_id=t1.id, people=1)
    with pytest.raises(PosError) as error:
        cash_service.close_session(user, session.id, [{'payment_method_id': cat.efectivo.id, 'counted': 0}], None)
    assert error.value.status == 409 and error.value.extra == {'open_sales': 1}
    assert 'Hay 1 ventas abiertas' in error.value.message


def test_close_stores_counts_with_server_expected(ctx):
    user, _admin, cat, (t1, t2) = ctx
    session = cash_service.open_session(user, make_register().id, '1000')
    _paid(user, cat, t1, cat.efectivo, tendered=1000)
    _paid(user, cat, t2, cat.debito)
    session = cash_service.close_session(user, session.id, [
        {'payment_method_id': cat.efectivo.id, 'counted': '1850'},
        {'payment_method_id': cat.debito.id, 'counted': 900},
    ], 'Faltan 50 en el cambio')
    assert session.status == 'closed' and session.closed_by == user.id
    assert session.closing_note == 'Faltan 50 en el cambio'
    rows = {c.method_name: (float(c.expected), float(c.counted), float(c.difference)) for c in session.counts}
    assert rows == {'Efectivo': (1900.0, 1850.0, -50.0), 'Débito': (900.0, 900.0, 0.0)}
    event = CashEvent.query.filter_by(kind='closed').one()
    assert event.payload['differences'] == {'Efectivo': '-50.00', 'Débito': '0.00'}


def test_note_is_required_with_a_difference(ctx):
    user, _admin, cat, _tables = ctx
    session = cash_service.open_session(user, make_register().id, '100')
    with pytest.raises(PosError) as error:
        cash_service.close_session(user, session.id, [{'payment_method_id': cat.efectivo.id, 'counted': 90}], '  ')
    assert error.value.status == 400


def test_omitted_methods_count_as_expected_and_cash_is_required(ctx):
    user, _admin, cat, (t1, _t2) = ctx
    session = cash_service.open_session(user, make_register().id, '100')
    _paid(user, cat, t1, cat.debito)
    with pytest.raises(PosError) as error:
        cash_service.close_session(user, session.id, [{'payment_method_id': cat.debito.id, 'counted': 900}], None)
    assert error.value.status == 400
    session = cash_service.close_session(user, session.id, [{'payment_method_id': cat.efectivo.id, 'counted': 100}],
                                         None)
    rows = {c.method_name: float(c.counted) for c in session.counts}
    assert rows == {'Efectivo': 100.0, 'Débito': 900.0}


def test_inactive_unused_methods_get_no_count_row(ctx):
    user, _admin, cat, _tables = ctx
    cat.debito.is_active = False
    db.session.commit()
    session = cash_service.open_session(user, make_register().id, '0')
    session = cash_service.close_session(user, session.id, [{'payment_method_id': cat.efectivo.id, 'counted': 0}],
                                         None)
    assert [c.method_name for c in session.counts] == ['Efectivo']


def test_unknown_method_and_double_close(ctx):
    user, _admin, cat, _tables = ctx
    session = cash_service.open_session(user, make_register().id, '0')
    with pytest.raises(PosError) as error:
        cash_service.close_session(user, session.id, [{'payment_method_id': 999, 'counted': 0}], None)
    assert error.value.status == 400
    cash_service.close_session(user, session.id, [{'payment_method_id': cat.efectivo.id, 'counted': 0}], None)
    with pytest.raises(PosError) as error:
        cash_service.close_session(user, session.id, [{'payment_method_id': cat.efectivo.id, 'counted': 0}], None)
    assert error.value.status == 409


def test_reopen_is_admin_only_and_clears_counts(ctx):
    user, admin, cat, _tables = ctx
    register = make_register()
    session = cash_service.open_session(user, register.id, '0')
    cash_service.close_session(user, session.id, [{'payment_method_id': cat.efectivo.id, 'counted': 0}], None)
    with pytest.raises(PosError) as error:
        cash_service.reopen_session(user, session.id, 'Error')
    assert error.value.status == 403
    session = cash_service.reopen_session(admin, session.id, 'Faltó un gasto')
    assert session.status == 'open' and session.closed_at is None and session.closing_note is None
    assert CashSessionCount.query.count() == 0
    assert CashEvent.query.order_by(CashEvent.id.desc()).first().kind == 'reopened'


def test_reopen_conflicts_with_another_open_session(ctx):
    user, admin, cat, _tables = ctx
    register = make_register()
    first = cash_service.open_session(user, register.id, '0')
    cash_service.close_session(user, first.id, [{'payment_method_id': cat.efectivo.id, 'counted': 0}], None)
    cash_service.open_session(user, register.id, '0')
    with pytest.raises(PosError) as error:
        cash_service.reopen_session(admin, first.id, 'x')
    assert error.value.status == 409


def test_list_sessions_filters_and_totals(ctx):
    user, _admin, cat, (t1, _t2) = ctx
    register = make_register()
    old = cash_service.open_session(user, register.id, '0')
    cash_service.close_session(user, old.id, [{'payment_method_id': cat.efectivo.id, 'counted': 10}], 'sobra')
    old.opened_at = datetime.utcnow() - timedelta(days=10)
    db.session.commit()
    today = cash_service.open_session(user, register.id, '0')
    _paid(user, cat, t1, cat.efectivo)
    day = date.today()
    result = cash_service.list_sessions(day - timedelta(days=1), day + timedelta(days=1))
    assert [row['id'] for row in result['sessions']] == [today.id]
    assert result['sessions'][0]['collected_net'] == 900.0 and result['sessions'][0]['cash_difference'] is None
    result = cash_service.list_sessions(day - timedelta(days=30), day + timedelta(days=1))
    assert [row['id'] for row in result['sessions']] == [today.id, old.id]
    assert result['sessions'][1]['cash_difference'] == 10.0 and result['total'] == 2 and result['pages'] == 1


def test_list_sessions_uses_argentina_day(ctx):
    user, _admin, _cat, _tables = ctx
    session = cash_service.open_session(user, make_register().id, '0')
    session.opened_at = datetime(2026, 10, 14, 2, 30)  # 23:30 del 13 en Argentina
    db.session.commit()
    assert [r['id'] for r in cash_service.list_sessions(date(2026, 10, 13), date(2026, 10, 13))['sessions']] == [
        session.id]
    assert cash_service.list_sessions(date(2026, 10, 14), date(2026, 10, 14))['sessions'] == []


def test_unassigned_payments_by_date(ctx):
    user, _admin, cat, (t1, t2) = ctx
    _paid(user, cat, t1, cat.efectivo)
    cash_service.open_session(user, make_register().id, '0')
    _paid(user, cat, t2, cat.debito)
    day = date.today()
    rows = cash_service.unassigned_payments(day - timedelta(days=1), day + timedelta(days=1))
    assert [(r['method_name'], r['amount'], r['table']) for r in rows] == [('Efectivo', 900.0, 'Mesa 1')]
