from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.supplier import Supplier
from app.models.expense import Expense
from app.utils.jwt_utils import token_required
from app.utils.decorators import admin_required
from sqlalchemy import func
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

bp = Blueprint('suppliers', __name__, url_prefix='/api/v1/suppliers')


@bp.route('', methods=['GET'])
@token_required
@admin_required
def list_suppliers(current_user):
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    search = request.args.get('search', '').strip()

    query = Supplier.query
    if not include_inactive:
        query = query.filter(Supplier.is_active == True)
    if search:
        query = query.filter(Supplier.name.ilike(f'%{search}%'))

    suppliers = query.order_by(Supplier.name).all()

    result = []
    for s in suppliers:
        d = s.to_dict()
        total_mes = db.session.query(func.sum(Expense.importe)).filter(
            Expense.supplier_id == s.id,
            Expense.cancelado == False,
            Expense.fecha >= date.today().replace(day=1)
        ).scalar() or 0
        last_expense = db.session.query(func.max(Expense.fecha)).filter(
            Expense.supplier_id == s.id
        ).scalar()
        d['total_mes_actual'] = float(total_mes)
        d['ultima_compra'] = last_expense.isoformat() if last_expense else None
        result.append(d)

    return jsonify({'suppliers': result, 'total': len(result)}), 200


@bp.route('', methods=['POST'])
@token_required
@admin_required
def create_supplier(current_user):
    data = request.get_json() or {}
    if not data.get('name', '').strip():
        return jsonify({'error': 'El nombre del proveedor es requerido'}), 400

    supplier = Supplier(
        name=data['name'].strip(),
        cuit=data.get('cuit', '').strip() or None,
        email=data.get('email', '').strip() or None,
        phone=data.get('phone', '').strip() or None,
        address=data.get('address', '').strip() or None,
        notes=data.get('notes', '').strip() or None,
    )
    db.session.add(supplier)
    db.session.commit()
    return jsonify(supplier.to_dict()), 201


@bp.route('/<int:supplier_id>', methods=['GET'])
@token_required
@admin_required
def get_supplier(current_user, supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    return jsonify(supplier.to_dict()), 200


@bp.route('/<int:supplier_id>', methods=['PUT'])
@token_required
@admin_required
def update_supplier(current_user, supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    data = request.get_json() or {}

    if 'name' in data:
        if not data['name'].strip():
            return jsonify({'error': 'El nombre no puede estar vacío'}), 400
        supplier.name = data['name'].strip()
    for field in ('cuit', 'email', 'phone', 'address', 'notes'):
        if field in data:
            setattr(supplier, field, data[field].strip() or None)
    if 'is_active' in data:
        supplier.is_active = bool(data['is_active'])

    supplier.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(supplier.to_dict()), 200


@bp.route('/<int:supplier_id>', methods=['DELETE'])
@token_required
@admin_required
def deactivate_supplier(current_user, supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    supplier.is_active = False
    supplier.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'Proveedor desactivado correctamente'}), 200
