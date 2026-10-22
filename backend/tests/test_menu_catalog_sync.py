from decimal import Decimal

from app.extensions import db
from app.models import Product, ProductCategory, ProductVariant
from app.models.menu import MenuCategory, MenuItem, MenuItemVariant
from app.services import cutover, menu_catalog_sync
from app.services.menu_publish_service import publish
from app.tasks.menu_tasks import sync_and_publish
from pos_helpers import make_catalog


def _menu_item(name, fudo_product_id, price, fudo_category_id='3'):
    category = MenuCategory.query.filter_by(fudo_category_id=fudo_category_id).first()
    if category is None:
        category = MenuCategory(name='Panadería carta', slug=f'cat-{fudo_category_id}', fudo_category_id=fudo_category_id)
        db.session.add(category)
        db.session.flush()
    item = MenuItem(category_id=category.id, name=name)
    item.variants = [MenuItemVariant(fudo_product_id=fudo_product_id, price=Decimal(price), fudo_status='ok')]
    db.session.add(item)
    db.session.commit()
    return item


def _linked_catalog():
    cat = make_catalog()
    cat.unidad.fudo_product_id = '77'
    cat.category.fudo_category_id = '3'
    db.session.commit()
    return cat


def _switch_on():
    settings = cutover.get_settings()
    settings.catalog_in_galia = True
    db.session.commit()


def test_link_to_catalog_by_fudo_ids(menu_app):
    cat = _linked_catalog()
    linked = _menu_item('Medialuna de manteca', '77', '900')
    orphan = _menu_item('Torta vieja', '99', '5000')
    stats = menu_catalog_sync.link_to_catalog()
    db.session.commit()
    assert stats == {'variants_linked': 1, 'variants_unlinked': 1, 'categories_linked': 1}
    assert linked.variants[0].product_variant_id == cat.unidad.id
    assert orphan.variants[0].fudo_status == 'missing'
    assert MenuCategory.query.filter_by(fudo_category_id='3').one().product_category_id == cat.category.id
    assert menu_catalog_sync.link_to_catalog() == stats  # idempotente


def test_sync_from_catalog_updates_price_and_publishes(menu_app, storage):
    cat = _linked_catalog()
    _menu_item('Medialuna', '77', '900')
    menu_catalog_sync.link_to_catalog()
    _switch_on()
    publish(storage)
    storage.objects.pop('menu.json')
    cat.unidad.price = Decimal('1000')
    db.session.commit()
    result = sync_and_publish(None, storage)
    assert result['price_changes'] == 1 and result['published'] is True
    assert MenuItemVariant.query.filter_by(product_variant_id=cat.unidad.id).one().price == Decimal('1000')


def test_sync_from_catalog_keeps_owner_text_and_flags_inactive(menu_app):
    cat = _linked_catalog()
    item = _menu_item('Medialuna', '77', '900')
    menu_catalog_sync.link_to_catalog()
    item.name = 'Medialuna de manteca'
    item.description = 'Recién horneada'
    cat.unidad.is_active = False
    db.session.commit()
    stats = menu_catalog_sync.sync_from_catalog()
    item = db.session.get(MenuItem, item.id)
    assert item is not None and item.name == 'Medialuna de manteca' and item.description == 'Recién horneada'
    assert item.variants[0].fudo_status == 'inactive' and stats['alerts'] >= 1


def test_new_galia_product_creates_hidden_item(menu_app):
    _linked_catalog()
    category = ProductCategory.query.first()
    tostado = Product(name='Tostado', category_id=category.id)
    db.session.add(tostado)
    db.session.flush()
    db.session.add_all([ProductVariant(product_id=tostado.id, name='Simple', price=Decimal('5000'), stock_quantity=0,
                                       min_stock=0),
                        ProductVariant(product_id=tostado.id, name='Doble', price=Decimal('7000'), stock_quantity=0,
                                       min_stock=0)])
    db.session.commit()
    stats = menu_catalog_sync.sync_from_catalog()
    item = MenuItem.query.filter_by(name='Tostado').one()
    assert item.is_visible is False and item.reviewed_at is None
    assert sorted(v.label for v in item.variants) == ['Doble', 'Simple']
    assert stats['items_created'] >= 1
    assert MenuCategory.query.filter_by(product_category_id=category.id).one() == item.category


def test_ignored_variant_not_recreated(menu_app):
    cat = _linked_catalog()
    cat.taza.menu_ignored = True
    db.session.commit()
    menu_catalog_sync.sync_from_catalog()
    assert MenuItem.query.filter_by(name='Cortado').count() == 0
    assert MenuItem.query.filter_by(name='Medialuna').count() == 1


def test_menu_routes_use_catalog_when_switched(menu_client, admin_headers, monkeypatch):
    cat = _linked_catalog()
    item = _menu_item('Medialuna', '77', '900')
    menu_catalog_sync.link_to_catalog()
    _switch_on()
    monkeypatch.setattr('app.routes.menu.FudoClient', lambda: (_ for _ in ()).throw(AssertionError('Fudo')))
    response = menu_client.post('/api/v1/menu/sync', headers=admin_headers)
    assert response.status_code == 200 and 'price_changes' in response.get_json()
    assert menu_client.post(f'/api/v1/menu/items/{item.id}/ignore', headers=admin_headers).status_code == 200
    assert db.session.get(ProductVariant, cat.unidad.id).menu_ignored is True


def test_tasks_use_catalog_when_switched(menu_app, storage, monkeypatch):
    _linked_catalog()
    _switch_on()
    from app.services import menu_sync_service

    def boom(client):
        raise AssertionError('no tiene que llamar a Fudo')

    monkeypatch.setattr(menu_sync_service, 'sync_fudo_products', boom)
    result = sync_and_publish(None, storage)
    assert 'price_changes' in result
