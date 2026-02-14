from flask import Blueprint, jsonify

csv_import_bp = Blueprint('csv_import', __name__, url_prefix='/api/csv-import')

@csv_import_bp.route('/status', methods=['GET'])
def status():
    """Check CSV import module status"""
    return jsonify({'status': 'available', 'message': 'CSV import module ready'}), 200
