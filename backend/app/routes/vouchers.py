"""API de vouchers de descuento: gestión de tandas (módulo Vouchers) y canje en caja (POS o Cobrar)."""
from flask import Blueprint, jsonify

from app.extensions import db
from app.routes.pos_sales import _body, _respond
from app.services.pos.errors import PosError
from app.services.vouchers import batches, redeem
from app.utils.decorators import module_required
from app.utils.jwt_utils import token_required

bp = Blueprint('vouchers', __name__, url_prefix='/api/v1/vouchers')


@bp.errorhandler(PosError)
def _voucher_error(exc):
    db.session.rollback()
    return jsonify({'error': exc.message, **exc.extra}), exc.status


def _guard(f):
    """token + módulo Vouchers, en ese orden."""
    return token_required(module_required('Vouchers')(f))


@bp.route('/batches', methods=['GET'])
@_guard
def list_batches(current_user):
    return jsonify(batches.list_batches())


@bp.route('/batches', methods=['POST'])
@_guard
def create_batch(current_user):
    batch = batches.create_batch(current_user, _body())
    return jsonify(batches.batch_detail(batch.id)), 201


@bp.route('/batches/<int:batch_id>', methods=['GET'])
@_guard
def get_batch(current_user, batch_id):
    return jsonify(batches.batch_detail(batch_id))


@bp.route('/batches/<int:batch_id>', methods=['PUT'])
@_guard
def extend_batch(current_user, batch_id):
    batches.extend_expiry(current_user, batch_id, _body().get('expires_at'))
    return jsonify(batches.batch_detail(batch_id))


@bp.route('/<int:voucher_id>/void', methods=['POST'])
@_guard
def void_voucher(current_user, voucher_id):
    voucher = batches.void_voucher(current_user, voucher_id, _body().get('reason'))
    return jsonify(batches.batch_detail(voucher.batch_id))


@bp.route('/pos-sales/<int:sale_id>/redeem', methods=['POST'])
@token_required
@module_required('POS', 'Cobrar')
def redeem_voucher(current_user, sale_id):
    return _respond(lambda: redeem.redeem_voucher(current_user, sale_id, _body().get('code')))
