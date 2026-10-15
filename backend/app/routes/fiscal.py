"""API de facturación electrónica ARCA."""
import logging
from datetime import date

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import DataError, IntegrityError

from app.extensions import db
from app.services.fiscal import invoice_service
from app.services.fiscal import settings as fiscal_settings
from app.services.pos.errors import PosError, bad_request
from app.utils.decorators import admin_required, module_required
from app.utils.jwt_utils import token_required
from app.utils.validation import json_object

logger = logging.getLogger(__name__)
bp = Blueprint('fiscal', __name__, url_prefix='/api/v1/fiscal')
ISSUE_STATUS = {'authorized': 201, 'pending': 202}


def _body():
    return json_object() or {}


def _run(action, status=200):
    try:
        payload, status = action(), status
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
        return jsonify({'error': 'Otra operación modificó la facturación al mismo tiempo, probá de nuevo'}), 409
    except DataError:
        db.session.rollback()
        return jsonify({'error': 'Algún valor es demasiado grande'}), 400
    except Exception:
        db.session.rollback()
        logger.exception('Error inesperado en la facturación')
        return jsonify({'error': 'Error interno, probá de nuevo'}), 500
    return jsonify(payload), status


def _issued(action):
    """Emisión: 201 autorizado, 202 pendiente, 409 rechazado (con el comprobante en 'invoice')."""
    def wrapped():
        invoice = action()
        data = invoice_service.invoice_to_dict(invoice)
        if invoice.status == 'rejected':
            raise PosError(invoice.error or 'ARCA rechazó el comprobante', invoice=data)
        return data, ISSUE_STATUS[invoice.status]
    return _run(wrapped)


def _date_arg(name):
    value = request.args.get(name)
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise bad_request('La fecha es inválida')


@bp.route('/sales/<int:sale_id>/preview', methods=['GET'])
@token_required
@module_required('POS')
def preview(current_user, sale_id):
    return _run(lambda: invoice_service.preview(sale_id))


@bp.route('/sales/<int:sale_id>/invoice', methods=['POST'])
@token_required
@module_required('POS')
def issue(current_user, sale_id):
    return _issued(lambda: invoice_service.issue(current_user, sale_id, _body().get('customer')))


@bp.route('/sales/<int:sale_id>/invoices', methods=['GET'])
@token_required
@module_required('POS')
def sale_invoices(current_user, sale_id):
    return _run(lambda: {'invoices': invoice_service.sale_invoices(sale_id)})


@bp.route('/invoices/<int:invoice_id>/verify', methods=['POST'])
@token_required
@module_required('POS')
def verify(current_user, invoice_id):
    return _run(lambda: invoice_service.invoice_to_dict(invoice_service.verify(current_user, invoice_id)))


@bp.route('/invoices/<int:invoice_id>/cancel', methods=['POST'])
@token_required
@module_required('POS')
def cancel(current_user, invoice_id):
    return _issued(lambda: invoice_service.cancel(current_user, invoice_id))


@bp.route('/invoices/<int:invoice_id>/reprint', methods=['POST'])
@token_required
@module_required('POS')
def reprint(current_user, invoice_id):
    return _run(lambda: invoice_service.invoice_to_dict(invoice_service.reprint(current_user, invoice_id)))


@bp.route('/invoices', methods=['GET'])
@token_required
@module_required('POS')
def list_invoices(current_user):
    def action():
        page = request.args.get('page', '1')
        if not page.isdigit() or int(page) < 1:
            raise bad_request('La página es inválida')
        return invoice_service.list_invoices(_date_arg('from'), _date_arg('to'), request.args.get('kind'),
                                             request.args.get('status'), int(page))
    return _run(action)


@bp.route('/invoices/<int:invoice_id>', methods=['GET'])
@token_required
@module_required('POS')
def get_invoice(current_user, invoice_id):
    return _run(lambda: invoice_service.get_invoice(invoice_id))


@bp.route('/customers', methods=['GET'])
@token_required
@module_required('POS')
def customers(current_user):
    return _run(lambda: {'customers': invoice_service.search_customers(request.args.get('q'))})


@bp.route('/settings', methods=['GET'])
@token_required
@admin_required
def get_settings(current_user):
    def action():
        settings = fiscal_settings.get_or_create_settings()
        db.session.commit()
        return fiscal_settings.settings_to_dict(settings)
    return _run(action)


@bp.route('/settings', methods=['PUT'])
@token_required
@admin_required
def put_settings(current_user):
    def action():
        settings = fiscal_settings.update_settings(_body())
        db.session.commit()
        return fiscal_settings.settings_to_dict(settings)
    return _run(action)


@bp.route('/settings/<environment>/csr', methods=['POST'])
@token_required
@admin_required
def generate_csr(current_user, environment):
    def action():
        csr = fiscal_settings.generate_csr(fiscal_settings.get_or_create_settings(), environment)
        db.session.commit()
        return {'csr': csr}
    return _run(action)


@bp.route('/settings/<environment>/certificate', methods=['PUT'])
@token_required
@admin_required
def save_certificate(current_user, environment):
    def action():
        settings = fiscal_settings.get_or_create_settings()
        fiscal_settings.save_certificate(settings, environment, _body().get('certificate'))
        db.session.commit()
        return fiscal_settings.settings_to_dict(settings)
    return _run(action)


@bp.route('/settings/test', methods=['POST'])
@token_required
@admin_required
def test_connection(current_user):
    return _run(invoice_service.test_connection)
