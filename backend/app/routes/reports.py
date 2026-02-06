from flask import Blueprint, request, jsonify
from app.utils.decorators import admin_required
from app.utils.jwt_utils import token_required

bp = Blueprint('reports', __name__, url_prefix='/api/v1/reports')

@bp.route('/sales', methods=['GET'])
@token_required
@admin_required
def sales_report(current_user):
    return jsonify({'message': 'Endpoint en desarrollo'}), 501

@bp.route('/expenses', methods=['GET'])
@token_required
@admin_required
def expenses_report(current_user):
    return jsonify({'message': 'Endpoint en desarrollo'}), 501

@bp.route('/balance', methods=['GET'])
@token_required
@admin_required
def balance_report(current_user):
    return jsonify({'message': 'Endpoint en desarrollo'}), 501

@bp.route('/payroll', methods=['GET'])
@token_required
@admin_required
def payroll_report(current_user):
    return jsonify({'message': 'Endpoint en desarrollo'}), 501
