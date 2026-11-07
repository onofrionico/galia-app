"""Expansión de recetas de producción a insumos por unidad de rendimiento."""
from dataclasses import dataclass, field
from decimal import Decimal

from app.services.units import convert

# Módulos de permiso de la sección de recetas.
RECIPE_MODULES = ('Recipes', 'RecipeCosts', 'RecipesAdmin')


@dataclass
class Expansion:
    # supply_id -> cantidad en la unidad del insumo, por 1 unidad de rendimiento.
    supplies: dict = field(default_factory=dict)
    issues: list = field(default_factory=list)


def _dec(value):
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _add(target, supply_id, quantity):
    target[supply_id] = target.get(supply_id, Decimal('0')) + quantity


def _expand(recipe, visiting):
    if recipe.id in visiting:
        raise ValueError(f'Ciclo de recetas: {recipe.name}')
    visiting = visiting | {recipe.id}

    result = Expansion()
    if recipe.yield_quantity is None or _dec(recipe.yield_quantity) <= 0:
        result.issues.append(f'{recipe.name}: sin rendimiento')
        return result
    batch_yield = _dec(recipe.yield_quantity)

    totals = {}
    for item in recipe.ingredients:
        if item.sub_recipe is not None:
            base = item.sub_recipe
            label = base.name
        else:
            base = None
            label = item.supply.name
        if item.quantity is None:
            result.issues.append(f'{label}: cantidad a completar')
            continue
        quantity = _dec(item.quantity)

        if base is not None:
            # La base se expande siempre (también detecta ciclos), aunque la unidad no cierre.
            base_exp = _expand(base, visiting)
            result.issues.extend(base_exp.issues)
            if base.yield_quantity is None or _dec(base.yield_quantity) <= 0:
                continue  # el issue 'sin rendimiento' ya vino con la expansión de la base
            in_base_units = convert(quantity, item.unit, base.yield_unit)
            if in_base_units is None:
                result.issues.append(
                    f"{label}: unidad '{item.unit}' no convertible a {base.yield_unit}")
                continue
            for supply_id, per_unit in base_exp.supplies.items():
                _add(totals, supply_id, per_unit * in_base_units)
        else:
            supply = item.supply
            converted = convert(quantity, item.unit, supply.unit)
            if converted is None:
                result.issues.append(
                    f"{label}: unidad '{item.unit or 'sin unidad'}' no convertible a {supply.unit}")
                continue
            _add(totals, supply.id, converted)

    result.supplies = {supply_id: total / batch_yield for supply_id, total in totals.items()}
    return result


def expand_per_yield_unit(recipe):
    """Insumos (en la unidad de cada insumo) por 1 unidad de rendimiento de `recipe`.

    Los datos incompletos (sin rendimiento, cantidad a completar, unidad no
    convertible) no son errores: se omiten del resultado y quedan en `issues`.
    Un ciclo entre sub-recetas levanta ValueError.
    """
    return _expand(recipe, frozenset())
