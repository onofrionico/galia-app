from decimal import Decimal

import pytest

from app.extensions import db
from app.models.menu import FudoProduct, MenuCategory, MenuItem, MenuItemVariant
from app.services.menu_sync_service import sync_fudo_products, unassigned_products, alert_variants
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
    assert stats == {'products': 1, 'price_changes': 0, 'alerts': 0}


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


def test_sync_never_creates_or_deletes_menu_items(menu_app):
    _item_with_variant('1', '6900')
    sync_fudo_products(FakeFudoClient(products=[fudo_product(2, 'Nuevo', 100)]))
    assert MenuItem.query.count() == 1
    assert MenuItemVariant.query.count() == 1


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


def test_unassigned_excludes_linked_ignored_and_inactive(menu_app):
    sync_fudo_products(FakeFudoClient(products=[
        fudo_product(1, 'Vinculado', 1),
        fudo_product(2, 'Ignorado', 1),
        fudo_product(3, 'Inactivo', 1, active=False),
        fudo_product(4, 'Libre', 1),
    ]))
    _item_with_variant('1', '1')
    db.session.get(FudoProduct, '2').ignored = True
    db.session.commit()

    assert [p.fudo_id for p in unassigned_products()] == ['4']
