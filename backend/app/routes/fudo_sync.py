from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.sale import Sale
from app.models.expense import Expense, ExpenseCategory
from app.utils.jwt_utils import token_required
from app.utils.decorators import admin_required
from app.utils.fudo_client import FudoClient
from datetime import datetime
from typing import Dict, List, Optional
import logging

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


def parse_fudo_expense(fudo_expense: Dict, category_mapping: Dict[str, int]) -> Optional[Dict]:
    """
    Parse Fudo expense data to Galia format
    
    Args:
        fudo_expense: Expense data from Fudo API
        category_mapping: Mapping from Fudo category IDs to Galia category IDs
    
    Returns:
        Dictionary with parsed expense data or None if category not mapped
    """
    attributes = fudo_expense.get('attributes', {})
    expense_id = fudo_expense.get('id')
    
    date_str = attributes.get('date')
    fecha = None
    if date_str:
        try:
            fecha = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            fecha = datetime.now().date()
    else:
        fecha = datetime.now().date()
    
    amount = attributes.get('amount', 0)
    # Convert to float even if amount is 0
    try:
        amount = float(amount) if amount is not None else 0.0
    except (ValueError, TypeError):
        amount = 0.0
    
    relationships = fudo_expense.get('relationships', {})
    fudo_category_data = relationships.get('expenseCategory', {}).get('data')
    fudo_category_id = fudo_category_data.get('id') if fudo_category_data else None
    
    galia_category_id = None
    if fudo_category_id and category_mapping:
        galia_category_id = category_mapping.get(fudo_category_id)
        if not galia_category_id:
            logger.info(f"No category mapping found for Fudo expense {expense_id} with category {fudo_category_id} - importing without category")
    
    provider_data = relationships.get('provider', {}).get('data')
    provider_id = provider_data.get('id') if provider_data else None
    
    payment_method_data = relationships.get('paymentMethod', {}).get('data')
    
    estado_pago_map = {
        'PENDING': 'Pendiente',
        'PAID': 'Pagado',
        'CANCELLED': 'Cancelado'
    }
    estado_pago = estado_pago_map.get(attributes.get('status'), 'Pendiente')
    
    return {
        'external_id': expense_id,
        'fecha': fecha,
        'fecha_vencimiento': None,
        'proveedor': attributes.get('providerName'),
        'category_id': galia_category_id,
        'comentario': attributes.get('description'),
        'estado_pago': estado_pago,
        'importe': amount,
        'de_caja': attributes.get('fromCashRegister', False),
        'caja': attributes.get('cashRegisterName'),
        'medio_pago': attributes.get('paymentMethodName'),
        'numero_fiscal': attributes.get('receiptNumber'),
        'tipo_comprobante': attributes.get('receiptTypeName'),
        'numero_comprobante': attributes.get('receiptNumber'),
        'creado_por': 'Fudo Sync',
        'cancelado': attributes.get('status') == 'CANCELLED'
    }


@bp.route('/sync/sales', methods=['POST'])
@token_required
@admin_required
def sync_sales(current_user):
    """
    Sync sales from Fudo API
    
    Query params:
        - start_date: Start date in ISO format (e.g., '2024-01-01T00:00:00Z')
        - end_date: End date in ISO format (e.g., '2024-01-31T23:59:59Z')
        - update_existing: Whether to update existing sales (default: false)
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        update_existing = request.args.get('update_existing', 'false').lower() == 'true'
        
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
        
        return jsonify({
            'message': f"Sincronización completada: {results['imported']} ventas importadas, {results['updated']} actualizadas",
            'results': results
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error syncing sales from Fudo: {str(e)}")
        return jsonify({'error': f'Error sincronizando ventas: {str(e)}'}), 500


@bp.route('/sync/expenses', methods=['POST'])
@token_required
@admin_required
def sync_expenses(current_user):
    """
    Sync expenses from Fudo API
    
    Query params:
        - start_date: Start date in format YYYY-MM-DD
        - end_date: End date in format YYYY-MM-DD
        - update_existing: Whether to update existing expenses (default: false)
    
    Body (optional):
        - category_mapping: Dict mapping Fudo category IDs to Galia category IDs
          Example: {"1": 5, "2": 7}
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        update_existing = request.args.get('update_existing', 'false').lower() == 'true'
        
        data = request.get_json() or {}
        category_mapping = data.get('category_mapping', {})
        
        # category_mapping is optional - expenses without mapping will have category_id = None
        
        client = FudoClient()
        
        fudo_expenses = client.get_all_expenses(start_date=start_date, end_date=end_date)
        
        results = {
            'total_fetched': len(fudo_expenses),
            'imported': 0,
            'updated': 0,
            'skipped': 0,
            'no_category_mapping': 0,
            'errors': []
        }
        
        for fudo_expense in fudo_expenses:
            try:
                expense_data = parse_fudo_expense(fudo_expense, category_mapping)
                
                if not expense_data:
                    results['errors'].append({
                        'expense_id': fudo_expense.get('id'),
                        'error': 'Error parsing expense data'
                    })
                    continue
                
                # Track if expense has no category mapping
                if not expense_data.get('category_id'):
                    results['no_category_mapping'] += 1
                
                external_id = expense_data.get('external_id')
                
                existing_expense = Expense.query.filter_by(external_id=external_id).first()
                
                if existing_expense:
                    if update_existing:
                        for key, value in expense_data.items():
                            if key != 'external_id':
                                setattr(existing_expense, key, value)
                        results['updated'] += 1
                    else:
                        results['skipped'] += 1
                else:
                    new_expense = Expense(**expense_data)
                    db.session.add(new_expense)
                    results['imported'] += 1
                    
            except Exception as e:
                logger.error(f"Error processing Fudo expense {fudo_expense.get('id')}: {str(e)}")
                results['errors'].append({
                    'expense_id': fudo_expense.get('id'),
                    'error': str(e)
                })
        
        db.session.commit()
        
        return jsonify({
            'message': f"Sincronización completada: {results['imported']} gastos importados, {results['updated']} actualizados",
            'results': results
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error syncing expenses from Fudo: {str(e)}")
        return jsonify({'error': f'Error sincronizando gastos: {str(e)}'}), 500


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
