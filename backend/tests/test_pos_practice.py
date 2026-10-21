from datetime import date
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import Expense, ExpenseCategory, Sale
from app.models.pos import CashSession, PosSale
from app.services import cutover, mercadopago
from app.services.fiscal import invoice_service
from app.services.mercadopago import point_service
from app.services.mercadopago import reconciliation_service as rs
from app.services.mercadopago.fake import FakeMercadoPago
from app.services.pos import cash_service, payment_service, practice, print_documents, sale_service
from app.services.pos.errors import PosError
from cash_helpers import make_register
from mp_helpers import configure_mp
from pos_helpers import make_catalog, make_user, pos_app  # noqa: F401


@pytest.fixture
def ctx(pos_app):
    admin = make_user('admin@test.com', role='admin')
    cat = make_catalog()
    register = make_register()
    category = ExpenseCategory(name='Insumos')
    db.session.add(category)
    db.session.commit()
    return admin, cat, register, category


def _practice_on(admin):
    cutover.set_flags(admin, practice_mode=True)


def _closed_counter_sale(user, cat):
    sale = sale_service.open_sale(user, 'counter')
    sale_service.add_item(user, sale.id, cat.unidad.id)
    return payment_service.add_payment(user, sale.id, cat.efectivo.id, 900)


def test_practice_does_not_touch_real_numbers(ctx):
    admin, cat, register, category = ctx
    _practice_on(admin)
    session = cash_service.open_session(admin, register.id, 1000)
    sale = _closed_counter_sale(admin, cat)
    cash_service.add_movement(admin, session.id, 'expense', 200, 'Hielo', category_id=category.id)
    db.session.refresh(cat.unidad)
    assert session.is_practice and sale.is_practice and sale.status == 'closed'
    assert cat.unidad.stock_quantity == Decimal('5')
    assert Sale.query.count() == 0 and Expense.query.count() == 0
    assert cash_service.list_sessions(date(2000, 1, 1), date(2100, 1, 1))['sessions'] == []


def test_practice_blocks_invoice_and_point(ctx, monkeypatch):
    admin, cat, _register, _category = ctx
    configure_mp()
    monkeypatch.setattr(mercadopago, 'get_client', lambda settings: FakeMercadoPago())
    _practice_on(admin)
    sale = sale_service.open_sale(admin, 'counter')
    sale_service.add_item(admin, sale.id, cat.unidad.id)
    with pytest.raises(PosError) as error:
        point_service.start(admin, sale.id, Decimal('900'))
    assert error.value.message == 'En modo práctica no se cobra con el Point'
    db.session.rollback()
    payment_service.add_payment(admin, sale.id, cat.efectivo.id, 900)
    with pytest.raises(PosError) as error:
        invoice_service.issue(admin, sale.id, None)
    assert error.value.message == 'En modo práctica no se factura'


def test_practice_print_header(ctx):
    admin, cat, _register, _category = ctx
    _practice_on(admin)
    sale = _closed_counter_sale(admin, cat)
    assert print_documents.receipt_document(sale)['title'].startswith('PRÁCTICA')
    assert print_documents.bill_document(sale)['title'].startswith('PRÁCTICA')
    cutover.set_flags(admin, practice_mode=False)  # una venta real conserva su título
    normal = _closed_counter_sale(admin, cat)
    assert print_documents.receipt_document(normal)['title'] == 'TICKET'


def test_toggle_rules(ctx):
    admin, cat, register, _category = ctx
    real = cash_service.open_session(admin, register.id, 0)
    with pytest.raises(PosError) as error:
        _practice_on(admin)
    assert error.value.message == 'Cerrá la caja antes de entrar en modo práctica'
    db.session.rollback()
    cash_service.close_session(admin, real.id, [{'payment_method_id': cat.efectivo.id, 'counted': 0}], None)
    open_sale = sale_service.open_sale(admin, 'counter')
    sale_service.add_item(admin, open_sale.id, cat.unidad.id)
    with pytest.raises(PosError) as error:
        _practice_on(admin)
    assert error.value.message == 'Hay ventas reales abiertas'
    db.session.rollback()
    sale_service.cancel_sale(admin, open_sale.id, 'Prueba')
    _practice_on(admin)
    practice_session = cash_service.open_session(admin, register.id, 0)
    with pytest.raises(PosError) as error:
        cutover.set_flags(admin, practice_mode=False)
    assert error.value.message == 'Cerrá la caja de práctica antes de salir'
    db.session.rollback()
    cash_service.close_session(admin, practice_session.id, [{'payment_method_id': cat.efectivo.id, 'counted': 0}], None)
    cutover.set_flags(admin, practice_mode=False)
    with pytest.raises(PosError) as error:
        cutover.set_flags(admin, fudo_off=True)
    assert error.value.message == 'Primero pasá el catálogo a Galia'
    db.session.rollback()
    with pytest.raises(PosError) as error:
        cutover.set_flags(make_user('caja@test.com', modules=('POS',)), practice_mode=True)
    assert error.value.status == 403


def test_clear_practice(ctx):
    admin, cat, register, _category = ctx
    real_sale = _closed_counter_sale(admin, cat)
    _practice_on(admin)
    session = cash_service.open_session(admin, register.id, 0)
    _closed_counter_sale(admin, cat)
    cash_service.close_session(admin, session.id, [{'payment_method_id': cat.efectivo.id, 'counted': 900}], None)
    with pytest.raises(PosError):
        practice.clear_practice(admin)  # el modo tiene que estar apagado
    db.session.rollback()
    cutover.set_flags(admin, practice_mode=False)
    counts = practice.clear_practice(admin)
    assert counts == {'sales': 1, 'cash_sessions': 1}
    assert PosSale.query.all() == [db.session.get(PosSale, real_sale.id)]
    assert CashSession.query.count() == 0 and Sale.query.count() == 1


def test_reconciliation_ignores_practice_payments(ctx):
    admin, cat, _register, _category = ctx
    cat.efectivo.is_mercadopago = True
    db.session.commit()
    _practice_on(admin)
    sale = _closed_counter_sale(admin, cat)
    data = rs.day(sale.business_date)
    assert data['only_galia'] == []
