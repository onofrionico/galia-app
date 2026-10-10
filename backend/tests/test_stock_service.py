import pytest

from app import create_app
from app.extensions import db
from app.models import Product, ProductCategory, ProductRecipeItem, ProductVariant, Supply
from app.services.stock_service import deduct_stock_for_sale


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _category():
    category = ProductCategory.query.filter_by(name='Cafés').first()
    if category is None:
        category = ProductCategory(name='Cafés')
        db.session.add(category)
        db.session.flush()
    return category


def _simple_variant(stock=10, track_stock=True):
    product = Product(name='Medialuna', category_id=_category().id, has_recipe=False, track_stock=track_stock)
    db.session.add(product)
    db.session.flush()
    variant = ProductVariant(product_id=product.id, name='Unidad', price=500, stock_quantity=stock, min_stock=2)
    db.session.add(variant)
    db.session.commit()
    return variant


def _recipe_variant():
    product = Product(name='Café con leche', category_id=_category().id, has_recipe=True)
    db.session.add(product)
    db.session.flush()
    cafe = Supply(name='Café', unit='kg', stock_quantity=5, min_stock=1)
    leche = Supply(name='Leche', unit='L', stock_quantity=10, min_stock=2)
    db.session.add_all([cafe, leche])
    db.session.flush()
    db.session.add_all([
        ProductRecipeItem(product_id=product.id, supply_id=cafe.id, quantity=0.02, unit='kg'),
        ProductRecipeItem(product_id=product.id, supply_id=leche.id, quantity=0.2, unit='L'),
    ])
    variant = ProductVariant(product_id=product.id, name='Taza', price=2500, stock_quantity=0, min_stock=0)
    db.session.add(variant)
    db.session.commit()
    return variant, cafe, leche


def test_deducts_variant_stock_for_simple_product(app):
    variant = _simple_variant(stock=10)
    deduct_stock_for_sale([{'product_variant_id': variant.id, 'quantity': 3}])
    db.session.commit()
    assert float(db.session.get(ProductVariant, variant.id).stock_quantity) == 7


def test_simple_product_insufficient_stock_raises(app):
    variant = _simple_variant(stock=2)
    with pytest.raises(ValueError, match='Stock insuficiente'):
        deduct_stock_for_sale([{'product_variant_id': variant.id, 'quantity': 3}])


def test_deducts_supplies_for_recipe_product(app):
    variant, cafe, leche = _recipe_variant()
    deduct_stock_for_sale([{'product_variant_id': variant.id, 'quantity': 5}])
    db.session.commit()
    assert float(db.session.get(Supply, cafe.id).stock_quantity) == pytest.approx(4.9)
    assert float(db.session.get(Supply, leche.id).stock_quantity) == pytest.approx(9.0)


def test_untracked_product_sells_without_stock(app):
    variant = _simple_variant(stock=0, track_stock=False)
    deduct_stock_for_sale([{'product_variant_id': variant.id, 'quantity': 4}])
    db.session.commit()
    assert float(db.session.get(ProductVariant, variant.id).stock_quantity) == 0


@pytest.mark.parametrize('quantity', [0, -1, 'abc', None, True])
def test_invalid_quantity_raises(app, quantity):
    variant = _simple_variant(stock=10)
    with pytest.raises(ValueError):
        deduct_stock_for_sale([{'product_variant_id': variant.id, 'quantity': quantity}])
    assert float(db.session.get(ProductVariant, variant.id).stock_quantity) == 10


def test_failure_in_second_item_does_not_deduct_first(app):
    first = _simple_variant(stock=10)
    cafe_variant, cafe, leche = _recipe_variant()
    with pytest.raises(ValueError, match='Stock insuficiente'):
        deduct_stock_for_sale([
            {'product_variant_id': first.id, 'quantity': 3},
            {'product_variant_id': cafe_variant.id, 'quantity': 1000},
        ])
    assert float(db.session.get(ProductVariant, first.id).stock_quantity) == 10
    assert float(db.session.get(Supply, cafe.id).stock_quantity) == 5


def test_exact_stock_boundary_is_allowed(app):
    variant = _simple_variant(stock=3)
    deduct_stock_for_sale([{'product_variant_id': variant.id, 'quantity': 3}])
    db.session.commit()
    assert float(db.session.get(ProductVariant, variant.id).stock_quantity) == 0


def test_duplicate_lines_are_aggregated(app):
    variant = _simple_variant(stock=5)
    with pytest.raises(ValueError, match='Stock insuficiente'):
        deduct_stock_for_sale([
            {'product_variant_id': variant.id, 'quantity': 3},
            {'product_variant_id': variant.id, 'quantity': 3},
        ])
    assert float(db.session.get(ProductVariant, variant.id).stock_quantity) == 5
    deduct_stock_for_sale([
        {'product_variant_id': variant.id, 'quantity': 2},
        {'product_variant_id': variant.id, 'quantity': 3},
    ])
    db.session.commit()
    assert float(db.session.get(ProductVariant, variant.id).stock_quantity) == 0


def test_recipe_supplies_aggregate_across_variants(app):
    variant, cafe, leche = _recipe_variant()
    with pytest.raises(ValueError, match='Stock insuficiente de Café'):
        deduct_stock_for_sale([
            {'product_variant_id': variant.id, 'quantity': 150},
            {'product_variant_id': variant.id, 'quantity': 150},
        ])
    assert float(db.session.get(Supply, cafe.id).stock_quantity) == 5


def test_unknown_variant_raises(app):
    with pytest.raises(ValueError, match='no encontrado'):
        deduct_stock_for_sale([{'product_variant_id': 999, 'quantity': 1}])
