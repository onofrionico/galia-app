import pytest

from app.extensions import db
from app.models.pos import PaymentMethod, PosPayment
from app.services.pos import cash_service, payment_service, sale_service
from cash_helpers import make_register
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401


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


def _close(session):
    session.status = 'closed'
    db.session.commit()


def test_payment_takes_the_open_session(ctx):
    user, cat, (t1, _t2) = ctx
    session = cash_service.open_session(user, make_register().id, 0)
    sale = _billed_sale(user, cat, t1)
    payment_service.add_payment(user, sale.id, cat.efectivo.id, 900, tendered=1000)
    assert PosPayment.query.one().cash_session_id == session.id


def test_payment_without_open_session_has_no_session(ctx):
    user, cat, (t1, _t2) = ctx
    sale = _billed_sale(user, cat, t1)
    payment_service.add_payment(user, sale.id, cat.efectivo.id, 900)
    assert PosPayment.query.one().cash_session_id is None


def test_payment_with_two_open_registers_has_no_session(ctx):
    user, cat, (t1, _t2) = ctx
    cash_service.open_session(user, make_register().id, 0)
    cash_service.open_session(user, make_register('Barra').id, 0)
    sale = _billed_sale(user, cat, t1)
    payment_service.add_payment(user, sale.id, cat.efectivo.id, 900)
    assert PosPayment.query.one().cash_session_id is None


def test_summary_counts_applied_amount_not_tendered(ctx):
    user, cat, (t1, t2) = ctx
    session = cash_service.open_session(user, make_register().id, '1000')
    payment_service.add_payment(user, _billed_sale(user, cat, t1).id, cat.efectivo.id, 900, tendered=2000)
    payment_service.add_payment(user, _billed_sale(user, cat, t2).id, cat.debito.id, 900)
    summary = cash_service.session_summary(session)
    by_name = {m['method_name']: m for m in summary['methods']}
    assert by_name['Efectivo']['collected'] == 900.0 and by_name['Efectivo']['expected'] == 1900.0
    assert by_name['Débito']['expected'] == 900.0
    assert summary['cash']['sales'] == 900.0 and summary['cash']['expected'] == 1900.0
    assert summary['collected_net'] == 1800.0


def test_cancel_in_same_session_nets_zero(ctx):
    user, cat, (t1, _t2) = ctx
    session = cash_service.open_session(user, make_register().id, 0)
    sale = payment_service.add_payment(user, _billed_sale(user, cat, t1).id, cat.debito.id, 900)
    payment_service.cancel_payment(user, sale.payments[0].id, 'Error')
    payment = PosPayment.query.one()
    assert payment.cancel_cash_session_id == session.id
    debit = next(m for m in cash_service.session_summary(session)['methods'] if m['method_name'] == 'Débito')
    assert (debit['collected'], debit['cancelled'], debit['expected']) == (900.0, 900.0, 0.0)


def test_cancel_after_close_hits_the_new_session_only(ctx):
    user, cat, (t1, _t2) = ctx
    register = make_register()
    first = cash_service.open_session(user, register.id, 0)
    sale = payment_service.add_payment(user, _billed_sale(user, cat, t1).id, cat.efectivo.id, 900)
    before = cash_service.session_summary(first)
    _close(first)
    second = cash_service.open_session(user, register.id, '500')
    payment_service.cancel_payment(user, sale.payments[0].id, 'Devolución')
    assert cash_service.session_summary(first)['methods'] == before['methods']
    cash = cash_service.session_summary(second)['cash']
    assert (cash['sales'], cash['cancelled'], cash['expected']) == (0.0, 900.0, -400.0)


def test_movements_apply_to_first_cash_method_only(ctx):
    user, cat, (t1, _t2) = ctx
    vales = PaymentMethod(name='Vales', kind='cash', position=9)
    db.session.add(vales)
    db.session.commit()
    session = cash_service.open_session(user, make_register().id, '300')
    payment_service.add_payment(user, _billed_sale(user, cat, t1).id, vales.id, 900)
    by_name = {m['method_name']: m for m in cash_service.session_summary(session)['methods']}
    assert by_name['Efectivo']['expected'] == 300.0
    assert by_name['Vales']['expected'] == 900.0
