"""API de ventas del POS. Las rutas solo validan permisos y traducen errores; la lógica está en los servicios."""
import logging

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import DataError, IntegrityError

from app.extensions import db
from app.models.pos import SALE_STATUSES, SALE_TYPES, PosSale, PosSaleEvent
from app.services.pos import discount_service, payment_service, sale_service
from app.services.pos.errors import PosError, not_found
from app.services.pos.serializers import sale_to_dict
from app.utils.decorators import module_required
from app.utils.jwt_utils import token_required

logger = logging.getLogger(__name__)
bp = Blueprint('pos_sales', __name__, url_prefix='/api/v1/pos')


def _body():
    data = request.get_json(silent=True)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise PosError('El cuerpo tiene que ser un objeto JSON', 400)
    return data


def _respond(action):
    """Ejecuta una acción del servicio y devuelve la venta resultante o el error como JSON."""
    try:
        sale = action()
    except PosError as exc:
        db.session.rollback()
        return jsonify({'error': exc.message, **exc.extra}), exc.status
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Otra operación modificó la venta al mismo tiempo, probá de nuevo'}), 409
    except DataError:
        db.session.rollback()
        return jsonify({'error': 'Algún valor es demasiado grande'}), 400
    except Exception:
        db.session.rollback()
        logger.exception('Error inesperado en el POS')
        return jsonify({'error': 'Error interno, probá de nuevo'}), 500
    return jsonify(sale_to_dict(sale)), 200


@bp.route('/sales', methods=['GET'])
@token_required
@module_required('POS', 'Camarero')
def list_sales(current_user):
    statuses = [s for s in request.args.get('status', 'open,billing').split(',') if s in SALE_STATUSES]
    query = PosSale.query.filter(PosSale.status.in_(statuses))
    sale_type = request.args.get('type')
    if sale_type in SALE_TYPES:
        query = query.filter_by(sale_type=sale_type)
    sales = query.order_by(PosSale.opened_at.desc()).limit(200).all()
    return jsonify({'sales': [sale_to_dict(s, include_items=False) for s in sales]}), 200


@bp.route('/sales', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def open_sale(current_user):
    def action():
        data = _body()
        return sale_service.open_sale(current_user, data.get('sale_type'), table_id=data.get('table_id'),
                                      people=data.get('people'), customer_name=data.get('customer_name'),
                                      comment=data.get('comment'), waiter_id=data.get('waiter_id'))
    return _respond(action)


@bp.route('/sales/<int:sale_id>', methods=['GET'])
@token_required
@module_required('POS', 'Camarero')
def get_sale(current_user, sale_id):
    def action():
        sale = db.session.get(PosSale, sale_id)
        if sale is None:
            raise not_found('La venta no existe')
        return sale
    return _respond(action)


@bp.route('/sales/<int:sale_id>/items', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def add_item(current_user, sale_id):
    def action():
        data = _body()
        return sale_service.add_item(current_user, sale_id, data.get('product_variant_id'),
                                     quantity=data.get('quantity', 1),
                                     modifier_option_ids=data.get('modifier_option_ids', []),
                                     note=data.get('note'))
    return _respond(action)


@bp.route('/sales/<int:sale_id>/items/<int:item_id>', methods=['DELETE'])
@token_required
@module_required('POS', 'Camarero')
def delete_item(current_user, sale_id, item_id):
    return _respond(lambda: sale_service.delete_item(current_user, sale_id, item_id))


@bp.route('/sales/<int:sale_id>/confirm', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def confirm(current_user, sale_id):
    return _respond(lambda: sale_service.confirm_batch(current_user, sale_id))


@bp.route('/sales/<int:sale_id>/items/<int:item_id>/cancel', methods=['POST'])
@token_required
@module_required('Anular')
def cancel_item(current_user, sale_id, item_id):
    return _respond(lambda: sale_service.cancel_item(current_user, sale_id, item_id, _body().get('reason')))


@bp.route('/sales/<int:sale_id>/request-bill', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def request_bill(current_user, sale_id):
    return _respond(lambda: sale_service.request_bill(current_user, sale_id))


@bp.route('/sales/<int:sale_id>/reopen', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def reopen(current_user, sale_id):
    return _respond(lambda: sale_service.reopen(current_user, sale_id))


@bp.route('/sales/<int:sale_id>/discounts', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def add_discount(current_user, sale_id):
    def action():
        data = _body()
        return discount_service.add_discount(current_user, sale_id, item_id=data.get('item_id'),
                                             template_id=data.get('template_id'), kind=data.get('kind'),
                                             value=data.get('value'), reason=data.get('reason'))
    return _respond(action)


@bp.route('/discounts/<int:discount_id>/cancel', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def cancel_discount(current_user, discount_id):
    return _respond(lambda: discount_service.cancel_discount(current_user, discount_id))


@bp.route('/sales/<int:sale_id>/payments', methods=['POST'])
@token_required
@module_required('POS', 'Cobrar')
def add_payment(current_user, sale_id):
    def action():
        data = _body()
        return payment_service.add_payment(current_user, sale_id, data.get('payment_method_id'), data.get('amount'),
                                           tendered=data.get('tendered'),
                                           client_request_id=data.get('client_request_id'))
    return _respond(action)


@bp.route('/payments/<int:payment_id>/cancel', methods=['POST'])
@token_required
@module_required('Anular')
def cancel_payment(current_user, payment_id):
    return _respond(lambda: payment_service.cancel_payment(current_user, payment_id, _body().get('reason')))


@bp.route('/sales/<int:sale_id>/close', methods=['POST'])
@token_required
@module_required('POS', 'Cobrar')
def close_sale(current_user, sale_id):
    return _respond(lambda: payment_service.close_sale(current_user, sale_id))


@bp.route('/sales/<int:sale_id>/move', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def move_sale(current_user, sale_id):
    return _respond(lambda: sale_service.move_sale(current_user, sale_id, _body().get('table_id')))


@bp.route('/sales/<int:sale_id>/split', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def split_sale(current_user, sale_id):
    """Devuelve la venta nueva; la UI recarga la original."""
    return _respond(lambda: sale_service.split_sale(current_user, sale_id, _body().get('items')))


@bp.route('/sales/<int:sale_id>/cancel', methods=['POST'])
@token_required
@module_required('Anular')
def cancel_sale(current_user, sale_id):
    return _respond(lambda: sale_service.cancel_sale(current_user, sale_id, _body().get('reason')))


@bp.route('/sales/<int:sale_id>/events', methods=['GET'])
@token_required
@module_required('POS')
def sale_events(current_user, sale_id):
    if db.session.get(PosSale, sale_id) is None:
        return jsonify({'error': 'La venta no existe'}), 404
    events = PosSaleEvent.query.filter_by(sale_id=sale_id).order_by(PosSaleEvent.id).all()
    return jsonify({'events': [e.to_dict() for e in events]}), 200
