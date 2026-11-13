"""Administración de fidelización: premios, cafecitos por producto, clientes, ajustes, historial y reportes.

Solo usuarios con el módulo Fidelizacion (o admin)."""
from datetime import date

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import Product, ProductVariant
from app.models.loyalty import Customer, LoyaltyChangeLog, LoyaltyMovement, LoyaltySettings, Reward, normalize_search
from app.services.loyalty import admin, reports, wallet
from app.services.loyalty.errors import LoyaltyError
from app.services.loyalty.search import find_customers
from app.utils.decorators import module_required
from app.utils.jwt_utils import token_required
from app.utils.timezone_utils import get_current_date_argentina

bp = Blueprint('loyalty_admin', __name__, url_prefix='/api/v1/loyalty/admin')


@bp.errorhandler(LoyaltyError)
def _loyalty_error(exc):
    db.session.rollback()
    return jsonify({'error': exc.message, **exc.extra}), exc.status


def _body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _date_arg(name):
    raw = request.args.get(name)
    try:
        return date.fromisoformat(raw)
    except (TypeError, ValueError):
        raise LoyaltyError(f'Fecha inválida en "{name}" (formato AAAA-MM-DD)')


def _reward(r):
    return {'id': r.id, 'name': r.name, 'product_variant_id': r.product_variant_id, 'cost': r.cost,
            'is_active': r.is_active, 'position': r.position,
            'product_name': r.variant.product.name if r.variant else None,
            'variant_name': r.variant.name if r.variant else None}


def _customer(c):
    return {'id': c.id, 'full_name': c.full_name, 'email': c.email, 'phone': c.phone,
            'balance': wallet.balance(c.id), 'promo_opt_in': c.promo_opt_in_at is not None,
            'created_at': c.created_at.isoformat()}


def _guard(f):
    """token + módulo Fidelizacion, en ese orden."""
    return token_required(module_required('Fidelizacion')(f))


@bp.route('/settings', methods=['GET'])
@_guard
def get_settings(current_user):
    return jsonify({'active_days': LoyaltySettings.get().active_days})


@bp.route('/settings', methods=['PUT'])
@_guard
def put_settings(current_user):
    return jsonify({'active_days': admin.update_settings(current_user, _body().get('active_days')).active_days})


@bp.route('/rewards', methods=['GET'])
@_guard
def list_rewards(current_user):
    return jsonify([_reward(r) for r in Reward.query.order_by(Reward.position, Reward.cost, Reward.id).all()])


@bp.route('/rewards', methods=['POST'])
@_guard
def create_reward(current_user):
    return jsonify(_reward(admin.create_reward(current_user, _body()))), 201


@bp.route('/rewards/<int:reward_id>', methods=['PUT'])
@_guard
def update_reward(current_user, reward_id):
    return jsonify(_reward(admin.update_reward(current_user, reward_id, _body())))


@bp.route('/variants', methods=['GET'])
@_guard
def list_variants(current_user):
    query = ProductVariant.query.join(Product).filter(ProductVariant.is_active.is_(True), Product.is_active.is_(True))
    rows = query.order_by(Product.name, ProductVariant.name).all()
    q = normalize_search(request.args.get('q', ''))
    if q:
        rows = [v for v in rows if q in normalize_search(f'{v.product.name} {v.name}')]
    return jsonify([{'id': v.id, 'product_id': v.product_id, 'product_name': v.product.name,
                     'variant_name': v.name, 'cafecitos': v.cafecitos} for v in rows])


@bp.route('/variants/cafecitos', methods=['PUT'])
@_guard
def set_variant_cafecitos(current_user):
    body = _body()
    variants = admin.set_variant_cafecitos(current_user, body.get('variant_ids'), body.get('cafecitos'))
    return jsonify([{'id': v.id, 'cafecitos': v.cafecitos} for v in variants])


@bp.route('/customers', methods=['GET'])
@_guard
def list_customers(current_user):
    q = request.args.get('q', '').strip()
    rows = find_customers(q, limit=100) if q else Customer.query.order_by(Customer.created_at.desc()).limit(100).all()
    return jsonify([_customer(c) for c in rows])


@bp.route('/customers/<int:customer_id>', methods=['GET'])
@_guard
def get_customer(current_user, customer_id):
    customer = db.session.get(Customer, customer_id)
    if customer is None:
        raise LoyaltyError('El cliente no existe', 404)
    movements = (LoyaltyMovement.query.filter_by(customer_id=customer.id)
                 .order_by(LoyaltyMovement.created_at.desc(), LoyaltyMovement.id.desc()).limit(200).all())
    data = _customer(customer)
    data['movements'] = [{'id': m.id, 'kind': m.kind, 'amount': m.amount, 'created_at': m.created_at.isoformat(),
                          'reason': m.reason, 'reward': m.reward.name if m.reward else None,
                          'pos_sale_id': m.pos_sale_id} for m in movements]
    return jsonify(data)


@bp.route('/customers/<int:customer_id>/adjustments', methods=['POST'])
@_guard
def adjust(current_user, customer_id):
    body = _body()
    if db.session.get(Customer, customer_id) is None:
        raise LoyaltyError('El cliente no existe', 404)
    wallet.adjust(current_user, customer_id, body.get('amount'), body.get('reason'))
    return jsonify({'balance': wallet.balance(customer_id)})


@bp.route('/customers/<int:customer_id>/regenerate-qr', methods=['POST'])
@_guard
def regenerate_qr(current_user, customer_id):
    admin.regenerate_qr(current_user, customer_id)
    return jsonify({'ok': True})


@bp.route('/change-log', methods=['GET'])
@_guard
def change_log(current_user):
    query = LoyaltyChangeLog.query
    if request.args.get('entity'):
        query = query.filter_by(entity=request.args['entity'])
    limit = min(max(request.args.get('limit', 100, type=int) or 100, 1), 500)
    rows = query.order_by(LoyaltyChangeLog.created_at.desc(), LoyaltyChangeLog.id.desc()).limit(limit).all()
    return jsonify([{'id': r.id, 'entity': r.entity, 'entity_id': r.entity_id, 'field': r.field,
                     'old_value': r.old_value, 'new_value': r.new_value, 'reason': r.reason,
                     'user': r.user.email if r.user else None, 'created_at': r.created_at.isoformat()}
                    for r in rows])


@bp.route('/reports/active', methods=['GET'])
@_guard
def report_active(current_user):
    return jsonify(reports.active_customers(get_current_date_argentina()))


@bp.route('/reports/inactive', methods=['GET'])
@_guard
def report_inactive(current_user):
    return jsonify(reports.inactive_customers(get_current_date_argentina()))


@bp.route('/reports/redemptions', methods=['GET'])
@_guard
def report_redemptions(current_user):
    return jsonify(reports.redemptions(_date_arg('from'), _date_arg('to')))


@bp.route('/reports/sales-comparison', methods=['GET'])
@_guard
def report_sales_comparison(current_user):
    return jsonify(reports.registered_vs_unregistered(_date_arg('from'), _date_arg('to')))
