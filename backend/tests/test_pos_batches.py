from decimal import Decimal

import pytest

from app.extensions import db
from app.models import ProductVariant, Supply
from app.services.pos import sale_service
from app.services.pos.errors import PosError
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401


def _sale_with_items(user, cat, table):
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=2)
    sale_service.add_item(user, sale.id, cat.taza.id, quantity=2, modifier_option_ids=[cat.almendras.id])
    sale_service.add_item(user, sale.id, cat.unidad.id, quantity=3)
    return sale


def test_confirm_batch_numbers_and_consumes_stock(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cat = make_catalog()
    _salon, t1, _t2 = make_floor()
    sale = _sale_with_items(waiter, cat, t1)
    sale = sale_service.confirm_batch(waiter, sale.id)
    assert {i.status for i in sale.items} == {'confirmed'} and {i.batch for i in sale.items} == {1}
    assert Decimal(db.session.get(Supply, cat.cafe.id).stock_quantity) == Decimal('0.96')
    assert Decimal(db.session.get(Supply, cat.almendras_supply.id).stock_quantity) == Decimal('0.6')
    assert Decimal(db.session.get(ProductVariant, cat.unidad.id).stock_quantity) == Decimal('2')

    sale_service.add_item(waiter, sale.id, cat.unidad.id, quantity=4)
    sale = sale_service.confirm_batch(waiter, sale.id)
    assert sale.items[-1].batch == 2
    assert Decimal(db.session.get(ProductVariant, cat.unidad.id).stock_quantity) == Decimal('-2')


def test_confirm_without_pending_is_409(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    _salon, t1, _t2 = make_floor()
    sale = sale_service.open_sale(waiter, 'salon', table_id=t1.id, people=1)
    with pytest.raises(PosError) as exc:
        sale_service.confirm_batch(waiter, sale.id)
    assert exc.value.status == 409


def test_request_bill_requires_no_pending_and_reopen(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cat = make_catalog()
    _salon, t1, _t2 = make_floor()
    sale = _sale_with_items(waiter, cat, t1)
    with pytest.raises(PosError, match='pendientes'):
        sale_service.request_bill(waiter, sale.id)
    sale_service.confirm_batch(waiter, sale.id)
    sale = sale_service.request_bill(waiter, sale.id)
    assert sale.status == 'billing' and sale.billing_at is not None
    with pytest.raises(PosError):
        sale_service.add_item(waiter, sale.id, cat.unidad.id)
    sale = sale_service.reopen(waiter, sale.id)
    assert sale.status == 'open'


def test_request_bill_on_empty_sale_is_409(pos_app):
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    _salon, t1, _t2 = make_floor()
    sale = sale_service.open_sale(waiter, 'salon', table_id=t1.id, people=1)
    with pytest.raises(PosError, match='ítems'):
        sale_service.request_bill(waiter, sale.id)
