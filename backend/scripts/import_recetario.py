"""Carga inicial del recetario de pastelería (planilla "Recetario Galia") en el módulo de recetas.

Uso (desde backend/):
    python scripts/import_recetario.py [--user-email admin@...] [--apply] [--if-empty] [--data ruta.json]

En el deploy (build.sh) corre con --apply --if-empty: carga el recetario solo la primera vez,
cuando todavía no hay ninguna receta; después no hace nada y no pisa lo que edite la cocina.

Sin --apply es una prueba: hace todo dentro de una transacción, imprime el informe y
deshace los cambios. Con --apply guarda (solo si no hubo errores).

Reglas:
- Idempotente por nombre: una receta que ya existe no se toca. Si el nombre coincide con
  la composición migrada de un producto (receta vinculada y sin pasos), la de la planilla
  se carga como "<nombre> (planilla)" sin vincular.
- Los insumos se buscan por nombre sin distinguir mayúsculas, acentos ni espacios; los
  que no existen se crean sin precio.
- Vincula cada receta a su producto por nombre si el producto no tiene receta y no
  descuenta stock (has_recipe en False). Nunca toca has_recipe.
- Las recetas se guardan con recipe_service.save_recipe (mismas validaciones que la app).
  Si alguna falla, no se guarda nada.
"""
import argparse
import json
import os
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.extensions import db  # noqa: E402
from app.models import Product, Recipe, Supply, User  # noqa: E402
from app.services.recipe_service import RecipeError, save_recipe  # noqa: E402
from app.services.units import normalize_unit  # noqa: E402

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'recetario_galia.json')
PLANILLA_SUFFIX = ' (planilla)'
UNKNOWN_UNIT = 'a completar'
_SUPPLY_UNIT_BY_FAMILY = {'g': 'kg', 'kg': 'kg', 'ml': 'l', 'l': 'l', 'unidad': 'unidad'}


@dataclass
class Report:
    created_recipes: list = field(default_factory=list)    # nombres
    skipped_existing: list = field(default_factory=list)   # nombres que ya estaban
    linked: list = field(default_factory=list)             # (receta, producto)
    unlinked_reasons: dict = field(default_factory=dict)   # receta -> motivo
    created_supplies: list = field(default_factory=list)   # (nombre, unidad)
    matched_supplies: list = field(default_factory=list)   # (nombre en la planilla, insumo) si difieren
    unmatched_products: list = field(default_factory=list)  # product_name sin producto
    errors: list = field(default_factory=list)
    applied: bool = False


def normalize_name(name):
    """Minúsculas, sin acentos y con los espacios colapsados."""
    text = unicodedata.normalize('NFD', name or '')
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return ' '.join(text.lower().split())


def _ordered(recipes, errors):
    """Recetas del JSON con las bases antes que quienes las usan."""
    by_name = {r['name']: r for r in recipes}
    ordered, state = [], {}

    def visit(recipe, path):
        name = recipe['name']
        if state.get(name) == 'done':
            return
        if state.get(name) == 'visiting':
            errors.append(f'Ciclo de recetas base: {" -> ".join(path + [name])}')
            return
        state[name] = 'visiting'
        for item in recipe.get('ingredients', []):
            sub = item.get('sub_recipe_name')
            if sub in by_name:
                visit(by_name[sub], path + [name])
        state[name] = 'done'
        ordered.append(recipe)

    for recipe in recipes:
        visit(recipe, [])
    return ordered


def _existing_recipe(name):
    """(receta existente o None, nombre con el que se cargaría)."""
    planilla = Recipe.query.filter_by(name=name + PLANILLA_SUFFIX).first()
    if planilla is not None:
        return planilla, planilla.name
    current = Recipe.query.filter_by(name=name).first()
    if current is None:
        return None, name
    if current.product_id is not None and not current.steps:
        return None, name + PLANILLA_SUFFIX  # es la composición migrada del producto
    return current, name


def _number_variants(key):
    """Singular/plural del nombre normalizado: huevo <-> huevos, nuez <-> nueces."""
    variants = {key + 's', key + 'es'}
    if key.endswith('z'):
        variants.add(key[:-1] + 'ces')
    if key.endswith('ces'):
        variants.add(key[:-3] + 'z')
    if key.endswith('es'):
        variants.add(key[:-2])
    if key.endswith('s'):
        variants.add(key[:-1])
    variants.discard(key)
    return variants


def _supply_unit(units):
    """Unidad para un insumo nuevo: kg, l o unidad según cómo lo usa la planilla."""
    families = Counter(_SUPPLY_UNIT_BY_FAMILY[u] for u in (normalize_unit(x) for x in units) if u)
    return families.most_common(1)[0][0] if families else UNKNOWN_UNIT


class _Supplies:
    def __init__(self, recipes, report):
        self.report = report
        self.usages = {}
        for recipe in recipes:
            for item in recipe.get('ingredients', []):
                if item.get('supply_name'):
                    self.usages.setdefault(normalize_name(item['supply_name']), []).append(item.get('unit'))
        self.by_key = {}
        for supply in Supply.query.order_by(Supply.id):
            self.by_key.setdefault(normalize_name(supply.name), []).append(supply)

    def _candidates(self, name):
        key = normalize_name(name)
        if key in self.by_key:
            return self.by_key[key]
        return [s for variant in sorted(_number_variants(key)) for s in self.by_key.get(variant, [])]

    def check(self, name):
        """Mensaje de error si el nombre no se puede resolver a un único insumo activo."""
        candidates = self._candidates(name)
        active = [s for s in candidates if s.is_active]
        if len(active) > 1 and not any(s.name == name for s in active):
            return f'Insumo "{name}": hay varios que coinciden ({", ".join(s.name for s in active)})'
        if candidates and not active:
            return f'Insumo "{name}": existe pero está inactivo ({candidates[0].name})'
        return None

    def resolve(self, name):
        key = normalize_name(name)
        active = [s for s in self._candidates(name) if s.is_active]
        exact = [s for s in active if s.name == name]
        if exact or active:
            supply = (exact or active)[0]
            if supply.name != name and (name, supply.name) not in self.report.matched_supplies:
                self.report.matched_supplies.append((name, supply.name))
            return supply
        supply = Supply(name=name, unit=_supply_unit(self.usages.get(key, [])))
        db.session.add(supply)
        db.session.flush()
        self.by_key[key] = [supply]
        self.report.created_supplies.append((supply.name, supply.unit))
        return supply


def _find_product(product_name, recipe_name, report):
    matches = [p for p in Product.query.filter_by(is_active=True)
               if normalize_name(p.name) == normalize_name(product_name)]
    if not matches:
        report.unmatched_products.append(product_name)
        report.unlinked_reasons[recipe_name] = f'no hay un producto activo llamado "{product_name}"'
        return None
    if len(matches) > 1:
        report.unlinked_reasons[recipe_name] = f'hay {len(matches)} productos llamados "{product_name}"'
        return None
    return matches[0]


def _link(recipe, entry, report):
    product_name = entry.get('product_name')
    if not product_name:
        if not entry.get('is_base'):
            report.unlinked_reasons[recipe.name] = 'la planilla no indica a qué producto corresponde'
        return
    product = _find_product(product_name, recipe.name, report)
    if product is None:
        return
    if product.recipe is not None:
        report.unlinked_reasons[recipe.name] = (
            f'el producto "{product.name}" ya tiene la receta "{product.recipe.name}"; decidir cuál vale')
        return
    if product.has_recipe:
        report.unlinked_reasons[recipe.name] = (
            f'el producto "{product.name}" ya descuenta stock sin receta; vincular a mano')
        return
    # Vínculo directo: no se toca has_recipe (vincular no activa el descuento de stock).
    recipe.product_id = product.id
    db.session.flush()
    db.session.expire(product, ['recipe'])
    report.linked.append((recipe.name, product.name))


def _payload(entry, name, supplies, recipe_ids):
    ingredients = []
    for item in entry.get('ingredients', []):
        ref = {}
        if item.get('sub_recipe_name'):
            ref['sub_recipe_id'] = recipe_ids[item['sub_recipe_name']]
        else:
            ref['supply_id'] = supplies.resolve(item['supply_name']).id
        ingredients.append({**ref, 'quantity': item.get('quantity'), 'unit': item.get('unit'),
                            'note': item.get('note')})
    payload = {key: entry.get(key) for key in ('yield_quantity', 'yield_unit', 'total_time_minutes',
                                                'advance_notes', 'notes', 'pending_notes', 'steps')}
    payload.update(name=name, ingredients=ingredients)
    return payload


def _validate_references(recipes, supplies, errors):
    json_names = {r['name'] for r in recipes}
    for entry in recipes:
        if entry.get('is_base') and entry.get('product_name'):
            errors.append(f'{entry["name"]}: una base no puede tener producto')
        for item in entry.get('ingredients', []):
            sub, supply = item.get('sub_recipe_name'), item.get('supply_name')
            if bool(sub) == bool(supply):
                errors.append(f'{entry["name"]}: cada ingrediente lleva supply_name o sub_recipe_name')
            elif sub and sub not in json_names and _existing_recipe(sub)[0] is None:
                errors.append(f'{entry["name"]}: la receta base "{sub}" no existe')
            elif supply:
                problem = supplies.check(supply)
                if problem and problem not in errors:
                    errors.append(problem)


def run_import(data, apply, user=None):
    """Importa `data` (formato de recetario_galia.json). Sin `apply` deshace todo al final."""
    report = Report()
    recipes = data.get('recipes', [])
    supplies = _Supplies(recipes, report)
    _validate_references(recipes, supplies, report.errors)
    ordered = _ordered(recipes, report.errors)

    recipe_ids = {}
    if not report.errors:
        for entry in ordered:
            existing, name = _existing_recipe(entry['name'])
            if existing is not None:
                report.skipped_existing.append(existing.name)
                recipe_ids[entry['name']] = existing.id
                continue
            try:
                recipe = save_recipe(None, _payload(entry, name, supplies, recipe_ids), user)
            except RecipeError as error:
                report.errors.append(f'{entry["name"]}: {error.message}')
                break
            recipe_ids[entry['name']] = recipe.id
            report.created_recipes.append(recipe.name)
            _link(recipe, entry, report)

    if apply and not report.errors:
        db.session.commit()
        report.applied = True
    else:
        db.session.rollback()
    return report


def format_report(report, doubts=()):
    lines = ['Guardado.' if report.applied else 'PRUEBA: no se guardó nada.' if not report.errors
             else 'Hubo errores: no se guardó nada.']

    def section(title, items):
        lines.append(f'\n{title} ({len(items)})')
        lines.extend(f'  - {item}' for item in items)

    if report.errors:
        section('Errores', report.errors)
    section('Recetas nuevas', report.created_recipes)
    section('Ya existían (no se tocan)', report.skipped_existing)
    section('Vinculadas a producto (sin activar stock)', [f'{r} -> {p}' for r, p in report.linked])
    section('Sin vincular', [f'{r}: {why}' for r, why in report.unlinked_reasons.items()])
    section('Productos no encontrados', report.unmatched_products)
    section('Insumos nuevos (sin precio)', [f'{n} ({u})' for n, u in report.created_supplies])
    section('Insumos encontrados con otro nombre', [f'{n} -> {s}' for n, s in report.matched_supplies])
    if doubts:
        section('Dudas para pastelería', list(doubts))
    return '\n'.join(lines)


def already_loaded():
    """True si ya hay alguna receta, activa o no (la carga inicial ya pasó o hay recetas propias)."""
    return db.session.query(Recipe.id).first() is not None


def resolve_author(email):
    """El admin activo con ese email, o el primer admin activo si no se indica. None si no hay."""
    query = User.query.filter_by(role='admin', is_active=True)
    if email:
        return query.filter_by(email=email).first()
    return query.order_by(User.id).first()


def main(argv=None):
    parser = argparse.ArgumentParser(description='Carga inicial del recetario.')
    parser.add_argument('--apply', action='store_true', help='guardar (sin esto es una prueba)')
    parser.add_argument('--user-email', help='admin que figura como autor (por defecto, el primer admin activo)')
    parser.add_argument('--data', default=DATA_PATH, help='JSON del recetario')
    parser.add_argument('--if-empty', action='store_true',
                        help='no hacer nada si ya hay recetas (para correrlo en cada deploy)')
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    from app import create_app
    app = create_app(os.environ.get('FLASK_ENV', 'production'))
    with app.app_context():
        if args.if_empty and already_loaded():
            print('Recetario: ya hay recetas cargadas, no se hace nada.')
            return 0
        user = resolve_author(args.user_email)
        if user is None:
            print(f'Negado: {args.user_email or "no hay ningún admin activo"} no es un admin activo.')
            return 1
        with open(args.data, encoding='utf-8') as handle:
            data = json.load(handle)
        report = run_import(data, apply=args.apply, user=user)
        print(format_report(report, data.get('doubts', [])))
        return 1 if report.errors else 0


if __name__ == '__main__':
    sys.exit(main())
