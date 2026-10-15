"""API de impresión del POS: precuenta, ticket, reimpresión, cola del punto de impresión y firma de QZ Tray."""
import logging

from flask import Blueprint, Response, jsonify
from sqlalchemy.exc import DataError, IntegrityError

from app.extensions import db
from app.models.pos import PrintStation
from app.services.pos import print_service, qz_signing
from app.services.pos.errors import PosError
from app.utils.decorators import module_required
from app.utils.jwt_utils import token_required
from app.utils.validation import json_object

logger = logging.getLogger(__name__)
bp = Blueprint('pos_print', __name__, url_prefix='/api/v1/pos')


def _body():
    return json_object() or {}


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
        return jsonify({'error': 'Otra operación modificó la impresión al mismo tiempo, probá de nuevo'}), 409
    except DataError:
        db.session.rollback()
        return jsonify({'error': 'Algún valor es demasiado grande'}), 400
    except Exception:
        db.session.rollback()
        logger.exception('Error inesperado en la impresión')
        return jsonify({'error': 'Error interno, probá de nuevo'}), 500
    return jsonify(payload), 200


def _job(job):
    return print_service.job_to_dict(job)


@bp.route('/sales/<int:sale_id>/print/bill', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def print_bill(current_user, sale_id):
    return _run(lambda: _job(print_service.print_bill(current_user, sale_id)))


@bp.route('/sales/<int:sale_id>/print/receipt', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def print_receipt(current_user, sale_id):
    return _run(lambda: _job(print_service.print_receipt(current_user, sale_id)))


@bp.route('/print/jobs/<int:job_id>/reprint', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def reprint(current_user, job_id):
    return _run(lambda: _job(print_service.reprint(current_user, job_id)))


@bp.route('/sales/<int:sale_id>/print-jobs', methods=['GET'])
@token_required
@module_required('POS', 'Camarero')
def sale_jobs(current_user, sale_id):
    return _run(lambda: {'jobs': [_job(j) for j in print_service.sale_jobs(sale_id)]})


@bp.route('/print/stations', methods=['GET'])
@token_required
@module_required('POS', 'Camarero', 'Products')
def stations(current_user):
    rows = PrintStation.query.filter_by(is_active=True).order_by(PrintStation.position, PrintStation.id).all()
    return jsonify({'stations': [s.to_dict() for s in rows]}), 200


@bp.route('/print/claim', methods=['POST'])
@token_required
@module_required('POS')
def claim(current_user):
    def action():
        jobs = print_service.claim(_body().get('print_point'))
        return {'jobs': [print_service.job_to_dict(j, with_printer=True) for j in jobs]}
    return _run(action)


@bp.route('/print/jobs/<int:job_id>/done', methods=['POST'])
@token_required
@module_required('POS')
def job_done(current_user, job_id):
    return _run(lambda: _job(print_service.mark_done(job_id)))


@bp.route('/print/jobs/<int:job_id>/failed', methods=['POST'])
@token_required
@module_required('POS')
def job_failed(current_user, job_id):
    return _run(lambda: _job(print_service.mark_failed(job_id, _body().get('error'))))


@bp.route('/print/jobs/<int:job_id>/retry', methods=['POST'])
@token_required
@module_required('POS')
def job_retry(current_user, job_id):
    return _run(lambda: _job(print_service.retry(job_id)))


@bp.route('/print/jobs/<int:job_id>/mark-printed', methods=['POST'])
@token_required
@module_required('POS')
def job_mark_printed(current_user, job_id):
    return _run(lambda: _job(print_service.mark_printed(job_id)))


@bp.route('/print/status', methods=['GET'])
@token_required
@module_required('POS')
def print_status(current_user):
    return _run(print_service.status)


@bp.route('/print/points', methods=['GET'])
@token_required
@module_required('POS')
def print_points(current_user):
    return _run(lambda: {'points': print_service.print_points()})


@bp.route('/print/printers/<int:printer_id>/test', methods=['POST'])
@token_required
@module_required('POS')
def test_print(current_user, printer_id):
    return _run(lambda: _job(print_service.test_print(current_user, printer_id)))


@bp.route('/print/qz-certificate', methods=['GET'])
@token_required
@module_required('POS')
def qz_certificate(current_user):
    return _run(lambda: {'certificate': qz_signing.qz_certificate()})


@bp.route('/print/qz-sign', methods=['POST'])
@token_required
@module_required('POS')
def qz_sign(current_user):
    return _run(lambda: {'signature': qz_signing.sign_qz(_body().get('request'))})


@bp.route('/print/qz-setup', methods=['GET'])
@token_required
@module_required('POS')
def qz_setup(current_user):
    """Descarga el .bat que instala el certificado de Galia en QZ Tray (un solo archivo sirve para todas las PCs)."""
    try:
        script = qz_signing.qz_setup_script()
    except Exception:
        db.session.rollback()
        logger.exception('Error generando el script de QZ Tray')
        return jsonify({'error': 'Error interno, probá de nuevo'}), 500
    return Response(script, mimetype='application/octet-stream',
                    headers={'Content-Disposition': f'attachment; filename="{qz_signing.SETUP_FILENAME}"'})
