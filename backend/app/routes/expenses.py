from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.expense import Expense, ExpenseCategory
from app.utils.decorators import admin_required
from app.utils.jwt_utils import token_required

bp = Blueprint('expenses', __name__, url_prefix='/api/v1/expenses')

@bp.route('', methods=['GET'])
@token_required
@admin_required
def get_expenses(current_user):
    expenses = Expense.query.order_by(Expense.expense_date.desc()).limit(100).all()
    return jsonify([expense.to_dict() for expense in expenses]), 200

@bp.route('', methods=['POST'])
@token_required
@admin_required
def create_expense(current_user):
    data = request.get_json()
    
    return jsonify({'message': 'Endpoint en desarrollo'}), 501

@bp.route('/categories', methods=['GET'])
@token_required
def get_categories(current_user):
    categories = ExpenseCategory.query.filter_by(is_active=True).all()
    return jsonify([category.to_dict() for category in categories]), 200
