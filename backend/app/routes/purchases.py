from flask import Blueprint

bp = Blueprint('purchases', __name__, url_prefix='/api/purchases')

@bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint for purchases module"""
    return {'status': 'ok', 'module': 'purchases'}, 200
