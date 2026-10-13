from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.menu import FudoProduct
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_variant import ProductVariant
from app.services import menu_sync_service, product_sync_service
from menu_fakes import FakeFudoClient, fudo_category, fudo_product


def _manual_product(name='Medialuna', category_name='Panadería', price='1500'):
    category = ProductCategory.query.filter_by(name=category_name).first()
    if category is None:
        category = ProductCategory(name=category_name)
        db.session.add(category)
        db.session.flush()
    product = Product(name=name, category_id=category.id)
    db.session.add(product)
    db.session.flush()
    db.session.add(ProductVariant(product_id=product.id, name=name, price=Decimal(price)))
    db.session.commit()
    return product


def test_fudo_columns_in_to_dict(menu_app):
    category = ProductCategory(name='Cafés', fudo_category_id='7')
    db.session.add(category)
    db.session.flush()
    product = Product(name='Latte', category_id=category.id)
    db.session.add(product)
    db.session.flush()
    variant = ProductVariant(product_id=product.id, name='Latte', price=Decimal('6500'),
                             fudo_product_id='42', fudo_status='ok')
    db.session.add(variant)
    db.session.commit()

    assert category.to_dict()['fudo_category_id'] == '7'
    assert category.to_dict()['fudo_status'] is None
    assert variant.to_dict()['fudo_product_id'] == '42'
    assert variant.to_dict()['fudo_status'] == 'ok'


def test_fudo_product_id_is_unique(menu_app):
    product = _manual_product()
    db.session.add(ProductVariant(product_id=product.id, name='A', price=1, fudo_product_id='9'))
    db.session.add(ProductVariant(product_id=product.id, name='B', price=1, fudo_product_id='9'))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def _stats():
    return {'categories_created': 0}


def test_creates_categories_from_fudo(menu_app):
    stats = _stats()
    result = product_sync_service.sync_product_categories(
        [fudo_category(1, 'Cafés'), fudo_category(2, 'Pastelería')], stats)
    db.session.commit()

    assert set(result) == {'1', '2'}
    assert result['1'].name == 'Cafés'
    assert result['1'].is_active is True
    assert stats['categories_created'] == 2


def test_adopts_unlinked_category_with_same_name_ignoring_case(menu_app):
    manual = ProductCategory(name='cafés', color='#123456', icon='☕')
    db.session.add(manual)
    db.session.commit()

    stats = _stats()
    result = product_sync_service.sync_product_categories([fudo_category(1, 'Cafés')], stats)
    db.session.commit()

    assert result['1'].id == manual.id
    assert manual.fudo_category_id == '1'
    assert manual.color == '#123456' and manual.icon == '☕'
    assert stats['categories_created'] == 0
    assert ProductCategory.query.count() == 1


def test_adopts_category_with_accented_uppercase_name(menu_app):
    manual = ProductCategory(name='PANADERÍA')
    db.session.add(manual)
    db.session.commit()

    result = product_sync_service.sync_product_categories([fudo_category(1, 'PANADERÍA')], _stats())
    db.session.commit()

    assert result['1'].id == manual.id
    assert ProductCategory.query.count() == 1


def test_accented_name_clash_gets_suffix_instead_of_failing(menu_app):
    product_sync_service.sync_product_categories([fudo_category(1, 'PANADERÍA')], _stats())
    result = product_sync_service.sync_product_categories(
        [fudo_category(1, 'PANADERÍA'), fudo_category(2, 'Panadería')], _stats())
    db.session.commit()

    assert result['2'].name == 'Panadería (Fudo)'


def test_name_clash_with_other_linked_category_gets_suffix(menu_app):
    product_sync_service.sync_product_categories([fudo_category(1, 'Bebidas')], _stats())
    result = product_sync_service.sync_product_categories(
        [fudo_category(1, 'Bebidas'), fudo_category(2, 'Bebidas')], _stats())
    db.session.commit()

    assert result['1'].name == 'Bebidas'
    assert result['2'].name == 'Bebidas (Fudo)'


def test_suffixed_name_is_stable_across_syncs(menu_app):
    raw = [fudo_category(1, 'Bebidas'), fudo_category(2, 'Bebidas')]
    product_sync_service.sync_product_categories(raw, _stats())
    result = product_sync_service.sync_product_categories(raw, _stats())
    db.session.commit()

    assert result['2'].name == 'Bebidas (Fudo)'


def test_renames_linked_category(menu_app):
    product_sync_service.sync_product_categories([fudo_category(1, 'Cafes')], _stats())
    result = product_sync_service.sync_product_categories([fudo_category(1, 'Cafés de especialidad')], _stats())
    db.session.commit()

    assert result['1'].name == 'Cafés de especialidad'


def test_missing_category_is_deactivated_and_comes_back(menu_app):
    product_sync_service.sync_product_categories([fudo_category(1, 'Cafés'), fudo_category(2, 'Té')], _stats())
    result = product_sync_service.sync_product_categories([fudo_category(1, 'Cafés')], _stats())
    db.session.commit()
    assert result['2'].is_active is False
    assert result['2'].fudo_status == 'missing'

    result = product_sync_service.sync_product_categories([fudo_category(1, 'Cafés'), fudo_category(2, 'Té')], _stats())
    db.session.commit()
    assert result['2'].is_active is True
    assert result['2'].fudo_status is None


def test_empty_categories_do_not_mark_missing(menu_app):
    product_sync_service.sync_product_categories([fudo_category(1, 'Cafés')], _stats())
    result = product_sync_service.sync_product_categories([], _stats())
    db.session.commit()

    assert result['1'].is_active is True
    assert result['1'].fudo_status is None


def _sync(products, categories=None):
    return menu_sync_service.sync_fudo_products(FakeFudoClient(products=products, categories=categories or []))


def _variant(fudo_id):
    return ProductVariant.query.filter_by(fudo_product_id=str(fudo_id)).one()


def test_creates_products_from_scratch(menu_app):
    result = _sync([fudo_product(1, 'Latte', 6500), fudo_product(2, 'Té verde', 3000, active=False)],
                   [fudo_category(1, 'Cafés')])

    variant = _variant(1)
    product = db.session.get(Product, variant.product_id)
    assert product.name == 'Latte'
    assert product.category.name == 'Cafés'
    assert product.is_active is True
    assert variant.name == 'Latte'
    assert Decimal(variant.price) == Decimal('6500')
    assert variant.fudo_status == 'ok'
    assert Decimal(variant.stock_quantity) == 0
    assert ProductVariant.query.filter_by(fudo_product_id='2').count() == 0
    assert result['catalog'] == {'categories_created': 1, 'products_created': 1, 'variants_updated': 0, 'alerts': 0}


def test_updates_price_and_name(menu_app):
    _sync([fudo_product(1, 'Latte', 6500)], [fudo_category(1, 'Cafés')])
    result = _sync([fudo_product(1, 'Latte grande', 6900)], [fudo_category(1, 'Cafés')])

    variant = _variant(1)
    assert variant.name == 'Latte grande'
    assert Decimal(variant.price) == Decimal('6900')
    assert db.session.get(Product, variant.product_id).name == 'Latte grande'
    assert result['catalog']['variants_updated'] == 1


def test_inactive_in_fudo_deactivates_variant_and_product(menu_app):
    _sync([fudo_product(1, 'Latte', 6500)], [fudo_category(1, 'Cafés')])
    result = _sync([fudo_product(1, 'Latte', 6500, active=False)], [fudo_category(1, 'Cafés')])

    variant = _variant(1)
    assert variant.is_active is False
    assert variant.fudo_status == 'inactive'
    assert db.session.get(Product, variant.product_id).is_active is False
    assert result['catalog']['alerts'] == 1


def test_missing_in_fudo_keeps_variant_inactive(menu_app):
    _sync([fudo_product(1, 'Latte', 6500), fudo_product(2, 'Té', 3000)], [fudo_category(1, 'Cafés')])
    _sync([fudo_product(2, 'Té', 3000)], [fudo_category(1, 'Cafés')])

    variant = _variant(1)
    assert variant.is_active is False
    assert variant.fudo_status == 'missing'
    assert db.session.get(Product, variant.product_id) is not None


def test_reactivated_in_fudo_comes_back(menu_app):
    _sync([fudo_product(1, 'Latte', 6500)], [fudo_category(1, 'Cafés')])
    _sync([fudo_product(1, 'Latte', 6500, active=False)], [fudo_category(1, 'Cafés')])
    _sync([fudo_product(1, 'Latte', 6500)], [fudo_category(1, 'Cafés')])

    variant = _variant(1)
    assert variant.is_active is True
    assert variant.fudo_status == 'ok'
    assert db.session.get(Product, variant.product_id).is_active is True


def test_moves_product_when_fudo_category_changes(menu_app):
    categories = [fudo_category(1, 'Cafés'), fudo_category(2, 'Especiales')]
    _sync([fudo_product(1, 'Latte', 6500, category_id='1')], categories)
    _sync([fudo_product(1, 'Latte', 6500, category_id='2')], categories)

    product = db.session.get(Product, _variant(1).product_id)
    assert product.category.name == 'Especiales'


def test_product_without_category_goes_to_sin_categoria(menu_app):
    _sync([fudo_product(1, 'Agua', 1000, category_id=None)], [fudo_category(1, 'Cafés')])

    product = db.session.get(Product, _variant(1).product_id)
    assert product.category.name == 'Sin categoría'
    assert product.category.fudo_category_id == '__none__'


def test_unknown_category_keeps_existing_product_and_sends_new_to_sin_categoria(menu_app):
    _sync([fudo_product(1, 'Latte', 6500, category_id='1')], [fudo_category(1, 'Cafés')])
    _sync([fudo_product(1, 'Latte', 6500, category_id='9'), fudo_product(2, 'Té', 3000, category_id='9')], [])

    assert db.session.get(Product, _variant(1).product_id).category.name == 'Cafés'
    assert db.session.get(Product, _variant(2).product_id).category.name == 'Sin categoría'


def test_grouped_product_keeps_galia_name(menu_app):
    categories = [fudo_category(1, 'Cafés')]
    _sync([fudo_product(1, 'Café chico', 3000), fudo_product(2, 'Café grande', 3500)], categories)
    target = db.session.get(Product, _variant(1).product_id)
    _variant(2).product_id = target.id
    target.name = 'Café'
    db.session.commit()

    _sync([fudo_product(1, 'Café chico', 3200), fudo_product(2, 'Café grande', 3700)], categories)

    assert target.name == 'Café'
    assert _variant(1).name == 'Café chico'
    assert Decimal(_variant(2).price) == Decimal('3700')


def test_sync_never_touches_galia_fields(menu_app):
    _sync([fudo_product(1, 'Latte', 6500)], [fudo_category(1, 'Cafés')])
    variant = _variant(1)
    product = db.session.get(Product, variant.product_id)
    product.description = 'Con leche de almendras'
    product.image_url = 'https://cdn.test/latte.webp'
    product.has_recipe = True
    product.track_stock = True
    variant.stock_quantity = Decimal('12')
    variant.min_stock = Decimal('3')
    product.category.color = '#ff0000'
    product.category.icon = 'C'
    db.session.commit()

    _sync([fudo_product(1, 'Latte', 7000)], [fudo_category(1, 'Cafés')])

    assert product.description == 'Con leche de almendras'
    assert product.image_url == 'https://cdn.test/latte.webp'
    assert product.has_recipe is True and product.track_stock is True
    assert Decimal(variant.stock_quantity) == Decimal('12')
    assert Decimal(variant.min_stock) == Decimal('3')
    assert product.category.color == '#ff0000' and product.category.icon == 'C'


def test_manual_products_are_left_alone(menu_app):
    manual = _manual_product('Medialuna', 'Panadería')
    _sync([fudo_product(1, 'Latte', 6500)], [fudo_category(1, 'Cafés')])

    assert manual.name == 'Medialuna'
    assert manual.is_active is True
    assert manual.variants.first().fudo_product_id is None


def test_ignored_menu_products_are_still_created(menu_app):
    db.session.add(FudoProduct(fudo_id='1', name='Latte', price=Decimal('6500'), ignored=True))
    db.session.commit()

    _sync([fudo_product(1, 'Latte', 6500)], [fudo_category(1, 'Cafés')])

    assert ProductVariant.query.filter_by(fudo_product_id='1').count() == 1


def test_sync_is_idempotent(menu_app):
    products = [fudo_product(1, 'Latte', 6500), fudo_product(2, 'Té', 3000, category_id=None)]
    categories = [fudo_category(1, 'Cafés'), fudo_category(2, 'Cafés')]
    _sync(products, categories)
    snapshot = sorted((p.id, p.name, p.category_id, p.is_active) for p in Product.query.all())

    result = _sync(products, categories)

    assert result['catalog'] == {'categories_created': 0, 'products_created': 0, 'variants_updated': 0, 'alerts': 0}
    assert sorted((p.id, p.name, p.category_id, p.is_active) for p in Product.query.all()) == snapshot


def test_fudo_failure_changes_nothing(menu_app):
    _sync([fudo_product(1, 'Latte', 6500)], [fudo_category(1, 'Cafés')])
    with pytest.raises(ValueError):
        _sync([], [fudo_category(1, 'Cafés')])
    db.session.rollback()

    assert _variant(1).fudo_status == 'ok'
