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


@bp.route('/<int:supplier_id>/expenses', methods=['GET'])
@token_required
@admin_required
def get_supplier_expenses(current_user, supplier_id):
    Supplier.query.get_or_404(supplier_id)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')

    query = Expense.query.filter(Expense.supplier_id == supplier_id, Expense.cancelado == False)

    if fecha_desde:
        try:
            query = query.filter(Expense.fecha >= datetime.strptime(fecha_desde, '%Y-%m-%d').date())
        except ValueError:
            return jsonify({'error': 'Formato de fecha_desde inválido. Use YYYY-MM-DD'}), 400
    if fecha_hasta:
        try:
            query = query.filter(Expense.fecha <= datetime.strptime(fecha_hasta, '%Y-%m-%d').date())
        except ValueError:
            return jsonify({'error': 'Formato de fecha_hasta inválido. Use YYYY-MM-DD'}), 400

    total = query.count()
    expenses = query.order_by(Expense.fecha.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'expenses': [e.to_dict() for e in expenses.items],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': expenses.pages
    }), 200


@bp.route('/<int:supplier_id>/link-expenses', methods=['POST'])
@token_required
@admin_required
def link_expenses(current_user, supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)

    unlinked = Expense.query.filter(
        Expense.supplier_id == None,
        func.lower(Expense.proveedor) == func.lower(supplier.name)
    ).all()

    for expense in unlinked:
        expense.supplier_id = supplier_id

    db.session.commit()
    return jsonify({'linked': len(unlinked), 'supplier_id': supplier_id}), 200


@bp.route('/<int:supplier_id>/analytics', methods=['GET'])
@token_required
@admin_required
def get_supplier_analytics(current_user, supplier_id):
    from app.models.expense import ExpenseCategory
    Supplier.query.get_or_404(supplier_id)

    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')

    query = Expense.query.filter(Expense.supplier_id == supplier_id, Expense.cancelado == False)

    if fecha_desde:
        try:
            query = query.filter(Expense.fecha >= datetime.strptime(fecha_desde, '%Y-%m-%d').date())
        except ValueError:
            pass
    if fecha_hasta:
        try:
            query = query.filter(Expense.fecha <= datetime.strptime(fecha_hasta, '%Y-%m-%d').date())
        except ValueError:
            pass

    total_periodo = float(
        db.session.query(func.sum(Expense.importe))
        .filter(Expense.supplier_id == supplier_id, Expense.cancelado == False)
        .scalar() or 0
    )

    twelve_months_ago = date.today() - relativedelta(months=12)
    if db.engine.dialect.name == 'postgresql':
        month_expr = func.date_trunc('month', Expense.fecha)
    else:
        month_expr = func.strftime('%Y-%m', Expense.fecha)
    monthly_totals = db.session.query(
        month_expr.label('month'),
        func.sum(Expense.importe).label('total')
    ).filter(
        Expense.supplier_id == supplier_id,
        Expense.cancelado == False,
        Expense.fecha >= twelve_months_ago
    ).group_by(month_expr).all()

    promedio_mensual = (
        sum(float(r.total) for r in monthly_totals) / len(monthly_totals)
        if monthly_totals else 0
    )

    por_categoria = db.session.query(
        ExpenseCategory.name,
        func.sum(Expense.importe).label('total')
    ).join(Expense, Expense.category_id == ExpenseCategory.id).filter(
        Expense.supplier_id == supplier_id,
        Expense.cancelado == False
    ).group_by(ExpenseCategory.name).all()

    last_expense = db.session.query(func.max(Expense.fecha)).filter(
        Expense.supplier_id == supplier_id
    ).scalar()

    return jsonify({
        'total_periodo': total_periodo,
        'promedio_mensual': round(promedio_mensual, 2),
        'por_categoria': [{'categoria': name, 'total': float(total)} for name, total in por_categoria],
        'ultima_compra': last_expense.isoformat() if last_expense else None,
    }), 200
