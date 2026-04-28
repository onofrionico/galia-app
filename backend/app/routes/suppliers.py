from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.supplier import Supplier
from app.models.expense import Expense
from app.utils.jwt_utils import token_required
from app.utils.decorators import admin_required
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
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

    month_start = date.today().replace(day=1)
    monthly_sums = db.session.query(
        Expense.supplier_id,
        func.sum(Expense.importe).label('total')
    ).filter(
        Expense.supplier_id.isnot(None),
        Expense.cancelado == False,
        Expense.fecha >= month_start
    ).group_by(Expense.supplier_id).all()
    monthly_map = {row.supplier_id: float(row.total) for row in monthly_sums}

    last_dates = db.session.query(
        Expense.supplier_id,
        func.max(Expense.fecha).label('last_date')
    ).filter(Expense.supplier_id.isnot(None)).group_by(Expense.supplier_id).all()
    last_date_map = {row.supplier_id: row.last_date for row in last_dates}

    result = []
    for s in suppliers:
        d = s.to_dict()
        d['total_mes_actual'] = monthly_map.get(s.id, 0.0)
        last = last_date_map.get(s.id)
        d['ultima_compra'] = last.isoformat() if last else None
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
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Ya existe un proveedor con ese CUIT'}), 409
    return jsonify(supplier.to_dict()), 201


@bp.route('/<int:supplier_id>', methods=['GET'])
@token_required
@admin_required
def get_supplier(current_user, supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    d = supplier.to_dict()
    month_start = date.today().replace(day=1)
    d['total_mes_actual'] = float(
        db.session.query(func.sum(Expense.importe)).filter(
            Expense.supplier_id == supplier_id,
            Expense.cancelado == False,
            Expense.fecha >= month_start
        ).scalar() or 0
    )
    last = db.session.query(func.max(Expense.fecha)).filter(
        Expense.supplier_id == supplier_id
    ).scalar()
    d['ultima_compra'] = last.isoformat() if last else None
    return jsonify(d), 200


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
            val = data[field]
            setattr(supplier, field, val.strip() if val else None)
    if 'is_active' in data:
        supplier.is_active = bool(data['is_active'])

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Ya existe un proveedor con ese CUIT'}), 409
    return jsonify(supplier.to_dict()), 200


@bp.route('/<int:supplier_id>', methods=['DELETE'])
@token_required
@admin_required
def deactivate_supplier(current_user, supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    supplier.is_active = False
    db.session.commit()
    return jsonify({'message': 'Proveedor desactivado correctamente'}), 200
