from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.menu import FudoProduct
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_variant import ProductVariant
from app.services import menu_sync_service
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
