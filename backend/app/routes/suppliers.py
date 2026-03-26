from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.utils.decorators import admin_required
from app.utils.jwt_utils import token_required
from app.services.supplier_service import SupplierService
from app.schemas.supplier_schema import SupplierSchema, SupplierListSchema

bp = Blueprint('suppliers', __name__, url_prefix='/api/v1/suppliers')

supplier_schema = SupplierSchema()
supplier_list_schema = SupplierListSchema()


@bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint for suppliers module"""
    return {'status': 'ok', 'module': 'suppliers'}, 200


@bp.route('', methods=['POST'])
@token_required
@admin_required
def create_supplier(current_user):
    """
    Create a new supplier
    Requires admin role
    """
    try:
        print(f"[CREATE SUPPLIER] Received data: {request.json}")
        data = supplier_schema.load(request.json)
        print(f"[CREATE SUPPLIER] Validated data: {data}")
        supplier = SupplierService.create_supplier(data, user_id=current_user.id)
        print(f"[CREATE SUPPLIER] Supplier created: {supplier.id}")
        return supplier_schema.dump(supplier), 201
    except ValidationError as e:
        print(f"[CREATE SUPPLIER] Validation error: {e.messages}")
        return {'message': 'Validation error', 'errors': e.messages}, 400
    except Exception as e:
        print(f"[CREATE SUPPLIER] Exception: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'message': str(e)}, 400


@bp.route('', methods=['GET'])
@token_required
def get_suppliers(current_user):
    """
    Get list of suppliers with optional search and filters
    Query params:
        - search: search term for name, tax_id, contact_person, email
        - status: filter by status (active, inactive, archived)
        - page: page number (default: 1)
        - per_page: items per page (default: 25)
    """
    search_term = request.args.get('search', None)
    status = request.args.get('status', None)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    
    pagination = SupplierService.search_suppliers(
        search_term=search_term,
        status=status,
        page=page,
        per_page=per_page
    )
    
    return {
        'suppliers': [supplier_schema.dump(s) for s in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages
    }, 200


@bp.route('/<int:supplier_id>', methods=['GET'])
@token_required
def get_supplier(current_user, supplier_id):
    """
    Get a single supplier by ID with statistics
    """
    try:
        supplier_data = SupplierService.get_supplier_with_stats(supplier_id)
        return supplier_data, 200
    except Exception as e:
        return {'message': str(e)}, 404


@bp.route('/<int:supplier_id>', methods=['PUT'])
@token_required
@admin_required
def update_supplier(current_user, supplier_id):
    """
    Update a supplier
    Requires: admin role
    """
    try:
        data = supplier_schema.load(request.json, partial=True)
        supplier = SupplierService.update_supplier(supplier_id, data, user_id=current_user.id)
        return supplier_schema.dump(supplier), 200
    except ValidationError as e:
        return {'message': 'Validation error', 'errors': e.messages}, 400
    except Exception as e:
        return {'message': str(e)}, 400


@bp.route('/<int:supplier_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_supplier(current_user, supplier_id):
    """
    Soft delete a supplier
    Requires: admin role
    Cannot delete if supplier has associated purchases
    """
    try:
        supplier = SupplierService.delete_supplier(supplier_id, user_id=current_user.id)
        return {'message': 'Proveedor eliminado exitosamente', 'id': supplier.id}, 200
    except Exception as e:
        return {'message': str(e)}, 400


@bp.route('/<int:supplier_id>/products', methods=['GET'])
@token_required
def get_supplier_products(current_user, supplier_id):
    """
    Get all products for a specific supplier
    Query params:
        - search: search term for name, sku
        - category: filter by category
        - status: filter by status
        - page: page number (default: 1)
        - per_page: items per page (default: 25)
    """
    from app.services.product_service import ProductService
    from app.schemas.product_schema import ProductSchema
    
    product_schema = ProductSchema()
    
    search_term = request.args.get('search', None)
    category = request.args.get('category', None)
    status = request.args.get('status', None)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    
    pagination = ProductService.search_products(
        supplier_id=supplier_id,
        search_term=search_term,
        category=category,
        status=status,
        page=page,
        per_page=per_page
    )
    
    return {
        'products': [product_schema.dump(p) for p in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages
    }, 200


@bp.route('/<int:supplier_id>/products', methods=['POST'])
@token_required
@admin_required
def create_supplier_product(current_user, supplier_id):
    """
    Create a new product for a specific supplier
    Requires admin role
    """
    from app.services.product_service import ProductService
    from app.schemas.product_schema import ProductSchema
    
    product_schema = ProductSchema()
    
    try:
        data = product_schema.load(request.json)
        # Ensure supplier_id matches the URL parameter
        data['supplier_id'] = supplier_id
        product = ProductService.create_product(data, user_id=current_user.id)
        return product_schema.dump(product), 201
    except ValidationError as e:
        return {'message': 'Validation error', 'errors': e.messages}, 400
    except Exception as e:
        return {'message': str(e)}, 400


@bp.route('/<int:supplier_id>/sales-history', methods=['GET'])
@token_required
def get_supplier_sales_history(current_user, supplier_id):
    """
    Get purchase history for a supplier with aggregations
    
    Query parameters:
    - date_from: Start date (YYYY-MM-DD)
    - date_to: End date (YYYY-MM-DD)
    - compare_period: If true, include comparison with previous period
    """
    from app.models.purchase import Purchase
    from app.models.purchase_item import PurchaseItem
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    try:
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return {'message': 'Supplier not found'}, 404
        
        # Parse date parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        compare_period = request.args.get('compare_period', 'false').lower() == 'true'
        
        if date_from:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        
        # Build query for current period
        query = Purchase.query.filter_by(
            supplier_id=supplier_id,
            is_deleted=False
        )
        
        if date_from:
            query = query.filter(Purchase.purchase_date >= date_from)
        if date_to:
            query = query.filter(Purchase.purchase_date <= date_to)
        
        purchases = query.order_by(Purchase.purchase_date.desc()).all()
        
        # Calculate aggregations
        total_amount = sum(p.total_amount for p in purchases)
        total_purchases = len(purchases)
        
        # Get item count
        item_count = db.session.query(func.count(PurchaseItem.id)).join(Purchase).filter(
            Purchase.supplier_id == supplier_id,
            Purchase.is_deleted == False
        )
        if date_from:
            item_count = item_count.filter(Purchase.purchase_date >= date_from)
        if date_to:
            item_count = item_count.filter(Purchase.purchase_date <= date_to)
        item_count = item_count.scalar()
        
        # Average per purchase
        avg_per_purchase = total_amount / total_purchases if total_purchases > 0 else 0
        
        result = {
            'supplier': {
                'id': supplier.id,
                'name': supplier.name,
                'tax_id': supplier.tax_id
            },
            'period': {
                'date_from': date_from.isoformat() if date_from else None,
                'date_to': date_to.isoformat() if date_to else None
            },
            'summary': {
                'total_amount': float(total_amount),
                'total_purchases': total_purchases,
                'total_items': item_count,
                'average_per_purchase': float(avg_per_purchase)
            },
            'purchases': [p.to_dict(include_items=True, include_supplier=False) for p in purchases]
        }
        
        # Add comparison if requested
        if compare_period and date_from and date_to:
            period_days = (date_to - date_from).days + 1
            compare_from = date_from - timedelta(days=period_days)
            compare_to = date_from - timedelta(days=1)
            
            compare_query = Purchase.query.filter_by(
                supplier_id=supplier_id,
                is_deleted=False
            ).filter(
                Purchase.purchase_date >= compare_from,
                Purchase.purchase_date <= compare_to
            )
            
            compare_purchases = compare_query.all()
            compare_total = sum(p.total_amount for p in compare_purchases)
            compare_count = len(compare_purchases)
            
            # Calculate change percentages
            amount_change = 0
            count_change = 0
            
            if compare_total > 0:
                amount_change = ((total_amount - compare_total) / compare_total) * 100
            if compare_count > 0:
                count_change = ((total_purchases - compare_count) / compare_count) * 100
            
            result['comparison'] = {
                'previous_period': {
                    'date_from': compare_from.isoformat(),
                    'date_to': compare_to.isoformat(),
                    'total_amount': float(compare_total),
                    'total_purchases': compare_count
                },
                'changes': {
                    'amount_change_percentage': round(amount_change, 2),
                    'count_change_percentage': round(count_change, 2)
                }
            }
        
        return result, 200
        
    except ValueError as e:
        return {'message': f'Invalid date format: {str(e)}'}, 400
    except Exception as e:
        return {'message': f'Error retrieving sales history: {str(e)}'}, 500


@bp.route('/<int:supplier_id>/export', methods=['GET'])
@token_required
def export_supplier_data(current_user, supplier_id):
    """
    Export supplier purchase history to CSV
    
    Query parameters:
    - date_from: Start date (YYYY-MM-DD)
    - date_to: End date (YYYY-MM-DD)
    - format: Export format (csv or pdf) - default: csv
    """
    from app.models.purchase import Purchase
    from datetime import datetime
    import csv
    from io import StringIO
    from flask import make_response
    
    try:
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return {'message': 'Supplier not found'}, 404
        
        # Parse parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        export_format = request.args.get('format', 'csv')
        
        if date_from:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        
        # Build query
        query = Purchase.query.filter_by(
            supplier_id=supplier_id,
            is_deleted=False
        )
        
        if date_from:
            query = query.filter(Purchase.purchase_date >= date_from)
        if date_to:
            query = query.filter(Purchase.purchase_date <= date_to)
        
        purchases = query.order_by(Purchase.purchase_date.desc()).all()
        
        if export_format == 'csv':
            # Create CSV
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Fecha',
                'Número de Factura',
                'CAE',
                'Moneda',
                'Tipo de Cambio',
                'Total',
                'Estado de Pago',
                'Items',
                'Notas'
            ])
            
            # Write data
            for purchase in purchases:
                writer.writerow([
                    purchase.purchase_date.strftime('%Y-%m-%d'),
                    purchase.invoice_number or '',
                    purchase.cae_number or '',
                    purchase.currency,
                    purchase.exchange_rate or '',
                    float(purchase.total_amount),
                    purchase.payment_status,
                    purchase.items.count(),
                    purchase.notes or ''
                ])
            
            # Create response
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=supplier_{supplier_id}_purchases.csv'
            
            return response
        else:
            return {'message': 'Only CSV format is currently supported'}, 400
        
    except ValueError as e:
        return {'message': f'Invalid date format: {str(e)}'}, 400
    except Exception as e:
        return {'message': f'Error exporting data: {str(e)}'}, 500
