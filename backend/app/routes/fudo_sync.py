from flask import Blueprint, current_app, request, jsonify
from app.extensions import db
from app.models.sale import Sale
from app.models.expense import ExpenseCategory
from app.utils.jwt_utils import token_required
from app.utils.decorators import admin_required
from app.utils.fudo_client import FudoClient
from app.models.fudo_sync_run import FudoSyncRun
from app.services import fudo_sync_runs
from app.services.fudo_sync_runs import SyncInProgress
from app.services.sale_fudo_parsing import parse_fudo_sale  # noqa: F401 (reexportado)
from app.services.sales_sync_service import apply_fudo_sales
from app.services import cutover
from app.services.pos.errors import PosError
from app.models.operation_settings import FudoImportMonth
from datetime import date, datetime
from typing import Dict, List, Optional
import logging
import threading

bp = Blueprint('fudo_sync', __name__, url_prefix='/api/v1/fudo')

logger = logging.getLogger(__name__)


def _sync_sales_background(start_date, end_date, update_existing):
    """Background task for syncing sales"""
    from app import create_app
    app = create_app('production')
    
    with app.app_context():
        try:
            logger.info(f"Starting background sales sync: {start_date} to {end_date}")
            client = FudoClient()
            
            payload = client.get_all_sales_with_included(start_date=start_date, end_date=end_date)
            results = apply_fudo_sales(payload, update_existing)
            for error in results['errors']:
                logger.error(f"Error processing Fudo sale {error['sale_id']}: {error['error']}")
            
            db.session.commit()
            logger.info(f"Sales sync completed: {results['imported']} imported, {results['updated']} updated, "
                        f"{results['items_backfilled']} con ítems completados")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in background sales sync: {str(e)}")


def _fudo_off_response():
    """409 si Fudo está apagado; None si se puede usar."""
    try:
        cutover.require_fudo_on()
    except PosError as exc:
        return jsonify({'error': exc.message}), exc.status
    return None


@bp.route('/sync/sales/history', methods=['POST'])
@token_required
@admin_required
def sync_sales_history(current_user):
    """Importa toda la historia de ventas de Fudo, mes por mes. Query: from_month (YYYY-MM), force."""
    blocked = _fudo_off_response()
    if blocked:
        return blocked
    from_month = None
    if request.args.get('from_month'):
        try:
            from_month = date.fromisoformat(f"{request.args['from_month']}-01")
        except ValueError:
            return jsonify({'error': 'Mes inválido, usá YYYY-MM'}), 400
    force = request.args.get('force', 'false').lower() == 'true'
    params = {'from_month': from_month.isoformat() if from_month else None, 'force': force}
    try:
        run = fudo_sync_runs.start_run('sales_history', params, current_user.id)
    except SyncInProgress as exc:
        return jsonify({'error': 'Ya hay una importación de ventas en curso', 'run_id': exc.run.id}), 409
    _launch(fudo_sync_runs.run_sales_history, current_app._get_current_object(), run.id, from_month, force,
            FudoClient)
    return jsonify({'message': 'Importación de la historia iniciada', 'status': 'processing', 'run_id': run.id}), 202


@bp.route('/import/months', methods=['GET'])
@token_required
@admin_required
def import_months(current_user):
    months = FudoImportMonth.query.order_by(FudoImportMonth.month.desc()).all()
    return jsonify({'months': [m.to_dict() for m in months]}), 200


@bp.route('/sync/sales', methods=['POST'])
@token_required
@admin_required
def sync_sales(current_user):
    """
    Sync sales from Fudo API (runs in background)
    
    Query params:
        - start_date: Start date in ISO format (e.g., '2024-01-01T00:00:00Z')
        - end_date: End date in ISO format (e.g., '2024-01-31T23:59:59Z')
        - update_existing: Whether to update existing sales (default: false)
    """
    blocked = _fudo_off_response()
    if blocked:
        return blocked
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        update_existing = request.args.get('update_existing', 'false').lower() == 'true'
        
        # Start background thread
        thread = threading.Thread(
            target=_sync_sales_background,
            args=(start_date, end_date, update_existing)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': 'Sincronización de ventas iniciada en segundo plano',
            'status': 'processing',
            'start_date': start_date,
            'end_date': end_date
        }), 202
        
    except Exception as e:
        logger.error(f"Error starting sales sync: {str(e)}")
        return jsonify({'error': f'Error iniciando sincronización: {str(e)}'}), 500


MAX_RANGE_DAYS = 366


def _parse_range(args):
    """(start, end) en ISO o un mensaje de error."""
    start_raw, end_raw = args.get('start_date'), args.get('end_date')
    if not start_raw or not end_raw:
        return None, 'start_date y end_date son obligatorias (YYYY-MM-DD)'
    try:
        start, end = date.fromisoformat(start_raw), date.fromisoformat(end_raw)
    except ValueError:
        return None, 'Formato de fecha inválido, usá YYYY-MM-DD'
    if start > end:
        return None, 'start_date no puede ser posterior a end_date'
    if (end - start).days > MAX_RANGE_DAYS:
        return None, f'El rango no puede superar {MAX_RANGE_DAYS} días'
    return (start.isoformat(), end.isoformat()), None


def _launch(target, *args):
    threading.Thread(target=target, args=args, daemon=True).start()


@bp.route('/sync/expenses', methods=['POST'])
@token_required
@admin_required
def sync_expenses(current_user):
    """Sincroniza gastos de Fudo en segundo plano. Query: start_date, end_date (YYYY-MM-DD)."""
    blocked = _fudo_off_response()
    if blocked:
        return blocked
    dates, error = _parse_range(request.args)
    if error:
        return jsonify({'error': error}), 400
    start, end = dates
    try:
        run = fudo_sync_runs.start_run('expenses', {'start_date': start, 'end_date': end}, current_user.id)
    except SyncInProgress as exc:
        return jsonify({'error': 'Ya hay una sincronización de gastos en curso', 'run_id': exc.run.id}), 409

    _launch(fudo_sync_runs.run_expenses_sync, current_app._get_current_object(), run.id, start, end, FudoClient)
    return jsonify({'message': 'Sincronización de gastos iniciada', 'status': 'processing', 'run_id': run.id}), 202


@bp.route('/sync/runs/<int:run_id>', methods=['GET'])
@token_required
@admin_required
def get_sync_run(current_user, run_id):
    run = db.session.get(FudoSyncRun, run_id)
    if run is None:
        return jsonify({'error': 'Corrida no encontrada'}), 404
    fudo_sync_runs.expire_stale(run.kind)
    db.session.commit()
    return jsonify(run.to_dict()), 200


@bp.route('/sync/runs', methods=['GET'])
@token_required
@admin_required
def list_sync_runs(current_user):
    kind = request.args.get('kind', 'expenses')
    fudo_sync_runs.expire_stale(kind)
    db.session.commit()
    try:
        limit = max(1, min(int(request.args.get('limit', 5)), 50))
    except ValueError:
        limit = 5
    runs = (FudoSyncRun.query.filter_by(kind=kind)
            .order_by(FudoSyncRun.started_at.desc(), FudoSyncRun.id.desc()).limit(limit).all())
    return jsonify({'runs': [run.to_dict() for run in runs]}), 200


@bp.route('/categories', methods=['GET'])
@token_required
@admin_required
def get_fudo_categories(current_user):
    """Get expense categories from Fudo API for mapping"""
    try:
        client = FudoClient()
        response = client.get_expense_categories()
        
        categories = []
        for category in response.get('data', []):
            attributes = category.get('attributes', {})
            
            categories.append({
                'id': category.get('id'),
                'name': attributes.get('name', f"Categoría {category.get('id')}"),
                'active': attributes.get('active', True),
                'financial_category': attributes.get('financialCategory')
            })
        
        return jsonify({
            'fudo_categories': categories,
            'galia_categories': [cat.to_dict() for cat in ExpenseCategory.query.filter_by(is_active=True).all()]
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching Fudo categories: {str(e)}")
        return jsonify({'error': f'Error obteniendo categorías: {str(e)}'}), 500


@bp.route('/payment-methods', methods=['GET'])
@token_required
@admin_required
def get_fudo_payment_methods(current_user):
    """Get payment methods from Fudo API"""
    try:
        client = FudoClient()
        response = client.get_payment_methods()
        
        payment_methods = []
        for method in response.get('data', []):
            payment_methods.append({
                'id': method.get('id'),
                'name': method.get('attributes', {}).get('name'),
                'type': method.get('attributes', {}).get('type')
            })
        
        return jsonify({'payment_methods': payment_methods}), 200
        
    except Exception as e:
        logger.error(f"Error fetching Fudo payment methods: {str(e)}")
        return jsonify({'error': f'Error obteniendo métodos de pago: {str(e)}'}), 500


@bp.route('/test-connection', methods=['GET'])
@token_required
@admin_required
def test_connection(current_user):
    """Test connection to Fudo API"""
    try:
        client = FudoClient()
        client._get_valid_token()
        
        return jsonify({
            'status': 'success',
            'message': 'Conexión exitosa con la API de Fudo',
            'token_expiration': client.token_expiration.isoformat() if client.token_expiration else None
        }), 200
        
    except Exception as e:
        logger.error(f"Error testing Fudo connection: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error conectando con la API de Fudo: {str(e)}'
        }), 500
