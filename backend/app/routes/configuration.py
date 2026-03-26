from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from datetime import datetime
from app.services.configuration_service import ConfigurableListService, ExchangeRateService
from app.schemas.configuration_schema import (
    ConfigurableListSchema, 
    ExchangeRateSchema,
    ConfigurableListListSchema,
    ExchangeRateListSchema
)
from app.utils.jwt_utils import token_required
from app.utils.decorators import admin_required

bp = Blueprint('configuration', __name__, url_prefix='/api/v1')

configurable_list_service = ConfigurableListService()
exchange_rate_service = ExchangeRateService()

configurable_list_schema = ConfigurableListSchema()
exchange_rate_schema = ExchangeRateSchema()
configurable_list_list_schema = ConfigurableListListSchema()
exchange_rate_list_schema = ExchangeRateListSchema()


# ============================================================================
# Configurable Lists Endpoints
# ============================================================================

@bp.route('/configurable-lists/<string:list_type>', methods=['GET'])
@token_required
def get_configurable_list(current_user, list_type):
    """
    Get all items for a specific list type
    
    Query parameters:
    - active_only: If true, only return active items (default: true)
    """
    try:
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        items = configurable_list_service.get_by_type(list_type, active_only=active_only)
        
        result = configurable_list_list_schema.dump({
            'items': items,
            'total': len(items)
        })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get configurable list: {str(e)}'}), 500


@bp.route('/configurable-lists/<string:list_type>/values', methods=['GET'])
@token_required
def get_configurable_list_values(current_user, list_type):
    """
    Get just the active values for a specific list type (simplified endpoint)
    
    Returns:
    {
        "values": ["value1", "value2", ...]
    }
    """
    try:
        values = configurable_list_service.get_active_values(list_type)
        
        return jsonify({'values': values}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get values: {str(e)}'}), 500


@bp.route('/configurable-lists', methods=['POST'])
@token_required
@admin_required
def create_configurable_list_item(current_user):
    """
    Create a new configurable list item
    
    Required fields:
    - list_type: Type of list (product_category, unit_of_measure, payment_term, etc.)
    - value: The value to add
    
    Optional fields:
    - display_order: Order for display (default: 0)
    - is_active: Active status (default: true)
    """
    try:
        data = request.get_json()
        
        validated_data = configurable_list_schema.load(data)
        
        item = configurable_list_service.create_item(
            validated_data,
            user_id=current_user.id
        )
        
        result = configurable_list_schema.dump(item)
        
        return jsonify(result), 201
        
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'messages': e.messages}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to create item: {str(e)}'}), 500


@bp.route('/configurable-lists/<int:item_id>', methods=['PUT'])
@token_required
@admin_required
def update_configurable_list_item(current_user, item_id):
    """
    Update a configurable list item
    
    Updatable fields:
    - value: The value
    - display_order: Display order
    - is_active: Active status
    """
    try:
        data = request.get_json()
        
        validated_data = configurable_list_schema.load(data, partial=True)
        
        item = configurable_list_service.update_item(
            item_id,
            validated_data,
            user_id=current_user.id
        )
        
        result = configurable_list_schema.dump(item)
        
        return jsonify(result), 200
        
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'messages': e.messages}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to update item: {str(e)}'}), 500


@bp.route('/configurable-lists/<int:item_id>', methods=['DELETE'])
@token_required
@admin_required
def deactivate_configurable_list_item(current_user, item_id):
    """
    Deactivate a configurable list item (soft delete)
    
    Note: Items in use cannot be deactivated
    """
    try:
        configurable_list_service.deactivate_item(item_id, user_id=current_user.id)
        
        return jsonify({'message': 'Item deactivated successfully'}), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to deactivate item: {str(e)}'}), 500


@bp.route('/configurable-lists/<string:list_type>/reorder', methods=['POST'])
@token_required
@admin_required
def reorder_configurable_list(current_user, list_type):
    """
    Reorder items in a configurable list
    
    Request body:
    {
        "items": [
            {"id": 1, "display_order": 0},
            {"id": 2, "display_order": 1},
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        items = data.get('items', [])
        
        if not items:
            return jsonify({'error': 'No items provided'}), 400
        
        updated_count = configurable_list_service.reorder_items(
            list_type,
            items,
            user_id=current_user.id
        )
        
        return jsonify({
            'message': f'Successfully reordered {updated_count} items',
            'updated_count': updated_count
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to reorder items: {str(e)}'}), 500


# ============================================================================
# Exchange Rates Endpoints
# ============================================================================

@bp.route('/exchange-rates', methods=['GET'])
@token_required
def get_exchange_rates(current_user):
    """
    Get exchange rates with optional filters
    
    Query parameters:
    - from_currency: Filter by source currency (e.g., USD)
    - to_currency: Filter by target currency (e.g., ARS)
    - date_from: Filter from this date (YYYY-MM-DD)
    - date_to: Filter to this date (YYYY-MM-DD)
    """
    try:
        from_currency = request.args.get('from_currency')
        to_currency = request.args.get('to_currency')
        date_from = None
        date_to = None
        
        if request.args.get('date_from'):
            date_from = datetime.strptime(request.args.get('date_from'), '%Y-%m-%d').date()
        
        if request.args.get('date_to'):
            date_to = datetime.strptime(request.args.get('date_to'), '%Y-%m-%d').date()
        
        rates = exchange_rate_service.get_rates_by_currency(
            from_currency=from_currency,
            to_currency=to_currency,
            date_from=date_from,
            date_to=date_to
        )
        
        result = exchange_rate_list_schema.dump({
            'rates': rates,
            'total': len(rates)
        })
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to get exchange rates: {str(e)}'}), 500


@bp.route('/exchange-rates/latest', methods=['GET'])
@token_required
def get_latest_exchange_rates(current_user):
    """
    Get the most recent exchange rate for each currency pair
    """
    try:
        rates = exchange_rate_service.get_latest_rates()
        
        result = exchange_rate_list_schema.dump({
            'rates': rates,
            'total': len(rates)
        })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get latest rates: {str(e)}'}), 500


@bp.route('/exchange-rates/rate', methods=['GET'])
@token_required
def get_exchange_rate_for_date(current_user):
    """
    Get exchange rate for a specific currency pair and date
    
    Query parameters:
    - from_currency: Source currency (required)
    - to_currency: Target currency (required)
    - date: Date for rate (optional, defaults to today, format: YYYY-MM-DD)
    """
    try:
        from_currency = request.args.get('from_currency')
        to_currency = request.args.get('to_currency')
        
        if not from_currency or not to_currency:
            return jsonify({'error': 'from_currency and to_currency are required'}), 400
        
        target_date = None
        if request.args.get('date'):
            target_date = datetime.strptime(request.args.get('date'), '%Y-%m-%d').date()
        
        rate = exchange_rate_service.get_rate_for_date(
            from_currency,
            to_currency,
            target_date
        )
        
        if not rate:
            return jsonify({'error': 'No exchange rate found for the specified criteria'}), 404
        
        result = exchange_rate_schema.dump(rate)
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to get exchange rate: {str(e)}'}), 500


@bp.route('/exchange-rates', methods=['POST'])
@token_required
@admin_required
def create_exchange_rate(current_user):
    """
    Create a new exchange rate
    
    Required fields:
    - from_currency: Source currency code (3 letters, uppercase)
    - to_currency: Target currency code (3 letters, uppercase)
    - rate: Exchange rate (must be > 0)
    - effective_date: Date when rate becomes effective (YYYY-MM-DD)
    
    Optional fields:
    - source: Source of rate (manual, api, import) - default: manual
    """
    try:
        data = request.get_json()
        
        validated_data = exchange_rate_schema.load(data)
        
        rate = exchange_rate_service.create_rate(
            validated_data,
            user_id=current_user.id
        )
        
        result = exchange_rate_schema.dump(rate)
        
        return jsonify(result), 201
        
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'messages': e.messages}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to create exchange rate: {str(e)}'}), 500


@bp.route('/exchange-rates/<int:rate_id>', methods=['PUT'])
@token_required
@admin_required
def update_exchange_rate(current_user, rate_id):
    """
    Update an exchange rate
    
    Updatable fields:
    - rate: Exchange rate value
    - source: Source of rate
    
    Note: Currency codes and effective date cannot be changed
    """
    try:
        data = request.get_json()
        
        validated_data = exchange_rate_schema.load(data, partial=True)
        
        rate = exchange_rate_service.update_rate(
            rate_id,
            validated_data,
            user_id=current_user.id
        )
        
        result = exchange_rate_schema.dump(rate)
        
        return jsonify(result), 200
        
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'messages': e.messages}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to update exchange rate: {str(e)}'}), 500


@bp.route('/exchange-rates/<int:rate_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_exchange_rate(current_user, rate_id):
    """
    Delete an exchange rate
    """
    try:
        exchange_rate_service.delete_rate(rate_id, user_id=current_user.id)
        
        return jsonify({'message': 'Exchange rate deleted successfully'}), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to delete exchange rate: {str(e)}'}), 500
