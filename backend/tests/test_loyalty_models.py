from app.extensions import db
from app.models.loyalty import LoyaltySettings
from app.models.pos import PosSaleItem
from loyalty_helpers import make_catalog, make_customer, make_reward, pos_app  # noqa: F401


def test_customer_gets_unique_qr_token_and_search_text(pos_app):
    a = make_customer(phone='1155550032')
    b = make_customer(first='Juan', last='Gómez', email='juan@test.com')
    assert len(a.qr_token) >= 24 and a.qr_token != b.qr_token
    assert 'lucia perez' in a.search_text
    assert 'lu@test.com' in a.search_text
    assert '1155550032' in a.search_text
    assert a.full_name == 'Lucía Pérez'


def test_search_text_updates_when_phone_changes(pos_app):
    a = make_customer()
    a.phone = '1144443333'
    db.session.commit()
    assert '1144443333' in a.search_text


def test_variant_cafecitos_defaults_to_zero(pos_app):
    cat = make_catalog()
    assert cat.taza.cafecitos == 0


def test_settings_get_creates_single_row_with_30_days(pos_app):
    first = LoyaltySettings.get()
    second = LoyaltySettings.get()
    assert first.id == second.id and first.active_days == 30
    assert LoyaltySettings.query.count() == 1


def test_redemption_item_flag(pos_app):
    cat = make_catalog()
    reward = make_reward(cat.taza, 8)
    assert PosSaleItem(reward_id=reward.id).is_redemption is True
    assert PosSaleItem().is_redemption is False
