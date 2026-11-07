import json
import os

import pytest

from app import create_app
from app.extensions import db
from app.models import Product, ProductCategory, Recipe, RecipeIngredient, RecipeStep, Supply, SupplyPrice, User
from scripts.import_recetario import DATA_PATH, run_import


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def admin(app):
    user = User(email='admin@test.com', role='admin', is_active=True)
    user.set_password('secret123')
    db.session.add(user)
    db.session.commit()
    return user


def _product(name, has_recipe=False):
    category = ProductCategory.query.first()
    if category is None:
        category = ProductCategory(name='Pastelería')
        db.session.add(category)
        db.session.flush()
    product = Product(name=name, category_id=category.id, has_recipe=has_recipe, track_stock=False)
    db.session.add(product)
    db.session.commit()
    return product


def _recipe(name, product_name=None, ingredients=None, is_base=False, yield_quantity=10):
    return {'name': name, 'product_name': product_name, 'is_base': is_base,
            'yield_quantity': yield_quantity, 'yield_unit': 'unidad' if yield_quantity else None,
            'total_time_minutes': None, 'advance_notes': None, 'notes': None, 'pending_notes': None,
            'ingredients': ingredients or [],
            'steps': [{'title': 'Hornear', 'instruction': 'Hornear', 'temperature_c': 180, 'time_min': 10,
                       'time_max': 12, 'doneness': None, 'tip': None}]}


def _data(*recipes):
    return {'recipes': list(recipes), 'doubts': []}


def test_dry_run_writes_nothing(app, admin):
    data = _data(_recipe('Chipa', 'Chipa', [{'supply_name': 'Mandioca', 'quantity': 1, 'unit': 'kg', 'note': None}]))
    _product('Chipa')

    report = run_import(data, apply=False, user=admin)

    assert report.created_recipes == ['Chipa']
    assert report.created_supplies == [('Mandioca', 'kg')]
    assert report.linked == [('Chipa', 'Chipa')]
    assert report.errors == []
    assert Recipe.query.count() == 0
    assert Supply.query.count() == 0
    assert RecipeIngredient.query.count() == 0
    assert RecipeStep.query.count() == 0


def test_matches_supply_ignoring_case_and_accents(app, admin):
    existing = Supply(name='Azúcar Rubia', unit='kg')
    db.session.add(existing)
    db.session.commit()
    data = _data(_recipe('Cookie', ingredients=[
        {'supply_name': 'azucar  rubia', 'quantity': 100, 'unit': 'g', 'note': None}]))

    report = run_import(data, apply=True, user=admin)

    assert report.created_supplies == []
    recipe = Recipe.query.filter_by(name='Cookie').one()
    assert recipe.ingredients[0].supply_id == existing.id
    assert Supply.query.count() == 1


def test_matches_supply_in_plural_and_reports_it(app, admin):
    huevos = Supply(name='Huevos', unit='unidad')
    nueces = Supply(name='Nueces', unit='kg')
    db.session.add_all([huevos, nueces])
    db.session.commit()
    data = _data(_recipe('Torta', ingredients=[
        {'supply_name': 'Huevo', 'quantity': 2, 'unit': 'unidad', 'note': None},
        {'supply_name': 'Nuez', 'quantity': 40, 'unit': 'g', 'note': None}]))

    report = run_import(data, apply=True, user=admin)

    assert report.created_supplies == []
    assert report.matched_supplies == [('Huevo', 'Huevos'), ('Nuez', 'Nueces')]
    recipe = Recipe.query.filter_by(name='Torta').one()
    assert [i.supply_id for i in recipe.ingredients] == [huevos.id, nueces.id]


def test_creates_missing_supply_without_price(app, admin):
    data = _data(_recipe('Torta', ingredients=[
        {'supply_name': 'Cacao amargo', 'quantity': 100, 'unit': 'g', 'note': None},
        {'supply_name': 'Leche', 'quantity': 150, 'unit': 'ml', 'note': None},
        {'supply_name': 'Huevo', 'quantity': 5, 'unit': 'unidad', 'note': None},
        {'supply_name': 'Sal', 'quantity': None, 'unit': None, 'note': 'pizca'}]))

    report = run_import(data, apply=True, user=admin)

    assert report.created_supplies == [('Cacao amargo', 'kg'), ('Leche', 'l'), ('Huevo', 'unidad'),
                                       ('Sal', 'a completar')]
    assert SupplyPrice.query.count() == 0
    recipe = Recipe.query.filter_by(name='Torta').one()
    assert recipe.updated_by == admin.id
    sal = recipe.ingredients[3]
    assert sal.quantity is None and sal.unit is None and sal.note == 'pizca'


def test_links_product_without_recipe_but_does_not_activate_stock(app, admin):
    product = _product('Chipa')

    report = run_import(_data(_recipe('Chipa', 'chipa')), apply=True, user=admin)

    assert report.linked == [('Chipa', 'Chipa')]
    db.session.refresh(product)
    assert product.recipe.name == 'Chipa'
    assert product.has_recipe is False


def test_does_not_overwrite_product_that_already_has_recipe(app, admin):
    product = _product('Torta Galia')
    db.session.add(Recipe(name='Composición vieja', product_id=product.id, yield_quantity=1, yield_unit='unidad'))
    db.session.commit()

    report = run_import(_data(_recipe('Torta de la planilla', 'Torta Galia')), apply=True, user=admin)

    assert report.created_recipes == ['Torta de la planilla']
    assert report.linked == []
    assert 'Composición vieja' in report.unlinked_reasons['Torta de la planilla']
    assert Recipe.query.filter_by(name='Torta de la planilla').one().product_id is None
    assert Recipe.query.filter_by(name='Composición vieja').one().product_id == product.id


def test_does_not_link_product_with_stock_active_and_no_recipe(app, admin):
    product = _product('Chipa', has_recipe=True)

    report = run_import(_data(_recipe('Chipa', 'Chipa')), apply=True, user=admin)

    assert report.linked == []
    assert 'Chipa' in report.unlinked_reasons
    assert Recipe.query.filter_by(name='Chipa').one().product_id is None
    db.session.refresh(product)
    assert product.has_recipe is True


def test_same_name_as_migrated_composition_loads_as_planilla(app, admin):
    product = _product('Torta Galia')
    db.session.add(Recipe(name='Torta Galia', product_id=product.id, yield_quantity=1, yield_unit='unidad'))
    db.session.commit()

    report = run_import(_data(_recipe('Torta Galia', 'Torta Galia')), apply=True, user=admin)
    assert report.created_recipes == ['Torta Galia (planilla)']
    assert 'Torta Galia (planilla)' in report.unlinked_reasons

    again = run_import(_data(_recipe('Torta Galia', 'Torta Galia')), apply=True, user=admin)
    assert again.created_recipes == []
    assert again.skipped_existing == ['Torta Galia (planilla)']


def test_unmatched_product_is_reported(app, admin):
    report = run_import(_data(_recipe('Matilda', 'Matilda')), apply=True, user=admin)

    assert report.unmatched_products == ['Matilda']
    assert report.linked == []
    assert Recipe.query.filter_by(name='Matilda').one().product_id is None


def test_rerun_skips_existing_recipe_by_name(app, admin):
    data = _data(_recipe('Chipa', ingredients=[{'supply_name': 'Mandioca', 'quantity': 1, 'unit': 'kg', 'note': None}]))
    run_import(data, apply=True, user=admin)

    report = run_import(data, apply=True, user=admin)

    assert report.created_recipes == []
    assert report.skipped_existing == ['Chipa']
    assert report.created_supplies == []
    assert Recipe.query.count() == 1
    assert Supply.query.count() == 1


def test_sub_recipes_created_before_parents(app, admin):
    parent = _recipe('Torta', ingredients=[
        {'sub_recipe_name': 'Almíbar', 'quantity': 1, 'unit': 'tanda', 'note': None}])
    base = _recipe('Almíbar', is_base=True, ingredients=[
        {'supply_name': 'Leche', 'quantity': 200, 'unit': 'ml', 'note': None}])
    base['yield_quantity'], base['yield_unit'] = 1, 'tanda'

    report = run_import(_data(parent, base), apply=True, user=admin)

    assert report.created_recipes == ['Almíbar', 'Torta']
    torta = Recipe.query.filter_by(name='Torta').one()
    almibar = Recipe.query.filter_by(name='Almíbar').one()
    assert torta.ingredients[0].sub_recipe_id == almibar.id
    assert almibar.product_id is None


def test_invalid_recipe_aborts_everything(app, admin):
    bad = _recipe('Mala', ingredients=[{'supply_name': 'Leche', 'quantity': 200, 'unit': None, 'note': None}])

    report = run_import(_data(_recipe('Buena'), bad), apply=True, user=admin)

    assert report.errors and 'Mala' in report.errors[0]
    assert Recipe.query.count() == 0
    assert Supply.query.count() == 0


def test_curated_recetario_imports_cleanly(app, admin):
    with open(DATA_PATH, encoding='utf-8') as handle:
        data = json.load(handle)
    _product('Torta Galia')

    report = run_import(data, apply=True, user=admin)

    assert report.errors == []
    assert len(report.created_recipes) == len(data['recipes']) == 18
    assert report.linked == [('Torta Galia', 'Torta Galia')]
    assert Product.query.filter_by(name='Torta Galia').one().has_recipe is False
    names = {s.name for s in Supply.query}
    assert 'Huevos' not in names and 'Huevo' in names
    cookie = Recipe.query.filter_by(name='Cookie red velvet').one()
    assert float(cookie.yield_quantity) == 6.5
    assert Recipe.query.filter_by(name='Matilda').one().yield_quantity is None
    assert os.path.basename(DATA_PATH) == 'recetario_galia.json'
