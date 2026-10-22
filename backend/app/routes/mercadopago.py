"""API de MercadoPago: cobros con Point, webhook, conciliación y configuración."""
import logging
from datetime import date

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import DataError, IntegrityError

from app.extensions import db
from app.models import MpPointOrder, PaymentMethod
from app.services import mercadopago
from app.services.mercadopago import MpRejected, MpUnavailable, point_service
from app.services.mercadopago import reconciliation_service as reconciliation
from app.services.mercadopago import settings as mp_settings
from app.services.mercadopago.webhook import verify_signature
from app.services.pos.common import now
from app.services.pos.errors import PosError, bad_request, not_found
from app.utils.decorators import admin_required, module_required
from app.utils.jwt_utils import token_required
from app.utils.validation import clean_str, json_object

logger = logging.getLogger(__name__)
bp = Blueprint('mercadopago', __name__, url_prefix='/api/v1')
FAKE_OUTCOMES = ('approved', 'rejected', 'expired', 'processing')


def _body():
    return json_object() or {}


def _run(action, status=200):
    try:
        payload = action()
        if isinstance(payload, tuple):
            payload, status = payload
    except PosError as exc:
        db.session.rollback()
        return jsonify({'error': exc.message, **exc.extra}), exc.status
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Otra operación modificó los datos al mismo tiempo, probá de nuevo'}), 409
    except DataError:
        db.session.rollback()
        return jsonify({'error': 'Algún valor es demasiado grande'}), 400
    except Exception:
        db.session.rollback()
        logger.exception('Error inesperado en MercadoPago')
        return jsonify({'error': 'Error interno, probá de nuevo'}), 500
    return jsonify(payload), status


def _day(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise bad_request('La fecha es inválida')


def _mp_call(fn):
    try:
        return fn()
    except MpUnavailable:
        raise PosError('MercadoPago no responde, probá de nuevo')
    except MpRejected as exc:
        raise PosError(f'MercadoPago respondió: {exc.message}')


# Cobros con Point

@bp.route('/mp/point-config', methods=['GET'])
@token_required
@module_required('POS', 'Cobrar')
def point_config(current_user):
    from app.services import cutover
    settings = mp_settings.get_settings()
    # En modo práctica el Point no aparece: cobraría tarjetas de verdad.
    return jsonify({'enabled': not mp_settings.missing(settings) and not cutover.practice_mode(),
                    'payment_method_id': settings.point_payment_method_id if settings else None,
                    'fake': mercadopago.fake_enabled()}), 200


@bp.route('/mp/sales/<int:sale_id>/point', methods=['POST'])
@token_required
@module_required('POS', 'Cobrar')
def start_point(current_user, sale_id):
    return _run(lambda: (point_service.order_to_dict(
        point_service.start(current_user, sale_id, _body().get('amount'))), 201))


@bp.route('/mp/point-orders/<int:order_id>', methods=['GET'])
@token_required
@module_required('POS', 'Cobrar')
def get_point_order(current_user, order_id):
    return _run(lambda: point_service.order_to_dict(point_service.refresh(order_id)))


@bp.route('/mp/point-orders/<int:order_id>/cancel', methods=['POST'])
@token_required
@module_required('POS', 'Cobrar')
def cancel_point_order(current_user, order_id):
    return _run(lambda: point_service.order_to_dict(point_service.cancel(current_user, order_id)))


@bp.route('/mp/sales/<int:sale_id>/point-orders', methods=['GET'])
@token_required
@module_required('POS', 'Cobrar')
def sale_point_orders(current_user, sale_id):
    return _run(lambda: {'orders': point_service.sale_orders(sale_id)})


@bp.route('/mp/fake/point-orders/<int:order_id>/<outcome>', methods=['POST'])
@token_required
@module_required('POS', 'Cobrar')
def fake_point(current_user, order_id, outcome):
    """Solo con FakeMercadoPago: simula lo que haría el Point (para el preview)."""
    def action():
        if not mercadopago.fake_enabled() or outcome not in FAKE_OUTCOMES:
            raise not_found('No disponible')
        from app.services.mercadopago.fake import FakeMercadoPago
        order = db.session.get(MpPointOrder, order_id)
        if order is None or not order.mp_order_id:
            raise not_found('El cobro no existe')
        FakeMercadoPago().simulate(order.mp_order_id, outcome)
        return point_service.order_to_dict(point_service.apply(order.id))
    return _run(action)


@bp.route('/mercadopago/webhook', methods=['POST'])
def webhook():
    """Aviso público de MercadoPago: se acepta solo con la firma válida; responde 200 aunque no aplique."""
    payload = request.get_json(silent=True) or {}
    data_id = request.args.get('data.id') or (payload.get('data') or {}).get('id')
    secret = mp_settings.webhook_secret(mp_settings.get_settings())
    if not verify_signature(secret, request.headers.get('x-signature'), request.headers.get('x-request-id'),
                            data_id):
        logger.warning('Webhook de MercadoPago con firma inválida (data.id=%s)', data_id)
        return jsonify({'error': 'firma inválida'}), 401
    topic = str(payload.get('type') or request.args.get('type') or '')
    if topic.startswith('order') and data_id:
        try:
            point_service.apply_by_mp_order_id(data_id)
        except Exception:
            db.session.rollback()
            logger.exception('Error procesando el webhook de la orden %s', data_id)
    return jsonify({'ok': True}), 200


# Conciliación

@bp.route('/mp/reconciliation', methods=['GET'])
@token_required
@module_required('Conciliar')
def reconciliation_summary(current_user):
    return _run(lambda: {'days': reconciliation.summary(_day(request.args.get('from')),
                                                        _day(request.args.get('to')))})


@bp.route('/mp/reconciliation/<day>', methods=['GET'])
@token_required
@module_required('Conciliar')
def reconciliation_day(current_user, day):
    return _run(lambda: reconciliation.day(_day(day)))


@bp.route('/mp/reconciliation/<day>/fetch', methods=['POST'])
@token_required
@module_required('Conciliar')
def reconciliation_fetch(current_user, day):
    return _run(lambda: reconciliation.fetch(current_user, _day(day)))


@bp.route('/mp/reconciliation/resolutions', methods=['POST'])
@token_required
@module_required('Conciliar')
def reconciliation_resolve(current_user):
    def action():
        data = _body()
        return reconciliation.resolve(current_user, data.get('kind'), data.get('movement_id'),
                                      data.get('payment_id'), data.get('sale_id'), data.get('payment_method_id'),
                                      data.get('note')), 201
    return _run(action)


@bp.route('/mp/reconciliation/resolutions/<int:resolution_id>', methods=['DELETE'])
@token_required
@module_required('Conciliar')
def reconciliation_undo(current_user, resolution_id):
    def action():
        reconciliation.undo(current_user, resolution_id)
        return {'ok': True}
    return _run(action)


# Configuración (admin)

@bp.route('/mp/settings', methods=['GET'])
@token_required
@admin_required
def get_settings(current_user):
    def action():
        settings = mp_settings.get_or_create_settings()
        db.session.commit()
        return mp_settings.settings_to_dict(settings)
    return _run(action)


@bp.route('/mp/settings', methods=['PUT'])
@token_required
@admin_required
def put_settings(current_user):
    def action():
        data = _body()
        settings = mp_settings.get_or_create_settings()
        if 'environment' in data:
            if data['environment'] not in ('test', 'production'):
                raise bad_request('El entorno tiene que ser prueba o producción')
            settings.environment = data['environment']
        if 'terminal_id' in data:
            settings.terminal_id = clean_str(data['terminal_id'], 80)
        if 'webhook_secret' in data:
            secret = clean_str(data['webhook_secret'], 200)
            settings.webhook_secret = mp_settings.encrypt(secret) if secret else None
        if 'point_payment_method_id' in data:
            method_id = data['point_payment_method_id']
            if method_id:
                method = db.session.get(PaymentMethod, method_id) if isinstance(method_id, int) else None
                if method is None or not method.is_active:
                    raise bad_request('El medio de pago no existe')
            settings.point_payment_method_id = method_id or None
        settings.updated_at = now()
        db.session.commit()
        return mp_settings.settings_to_dict(settings)
    return _run(action)


@bp.route('/mp/settings/token', methods=['PUT'])
@token_required
@admin_required
def put_token(current_user):
    def action():
        data = _body()
        environment = data.get('environment')
        token = clean_str(data.get('access_token'), 300)
        if environment not in ('test', 'production') or not token:
            raise bad_request('Indicá el entorno y el access token')
        settings = mp_settings.get_or_create_settings()
        previous = settings.environment
        settings.set_token(environment, mp_settings.encrypt(token))
        settings.environment = environment
        try:
            account = mercadopago.get_client(settings).me()
        except MpUnavailable:
            raise PosError('MercadoPago no responde, probá de nuevo')
        except MpRejected:
            raise bad_request('MercadoPago no aceptó el token: revisá que sea el access token de la integración')
        settings.environment = previous
        settings.user_id = str(account.get('id'))
        settings.updated_at = now()
        db.session.commit()
        return mp_settings.settings_to_dict(settings)
    return _run(action)


@bp.route('/mp/settings/terminals', methods=['GET'])
@token_required
@admin_required
def list_terminals(current_user):
    def action():
        client = mercadopago.get_client(mp_settings.get_settings())
        return {'terminals': _mp_call(client.list_terminals)}
    return _run(action)


@bp.route('/mp/settings/terminals/<terminal_id>/pdv', methods=['POST'])
@token_required
@admin_required
def set_pdv(current_user, terminal_id):
    def action():
        client = mercadopago.get_client(mp_settings.get_settings())
        _mp_call(lambda: client.set_pdv_mode(terminal_id))
        return {'ok': True, 'message': 'Listo: reiniciá el Point para que tome el modo PDV'}
    return _run(action)


@bp.route('/mp/settings/test', methods=['POST'])
@token_required
@admin_required
def test_connection(current_user):
    def action():
        settings = mp_settings.get_settings()
        mp_settings.require_ready(settings)
        client = mercadopago.get_client(settings)
        account = _mp_call(client.me)
        terminals = {t['id']: t for t in _mp_call(client.list_terminals)}
        terminal = terminals.get(settings.terminal_id)
        if terminal is None:
            raise PosError('La terminal configurada no está en la cuenta')
        if terminal.get('operating_mode') != 'PDV':
            raise PosError('La terminal no está en modo PDV')
        return {'ok': True, 'account': account.get('nickname') or account.get('id'), 'terminal': settings.terminal_id}
    return _run(action)
