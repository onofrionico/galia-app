"""Expansión de recetas de producción a insumos por unidad de rendimiento."""
from dataclasses import dataclass, field
from decimal import Decimal

from app.extensions import db
from app.models import Product, Recipe, RecipeIngredient, RecipeStep, Supply, SupplyPrice
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


# ---------------------------------------------------------------------------
# Costo
# ---------------------------------------------------------------------------

def _latest_price(supply_id):
    """Último precio cargado del insumo (por la unidad del insumo), o None."""
    row = (SupplyPrice.query.filter_by(supply_id=supply_id)
           .order_by(SupplyPrice.recorded_at.desc(), SupplyPrice.id.desc()).first())
    return _dec(row.price) if row is not None else None


def _cost(recipe, visiting):
    if recipe.id in visiting:
        raise ValueError(f'Ciclo de recetas: {recipe.name}')
    visiting = visiting | {recipe.id}

    issues, lines, batch_cost = [], [], Decimal('0')
    for item in recipe.ingredients:
        line = {'ingredient_id': item.id, 'cost': None, 'issue': None}
        lines.append(line)
        base = item.sub_recipe
        label = base.name if base is not None else item.supply.name

        def fail(message):
            line['issue'] = f'{label}: {message}'
            issues.append(line['issue'])

        if item.quantity is None:
            fail('cantidad a completar')
            continue
        quantity = _dec(item.quantity)

        if base is not None:
            base_cost = _cost(base, visiting)
            issues.extend(base_cost['issues'])
            if base_cost['unit_cost'] is None:
                continue  # el issue 'sin rendimiento' ya vino con el costo de la base
            in_base_units = convert(quantity, item.unit, base.yield_unit)
            if in_base_units is None:
                fail(f"unidad '{item.unit}' no convertible a {base.yield_unit}")
                continue
            line['cost'] = base_cost['unit_cost'] * in_base_units
        else:
            supply = item.supply
            converted = convert(quantity, item.unit, supply.unit)
            if converted is None:
                fail(f"unidad '{item.unit or 'sin unidad'}' no convertible a {supply.unit}")
                continue
            price = _latest_price(supply.id)
            if price is None:
                fail('Sin precio cargado')
                continue
            line['cost'] = converted * price
        batch_cost += line['cost']

    unit_cost = None
    if recipe.yield_quantity is not None and _dec(recipe.yield_quantity) > 0:
        unit_cost = batch_cost / _dec(recipe.yield_quantity)
    else:
        issues.append(f'{recipe.name}: sin rendimiento')
    return {'batch_cost': batch_cost, 'unit_cost': unit_cost, 'complete': not issues,
            'issues': issues, 'lines': lines}


def recipe_cost(recipe):
    """Costo de una tanda y por unidad de rendimiento, con los datos faltantes en `issues`.

    El costo es parcial si algo falta: `batch_cost` suma sólo las líneas con costo
    y `complete` indica si no quedó nada afuera. Un ciclo levanta ValueError.
    """
    return _cost(recipe, frozenset())


# ---------------------------------------------------------------------------
# Validación y guardado
# ---------------------------------------------------------------------------

class RecipeError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


MAX_YIELD = Decimal('10000000')       # Numeric(10, 3)
MAX_QUANTITY = Decimal('100000000')   # Numeric(12, 4)


def _text(value, label, max_len=None):
    if value is None:
        return None
    if not isinstance(value, str):
        raise RecipeError(f'{label} debe ser texto')
    value = value.strip()
    if not value:
        return None
    if max_len is not None and len(value) > max_len:
        raise RecipeError(f'{label} no puede superar {max_len} caracteres')
    return value


def _number(value, label, maximum):
    """Decimal > 0, o None si viene vacío."""
    if value is None or value == '':
        return None
    if isinstance(value, bool):
        raise RecipeError(f'{label} debe ser un número')
    try:
        number = Decimal(str(value).strip())
    except Exception:
        raise RecipeError(f'{label} debe ser un número')
    if not number.is_finite():
        raise RecipeError(f'{label} debe ser un número')
    if number <= 0:
        raise RecipeError(f'{label} tiene que ser mayor a 0')
    if number >= maximum:
        raise RecipeError(f'{label} es demasiado grande')
    return number


def _minutes(value, label):
    if value is None or value == '':
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 100000:
        raise RecipeError(f'{label} es inválido')
    return value


def _clean_ingredients(raw):
    if not isinstance(raw, list):
        raise RecipeError('Los ingredientes tienen que ser una lista')
    cleaned = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise RecipeError(f'Ingrediente {index}: formato inválido')
        supply_id, sub_id = item.get('supply_id'), item.get('sub_recipe_id')
        if (supply_id is None) == (sub_id is None):
            raise RecipeError(f'Ingrediente {index}: indicá un insumo o una receta base, no ambos')
        ref = supply_id if supply_id is not None else sub_id
        if isinstance(ref, bool) or not isinstance(ref, int):
            raise RecipeError(f'Ingrediente {index}: referencia inválida')
        quantity = _number(item.get('quantity'), f'Ingrediente {index}: la cantidad', MAX_QUANTITY)
        unit = _text(item.get('unit'), f'Ingrediente {index}: la unidad', 50)
        if quantity is not None and unit is None:
            raise RecipeError(f'Ingrediente {index}: falta la unidad')
        cleaned.append({'supply_id': supply_id, 'sub_recipe_id': sub_id, 'quantity': quantity, 'unit': unit,
                        'note': _text(item.get('note'), f'Ingrediente {index}: la nota', 200)})
    return cleaned


def _clean_steps(raw):
    if not isinstance(raw, list):
        raise RecipeError('Los pasos tienen que ser una lista')
    cleaned = []
    for index, step in enumerate(raw, start=1):
        if not isinstance(step, dict):
            raise RecipeError(f'Paso {index}: formato inválido')
        title = _text(step.get('title'), f'Paso {index}: el título', 120)
        if title is None:
            raise RecipeError(f'Paso {index}: falta el título')
        temperature = step.get('temperature_c')
        if temperature is not None and (isinstance(temperature, bool) or not isinstance(temperature, int)
                                        or not -100 <= temperature <= 1000):
            raise RecipeError(f'Paso {index}: la temperatura es inválida')
        time_min = _minutes(step.get('time_min'), f'Paso {index}: el tiempo mínimo')
        time_max = _minutes(step.get('time_max'), f'Paso {index}: el tiempo máximo')
        if time_min is not None and time_max is not None and time_max < time_min:
            raise RecipeError(f'Paso {index}: el tiempo máximo es menor al mínimo')
        cleaned.append({'title': title, 'instruction': _text(step.get('instruction'), 'La instrucción'),
                        'temperature_c': temperature, 'time_min': time_min, 'time_max': time_max,
                        'doneness': _text(step.get('doneness'), 'El punto'),
                        'tip': _text(step.get('tip'), 'El consejo')})
    return cleaned


def _reaches(start_ids, target_id):
    """True si desde `start_ids` se llega a `target_id` siguiendo TODAS las aristas de sub-receta.

    No depende de cantidades ni rendimientos: un ciclo con datos incompletos igual
    rompería el descuento de stock cuando se completen. Las aristas salientes de
    `target_id` no importan (al llegar a él ya hay ciclo), así que no hace falta
    reemplazarlas por las nuevas.
    """
    edges = {}
    rows = db.session.query(RecipeIngredient.recipe_id, RecipeIngredient.sub_recipe_id) \
        .filter(RecipeIngredient.sub_recipe_id.isnot(None))
    for recipe_id, sub_id in rows:
        edges.setdefault(recipe_id, set()).add(sub_id)
    seen, stack = set(), list(start_ids)
    while stack:
        current = stack.pop()
        if current == target_id:
            return True
        if current in seen:
            continue
        seen.add(current)
        stack.extend(edges.get(current, ()))
    return False


def save_recipe(recipe, payload, user):
    """Crea (recipe=None) o reemplaza por completo una receta. Levanta RecipeError. No hace commit."""
    if not isinstance(payload, dict):
        raise RecipeError('El cuerpo tiene que ser un objeto JSON')

    name = _text(payload.get('name'), 'El nombre', 150)
    if name is None:
        raise RecipeError('El nombre de la receta es requerido')
    duplicate = Recipe.query.filter(Recipe.name == name)
    if recipe is not None:
        duplicate = duplicate.filter(Recipe.id != recipe.id)
    if duplicate.first() is not None:
        raise RecipeError('Ya existe una receta con ese nombre')

    yield_quantity = _number(payload.get('yield_quantity'), 'El rendimiento', MAX_YIELD)
    yield_unit = _text(payload.get('yield_unit'), 'La unidad de rendimiento', 50)
    if yield_quantity is not None and yield_unit is None:
        raise RecipeError('Falta la unidad de rendimiento')
    if yield_quantity is None:
        yield_unit = None
        product = recipe.product if recipe is not None else None
        if product is not None and product.has_recipe:
            raise RecipeError('No se puede quitar el rendimiento mientras la receta descuenta stock', 409)

    ingredients = _clean_ingredients(payload.get('ingredients', []))
    steps = _clean_steps(payload.get('steps', []))

    supply_ids = {i['supply_id'] for i in ingredients if i['supply_id'] is not None}
    if supply_ids:
        found = {s.id for s in Supply.query.filter(Supply.id.in_(supply_ids), Supply.is_active.is_(True))}
        if supply_ids - found:
            raise RecipeError('Algún insumo no existe o está inactivo')
    sub_ids = {i['sub_recipe_id'] for i in ingredients if i['sub_recipe_id'] is not None}
    if sub_ids:
        found = {r.id for r in Recipe.query.filter(Recipe.id.in_(sub_ids), Recipe.is_active.is_(True))}
        if sub_ids - found:
            raise RecipeError('Alguna receta base no existe o está inactiva')
    if recipe is not None and (recipe.id in sub_ids or _reaches(sub_ids, recipe.id)):
        raise RecipeError('Las recetas base no pueden formar un ciclo')

    if recipe is None:
        recipe = Recipe(name=name)
        db.session.add(recipe)
    recipe.name = name
    recipe.yield_quantity = yield_quantity
    recipe.yield_unit = yield_unit
    recipe.total_time_minutes = _minutes(payload.get('total_time_minutes'), 'El tiempo total')
    recipe.advance_notes = _text(payload.get('advance_notes'), 'Las notas de anticipación')
    recipe.notes = _text(payload.get('notes'), 'Las notas')
    recipe.pending_notes = _text(payload.get('pending_notes'), 'Los pendientes')
    recipe.updated_by = user.id if user is not None else None

    recipe.ingredients[:] = [RecipeIngredient(position=position, **item)
                             for position, item in enumerate(ingredients)]
    recipe.steps[:] = [RecipeStep(position=position, **step) for position, step in enumerate(steps)]
    db.session.flush()
    return recipe


# ---------------------------------------------------------------------------
# Baja y vínculo con el producto
# ---------------------------------------------------------------------------

def deactivate_recipe(recipe):
    """Da de baja la receta (is_active=False) y libera su producto. Levanta RecipeError 409."""
    in_use = (db.session.query(Recipe.name).join(RecipeIngredient, RecipeIngredient.recipe_id == Recipe.id)
              .filter(RecipeIngredient.sub_recipe_id == recipe.id, Recipe.is_active.is_(True)).first())
    if in_use is not None:
        raise RecipeError(f'Es base de la receta "{in_use[0]}"; sacala de ahí primero', 409)
    if recipe.product is not None and recipe.product.has_recipe:
        raise RecipeError('Descuenta stock de un producto; desactivalo primero', 409)
    recipe.is_active = False
    recipe.product_id = None
    db.session.flush()


def _variant_units(raw, product):
    if not isinstance(raw, dict):
        raise RecipeError('variant_units tiene que ser un objeto')
    if raw and product is None:
        raise RecipeError('Para cargar unidades por variante hay que vincular un producto')
    valid_ids = {v.id for v in product.variants} if product is not None else set()
    result = {}
    for key, value in raw.items():
        try:
            variant_id = int(key)
        except (TypeError, ValueError):
            raise RecipeError('Variante inválida')
        if variant_id not in valid_ids:
            raise RecipeError('La variante no pertenece al producto')
        units = _number(value, 'Las unidades de receta', Decimal('10000000'))
        if units is None:
            raise RecipeError('Las unidades de receta tienen que ser mayores a 0')
        result[variant_id] = units
    return result


def link_product(recipe, payload):
    """Vincula/desvincula el producto y configura el descuento de stock. Levanta RecipeError."""
    if not isinstance(payload, dict):
        raise RecipeError('El cuerpo tiene que ser un objeto JSON')
    if not recipe.is_active:
        raise RecipeError('La receta está inactiva')
    product_id = payload.get('product_id')
    stock_active = payload.get('stock_active', False)
    if not isinstance(stock_active, bool):
        raise RecipeError('stock_active tiene que ser verdadero o falso')
    if product_id is not None and (isinstance(product_id, bool) or not isinstance(product_id, int)):
        raise RecipeError('Producto inválido')

    product = None
    if product_id is not None:
        product = db.session.get(Product, product_id)
        if product is None:
            raise RecipeError('El producto no existe')
        other = Recipe.query.filter(Recipe.product_id == product.id, Recipe.id != recipe.id).first()
        if other is not None:
            raise RecipeError(f'El producto ya tiene la receta "{other.name}"', 409)
    if stock_active:
        if product is None:
            raise RecipeError('Para descontar stock hay que vincular un producto')
        if recipe.yield_quantity is None or _dec(recipe.yield_quantity) <= 0 or not recipe.yield_unit:
            raise RecipeError('Para descontar stock la receta necesita un rendimiento')
        if product.track_stock:
            raise RecipeError('El producto ya controla stock propio; desactivalo antes de usar la receta')
    units = _variant_units(payload.get('variant_units', {}), product)

    previous = recipe.product
    if previous is not None and (product is None or previous.id != product.id):
        previous.has_recipe = False  # el producto que se suelta deja de descontar de esta receta
    recipe.product_id = product.id if product is not None else None
    if product is not None:
        product.has_recipe = stock_active
        for variant in product.variants:
            if variant.id in units:
                variant.recipe_units = units[variant.id]
    db.session.flush()
    db.session.expire(recipe, ['product'])


# ---------------------------------------------------------------------------
# Serialización
# ---------------------------------------------------------------------------

def _num(value):
    return float(value) if value is not None else None


def _cost_dict(cost):
    return {'batch_cost': _num(cost['batch_cost']), 'unit_cost': _num(cost['unit_cost']),
            'complete': cost['complete'], 'issues': cost['issues'],
            'lines': [{'ingredient_id': line['ingredient_id'], 'cost': _num(line['cost']), 'issue': line['issue']}
                      for line in cost['lines']]}


def _has_pending(recipe):
    return bool(recipe.pending_notes) or any(i.quantity is None for i in recipe.ingredients)


def serialize_recipe_summary(recipe, include_cost):
    data = {'id': recipe.id, 'name': recipe.name,
            'product': {'id': recipe.product.id, 'name': recipe.product.name} if recipe.product else None,
            'yield_quantity': _num(recipe.yield_quantity), 'yield_unit': recipe.yield_unit,
            'total_time_minutes': recipe.total_time_minutes, 'has_pending': _has_pending(recipe),
            'is_base': recipe.product_id is None}
    if include_cost:
        cost = recipe_cost(recipe)
        data['unit_cost'] = _num(cost['unit_cost'])
        data['cost_complete'] = cost['complete']
    return data


def serialize_recipe(recipe, include_cost):
    """Receta completa. Sin `include_cost` no lleva ninguna clave de costo."""
    from app.models import User
    used_in = (Recipe.query.join(RecipeIngredient, RecipeIngredient.recipe_id == Recipe.id)
               .filter(RecipeIngredient.sub_recipe_id == recipe.id, Recipe.is_active.is_(True))
               .order_by(Recipe.name).all())
    author = db.session.get(User, recipe.updated_by) if recipe.updated_by else None
    author_name = None
    if author is not None:
        author_name = author.employee.full_name if author.employee is not None else author.email

    data = serialize_recipe_summary(recipe, include_cost=False)
    product = recipe.product
    data['product'] = None if product is None else {
        'id': product.id, 'name': product.name, 'has_recipe': product.has_recipe,
        'track_stock': product.track_stock,
        'variants': [{'id': v.id, 'name': v.name, 'recipe_units': _num(v.recipe_units)}
                     for v in sorted(product.variants, key=lambda v: v.id)]}
    data.update({
        'advance_notes': recipe.advance_notes, 'notes': recipe.notes, 'pending_notes': recipe.pending_notes,
        'is_active': recipe.is_active,
        'ingredients': [{
            'id': i.id, 'position': i.position, 'quantity': _num(i.quantity), 'unit': i.unit, 'note': i.note,
            'supply': {'id': i.supply.id, 'name': i.supply.name, 'unit': i.supply.unit} if i.supply else None,
            'sub_recipe': {'id': i.sub_recipe.id, 'name': i.sub_recipe.name} if i.sub_recipe else None,
        } for i in recipe.ingredients],
        'steps': [{'id': s.id, 'position': s.position, 'title': s.title, 'instruction': s.instruction,
                   'temperature_c': s.temperature_c, 'time_min': s.time_min, 'time_max': s.time_max,
                   'doneness': s.doneness, 'tip': s.tip} for s in recipe.steps],
        'updated_at': recipe.updated_at.isoformat() if recipe.updated_at else None,
        'updated_by_name': author_name,
        'used_in': [{'id': r.id, 'name': r.name} for r in used_in],
    })
    if include_cost:
        cost = recipe_cost(recipe)
        data['cost'] = _cost_dict(cost)
        data['unit_cost'] = _num(cost['unit_cost'])
        data['cost_complete'] = cost['complete']
    return data
