from flask import Blueprint

bp = Blueprint('dashboards', __name__, url_prefix='/api/dashboards')

@bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint for dashboards module"""
    return {'status': 'ok', 'module': 'dashboards'}, 200
