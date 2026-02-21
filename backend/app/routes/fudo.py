from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required
from app.services.fudo_sync_service import FudoSyncService
from app.services.fudo_api_client import FudoAPIClient
from app.models import FudoSyncLog
import hmac
import hashlib

fudo_bp = Blueprint('fudo', __name__, url_prefix='/api/fudo')

@fudo_bp.route('/sync/all', methods=['POST'])
@login_required
def sync_all():
    try:
        data = request.get_json() or {}
        days_back = data.get('days_back', 7)
        
        if not current_app.config.get('FUDO_SYNC_ENABLED'):
            return jsonify({
                'error': 'FUdo sync is not enabled'
            }), 400
        
        sync_service = FudoSyncService()
        results = sync_service.sync_all(days_back=days_back)
        
        return jsonify({
            'status': 'success',
            'message': 'Sync completed',
            'results': results
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in sync_all: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500

@fudo_bp.route('/sync/sales', methods=['POST'])
@login_required
def sync_sales():
    try:
        data = request.get_json() or {}
        days_back = data.get('days_back', 7)
        
        if not current_app.config.get('FUDO_SYNC_ENABLED'):
            return jsonify({
                'error': 'FUdo sync is not enabled'
            }), 400
        
        sync_service = FudoSyncService()
        result = sync_service.sync_sales(days_back=days_back)
        
        return jsonify({
            'status': 'success',
            'message': 'Sales sync completed',
            'result': result
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in sync_sales: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500

@fudo_bp.route('/sync/expenses', methods=['POST'])
@login_required
def sync_expenses():
    try:
        data = request.get_json() or {}
        days_back = data.get('days_back', 7)
        
        if not current_app.config.get('FUDO_SYNC_ENABLED'):
            return jsonify({
                'error': 'FUdo sync is not enabled'
            }), 400
        
        sync_service = FudoSyncService()
        result = sync_service.sync_expenses(days_back=days_back)
        
        return jsonify({
            'status': 'success',
            'message': 'Expenses sync completed',
            'result': result
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in sync_expenses: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500

@fudo_bp.route('/sync/payments', methods=['POST'])
@login_required
def sync_payments():
    try:
        data = request.get_json() or {}
        days_back = data.get('days_back', 7)
        
        if not current_app.config.get('FUDO_SYNC_ENABLED'):
            return jsonify({
                'error': 'FUdo sync is not enabled'
            }), 400
        
        sync_service = FudoSyncService()
        result = sync_service.sync_payments(days_back=days_back)
        
        return jsonify({
            'status': 'success',
            'message': 'Payments sync completed',
            'result': result
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in sync_payments: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500

@fudo_bp.route('/sync/logs', methods=['GET'])
@login_required
def get_sync_logs():
    try:
        limit = request.args.get('limit', 50, type=int)
        
        sync_service = FudoSyncService()
        logs = sync_service.get_sync_logs(limit=limit)
        
        return jsonify({
            'status': 'success',
            'logs': [log.to_dict() for log in logs]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in get_sync_logs: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500

@fudo_bp.route('/webhook/order', methods=['POST'])
def webhook_order():
    try:
        webhook_secret = current_app.config.get('FUDO_WEBHOOK_SECRET')
        
        if webhook_secret:
            signature = request.headers.get('X-Fudo-Signature')
            if not signature:
                return jsonify({'error': 'Missing signature'}), 401
            
            body = request.get_data()
            expected_signature = hmac.new(
                webhook_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return jsonify({'error': 'Invalid signature'}), 401
        
        data = request.get_json()
        event_type = data.get('event')
        order_data = data.get('order')
        
        if not order_data:
            return jsonify({'error': 'Missing order data'}), 400
        
        sync_service = FudoSyncService()
        
        if event_type in ['ORDER-CONFIRMED', 'ORDER-CLOSED', 'ORDER-REJECTED', 
                          'ORDER-READY-TO-DELIVER', 'ORDER-DELIVERY-SENT']:
            sale = sync_service._process_sale(order_data)
            
            return jsonify({
                'status': 'success',
                'message': f'Order {event_type} processed',
                'sale_id': sale.id
            }), 200
        
        return jsonify({
            'status': 'success',
            'message': 'Event received but not processed'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in webhook_order: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500

@fudo_bp.route('/test/connection', methods=['GET'])
@login_required
def test_connection():
    try:
        client = FudoAPIClient()
        
        response = client.get_payment_methods(page_size=1, page_number=1)
        
        return jsonify({
            'status': 'success',
            'message': 'Connection to FUdo API successful',
            'data': response
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error testing FUdo connection: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@fudo_bp.route('/config/status', methods=['GET'])
@login_required
def get_config_status():
    try:
        config = {
            'sync_enabled': current_app.config.get('FUDO_SYNC_ENABLED', False),
            'api_configured': bool(current_app.config.get('FUDO_CLIENT_ID') and 
                                  current_app.config.get('FUDO_CLIENT_SECRET')),
            'webhook_configured': bool(current_app.config.get('FUDO_WEBHOOK_SECRET')),
            'base_url': current_app.config.get('FUDO_API_BASE_URL')
        }
        
        return jsonify({
            'status': 'success',
            'config': config
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500
