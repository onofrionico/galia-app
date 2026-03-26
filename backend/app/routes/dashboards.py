from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from app.utils.jwt_utils import token_required
from app.services.dashboard_service import DashboardService

bp = Blueprint('dashboards', __name__, url_prefix='/api/v1/dashboards')

@bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint for dashboards module"""
    return {'status': 'ok', 'module': 'dashboards'}, 200

@bp.route('/suppliers', methods=['GET'])
@token_required
def get_suppliers_dashboard(current_user):
    """
    Get supplier purchases dashboard with analytics
    
    Query Parameters:
        - start_date: Start date (YYYY-MM-DD), default: first day of current month
        - end_date: End date (YYYY-MM-DD), default: today
        - currency: Currency code (default: ARS)
        - period: Predefined period (today, week, month, quarter, year)
    """
    try:
        # Get query parameters
        period = request.args.get('period', 'month')
        currency = request.args.get('currency', 'ARS')
        
        # Calculate dates based on period
        today = datetime.now().date()
        
        if period == 'today':
            start_date = today
            end_date = today
        elif period == 'week':
            start_date = today - timedelta(days=today.weekday())
            end_date = today
        elif period == 'month':
            start_date = datetime(today.year, today.month, 1).date()
            end_date = today
        elif period == 'quarter':
            quarter = (today.month - 1) // 3
            start_date = datetime(today.year, quarter * 3 + 1, 1).date()
            end_date = today
        elif period == 'year':
            start_date = datetime(today.year, 1, 1).date()
            end_date = today
        elif period == 'custom':
            # Allow custom date range
            start_date_str = request.args.get('start_date')
            end_date_str = request.args.get('end_date')
            
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            else:
                start_date = datetime(today.year, today.month, 1).date()
            
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            else:
                end_date = today
        else:
            # Default to current month
            start_date = datetime(today.year, today.month, 1).date()
            end_date = today
        
        # Get dashboard data
        dashboard_data = DashboardService.get_suppliers_dashboard(
            start_date=start_date,
            end_date=end_date,
            currency=currency
        )
        
        return jsonify(dashboard_data), 200
        
    except ValueError as e:
        return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/suppliers/compare', methods=['GET'])
@token_required
def compare_suppliers(current_user):
    """
    Compare multiple suppliers side by side
    
    Query Parameters:
        - supplier_ids: Comma-separated list of supplier IDs
        - start_date: Start date (YYYY-MM-DD)
        - end_date: End date (YYYY-MM-DD)
        - currency: Currency code (default: ARS)
    """
    try:
        supplier_ids_str = request.args.get('supplier_ids', '')
        if not supplier_ids_str:
            return jsonify({'error': 'supplier_ids parameter is required'}), 400
        
        supplier_ids = [int(sid) for sid in supplier_ids_str.split(',')]
        
        # Get date parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        currency = request.args.get('currency', 'ARS')
        
        today = datetime.now().date()
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else datetime(today.year, today.month, 1).date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else today
        
        # Get comparison data
        comparison_data = DashboardService.get_supplier_comparison(
            supplier_ids=supplier_ids,
            start_date=start_date,
            end_date=end_date,
            currency=currency
        )
        
        return jsonify(comparison_data), 200
        
    except ValueError as e:
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/frequency', methods=['GET'])
@token_required
def get_purchase_frequency(current_user):
    """
    Get purchase frequency analysis for suppliers
    
    Query parameters:
    - supplier_id: Optional supplier ID to filter by specific supplier
    - days: Number of days to analyze (default: 90)
    """
    try:
        supplier_id = request.args.get('supplier_id', type=int)
        days = request.args.get('days', default=90, type=int)
        
        if days < 7 or days > 365:
            return jsonify({'error': 'Days must be between 7 and 365'}), 400
        
        data = DashboardService.get_purchase_frequency_analysis(
            supplier_id=supplier_id,
            days=days
        )
        
        return jsonify(data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
