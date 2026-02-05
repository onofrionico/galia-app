from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.expense import Expense, ExpenseCategory
from app.utils.decorators import admin_required

bp = Blueprint('expenses', __name__, url_prefix='/api/v1/expenses')

@bp.route('', methods=['GET'])
@login_required
@admin_required
def get_expenses():
    expenses = Expense.query.order_by(Expense.expense_date.desc()).limit(100).all()
    return jsonify([expense.to_dict() for expense in expenses]), 200

@bp.route('', methods=['POST'])
@login_required
@admin_required
def create_expense():
    data = request.get_json()
    
    return jsonify({'message': 'Endpoint en desarrollo'}), 501

@bp.route('/categories', methods=['GET'])
@login_required
def get_categories():
    categories = ExpenseCategory.query.filter_by(is_active=True).all()
    return jsonify([category.to_dict() for category in categories]), 200
