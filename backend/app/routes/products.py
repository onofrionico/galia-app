from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.utils.decorators import admin_required
from app.utils.jwt_utils import token_required
from app.services.product_service import ProductService, ProductMasterService
from app.schemas.product_schema import ProductSchema, ProductMasterSchema

bp = Blueprint('products', __name__, url_prefix='/api/v1/products')

product_schema = ProductSchema()
product_master_schema = ProductMasterSchema()


@bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint for products module"""
    return {'status': 'ok', 'module': 'products'}, 200


@bp.route('', methods=['POST'])
@token_required
@admin_required
def create_product(current_user):
    """
    Create a new product in a supplier's catalog
    Requires admin role
    """
    try:
        data = product_schema.load(request.json)
        product = ProductService.create_product(data, user_id=current_user.id)
        return product_schema.dump(product), 201
    except ValidationError as e:
        return {'message': 'Validation error', 'errors': e.messages}, 400
    except Exception as e:
        return {'message': str(e)}, 400


@bp.route('', methods=['GET'])
@token_required
def get_products(current_user):
    """
    Get list of products with optional filters
    Query params:
        - supplier_id: filter by supplier
        - search: search term for name, sku
        - category: filter by category
        - status: filter by status
        - page: page number (default: 1)
        - per_page: items per page (default: 25)
    """
    supplier_id = request.args.get('supplier_id', None, type=int)
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


@bp.route('/<int:product_id>', methods=['GET'])
@token_required
def get_product(current_user, product_id):
    """
    Get a single product by ID with price history and statistics
    """
    try:
        product_data = ProductService.get_product_with_statistics(product_id)
        return product_data, 200
    except Exception as e:
        return {'message': str(e)}, 404


@bp.route('/<int:product_id>', methods=['PUT'])
@token_required
@admin_required
def update_product(current_user, product_id):
    """
    Update a product
    Requires admin role
    Automatically tracks price changes in price history
    """
    try:
        data = product_schema.load(request.json, partial=True)
        product = ProductService.update_product(product_id, data, user_id=current_user.id)
        return product_schema.dump(product), 200
    except ValidationError as e:
        return {'message': 'Validation error', 'errors': e.messages}, 400
    except Exception as e:
        return {'message': str(e)}, 400


@bp.route('/<int:product_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_product(current_user, product_id):
    """
    Soft delete a product
    Requires admin role
    Cannot delete if product has purchase history
    """
    try:
        product = ProductService.delete_product(product_id, user_id=current_user.id)
        return {'message': 'Producto eliminado exitosamente', 'id': product.id}, 200
    except Exception as e:
        return {'message': str(e)}, 400


@bp.route('/search', methods=['GET'])
@token_required
def search_across_suppliers(current_user):
    """
    Search products across all suppliers for price comparison
    Query params:
        - search: search term (required)
        - category: filter by category
        - page: page number (default: 1)
        - per_page: items per page (default: 25)
    """
    search_term = request.args.get('search', None)
    category = request.args.get('category', None)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    
    if not search_term:
        return {'message': 'Search term is required'}, 400
    
    pagination = ProductService.search_across_suppliers(
        search_term=search_term,
        category=category,
        page=page,
        per_page=per_page
    )
    
    products_with_supplier = []
    for product in pagination.items:
        product_dict = product.to_dict(include_supplier=True)
        products_with_supplier.append(product_dict)
    
    return {
        'products': products_with_supplier,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages
    }, 200


@bp.route('/<int:product_id>/link', methods=['POST'])
@token_required
@admin_required
def link_to_product_master(current_user, product_id):
    """
    Link a product to a ProductMaster for cross-supplier comparison
    Requires admin role
    Body: { "product_master_id": int }
    """
    try:
        product_master_id = request.json.get('product_master_id')
        if not product_master_id:
            return {'message': 'product_master_id is required'}, 400
        
        product = ProductService.link_to_product_master(
            product_id, 
            product_master_id, 
            user_id=current_user.id
        )
        return product_schema.dump(product), 200
    except Exception as e:
        return {'message': str(e)}, 400


@bp.route('/<int:product_id>/unlink', methods=['POST'])
@token_required
@admin_required
def unlink_from_product_master(current_user, product_id):
    """
    Unlink a product from its ProductMaster
    Requires admin role
    """
    try:
        product = ProductService.unlink_from_product_master(product_id, user_id=current_user.id)
        return product_schema.dump(product), 200
    except Exception as e:
        return {'message': str(e)}, 400


@bp.route('/masters', methods=['POST'])
@token_required
@admin_required
def create_product_master(current_user):
    """
    Create a new ProductMaster for linking products across suppliers
    Requires admin role
    """
    try:
        data = product_master_schema.load(request.json)
        product_master = ProductMasterService.create_product_master(data, user_id=current_user.id)
        return product_master_schema.dump(product_master), 201
    except ValidationError as e:
        return {'message': 'Validation error', 'errors': e.messages}, 400
    except Exception as e:
        return {'message': str(e)}, 400


@bp.route('/masters', methods=['GET'])
@token_required
def get_product_masters(current_user):
    """
    Get list of ProductMasters with optional filters
    Query params:
        - search: search term for name
        - category: filter by category
        - page: page number (default: 1)
        - per_page: items per page (default: 25)
    """
    search_term = request.args.get('search', None)
    category = request.args.get('category', None)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    
    pagination = ProductMasterService.search_product_masters(
        search_term=search_term,
        category=category,
        page=page,
        per_page=per_page
    )
    
    return {
        'product_masters': [product_master_schema.dump(pm) for pm in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages
    }, 200


@bp.route('/masters/<int:product_master_id>', methods=['GET'])
@token_required
def get_product_master(current_user, product_master_id):
    """
    Get a ProductMaster with all linked products for price comparison
    """
    try:
        pm_data = ProductMasterService.get_product_master_with_products(product_master_id)
        return pm_data, 200
    except Exception as e:
        return {'message': str(e)}, 404


@bp.route('/bulk-update', methods=['POST'])
@token_required
@admin_required
def bulk_update_products(current_user):
    """
    Perform bulk operations on multiple products
    Requires admin role
    
    Body: {
        "product_ids": [1, 2, 3],
        "operation": "update_category" | "update_status" | "link_master",
        "data": { "category": "...", "status": "...", "product_master_id": ... }
    }
    """
    try:
        product_ids = request.json.get('product_ids', [])
        operation = request.json.get('operation')
        data = request.json.get('data', {})
        
        if not product_ids:
            return {'message': 'product_ids is required'}, 400
        
        if not operation:
            return {'message': 'operation is required'}, 400
        
        result = ProductService.bulk_update(
            product_ids=product_ids,
            operation=operation,
            data=data,
            user_id=current_user.id
        )
        
        return {
            'message': f'{result["updated"]} productos actualizados exitosamente',
            'updated': result['updated'],
            'failed': result['failed'],
            'errors': result['errors']
        }, 200
    except Exception as e:
        return {'message': str(e)}, 400


@bp.route('/export', methods=['GET'])
@token_required
def export_products(current_user):
    """
    Export products to CSV
    Query params: same as GET /products for filtering
    """
    try:
        supplier_id = request.args.get('supplier_id', None, type=int)
        search_term = request.args.get('search', None)
        category = request.args.get('category', None)
        status = request.args.get('status', None)
        
        csv_data = ProductService.export_to_csv(
            supplier_id=supplier_id,
            search_term=search_term,
            category=category,
            status=status
        )
        
        from flask import Response
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=productos.csv'}
        )
    except Exception as e:
        return {'message': str(e)}, 500


@bp.route('/import', methods=['POST'])
@token_required
@admin_required
def import_products(current_user):
    """
    Import products from Excel file
    Requires admin role
    
    Expected Excel columns:
    - Proveedor (nombre o ID)
    - Nombre
    - SKU
    - Categoría
    - Unidad de Medida
    - Precio
    - Estado (opcional, default: active)
    """
    try:
        if 'file' not in request.files:
            return {'message': 'No se proporcionó archivo'}, 400
        
        file = request.files['file']
        if file.filename == '':
            return {'message': 'No se seleccionó archivo'}, 400
        
        if not file.filename.endswith(('.xls', '.xlsx')):
            return {'message': 'El archivo debe ser Excel (.xls o .xlsx)'}, 400
        
        result = ProductService.import_from_excel(file, user_id=current_user.id)
        
        return {
            'message': f'Importación completada: {result["created"]} creados, {result["updated"]} actualizados, {result["failed"]} fallidos',
            'created': result['created'],
            'updated': result['updated'],
            'failed': result['failed'],
            'errors': result['errors']
        }, 200
    except Exception as e:
        return {'message': f'Error al importar: {str(e)}'}, 500


@bp.route('/<int:product_id>/price-history', methods=['GET'])
@token_required
def get_price_history(current_user, product_id):
    """
    Get price history for a specific product with trend analysis
    Query params:
        - start_date: filter from date (YYYY-MM-DD)
        - end_date: filter to date (YYYY-MM-DD)
        - limit: max number of records (default: 100)
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 100, type=int)
        
        result = ProductService.get_price_history_with_analysis(
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        if not result:
            return {'message': 'Producto no encontrado'}, 404
        
        return jsonify(result), 200
    except Exception as e:
        return {'message': str(e)}, 500


@bp.route('/volatile', methods=['GET'])
@token_required
def get_volatile_products(current_user):
    """
    Get products ranked by price volatility
    Query params:
        - days: number of days to analyze (default: 30)
        - limit: max number of products (default: 20)
        - min_changes: minimum price changes required (default: 2)
    """
    try:
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 20, type=int)
        min_changes = request.args.get('min_changes', 2, type=int)
        
        result = ProductService.get_volatile_products(
            days=days,
            limit=limit,
            min_changes=min_changes
        )
        
        return jsonify(result), 200
    except Exception as e:
        return {'message': str(e)}, 500
