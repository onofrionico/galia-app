from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.sale import Sale

bp = Blueprint('sales', __name__, url_prefix='/api/v1/sales')

@bp.route('', methods=['GET'])
@login_required
def get_sales():
    sales = Sale.query.order_by(Sale.created_at.desc()).limit(100).all()
    return jsonify([sale.to_dict() for sale in sales]), 200

@bp.route('', methods=['POST'])
@login_required
def create_sale():
    data = request.get_json()
    
    return jsonify({'message': 'Endpoint en desarrollo'}), 501

@bp.route('/<int:sale_id>', methods=['GET'])
@login_required
def get_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return jsonify(sale.to_dict(include_items=True)), 200
