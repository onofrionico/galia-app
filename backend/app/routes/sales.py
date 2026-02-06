from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.sale import Sale
from app.utils.jwt_utils import token_required

bp = Blueprint('sales', __name__, url_prefix='/api/v1/sales')

@bp.route('', methods=['GET'])
@token_required
def get_sales(current_user):
    sales = Sale.query.order_by(Sale.created_at.desc()).limit(100).all()
    return jsonify([sale.to_dict() for sale in sales]), 200

@bp.route('', methods=['POST'])
@token_required
def create_sale(current_user):
    data = request.get_json()
    
    return jsonify({'message': 'Endpoint en desarrollo'}), 501

@bp.route('/<int:sale_id>', methods=['GET'])
@token_required
def get_sale(current_user, sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return jsonify(sale.to_dict(include_items=True)), 200
