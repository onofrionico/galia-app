"""API de fidelización para la caja: buscar clientes, asociarlos a la venta y canjear. Solo módulo POS."""
from flask import Blueprint, jsonify, request

from app.models.loyalty import Reward
from app.routes.pos_sales import _body, _respond
from app.services.loyalty import pos_hooks, wallet
from app.services.loyalty.search import find_customers, mask_email, mask_phone
from app.utils.decorators import module_required
from app.utils.jwt_utils import token_required

bp = Blueprint('loyalty_pos', __name__, url_prefix='/api/v1/loyalty')


@bp.route('/customers/search', methods=['GET'])
@token_required
@module_required('POS')
def search_customers(current_user):
    customers = find_customers(request.args.get('q', ''))
    return jsonify([{
        'id': c.id, 'full_name': c.full_name, 'email_masked': mask_email(c.email),
        'phone_masked': mask_phone(c.phone), 'balance': wallet.balance(c.id),
    } for c in customers])


@bp.route('/rewards', methods=['GET'])
@token_required
@module_required('POS')
def list_rewards(current_user):
    rewards = Reward.query.filter_by(is_active=True).order_by(Reward.position, Reward.cost, Reward.id).all()
    return jsonify([{'id': r.id, 'name': r.name, 'cost': r.cost, 'product_variant_id': r.product_variant_id,
                     'product_id': r.variant.product_id} for r in rewards])


@bp.route('/pos-sales/<int:sale_id>/customer', methods=['PUT'])
@token_required
@module_required('POS')
def set_sale_customer(current_user, sale_id):
    return _respond(lambda: pos_hooks.set_customer(current_user, sale_id, _body().get('customer_id')))


@bp.route('/pos-sales/<int:sale_id>/redemptions', methods=['POST'])
@token_required
@module_required('POS')
def add_redemption(current_user, sale_id):
    def action():
        body = _body()
        return pos_hooks.add_redemption(current_user, sale_id, body.get('reward_id'),
                                        body.get('modifier_option_ids'))
    return _respond(action)
