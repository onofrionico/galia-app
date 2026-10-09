from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.supply import Supply, SupplyPrice
from app.utils.jwt_utils import token_required
from app.utils.decorators import module_required, authenticated_only
from datetime import date
from decimal import Decimal
from app.utils.validation import clean_str, json_object, parse_decimal

MAX_STOCK = Decimal('10000000')   # Numeric(10, 3)
MAX_PRICE = Decimal('100000000')  # Numeric(10, 2)

bp = Blueprint('supplies', __name__, url_prefix='/api/v1/supplies')


def _bad_body():
    return jsonify({'error': 'El cuerpo de la petición debe ser un objeto JSON'}), 400


@bp.route('', methods=['GET'])
@token_required
@authenticated_only
def list_supplies(current_user):
    """Get all supplies with optional filtering"""
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = max(1, min(request.args.get('per_page', 50, type=int), 200))

    query = Supply.query
    if not include_inactive:
        query = query.filter(Supply.is_active == True)
    if search:
        query = query.filter(Supply.name.ilike(f'%{search}%'))

    paginated = query.order_by(Supply.name).paginate(page=page, per_page=per_page, error_out=False)
    supplies = [s.to_dict() for s in paginated.items]

    for s in supplies:
        prices = SupplyPrice.query.filter_by(supply_id=s['id']).order_by(SupplyPrice.recorded_at.desc()).limit(3).all()
        s['recent_prices'] = [p.to_dict() for p in prices]

    return jsonify({
        'supplies': supplies,
        'total': paginated.total,
        'page': page,
        'per_page': per_page,
        'pages': paginated.pages
    }), 200


@bp.route('', methods=['POST'])
@token_required
@module_required('Stock')
def create_supply(current_user):
    """Create a new supply"""
    data = json_object()
    if data is None:
        return _bad_body()

    try:
        name = clean_str(data.get('name'), 200)
        unit = clean_str(data.get('unit'), 50)
        if not name:
            return jsonify({'error': 'El nombre del insumo es requerido'}), 400
        if not unit:
            return jsonify({'error': 'La unidad es requerida'}), 400
        stock = parse_decimal(data.get('stock_quantity', 0), 'stock_quantity', maximum=MAX_STOCK)
        min_stock = parse_decimal(data.get('min_stock', 0), 'min_stock', maximum=MAX_STOCK)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    existing = Supply.query.filter_by(name=name).first()
    if existing:
        return jsonify({'error': 'Ya existe un insumo con este nombre'}), 409

    supply = Supply(name=name, unit=unit, stock_quantity=stock, min_stock=min_stock)

    db.session.add(supply)
    db.session.commit()
    return jsonify(supply.to_dict()), 201


@bp.route('/<int:supply_id>', methods=['GET'])
@token_required
@authenticated_only
def get_supply(current_user, supply_id):
    """Get supply details with price history"""
    supply = Supply.query.get_or_404(supply_id)
    data = supply.to_dict()

    prices = SupplyPrice.query.filter_by(supply_id=supply_id).order_by(SupplyPrice.recorded_at.desc()).all()
    data['prices'] = [p.to_dict() for p in prices]

    return jsonify(data), 200


@bp.route('/<int:supply_id>', methods=['PUT'])
@token_required
@module_required('Stock')
def update_supply(current_user, supply_id):
    """Update supply"""
    supply = Supply.query.get_or_404(supply_id)
    data = json_object()
    if data is None:
        return _bad_body()

    try:
        updates = {}
        if 'name' in data:
            name = clean_str(data['name'], 200)
            if not name:
                return jsonify({'error': 'El nombre no puede estar vacío'}), 400
            if Supply.query.filter(Supply.id != supply_id, Supply.name == name).first():
                return jsonify({'error': 'Ya existe un insumo con este nombre'}), 409
            updates['name'] = name
        if 'unit' in data:
            unit = clean_str(data['unit'], 50)
            if not unit:
                return jsonify({'error': 'La unidad no puede estar vacía'}), 400
            updates['unit'] = unit
        if 'stock_quantity' in data:
            updates['stock_quantity'] = parse_decimal(data['stock_quantity'], 'stock_quantity', maximum=MAX_STOCK)
        if 'min_stock' in data:
            updates['min_stock'] = parse_decimal(data['min_stock'], 'min_stock', maximum=MAX_STOCK)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    for field, value in updates.items():
        setattr(supply, field, value)
    if 'is_active' in data:
        supply.is_active = bool(data['is_active'])

    db.session.commit()
    return jsonify(supply.to_dict()), 200


@bp.route('/<int:supply_id>', methods=['DELETE'])
@token_required
@module_required('Stock')
def delete_supply(current_user, supply_id):
    """Soft delete supply (mark as inactive)"""
    supply = Supply.query.get_or_404(supply_id)
    supply.is_active = False
    db.session.commit()
    return jsonify(supply.to_dict()), 200


@bp.route('/<int:supply_id>/prices', methods=['POST'])
@token_required
@module_required('Stock')
def add_supply_price(current_user, supply_id):
    """Record a price for a supply from a supplier"""
    supply = Supply.query.get_or_404(supply_id)
    data = json_object()
    if data is None:
        return _bad_body()

    if 'price' not in data:
        return jsonify({'error': 'El precio es requerido'}), 400
    try:
        price = parse_decimal(data['price'], 'El precio', maximum=MAX_PRICE)
        recorded_at = date.today()
        if data.get('recorded_at'):
            try:
                recorded_at = date.fromisoformat(data['recorded_at'])
            except (TypeError, ValueError):
                raise ValueError('recorded_at debe tener formato YYYY-MM-DD')
        supplier = clean_str(data.get('supplier'), 200)
        notes = clean_str(data.get('notes'))
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    price_record = SupplyPrice(
        supply_id=supply_id,
        price=price,
        recorded_at=recorded_at,
        supplier=supplier,
        notes=notes,
        created_by=current_user.id
    )

    db.session.add(price_record)
    db.session.commit()

    return jsonify(price_record.to_dict()), 201
