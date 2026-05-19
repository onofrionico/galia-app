from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.supply import Supply, SupplyPrice
from app.utils.jwt_utils import token_required
from app.utils.decorators import admin_required
from datetime import date
from decimal import Decimal

bp = Blueprint('supplies', __name__, url_prefix='/api/v1/supplies')


@bp.route('', methods=['GET'])
@token_required
def list_supplies(current_user):
    """Get all supplies with optional filtering"""
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

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
@admin_required
def create_supply(current_user):
    """Create a new supply"""
    data = request.get_json() or {}

    if not data.get('name', '').strip():
        return jsonify({'error': 'El nombre del insumo es requerido'}), 400
    if not data.get('unit', '').strip():
        return jsonify({'error': 'La unidad es requerida'}), 400

    existing = Supply.query.filter_by(name=data['name'].strip()).first()
    if existing:
        return jsonify({'error': 'Ya existe un insumo con este nombre'}), 409

    supply = Supply(
        name=data['name'].strip(),
        unit=data['unit'].strip(),
        stock_quantity=Decimal(str(data.get('stock_quantity', 0))),
        min_stock=Decimal(str(data.get('min_stock', 0))),
    )

    db.session.add(supply)
    db.session.commit()
    return jsonify(supply.to_dict()), 201


@bp.route('/<int:supply_id>', methods=['GET'])
@token_required
def get_supply(current_user, supply_id):
    """Get supply details with price history"""
    supply = Supply.query.get_or_404(supply_id)
    data = supply.to_dict()

    prices = SupplyPrice.query.filter_by(supply_id=supply_id).order_by(SupplyPrice.recorded_at.desc()).all()
    data['prices'] = [p.to_dict() for p in prices]

    return jsonify(data), 200


@bp.route('/<int:supply_id>', methods=['PUT'])
@token_required
@admin_required
def update_supply(current_user, supply_id):
    """Update supply"""
    supply = Supply.query.get_or_404(supply_id)
    data = request.get_json() or {}

    if 'name' in data and data['name'].strip():
        existing = Supply.query.filter(Supply.id != supply_id, Supply.name == data['name'].strip()).first()
        if existing:
            return jsonify({'error': 'Ya existe un insumo con este nombre'}), 409
        supply.name = data['name'].strip()

    if 'unit' in data:
        supply.unit = data['unit'].strip()
    if 'stock_quantity' in data:
        supply.stock_quantity = Decimal(str(data['stock_quantity']))
    if 'min_stock' in data:
        supply.min_stock = Decimal(str(data['min_stock']))
    if 'is_active' in data:
        supply.is_active = bool(data['is_active'])

    db.session.commit()
    return jsonify(supply.to_dict()), 200


@bp.route('/<int:supply_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_supply(current_user, supply_id):
    """Soft delete supply (mark as inactive)"""
    supply = Supply.query.get_or_404(supply_id)
    supply.is_active = False
    db.session.commit()
    return jsonify(supply.to_dict()), 200


@bp.route('/<int:supply_id>/prices', methods=['POST'])
@token_required
@admin_required
def add_supply_price(current_user, supply_id):
    """Record a price for a supply from a supplier"""
    supply = Supply.query.get_or_404(supply_id)
    data = request.get_json() or {}

    if not data.get('price'):
        return jsonify({'error': 'El precio es requerido'}), 400

    price_record = SupplyPrice(
        supply_id=supply_id,
        price=Decimal(str(data['price'])),
        recorded_at=date.fromisoformat(data['recorded_at']) if data.get('recorded_at') else date.today(),
        supplier=data.get('supplier', '').strip() or None,
        notes=data.get('notes', '').strip() or None,
        created_by=current_user.id
    )

    db.session.add(price_record)
    db.session.commit()

    return jsonify(price_record.to_dict()), 201
