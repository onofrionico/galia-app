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
