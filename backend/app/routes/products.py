from flask import Blueprint

bp = Blueprint('products', __name__, url_prefix='/api/products')

@bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint for products module"""
    return {'status': 'ok', 'module': 'products'}, 200
