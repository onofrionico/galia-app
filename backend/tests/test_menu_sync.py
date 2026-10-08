from datetime import datetime
from decimal import Decimal

import pytest

from app.extensions import db
from app.models.menu import FudoProduct, MenuCategory, MenuItem, MenuItemVariant
from app.services.menu_sync_service import sync_fudo_products, new_items, alert_variants
from menu_fakes import FakeFudoClient, fudo_product, fudo_category


def _item_with_variant(fudo_id, price):
    category = MenuCategory(name='Cafés', slug='cafes')
    db.session.add(category)
    db.session.flush()
    item = MenuItem(category_id=category.id, name='Latte')
    variant = MenuItemVariant(fudo_product_id=fudo_id, price=Decimal(price), fudo_status='ok')
    item.variants = [variant]
    db.session.add(item)
    db.session.commit()
    return item, variant


def test_sync_caches_products_with_category_names(menu_app):
    client = FakeFudoClient(
        products=[fudo_product(1, 'Latte', 6900, category_id='10')],
        categories=[fudo_category(10, 'Cafetería')],
    )
    stats = sync_fudo_products(client)

    product = db.session.get(FudoProduct, '1')
    assert product.name == 'Latte'
    assert product.price == Decimal('6900')
    assert product.category_name == 'Cafetería'
    assert stats == {'products': 1, 'price_changes': 0, 'alerts': 0, 'categories_created': 1, 'items_created': 1}


def test_sync_updates_linked_variant_price(menu_app):
    _, variant = _item_with_variant('1', '6500')
    stats = sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'Latte', 6900)]))

    assert variant.price == Decimal('6900')
    assert variant.fudo_status == 'ok'
    assert stats['price_changes'] == 1


def test_sync_flags_inactive_and_missing_products(menu_app):
    _, inactive_variant = _item_with_variant('1', '6900')
    item2 = MenuItem(category_id=inactive_variant.item.category_id, name='Moka')
    missing_variant = MenuItemVariant(fudo_product_id='2', price=Decimal('7000'), fudo_status='ok')
    item2.variants = [missing_variant]
    db.session.add(item2)
    db.session.commit()

    stats = sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'Latte', 6900, active=False)]))

    assert inactive_variant.fudo_status == 'inactive'
    assert missing_variant.fudo_status == 'missing'
    assert stats['alerts'] == 2
    assert {v.id for v in alert_variants()} == {inactive_variant.id, missing_variant.id}


def test_sync_removes_products_no_longer_in_fudo(menu_app):
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'A', 1), fudo_product(2, 'B', 2)]))
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'A', 1)]))
    assert [p.fudo_id for p in FudoProduct.query.all()] == ['1']


def test_sync_keeps_ignored_flag(menu_app):
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'A', 1)]))
    db.session.get(FudoProduct, '1').ignored = True
    db.session.commit()
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'A', 2)]))
    assert db.session.get(FudoProduct, '1').ignored is True


def test_sync_refuses_empty_product_list(menu_app):
    _item_with_variant('1', '6900')
    with pytest.raises(ValueError):
        sync_fudo_products(FakeFudoClient(products=[]))
    assert MenuItemVariant.query.first().fudo_status == 'ok'


def test_sync_quantizes_prices_so_second_sync_has_no_changes(menu_app):
    _, variant = _item_with_variant('1', '6500')
    client = FakeFudoClient(products=[fudo_product(1, 'Latte', '6900.123')])
    sync_fudo_products(client)
    stats = sync_fudo_products(client)

    assert stats['price_changes'] == 0
    assert variant.price == Decimal('6900.12')


def test_sync_tolerates_duplicate_product_ids(menu_app):
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'A', 1), fudo_product(1, 'A', 2)]))
    assert FudoProduct.query.count() == 1


def _categories():
    return [fudo_category(1, 'Cafetería'), fudo_category(2, 'Pastelería')]


def test_sync_creates_categories_from_fudo(menu_app):
    stats = sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'Latte', 6900)], categories=_categories()))
    cats = {c.fudo_category_id: c for c in MenuCategory.query.all()}
    assert set(cats) == {'1', '2'}
    assert cats['1'].name == 'Cafetería' and cats['1'].is_visible and cats['1'].group_id is None
    assert stats['categories_created'] == 2


def test_sync_renames_and_flags_missing_categories(menu_app):
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'Latte', 1)], categories=_categories()))
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'Latte', 1)], categories=[fudo_category(1, 'Cafés')]))
    cafe = MenuCategory.query.filter_by(fudo_category_id='1').one()
    pasteleria = MenuCategory.query.filter_by(fudo_category_id='2').one()
    assert cafe.name == 'Cafés' and cafe.slug == 'cafes'
    assert pasteleria.is_visible is False and pasteleria.fudo_status == 'missing'


def test_sync_creates_hidden_items_for_new_products(menu_app):
    stats = sync_fudo_products(FakeFudoClient(
        products=[fudo_product(1, 'Latte', 6900, category_id='1'), fudo_product(2, 'Medialuna', 2500, category_id='2')],
        categories=_categories(),
    ))
    latte = MenuItem.query.filter_by(name='Latte').one()
    assert latte.is_visible is False and latte.reviewed_at is None
    assert latte.category.fudo_category_id == '1'
    assert [(v.fudo_product_id, v.price, v.fudo_status) for v in latte.variants] == [('1', Decimal('6900'), 'ok')]
    assert stats['items_created'] == 2

    again = sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'Latte', 6900, category_id='1')], categories=_categories()))
    assert again['items_created'] == 0
    assert MenuItem.query.filter_by(name='Latte').count() == 1


def test_sync_skips_ignored_and_inactive_products(menu_app):
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'A', 1)], categories=_categories()))
    item = MenuItem.query.one()
    db.session.get(FudoProduct, '1').ignored = True
    db.session.delete(item)
    db.session.commit()

    stats = sync_fudo_products(FakeFudoClient(
        products=[fudo_product(1, 'A', 1), fudo_product(2, 'B', 1, active=False)], categories=_categories(),
    ))
    assert stats['items_created'] == 0
    assert MenuItem.query.count() == 0


def test_sync_moves_item_when_fudo_category_changes(menu_app):
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'Latte', 1, category_id='1')], categories=_categories()))
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'Latte', 1, category_id='2')], categories=_categories()))
    assert MenuItem.query.one().category.fudo_category_id == '2'


def test_sync_puts_products_without_category_in_sin_categoria(menu_app):
    product = fudo_product(1, 'Raro', 1)
    product['relationships'] = {}
    sync_fudo_products(FakeFudoClient(products=[product], categories=_categories()))
    assert MenuItem.query.one().category.name == 'Sin categoría'
    assert MenuItem.query.one().category.fudo_category_id == '__none__'


def test_hidden_new_items_do_not_create_unpublished_changes(menu_app, storage):
    from app.services.menu_publish_service import publish, has_unpublished_changes
    publish(storage)
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'Latte', 1)], categories=_categories()))
    assert has_unpublished_changes() is False


def test_new_items_lists_unreviewed(menu_app):
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'A', 1), fudo_product(2, 'B', 1)], categories=_categories()))
    reviewed = MenuItem.query.filter_by(name='A').one()
    reviewed.reviewed_at = datetime.utcnow()
    db.session.commit()
    assert [i.name for i in new_items()] == ['B']


def test_reappearing_category_becomes_visible_again(menu_app):
    prods = [fudo_product(1, 'Latte', 1)]
    sync_fudo_products(FakeFudoClient(products=prods, categories=_categories()))
    sync_fudo_products(FakeFudoClient(products=prods, categories=[fudo_category(1, 'Cafetería')]))
    sync_fudo_products(FakeFudoClient(products=prods, categories=_categories()))
    cat = MenuCategory.query.filter_by(fudo_category_id='2').one()
    assert cat.is_visible is True and cat.fudo_status is None


def test_admin_hidden_category_stays_hidden(menu_app):
    prods = [fudo_product(1, 'Latte', 1)]
    sync_fudo_products(FakeFudoClient(products=prods, categories=_categories()))
    MenuCategory.query.filter_by(fudo_category_id='2').one().is_visible = False
    db.session.commit()
    sync_fudo_products(FakeFudoClient(products=prods, categories=_categories()))
    assert MenuCategory.query.filter_by(fudo_category_id='2').one().is_visible is False


def test_empty_category_list_does_not_flag_missing(menu_app):
    prods = [fudo_product(1, 'Latte', 1)]
    sync_fudo_products(FakeFudoClient(products=prods, categories=_categories()))
    sync_fudo_products(FakeFudoClient(products=prods, categories=[]))
    assert all(c.is_visible and c.fudo_status is None for c in MenuCategory.query.filter(MenuCategory.fudo_category_id.in_(['1', '2'])))


def test_long_category_name_gives_bounded_slug(menu_app):
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'L', 1)], categories=[fudo_category(1, 'x' * 300)]))
    assert len(MenuCategory.query.filter_by(fudo_category_id='1').one().slug) <= 120
