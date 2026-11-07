"""Costo de recetas de producción."""
from datetime import date
from decimal import Decimal

from app.extensions import db
from app.models import Recipe, RecipeIngredient, Supply, SupplyPrice
from app.services.recipe_service import recipe_cost
from pos_helpers import make_user, pos_app  # noqa: F401


def _supply(name, unit, *prices):
    supply = Supply(name=name, unit=unit, stock_quantity=0, min_stock=0)
    db.session.add(supply)
    db.session.flush()
    user = make_user(f'{name}@x.com'.replace(' ', ''))
    for day, price in enumerate(prices, start=1):
        db.session.add(SupplyPrice(supply_id=supply.id, price=Decimal(price), recorded_at=date(2026, 1, day),
                                   created_by=user.id))
    db.session.flush()
    return supply


def _recipe(name, yield_quantity, yield_unit, items):
    recipe = Recipe(name=name, yield_quantity=Decimal(yield_quantity), yield_unit=yield_unit)
    db.session.add(recipe)
    db.session.flush()
    for position, (kind, ref, quantity, unit) in enumerate(items):
        db.session.add(RecipeIngredient(
            recipe_id=recipe.id, position=position, quantity=Decimal(quantity), unit=unit,
            supply_id=ref.id if kind == 'supply' else None,
            sub_recipe_id=ref.id if kind == 'base' else None))
    db.session.flush()
    db.session.refresh(recipe)
    return recipe


def test_cost_uses_latest_price_and_converts(pos_app):
    manteca = _supply('Manteca', 'kg', '5000', '8000')
    recipe = _recipe('Masa', '1', 'unidad', [('supply', manteca, '250', 'g')])
    cost = recipe_cost(recipe)
    assert cost['lines'][0]['cost'] == Decimal('2000')
    assert cost['batch_cost'] == Decimal('2000')
    assert cost['complete'] is True


def test_unit_cost_divides_by_yield(pos_app):
    harina = _supply('Harina', 'kg', '3000')
    recipe = _recipe('Budín', '20', 'porción', [('supply', harina, '1', 'kg')])
    cost = recipe_cost(recipe)
    assert cost['batch_cost'] == Decimal('3000')
    assert cost['unit_cost'] == Decimal('150')


def test_base_cost_flows_into_parent(pos_app):
    dulce = _supply('Dulce de leche', 'kg', '5000')
    base = _recipe('Relleno', '1000', 'g', [('supply', dulce, '1', 'kg')])
    assert recipe_cost(base)['unit_cost'] == Decimal('5')
    parent = _recipe('Alfajor', '10', 'unidad', [('base', base, '300', 'g')])
    cost = recipe_cost(parent)
    assert cost['lines'][0]['cost'] == Decimal('1500')
    assert cost['batch_cost'] == Decimal('1500')


def test_missing_price_is_incomplete(pos_app):
    sal = _supply('Sal fina', 'kg')
    recipe = _recipe('Mezcla', '1', 'unidad', [('supply', sal, '10', 'g')])
    cost = recipe_cost(recipe)
    assert cost['complete'] is False
    assert cost['batch_cost'] == Decimal('0')
    assert any('Sal fina' in issue and 'Sin precio cargado' in issue for issue in cost['issues'])
    assert cost['lines'][0]['cost'] is None
