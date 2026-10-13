"""API de caja del POS. Las rutas validan permisos y traducen errores; la lógica está en cash_service."""
import logging
from datetime import date, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import DataError, IntegrityError

from app.extensions import db
from app.models import ExpenseCategory
from app.models.pos import CashEvent, CashRegister, CashSession
from app.services.pos import cash_service
from app.services.pos.cash_serializers import register_to_dict, session_to_dict
from app.services.pos.errors import PosError, bad_request, not_found
from app.utils.decorators import admin_required, module_required
from app.utils.jwt_utils import token_required
from app.utils.timezone_utils import get_current_date_argentina

logger = logging.getLogger(__name__)
bp = Blueprint('pos_cash', __name__, url_prefix='/api/v1/pos/cash')


def _body():
    data = request.get_json(silent=True)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise bad_request('El cuerpo tiene que ser un objeto JSON')
    return data


def _run(action):
    try:
        payload = action()
    except PosError as exc:
        db.session.rollback()
        return jsonify({'error': exc.message, **exc.extra}), exc.status
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Otra operación modificó la caja al mismo tiempo, probá de nuevo'}), 409
    except DataError:
        db.session.rollback()
        return jsonify({'error': 'Algún valor es demasiado grande'}), 400
    except Exception:
        db.session.rollback()
        logger.exception('Error inesperado en la caja')
        return jsonify({'error': 'Error interno, probá de nuevo'}), 500
    return jsonify(payload), 200


def _payload(session, detail=False):
    events = (CashEvent.query.filter_by(session_id=session.id).order_by(CashEvent.id).all() if detail else None)
    return session_to_dict(session, cash_service.session_summary(session), events)


def _date_arg(name, default):
    value = request.args.get(name)
    if not value:
        return default
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise bad_request('La fecha tiene que tener el formato AAAA-MM-DD')


def _range():
    today = get_current_date_argentina()
    start = _date_arg('from', today - timedelta(days=6))
    end = _date_arg('to', today)
    if end < start:
        raise bad_request('La fecha final es anterior a la inicial')
    return start, end


@bp.route('/registers', methods=['GET'])
@token_required
@module_required('POS', 'Camarero')
def registers(current_user):
    def action():
        rows = CashRegister.query.filter_by(is_active=True).order_by(CashRegister.position, CashRegister.id).all()
        open_by_register = {s.register_id: s for s in CashSession.query.filter_by(status='open').all()}
        return {'registers': [register_to_dict(r, open_by_register.get(r.id)) for r in rows]}
    return _run(action)


@bp.route('/sessions', methods=['POST'])
@token_required
@module_required('POS')
def open_session(current_user):
    def action():
        data = _body()
        return _payload(cash_service.open_session(current_user, data.get('register_id'), data.get('opening_float')))
    return _run(action)


@bp.route('/sessions/current', methods=['GET'])
@token_required
@module_required('POS')
def current_session(current_user):
    def action():
        register_id = request.args.get('register_id', type=int)
        session = CashSession.query.filter_by(register_id=register_id, status='open').first()
        if session is None:
            raise not_found('La caja no está abierta')
        return _payload(session)
    return _run(action)


@bp.route('/sessions/<int:session_id>', methods=['GET'])
@token_required
@module_required('POS')
def session_detail(current_user, session_id):
    return _run(lambda: _payload(cash_service.load_session(session_id), detail=True))


@bp.route('/sessions/<int:session_id>/movements', methods=['POST'])
@token_required
@module_required('POS')
def add_movement(current_user, session_id):
    def action():
        data = _body()
        return _payload(cash_service.add_movement(
            current_user, session_id, data.get('kind'), data.get('amount'), data.get('reason'),
            category_id=data.get('category_id'), supplier_id=data.get('supplier_id')))
    return _run(action)


@bp.route('/movements/<int:movement_id>/cancel', methods=['POST'])
@token_required
@admin_required
def cancel_movement(current_user, movement_id):
    return _run(lambda: _payload(cash_service.cancel_movement(current_user, movement_id, _body().get('reason'))))


@bp.route('/sessions/<int:session_id>/close', methods=['POST'])
@token_required
@module_required('POS')
def close_session(current_user, session_id):
    def action():
        data = _body()
        return _payload(cash_service.close_session(current_user, session_id, data.get('counts'), data.get('note')))
    return _run(action)


@bp.route('/sessions/<int:session_id>/reopen', methods=['POST'])
@token_required
@admin_required
def reopen_session(current_user, session_id):
    return _run(lambda: _payload(cash_service.reopen_session(current_user, session_id, _body().get('reason'))))


@bp.route('/sessions', methods=['GET'])
@token_required
@module_required('POS')
def list_sessions(current_user):
    def action():
        start, end = _range()
        page = max(1, request.args.get('page', 1, type=int))
        return cash_service.list_sessions(start, end, request.args.get('register_id', type=int), page)
    return _run(action)


@bp.route('/unassigned-payments', methods=['GET'])
@token_required
@module_required('POS')
def unassigned_payments(current_user):
    def action():
        start, end = _range()
        return {'payments': cash_service.unassigned_payments(start, end)}
    return _run(action)


@bp.route('/expense-categories', methods=['GET'])
@token_required
@module_required('POS')
def expense_categories(current_user):
    rows = ExpenseCategory.query.filter_by(is_active=True).order_by(ExpenseCategory.name).all()
    return jsonify({'categories': [{'id': c.id, 'name': c.name} for c in rows]}), 200
