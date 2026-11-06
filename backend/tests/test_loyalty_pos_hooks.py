from decimal import Decimal

import pytest

from app.extensions import db
from app.models.loyalty import LoyaltyMovement
from app.services.loyalty import pos_hooks, wallet
from app.services.loyalty.errors import LoyaltyError
from app.services.pos import payment_service, sale_service
from app.services.pos.serializers import sale_to_dict
from loyalty_helpers import balance_of, make_catalog, make_customer, make_reward, make_user, pos_app  # noqa: F401


def _setup():
    cashier = make_user('caja@test.com', modules=('POS', 'Anular', 'Cobrar', 'Descuentos'))
    cat = make_catalog()
    cat.taza.cafecitos = 2
    cat.unidad.cafecitos = 1
    db.session.commit()
    return cashier, cat, make_customer()


def _seed(customer, amount):
    db.session.add(LoyaltyMovement(customer_id=customer.id, kind='adjustment', amount=amount, reason='seed'))
    db.session.commit()


def _open_with(cashier, cat, customer, medialunas=3):
    sale = sale_service.open_sale(cashier, 'counter')
    pos_hooks.set_customer(cashier, sale.id, customer.id)
    if medialunas:
        sale_service.add_item(cashier, sale.id, cat.unidad.id, quantity=medialunas)
    return sale


def _pay_all(cashier, cat, sale):
    sale_service.confirm_batch(cashier, sale.id)
    sale_service.request_bill(cashier, sale.id)
    return payment_service.add_payment(cashier, sale.id, cat.efectivo.id, sale.balance)


def test_closing_sale_with_customer_credits(pos_app):
    cashier, cat, customer = _setup()
    sale = _open_with(cashier, cat, customer)
    preview = wallet.earn_preview(sale)
    sale = _pay_all(cashier, cat, sale)
    assert sale.status == 'closed'
    assert preview == 3 and balance_of(customer) == 3


def test_reopen_by_cancelling_payment_then_reclose_credits_once(pos_app):
    cashier, cat, customer = _setup()
    sale = _pay_all(cashier, cat, _open_with(cashier, cat, customer))
    payment_service.cancel_payment(cashier, sale.payments[0].id, 'Error de cobro')
    assert sale.status == 'billing' and balance_of(customer) == 0
    payment_service.add_payment(cashier, sale.id, cat.efectivo.id, sale.balance)
    assert sale.status == 'closed' and balance_of(customer) == 3
    assert LoyaltyMovement.query.filter_by(kind='earn_reversal').count() == 1


def test_cancel_closed_sale_reverses_credits_and_redemptions(pos_app):
    cashier, cat, customer = _setup()
    reward = make_reward(cat.unidad, 4)
    _seed(customer, 4)
    sale = _open_with(cashier, cat, customer)
    pos_hooks.add_redemption(cashier, sale.id, reward.id, None)
    sale = _pay_all(cashier, cat, sale)
    assert balance_of(customer) == 3  # 4 - 4 + 3
    payment_service.cancel_payment(cashier, sale.payments[0].id, 'Error')
    sale_service.cancel_sale(cashier, sale.id, 'Se fue')
    assert balance_of(customer) == 4


def test_redemption_item_is_free_and_does_not_earn(pos_app):
    cashier, cat, customer = _setup()
    reward = make_reward(cat.taza, 8)
    _seed(customer, 8)
    sale = _open_with(cashier, cat, customer, medialunas=1)
    sale = pos_hooks.add_redemption(cashier, sale.id, reward.id, [cat.almendras.id])
    item = sale.items[-1]
    assert item.is_redemption and item.unit_price == 0 and item.modifiers_total == 0 and item.line_total == 0
    assert [m.option_name for m in item.modifiers] == ['Almendras']
    assert sale.total == Decimal('900')
    _pay_all(cashier, cat, sale)
    earns = LoyaltyMovement.query.filter_by(kind='earn').all()
    assert [e.pos_sale_item_id for e in earns] == [sale.items[0].id]
    redeem = LoyaltyMovement.query.filter_by(kind='redeem').one()
    assert redeem.pesos_value == Decimal('2300')
    assert balance_of(customer) == 1


def test_redemption_requires_customer_and_open_sale(pos_app):
    cashier, cat, _customer = _setup()
    reward = make_reward(cat.unidad, 1)
    sale = sale_service.open_sale(cashier, 'counter')
    with pytest.raises(LoyaltyError, match='cliente'):
        pos_hooks.add_redemption(cashier, sale.id, reward.id, None)


def test_concurrent_redemptions_cannot_spend_twice(pos_app):
    cashier, cat, customer = _setup()
    reward = make_reward(cat.unidad, 8)
    _seed(customer, 8)
    first = _open_with(cashier, cat, customer, medialunas=0)
    second = _open_with(cashier, cat, customer, medialunas=0)
    pos_hooks.add_redemption(cashier, first.id, reward.id, None)
    with pytest.raises(LoyaltyError, match='Le faltan 8 cafecitos'):
        pos_hooks.add_redemption(cashier, second.id, reward.id, None)
    db.session.rollback()
    assert balance_of(customer) == 0
    assert len([i for i in second.items if i.is_redemption]) == 0


def test_delete_pending_redemption_item_refunds_once(pos_app):
    cashier, cat, customer = _setup()
    reward = make_reward(cat.unidad, 5)
    _seed(customer, 5)
    sale = _open_with(cashier, cat, customer, medialunas=0)
    sale = pos_hooks.add_redemption(cashier, sale.id, reward.id, None)
    sale_service.delete_item(cashier, sale.id, sale.items[-1].id)
    assert balance_of(customer) == 5
    assert LoyaltyMovement.query.filter_by(kind='redeem_reversal').count() == 1


def test_cancel_confirmed_redemption_item_refunds_once(pos_app):
    cashier, cat, customer = _setup()
    reward = make_reward(cat.unidad, 5)
    _seed(customer, 5)
    sale = _open_with(cashier, cat, customer, medialunas=1)
    sale = pos_hooks.add_redemption(cashier, sale.id, reward.id, None)
    sale_service.confirm_batch(cashier, sale.id)
    item_id = sale.items[-1].id
    sale_service.cancel_item(cashier, sale.id, item_id, 'No lo quiso')
    assert balance_of(customer) == 5
    sale_service.cancel_sale(cashier, sale.id, 'Se fue')
    assert balance_of(customer) == 5
    assert LoyaltyMovement.query.filter_by(kind='redeem_reversal').count() == 1


def test_split_keeps_customer_and_refunds_moved_redemption_once(pos_app):
    cashier, cat, customer = _setup()
    reward = make_reward(cat.unidad, 5)
    _seed(customer, 5)
    sale = _open_with(cashier, cat, customer, medialunas=2)
    sale = pos_hooks.add_redemption(cashier, sale.id, reward.id, None)
    sale_service.confirm_batch(cashier, sale.id)
    redemption = sale.items[-1]
    new = sale_service.split_sale(cashier, sale.id, [{'item_id': redemption.id, 'quantity': 1}])
    assert new.customer_id == customer.id
    sale_service.cancel_sale(cashier, new.id, 'Se fue')
    assert balance_of(customer) == 5
    sale_service.cancel_sale(cashier, sale.id, 'Se fue')
    assert balance_of(customer) == 5
    assert LoyaltyMovement.query.filter_by(kind='redeem_reversal').count() == 1


def test_cannot_change_customer_with_active_redemption(pos_app):
    cashier, cat, customer = _setup()
    other = make_customer(first='Juan', last='Gómez', email='juan@test.com')
    reward = make_reward(cat.unidad, 1)
    _seed(customer, 1)
    sale = _open_with(cashier, cat, customer, medialunas=0)
    pos_hooks.add_redemption(cashier, sale.id, reward.id, None)
    with pytest.raises(LoyaltyError, match='Anulá los canjes'):
        pos_hooks.set_customer(cashier, sale.id, other.id)
    with pytest.raises(LoyaltyError, match='Anulá los canjes'):
        pos_hooks.set_customer(cashier, sale.id, None)


def test_set_customer_fills_empty_customer_name(pos_app):
    cashier, _cat, customer = _setup()
    sale = sale_service.open_sale(cashier, 'counter')
    sale = pos_hooks.set_customer(cashier, sale.id, customer.id)
    assert sale.customer_id == customer.id and sale.customer_name == 'Lucía Pérez'
    sale = pos_hooks.set_customer(cashier, sale.id, None)
    assert sale.customer_id is None


def test_serialized_sale_includes_customer_and_preview(pos_app):
    cashier, cat, customer = _setup()
    _seed(customer, 14)
    sale = _open_with(cashier, cat, customer, medialunas=2)
    data = sale_to_dict(sale)
    assert data['customer'] == {'id': customer.id, 'full_name': 'Lucía Pérez', 'balance': 14}
    assert data['cafecitos_preview'] == 2
    assert data['items'][0]['is_redemption'] is False
