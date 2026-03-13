from flask import Blueprint

bp = Blueprint('suppliers', __name__, url_prefix='/api/suppliers')

@bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint for suppliers module"""
    return {'status': 'ok', 'module': 'suppliers'}, 200
