import importlib.util
import os
from decimal import Decimal

import pytest
import sqlalchemy as sa

from app import create_app
from app.extensions import db
from app.models import Product, ProductCategory, Recipe, RecipeIngredient, Supply
from app.services.recipe_service import expand_per_yield_unit

MIGRATION = os.path.join(os.path.dirname(__file__), '..', 'migrations', 'versions', 'b7a0_add_recipes.py')

# Tabla legada definida aparte: no depende del modelo ProductRecipeItem (que se elimina después).
_legacy = sa.Table(
    'product_recipe_items', sa.MetaData(),
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('product_id', sa.Integer, nullable=False),
    sa.Column('supply_id', sa.Integer, nullable=False),
    sa.Column('quantity', sa.Numeric(10, 4), nullable=False),
    sa.Column('unit', sa.String(50), nullable=False),
)


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        created = not sa.inspect(db.engine).has_table('product_recipe_items')
        if created:
            _legacy.create(db.engine)
        yield app
        db.session.remove()
        if created:
            _legacy.drop(db.engine)
        db.drop_all()


def _migration():
    spec = importlib.util.spec_from_file_location('b7a0_add_recipes', MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _product_with_composition():
    category = ProductCategory(name='Tortas')
    db.session.add(category)
    db.session.flush()
    product = Product(name='Torta de chocolate', category_id=category.id, has_recipe=True)
    harina = Supply(name='Harina', unit='kg')
    cacao = Supply(name='Cacao', unit='kg')
    db.session.add_all([product, harina, cacao])
    db.session.flush()
    db.session.execute(_legacy.insert(), [
        {'product_id': product.id, 'supply_id': harina.id, 'quantity': Decimal('250.0000'), 'unit': 'g'},
        {'product_id': product.id, 'supply_id': cacao.id, 'quantity': Decimal('0.0500'), 'unit': 'g'},
    ])
    db.session.commit()
    return product, harina, cacao


def test_copy_compositions_keeps_quantities(app):
    product, harina, cacao = _product_with_composition()
    _migration().copy_compositions(db.session.connection())
    db.session.commit()

    recipe = Recipe.query.filter_by(product_id=product.id).one()
    assert recipe.name == 'Torta de chocolate'
    assert recipe.yield_quantity == Decimal('1')
    assert recipe.yield_unit == 'unidad'
    assert recipe.pending_notes == 'Migrada de la composición anterior: faltan pasos.'
    by_supply = {i.supply_id: i for i in recipe.ingredients}
    assert by_supply[harina.id].quantity == Decimal('250')
    assert by_supply[cacao.id].quantity == Decimal('0.05')
    assert all(i.unit == 'kg' for i in recipe.ingredients)
    assert expand_per_yield_unit(recipe).supplies == {harina.id: Decimal('250'), cacao.id: Decimal('0.05')}


def test_copy_compositions_name_clash_gets_suffix(app):
    product, _, _ = _product_with_composition()
    db.session.add(Recipe(name='Torta de chocolate'))
    db.session.commit()
    _migration().copy_compositions(db.session.connection())
    db.session.commit()
    recipe = Recipe.query.filter_by(product_id=product.id).one()
    assert recipe.name == f'Torta de chocolate (producto #{product.id})'


def test_copy_compositions_is_idempotent(app):
    product, _, _ = _product_with_composition()
    migration = _migration()
    migration.copy_compositions(db.session.connection())
    migration.copy_compositions(db.session.connection())
    db.session.commit()
    recipe = Recipe.query.filter_by(product_id=product.id).one()
    assert Recipe.query.count() == 1
    assert len(recipe.ingredients) == 2


def test_copy_compositions_keeps_free_text_supply_unit(app):
    """Un insumo con unidad libre ('paquete') sigue expandiéndose con la cantidad vieja."""
    category = ProductCategory(name='Tortas')
    db.session.add(category)
    db.session.flush()
    product = Product(name='Caja de alfajores', category_id=category.id, has_recipe=True)
    envase = Supply(name='Envase', unit='paquete')
    db.session.add_all([product, envase])
    db.session.flush()
    db.session.execute(_legacy.insert(), [
        {'product_id': product.id, 'supply_id': envase.id, 'quantity': Decimal('250.0000'), 'unit': 'paquete'},
    ])
    db.session.commit()
    _migration().copy_compositions(db.session.connection())
    db.session.commit()
    recipe = Recipe.query.filter_by(product_id=product.id).one()
    result = expand_per_yield_unit(recipe)
    assert result.supplies == {envase.id: Decimal('250')}
    assert result.issues == []


def test_copy_compositions_accepts_long_supply_unit(app):
    assert Recipe.__table__.c.yield_unit.type.length == 50
    assert RecipeIngredient.__table__.c.unit.type.length == 50
