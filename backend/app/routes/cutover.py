"""Interruptores del corte con Fudo: catálogo en Galia, Fudo apagado y modo práctica."""
from flask import Blueprint, jsonify

from app.extensions import db
from app.services import cutover
from app.services.pos import practice
from app.services.pos.errors import PosError
from app.utils.decorators import admin_required, authenticated_only
from app.utils.jwt_utils import token_required
from app.utils.validation import json_object

bp = Blueprint('cutover', __name__, url_prefix='/api/v1/system')


def _error(exc):
    db.session.rollback()
    return jsonify({'error': exc.message, **exc.extra}), exc.status


@bp.route('/cutover', methods=['GET'])
@token_required
@authenticated_only
def get_cutover(current_user):
    """Cualquier usuario: el frontend lo usa para la franja de práctica y los botones de Fudo."""
    settings = cutover.get_settings()
    db.session.commit()
    return jsonify(settings.to_dict()), 200


@bp.route('/cutover', methods=['PUT'])
@token_required
@admin_required
def put_cutover(current_user):
    data = json_object() or {}
    flags = {key: bool(data[key]) for key in ('catalog_in_galia', 'fudo_off', 'practice_mode') if key in data}
    try:
        settings = cutover.set_flags(current_user, **flags)
    except PosError as exc:
        return _error(exc)
    return jsonify({**settings.to_dict(), 'link': getattr(settings, 'last_link', None)}), 200


@bp.route('/cutover/clear-practice', methods=['POST'])
@token_required
@admin_required
def clear_practice(current_user):
    try:
        counts = practice.clear_practice(current_user)
    except PosError as exc:
        return _error(exc)
    return jsonify(counts), 200
