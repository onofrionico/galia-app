from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from marshmallow import ValidationError
from datetime import datetime
from app.services.purchase_service import PurchaseService
from app.schemas.purchase_schema import PurchaseSchema, PurchaseListSchema
from app.utils.decorators import admin_required

bp = Blueprint('purchases', __name__, url_prefix='/api/v1/purchases')

purchase_service = PurchaseService()
purchase_schema = PurchaseSchema()
purchase_list_schema = PurchaseListSchema()


@bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint for purchases module"""
    return {'status': 'ok', 'module': 'purchases'}, 200


@bp.route('', methods=['POST'])
@login_required
@admin_required
def create_purchase():
    """
    Create a new purchase with items
    
    Required fields:
    - supplier_id: ID of the supplier
    - purchase_date: Date of purchase
    - items: List of purchase items with product_id, quantity, unit_price
    
    Optional fields:
    - related_expense_id: Link to expense record
    - currency: Currency code (default: ARS)
    - exchange_rate: Exchange rate if foreign currency
    - invoice_number: Invoice number
    - cae_number: CAE number
    - payment_status: Payment status (default: pending)
    - notes: Additional notes
    """
    try:
        data = request.get_json()
        
        validated_data = purchase_schema.load(data)
        
        purchase = purchase_service.create_purchase(
            validated_data,
            user_id=current_user.id
        )
        
        result = purchase_schema.dump(purchase)
        
        return jsonify(result), 201
        
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'messages': e.messages}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to create purchase: {str(e)}'}), 500


@bp.route('', methods=['GET'])
@login_required
def list_purchases():
    """
    List purchases with optional filters
    
    Query parameters:
    - supplier_id: Filter by supplier
    - payment_status: Filter by payment status
    - currency: Filter by currency
    - date_from: Filter purchases from this date
    - date_to: Filter purchases until this date
    - invoice_number: Search by invoice number
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20)
    """
    try:
        filters = {}
        
        if request.args.get('supplier_id'):
            filters['supplier_id'] = int(request.args.get('supplier_id'))
        
        if request.args.get('payment_status'):
            filters['payment_status'] = request.args.get('payment_status')
        
        if request.args.get('currency'):
            filters['currency'] = request.args.get('currency')
        
        if request.args.get('date_from'):
            filters['date_from'] = datetime.strptime(request.args.get('date_from'), '%Y-%m-%d').date()
        
        if request.args.get('date_to'):
            filters['date_to'] = datetime.strptime(request.args.get('date_to'), '%Y-%m-%d').date()
        
        if request.args.get('invoice_number'):
            filters['invoice_number'] = request.args.get('invoice_number')
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        result = purchase_service.search_purchases(
            filters=filters,
            page=page,
            per_page=per_page
        )
        
        return jsonify(purchase_list_schema.dump(result)), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to list purchases: {str(e)}'}), 500


@bp.route('/<int:purchase_id>', methods=['GET'])
@login_required
def get_purchase(purchase_id):
    """Get a single purchase with all items"""
    try:
        purchase = purchase_service.get_purchase_with_items(purchase_id)
        
        result = purchase_schema.dump(purchase)
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Failed to get purchase: {str(e)}'}), 500


@bp.route('/<int:purchase_id>', methods=['PUT'])
@login_required
@admin_required
def update_purchase(purchase_id):
    """
    Update an existing purchase
    
    Supports optimistic locking via version field.
    Include current version in request to prevent conflicts.
    """
    try:
        data = request.get_json()
        
        validated_data = purchase_schema.load(data, partial=True)
        
        purchase = purchase_service.update_purchase(
            purchase_id,
            validated_data,
            user_id=current_user.id
        )
        
        result = purchase_schema.dump(purchase)
        
        return jsonify(result), 200
        
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'messages': e.messages}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to update purchase: {str(e)}'}), 500


@bp.route('/<int:purchase_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_purchase(purchase_id):
    """
    Soft delete a purchase (only allowed within 7 days of creation)
    """
    try:
        purchase_service.delete_purchase(purchase_id, user_id=current_user.id)
        
        return jsonify({'message': 'Purchase deleted successfully'}), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to delete purchase: {str(e)}'}), 500


@bp.route('/from-expense/<int:expense_id>', methods=['GET'])
@login_required
def get_purchase_from_expense(expense_id):
    """Get purchase linked to a specific expense"""
    try:
        purchase = purchase_service.get_purchase_from_expense(expense_id)
        
        if not purchase:
            return jsonify({'error': 'No purchase found for this expense'}), 404
        
        result = purchase_schema.dump(purchase)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get purchase: {str(e)}'}), 500


@bp.route('/<int:purchase_id>/update-prices', methods=['POST'])
@login_required
@admin_required
def update_product_prices(purchase_id):
    """
    Update product catalog prices based on purchase prices
    
    Request body:
    {
        "price_updates": [
            {"product_id": 1, "new_price": 150.00},
            {"product_id": 2, "new_price": 200.00}
        ]
    }
    """
    try:
        data = request.get_json()
        price_updates = data.get('price_updates', [])
        
        if not price_updates:
            return jsonify({'error': 'No price updates provided'}), 400
        
        updated_count = purchase_service.update_product_prices_from_purchase(
            purchase_id,
            price_updates,
            user_id=current_user.id
        )
        
        return jsonify({
            'message': f'Successfully updated {updated_count} product prices',
            'updated_count': updated_count
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to update prices: {str(e)}'}), 500
