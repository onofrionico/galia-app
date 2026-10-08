from decimal import Decimal

from app.extensions import db
from app.models.menu import MenuCategory, MenuItem, MenuItemVariant
from app.services.menu_publish_service import publish
from app.tasks.menu_tasks import sync_and_publish
from menu_fakes import FakeFudoClient, fudo_product


def _linked_item(price='6500'):
    category = MenuCategory(name='Cafés', slug='cafes')
    db.session.add(category)
    db.session.flush()
    item = MenuItem(category_id=category.id, name='Latte')
    item.variants = [MenuItemVariant(fudo_product_id='1', price=Decimal(price), fudo_status='ok')]
    db.session.add(item)
    db.session.commit()
    return item


def test_republishes_when_prices_change_and_no_drafts(menu_app, storage):
    _linked_item()
    publish(storage)
    storage.objects.pop('menu.json')

    result = sync_and_publish(FakeFudoClient(products=[fudo_product(1, 'Latte', 6900)]), storage)

    assert result['published'] is True
    assert 'menu.json' in storage.objects


def test_does_not_publish_drafts(menu_app, storage):
    item = _linked_item()
    publish(storage)
    item.name = 'Borrador'
    db.session.commit()
    storage.objects.pop('menu.json')

    result = sync_and_publish(FakeFudoClient(products=[fudo_product(1, 'Latte', 6900)]), storage)

    assert result['published'] is False
    assert 'menu.json' not in storage.objects


def test_does_not_publish_without_price_changes(menu_app, storage):
    _linked_item('6900')
    publish(storage)
    storage.objects.pop('menu.json')

    assert sync_and_publish(FakeFudoClient(products=[fudo_product(1, 'Latte', 6900)]), storage)['published'] is False


def test_does_not_publish_if_never_published(menu_app, storage):
    _linked_item()
    assert sync_and_publish(FakeFudoClient(products=[fudo_product(1, 'Latte', 6900)]), storage)['published'] is False


def test_does_not_publish_structure_changes(menu_app, storage):
    from app.models.menu import MenuCategory as Cat
    _linked_item()
    publish(storage)
    storage.objects.pop('menu.json')

    client = FakeFudoClient(
        products=[fudo_product(1, 'Latte', 6900, category_id='7')],
        categories=[{'id': '7', 'type': 'ProductCategory', 'attributes': {'name': 'Nueva'}}],
    )
    result = sync_and_publish(client, storage)

    assert result['price_changes'] == 1
    assert result['structure_changed'] is True
    assert result['published'] is False
    assert 'menu.json' not in storage.objects


def test_price_only_change_reports_no_structure_change(menu_app, storage):
    _linked_item()
    publish(storage)
    result = sync_and_publish(FakeFudoClient(products=[fudo_product(1, 'Latte', 6900)]), storage)
    assert result['published'] is True and result['structure_changed'] is False
