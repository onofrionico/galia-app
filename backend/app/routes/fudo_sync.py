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
from datetime import date, datetime
from typing import Dict, List, Optional
import logging
import threading

bp = Blueprint('fudo_sync', __name__, url_prefix='/api/v1/fudo')

logger = logging.getLogger(__name__)


def parse_fudo_sale(fudo_sale: Dict) -> Dict:
    """
    Parse Fudo sale data to Galia format
    
    Args:
        fudo_sale: Sale data from Fudo API
    
    Returns:
        Dictionary with parsed sale data
    """
    attributes = fudo_sale.get('attributes', {})
    sale_id = fudo_sale.get('id')
    
    created_at = attributes.get('createdAt')
    closed_at = attributes.get('closedAt')
    
    creacion = None
    if created_at:
        try:
            creacion = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            creacion = datetime.now()
    
    cerrada = None
    if closed_at:
        try:
            cerrada = datetime.fromisoformat(closed_at.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass
    
    fecha = cerrada.date() if cerrada else (creacion.date() if creacion else datetime.now().date())
    
    total = attributes.get('total', 0)
    if total:
        total = float(total)
    
    estado_map = {
        'OPEN': 'Abierta',
        'CLOSED': 'Cerrada',
        'CANCELLED': 'Cancelada'
    }
    estado = estado_map.get(attributes.get('status'), 'Cerrada')
    
    tipo_venta_map = {
        'DELIVERY': 'Delivery',
        'TAKE_AWAY': 'Para llevar',
        'TABLE': 'Local',
        'COUNTER': 'Mostrador'
    }
    tipo_venta = tipo_venta_map.get(attributes.get('type'), 'Local')
    
    relationships = fudo_sale.get('relationships', {})
    table_data = relationships.get('table', {}).get('data')
    room_data = relationships.get('room', {}).get('data')
    
    return {
        'external_id': sale_id,
        'fecha': fecha,
        'creacion': creacion,
        'cerrada': cerrada,
        'caja': attributes.get('cashRegisterName'),
        'estado': estado,
        'cliente': attributes.get('customerName'),
        'mesa': table_data.get('id') if table_data else None,
        'sala': room_data.get('id') if room_data else None,
        'personas': attributes.get('people'),
        'camarero': attributes.get('userName'),
        'medio_pago': None,
        'total': total,
        'fiscal': attributes.get('fiscalReceipt', False),
        'tipo_venta': tipo_venta,
        'comentario': attributes.get('comments'),
        'origen': 'Fudo',
        'id_origen': sale_id
    }


def _sync_sales_background(start_date, end_date, update_existing):
    """Background task for syncing sales"""
    from app import create_app
    app = create_app('production')
    
    with app.app_context():
        try:
            logger.info(f"Starting background sales sync: {start_date} to {end_date}")
            client = FudoClient()
            
            fudo_sales = client.get_all_sales(start_date=start_date, end_date=end_date)
            
            results = {
                'total_fetched': len(fudo_sales),
                'imported': 0,
                'updated': 0,
                'skipped': 0,
                'errors': []
            }
            
            for fudo_sale in fudo_sales:
                try:
                    sale_data = parse_fudo_sale(fudo_sale)
                    external_id = sale_data.get('external_id')
                    
                    existing_sale = Sale.query.filter_by(external_id=external_id).first()
                    
                    if existing_sale:
                        if update_existing:
                            for key, value in sale_data.items():
                                if key != 'external_id':
                                    setattr(existing_sale, key, value)
                            results['updated'] += 1
                        else:
                            results['skipped'] += 1
                    else:
                        new_sale = Sale(**sale_data)
                        db.session.add(new_sale)
                        results['imported'] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing Fudo sale {fudo_sale.get('id')}: {str(e)}")
                    results['errors'].append({
                        'sale_id': fudo_sale.get('id'),
                        'error': str(e)
                    })
            
            db.session.commit()
            logger.info(f"Sales sync completed: {results['imported']} imported, {results['updated']} updated")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in background sales sync: {str(e)}")


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
    return jsonify(run.to_dict()), 200


@bp.route('/sync/runs', methods=['GET'])
@token_required
@admin_required
def list_sync_runs(current_user):
    kind = request.args.get('kind', 'expenses')
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
