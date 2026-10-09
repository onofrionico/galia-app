from decimal import Decimal

import pytest

from app import create_app
from app.extensions import db
from app.models import Product, ProductCategory, ProductRecipeItem, ProductVariant, Supply
from app.services.stock_service import deduct_stock_for_sale, move_stock, stock_requirements


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _setup():
    cat = ProductCategory(name='Cafés')
    db.session.add(cat)
    db.session.flush()
    cafe = Supply(name='Café', unit='kg', stock_quantity=Decimal('1'), min_stock=0)
    db.session.add(cafe)
    simple = Product(name='Medialuna', category_id=cat.id, has_recipe=False, track_stock=True)
    untracked = Product(name='Agua', category_id=cat.id, has_recipe=False, track_stock=False)
    recipe = Product(name='Cortado', category_id=cat.id, has_recipe=True)
    db.session.add_all([simple, untracked, recipe])
    db.session.flush()
    db.session.add(ProductRecipeItem(product_id=recipe.id, supply_id=cafe.id, quantity=Decimal('0.02'), unit='kg'))
    v_simple = ProductVariant(product_id=simple.id, name='Unidad', price=900, stock_quantity=Decimal('2'), min_stock=0)
    v_untracked = ProductVariant(product_id=untracked.id, name='Botella', price=1000, stock_quantity=0, min_stock=0)
    v_recipe = ProductVariant(product_id=recipe.id, name='Taza', price=2000, stock_quantity=0, min_stock=0)
    db.session.add_all([v_simple, v_untracked, v_recipe])
    db.session.commit()
    return cafe, v_simple, v_untracked, v_recipe


def test_requirements_split_variants_and_supplies(app):
    cafe, v_simple, v_untracked, v_recipe = _setup()
    variants, supplies = stock_requirements(
        {v_simple.id: Decimal('3'), v_untracked.id: Decimal('1'), v_recipe.id: Decimal('5')},
        extra_supplies={cafe.id: Decimal('0.1')},
    )
    assert variants == {v_simple.id: Decimal('3')}
    assert supplies == {cafe.id: Decimal('0.2')}


def test_unknown_variant_raises(app):
    with pytest.raises(ValueError, match='no encontrado'):
        stock_requirements({999: Decimal('1')})


def test_move_stock_allows_negative_when_asked(app):
    cafe, v_simple, _u, _r = _setup()
    move_stock({v_simple.id: Decimal('3')}, {cafe.id: Decimal('2')}, sign=-1, allow_negative=True)
    db.session.commit()
    assert Decimal(db.session.get(ProductVariant, v_simple.id).stock_quantity) == Decimal('-1')
    assert Decimal(db.session.get(Supply, cafe.id).stock_quantity) == Decimal('-1')


def test_move_stock_validates_by_default(app):
    _cafe, v_simple, _u, _r = _setup()
    with pytest.raises(ValueError, match='Stock insuficiente'):
        move_stock({v_simple.id: Decimal('3')}, {}, sign=-1)
    assert Decimal(db.session.get(ProductVariant, v_simple.id).stock_quantity) == Decimal('2')


def test_move_stock_restores(app):
    cafe, v_simple, _u, _r = _setup()
    move_stock({v_simple.id: Decimal('1')}, {cafe.id: Decimal('0.5')}, sign=1)
    db.session.commit()
    assert Decimal(db.session.get(ProductVariant, v_simple.id).stock_quantity) == Decimal('3')
    assert Decimal(db.session.get(Supply, cafe.id).stock_quantity) == Decimal('1.5')


def test_deduct_stock_for_sale_keeps_its_behavior(app):
    cafe, v_simple, _u, v_recipe = _setup()
    deduct_stock_for_sale([{'product_variant_id': v_simple.id, 'quantity': 2},
                           {'product_variant_id': v_recipe.id, 'quantity': 10}])
    db.session.commit()
    assert Decimal(db.session.get(ProductVariant, v_simple.id).stock_quantity) == Decimal('0')
    assert Decimal(db.session.get(Supply, cafe.id).stock_quantity) == Decimal('0.8')
    with pytest.raises(ValueError, match='Stock insuficiente'):
        deduct_stock_for_sale([{'product_variant_id': v_simple.id, 'quantity': 1}])
