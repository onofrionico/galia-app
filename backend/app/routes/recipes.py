"""Recetas de producción: consulta, edición y vínculo con el producto."""
import logging

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Recipe
from app.services.recipe_service import (RecipeError, deactivate_recipe, link_product, save_recipe,
                                         serialize_recipe, serialize_recipe_summary)
from app.utils.decorators import module_required
from app.utils.jwt_utils import token_required
from app.utils.permissions import check_module_access
from app.utils.validation import json_object

logger = logging.getLogger(__name__)
bp = Blueprint('recipes', __name__, url_prefix='/api/v1/recipes')


def _include_cost(user):
    return check_module_access(user, 'RecipeCosts')


def _commit(action, user, status=200, full=True):
    """Corre `action`, confirma y responde la receta serializada (o el error de negocio)."""
    try:
        recipe = action()
        db.session.commit()
        include_cost = _include_cost(user)
        body = serialize_recipe(recipe, include_cost) if full else {'message': 'Receta desactivada'}
    except RecipeError as exc:
        db.session.rollback()
        return jsonify({'error': exc.message}), exc.status
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Ya existe una receta con esos datos'}), 409
    except Exception:
        db.session.rollback()
        logger.exception('Error inesperado al guardar una receta')
        return jsonify({'error': 'Error interno, probá de nuevo'}), 500
    return jsonify(body), status


@bp.route('', methods=['GET'])
@token_required
@module_required('Recipes')
def list_recipes(current_user):
    query = Recipe.query.filter(Recipe.is_active.is_(True))
    search = request.args.get('q', '').strip()
    if search:
        query = query.filter(Recipe.name.ilike(f'%{search}%'))
    if request.args.get('bases') == '1':
        query = query.filter(Recipe.product_id.is_(None))
    include_cost = _include_cost(current_user)
    return jsonify([serialize_recipe_summary(r, include_cost) for r in query.order_by(Recipe.name)]), 200


@bp.route('/<int:recipe_id>', methods=['GET'])
@token_required
@module_required('Recipes')
def get_recipe(current_user, recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    return jsonify(serialize_recipe(recipe, _include_cost(current_user))), 200


@bp.route('', methods=['POST'])
@token_required
@module_required('RecipesAdmin')
def create_recipe(current_user):
    payload = json_object()
    return _commit(lambda: save_recipe(None, payload, current_user), current_user, status=201)


@bp.route('/<int:recipe_id>', methods=['PUT'])
@token_required
@module_required('RecipesAdmin')
def update_recipe(current_user, recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    payload = json_object()
    return _commit(lambda: save_recipe(recipe, payload, current_user), current_user)


@bp.route('/<int:recipe_id>', methods=['DELETE'])
@token_required
@module_required('RecipesAdmin')
def delete_recipe(current_user, recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)

    def action():
        deactivate_recipe(recipe)
        return recipe
    return _commit(action, current_user, full=False)


@bp.route('/<int:recipe_id>/product', methods=['PUT'])
@token_required
@module_required('RecipesAdmin')
def update_recipe_product(current_user, recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    payload = json_object()

    def action():
        link_product(recipe, payload)
        return recipe
    return _commit(action, current_user)
