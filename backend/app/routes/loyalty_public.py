"""API pública de "Mis cafecitos" (carta digital). Autenticación de clientes, nunca de empleados."""
from datetime import datetime

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models.loyalty import Customer, LoyaltyMovement, Reward
from app.services.loyalty import customer_auth, wallet
from app.services.loyalty.customer_auth import customer_required, issue_customer_token
from app.services.loyalty.errors import LoyaltyError

bp = Blueprint('loyalty_public', __name__, url_prefix='/api/public/loyalty')

LABELS = {'earn': 'compra', 'earn_reversal': 'compra anulada', 'redeem_reversal': 'canje anulado',
          'adjustment': 'ajuste'}


def _body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _me(customer):
    return {'first_name': customer.first_name, 'last_name': customer.last_name, 'email': customer.email,
            'phone': customer.phone, 'balance': wallet.balance(customer.id), 'qr_token': customer.qr_token,
            'promo_opt_in': customer.promo_opt_in_at is not None}


@bp.errorhandler(LoyaltyError)
def _loyalty_error(exc):
    db.session.rollback()
    return jsonify({'error': exc.message, **exc.extra}), exc.status


@bp.route('/auth/google', methods=['POST'])
def google_login():
    body = _body()
    info = customer_auth.verify_google_credential(body.get('credential'))
    customer = Customer.query.filter_by(google_sub=info['sub']).first()
    if customer is not None:
        return jsonify({'token': issue_customer_token(customer), 'customer': _me(customer)}), 200
    if body.get('accept_terms') is not True:
        return jsonify({'needs_terms': True, 'first_name': info.get('given_name')}), 409
    now = datetime.utcnow()
    customer = Customer(google_sub=info['sub'], email=info.get('email'), first_name=info.get('given_name'),
                        last_name=info.get('family_name'), terms_accepted_at=now,
                        promo_opt_in_at=now if body.get('promo_opt_in') is True else None)
    db.session.add(customer)
    db.session.commit()
    return jsonify({'token': issue_customer_token(customer), 'customer': _me(customer)}), 201


@bp.route('/me', methods=['GET'])
@customer_required
def me(customer):
    return jsonify(_me(customer))


@bp.route('/me', methods=['PATCH'])
@customer_required
def update_me(customer):
    body = _body()
    if 'phone' in body:
        phone = (body.get('phone') or '').strip()[:30]
        customer.phone = phone or None
    if 'promo_opt_in' in body:
        wants = body.get('promo_opt_in') is True
        if wants and customer.promo_opt_in_at is None:
            customer.promo_opt_in_at = datetime.utcnow()
        elif not wants:
            customer.promo_opt_in_at = None
    db.session.commit()
    return jsonify(_me(customer))


@bp.route('/me/movements', methods=['GET'])
@customer_required
def movements(customer):
    limit = min(max(request.args.get('limit', 50, type=int) or 50, 1), 200)
    rows = (LoyaltyMovement.query.filter_by(customer_id=customer.id)
            .order_by(LoyaltyMovement.created_at.desc(), LoyaltyMovement.id.desc()).limit(limit).all())
    return jsonify([{
        'date': m.created_at.date().isoformat(), 'kind': m.kind, 'amount': m.amount,
        'label': f'canje {m.reward.name}' if m.kind == 'redeem' and m.reward else LABELS.get(m.kind, 'canje'),
    } for m in rows])


@bp.route('/rewards', methods=['GET'])
def rewards():
    rows = Reward.query.filter_by(is_active=True).order_by(Reward.position, Reward.cost, Reward.id).all()
    return jsonify([{'name': r.name, 'cost': r.cost} for r in rows])
