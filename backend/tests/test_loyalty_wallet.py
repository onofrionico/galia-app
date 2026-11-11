from decimal import Decimal

import pytest

from app.extensions import db
from app.models.loyalty import LoyaltyChangeLog, LoyaltyMovement
from app.services.loyalty import wallet
from app.services.loyalty.errors import LoyaltyError
from app.services.pos import discount_service, sale_service
from loyalty_helpers import balance_of, make_catalog, make_customer, make_reward, make_user, pos_app  # noqa: F401


def _setup():
    cashier = make_user('caja@test.com', modules=('POS', 'Descuentos'))
    cat = make_catalog()
    cat.taza.cafecitos = 2
    cat.unidad.cafecitos = 1
    db.session.commit()
    customer = make_customer()
    return cashier, cat, customer


def _sale(user, customer, cat, cortados=2, medialunas=3, milk=None):
    sale = sale_service.open_sale(user, 'counter')
    sale.customer_id = customer.id
    db.session.commit()
    if cortados:
        sale_service.add_item(user, sale.id, cat.taza.id, quantity=cortados,
                              modifier_option_ids=[(milk or cat.entera).id])
    if medialunas:
        sale_service.add_item(user, sale.id, cat.unidad.id, quantity=medialunas)
    sale_service.confirm_batch(user, sale.id)
    return sale


def _credit(customer, amount):
    db.session.add(LoyaltyMovement(customer_id=customer.id, kind='adjustment', amount=amount, reason='seed'))
    db.session.commit()


def test_credit_sale_counts_confirmed_non_redemption_items(pos_app):
    cashier, cat, customer = _setup()
    sale = _sale(cashier, customer, cat)
    sale_service.add_item(cashier, sale.id, cat.unidad.id, quantity=1)
    sale_service.confirm_batch(cashier, sale.id)
    sale.items[-1].status = 'cancelled'
    assert wallet.earn_preview(sale) == 7
    assert wallet.credit_sale(sale, cashier) == 7
    db.session.commit()
    assert balance_of(customer) == 7 and wallet.balance(customer.id) == 7


def test_credit_ignores_discounts_and_floors_fractional_quantity(pos_app):
    cashier, cat, customer = _setup()
    sale = _sale(cashier, customer, cat, cortados=1, medialunas=1)
    cortado = sale.items[0]
    discount_service.add_discount(cashier, sale.id, item_id=cortado.id, template_id=cat.cortesia.id)
    sale.items[1].quantity = Decimal('1.5')
    assert wallet.credit_sale(sale, cashier) == 3


def test_practice_sale_does_not_credit(pos_app):
    cashier, cat, customer = _setup()
    sale = _sale(cashier, customer, cat)
    sale.is_practice = True
    assert wallet.credit_sale(sale, cashier) == 0
    assert LoyaltyMovement.query.count() == 0


def test_sale_without_customer_does_not_credit(pos_app):
    cashier, cat, customer = _setup()
    sale = _sale(cashier, customer, cat)
    sale.customer_id = None
    assert wallet.credit_sale(sale, cashier) == 0


def test_reverse_sale_credits_is_idempotent(pos_app):
    cashier, cat, customer = _setup()
    sale = _sale(cashier, customer, cat)
    wallet.credit_sale(sale, cashier)
    db.session.commit()
    assert wallet.reverse_sale_credits(sale, cashier) == -7
    assert wallet.reverse_sale_credits(sale, cashier) == 0
    db.session.commit()
    assert balance_of(customer) == 0
    assert LoyaltyMovement.query.filter_by(kind='earn_reversal').count() == 2  # una por ítem acreditado


def _redemption_item(cashier, sale, cat, reward, milk):
    sale_service.add_item(cashier, sale.id, cat.taza.id, quantity=1, modifier_option_ids=[milk.id])
    item = sale.items[-1]
    item.reward_id = reward.id
    return item


def test_redeem_rejects_when_short(pos_app):
    cashier, cat, customer = _setup()
    reward = make_reward(cat.taza, 8)
    _credit(customer, 5)
    sale = _sale(cashier, customer, cat, cortados=0, medialunas=1)
    item = _redemption_item(cashier, sale, cat, reward, cat.entera)
    with pytest.raises(LoyaltyError, match='Le faltan 3 cafecitos'):
        wallet.redeem(sale, item, reward, cashier)


def test_redeem_records_cost_and_pesos_value(pos_app):
    cashier, cat, customer = _setup()
    reward = make_reward(cat.taza, 8)
    _credit(customer, 10)
    sale = _sale(cashier, customer, cat, cortados=0, medialunas=1)
    item = _redemption_item(cashier, sale, cat, reward, cat.almendras)
    movement = wallet.redeem(sale, item, reward, cashier)
    db.session.commit()
    assert movement.kind == 'redeem' and movement.amount == -8
    assert movement.reward_cost == 8 and movement.pesos_value == Decimal('2300')
    assert balance_of(customer) == 2


def test_reverse_redemption_refunds_once(pos_app):
    cashier, cat, customer = _setup()
    reward = make_reward(cat.taza, 8)
    _credit(customer, 8)
    sale = _sale(cashier, customer, cat, cortados=0, medialunas=1)
    item = _redemption_item(cashier, sale, cat, reward, cat.entera)
    wallet.redeem(sale, item, reward, cashier)
    db.session.commit()
    assert wallet.reverse_redemption(item, cashier).amount == 8
    assert wallet.reverse_redemption(item, cashier) is None
    db.session.commit()
    assert balance_of(customer) == 8


def test_adjust_requires_reason_and_cannot_go_negative(pos_app):
    cashier, _cat, customer = _setup()
    with pytest.raises(LoyaltyError, match='motivo'):
        wallet.adjust(cashier, customer.id, 5, '  ')
    with pytest.raises(LoyaltyError):
        wallet.adjust(cashier, customer.id, 0, 'nada')
    with pytest.raises(LoyaltyError, match='negativo'):
        wallet.adjust(cashier, customer.id, -1, 'error')


def test_adjust_writes_change_log(pos_app):
    cashier, _cat, customer = _setup()
    movement = wallet.adjust(cashier, customer.id, 6, 'Sellos de tarjeta de papel')
    assert movement.kind == 'adjustment' and balance_of(customer) == 6
    log = LoyaltyChangeLog.query.one()
    assert (log.entity, log.entity_id, log.field) == ('adjustment', customer.id, 'balance')
    assert (log.old_value, log.new_value, log.reason) == ('0', '6', 'Sellos de tarjeta de papel')
    assert log.user_id == cashier.id


def test_earn_reversal_may_leave_negative_balance(pos_app):
    cashier, cat, customer = _setup()
    reward = make_reward(cat.unidad, 7)
    sale = _sale(cashier, customer, cat)
    wallet.credit_sale(sale, cashier)
    db.session.commit()
    other = _sale(cashier, customer, cat, cortados=0, medialunas=1)
    sale_service.add_item(cashier, other.id, cat.unidad.id, quantity=1)
    item = other.items[-1]
    item.reward_id = reward.id
    wallet.redeem(other, item, reward, cashier)
    wallet.reverse_sale_credits(sale, cashier)
    db.session.commit()
    assert balance_of(customer) == -7
