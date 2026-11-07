from decimal import Decimal

import pytest

from app import create_app
from app.extensions import db
from app.models import Recipe, RecipeIngredient, Supply
from app.services.recipe_service import RECIPE_MODULES, expand_per_yield_unit


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _supply(name, unit='kg'):
    supply = Supply(name=name, unit=unit)
    db.session.add(supply)
    db.session.flush()
    return supply


def _recipe(name, yield_quantity, yield_unit, ingredients):
    """ingredients: lista de (supply|Recipe|None, cantidad, unidad)."""
    recipe = Recipe(name=name, yield_quantity=yield_quantity, yield_unit=yield_unit)
    for position, (source, quantity, unit) in enumerate(ingredients):
        item = RecipeIngredient(position=position, quantity=quantity, unit=unit)
        if isinstance(source, Recipe):
            item.sub_recipe = source
        else:
            item.supply = source
        recipe.ingredients.append(item)
    db.session.add(recipe)
    db.session.flush()
    return recipe


def test_modules_constant():
    assert RECIPE_MODULES == ('Recipes', 'RecipeCosts', 'RecipesAdmin')


def test_batch_divided_by_yield(app):
    mandioca = _supply('Mandioca', 'kg')
    chipa = _recipe('Chipa', 20, 'unidad', [(mandioca, 1000, 'g')])
    result = expand_per_yield_unit(chipa)
    assert result.supplies == {mandioca.id: Decimal('0.05')}
    assert result.issues == []


def test_sub_recipe_expands_through_base(app):
    harina = _supply('Harina', 'kg')
    bizcocho = _recipe('Bizcocho', 1, 'unidad', [(harina, 400, 'g')])
    torta = _recipe('Torta', 1, 'unidad', [(bizcocho, 1, 'unidad')])
    result = expand_per_yield_unit(torta)
    assert result.supplies == {harina.id: Decimal('0.4')}
    assert result.issues == []


def test_sub_recipe_in_grams_of_base_in_grams(app):
    harina = _supply('Harina', 'kg')
    azucar = _supply('Azúcar', 'kg')
    base = _recipe('Masa base', 1200, 'g', [(harina, 800, 'g'), (azucar, 400, 'g')])
    torta = _recipe('Torta', 1, 'unidad', [(base, 600, 'g')])
    result = expand_per_yield_unit(torta)
    assert result.supplies == {harina.id: Decimal('0.4'), azucar.id: Decimal('0.2')}
    assert result.issues == []


def test_base_unit_mismatch_is_issue(app):
    harina = _supply('Harina', 'kg')
    manteca = _supply('Manteca', 'kg')
    bizcocho = _recipe('Bizcocho', 1, 'unidad', [(harina, 400, 'g')])
    torta = _recipe('Torta', 1, 'unidad', [(bizcocho, 500, 'g'), (manteca, 100, 'g')])
    result = expand_per_yield_unit(torta)
    assert result.supplies == {manteca.id: Decimal('0.1')}
    assert len(result.issues) == 1
    assert 'Bizcocho' in result.issues[0]


def test_null_quantity_is_issue_not_error(app):
    leche = _supply('Leche', 'l')
    sal = _supply('Sal', 'kg')
    receta = _recipe('Pan', 10, 'unidad', [(leche, None, 'l'), (sal, 100, 'g')])
    result = expand_per_yield_unit(receta)
    assert result.supplies == {sal.id: Decimal('0.01')}
    assert result.issues == ['Leche: cantidad a completar']


def test_unconvertible_unit_is_issue(app):
    manteca = _supply('Manteca', 'kg')
    receta = _recipe('Masa', 1, 'unidad', [(manteca, 2, 'cucharada')])
    result = expand_per_yield_unit(receta)
    assert result.supplies == {}
    assert result.issues == ["Manteca: unidad 'cucharada' no convertible a kg"]


def test_missing_yield_is_issue(app):
    harina = _supply('Harina', 'kg')
    receta = _recipe('Bizcocho', None, None, [(harina, 400, 'g')])
    result = expand_per_yield_unit(receta)
    assert result.supplies == {}
    assert result.issues == ['Bizcocho: sin rendimiento']


def test_cycle_raises(app):
    a = _recipe('A', 1, 'unidad', [])
    b = _recipe('B', 1, 'unidad', [(a, 1, 'unidad')])
    a.ingredients.append(RecipeIngredient(position=0, quantity=1, unit='unidad', sub_recipe=b))
    db.session.flush()
    with pytest.raises(ValueError, match='Ciclo de recetas'):
        expand_per_yield_unit(a)
