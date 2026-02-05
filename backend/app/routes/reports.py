from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.utils.decorators import admin_required

bp = Blueprint('reports', __name__, url_prefix='/api/v1/reports')

@bp.route('/sales', methods=['GET'])
@login_required
@admin_required
def sales_report():
    return jsonify({'message': 'Endpoint en desarrollo'}), 501

@bp.route('/expenses', methods=['GET'])
@login_required
@admin_required
def expenses_report():
    return jsonify({'message': 'Endpoint en desarrollo'}), 501

@bp.route('/balance', methods=['GET'])
@login_required
@admin_required
def balance_report():
    return jsonify({'message': 'Endpoint en desarrollo'}), 501

@bp.route('/payroll', methods=['GET'])
@login_required
@admin_required
def payroll_report():
    return jsonify({'message': 'Endpoint en desarrollo'}), 501
