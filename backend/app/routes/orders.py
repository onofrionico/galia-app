from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.order import Order, OrderItem
from app.models.product_variant import ProductVariant
from app.models.mesa import Mesa
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.services.stock_service import deduct_stock_for_sale
from app.utils.jwt_utils import token_required
from app.utils.decorators import admin_required
from datetime import datetime
from decimal import Decimal

bp = Blueprint('orders', __name__, url_prefix='/api/v1/orders')


@bp.route('', methods=['POST'])
@token_required
def create_order(current_user):
    """
    Create a new order with status='abierta'
    Body: { "mesa_id": int (optional), "salon_id": int (optional) }
    """
    data = request.get_json() or {}
    mesa_id = data.get('mesa_id')
    salon_id = data.get('salon_id')

    # Check if mesa already has an open order
    if mesa_id:
        existing_order = Order.query.filter_by(
            mesa_id=mesa_id,
            status='abierta'
        ).first()
        if existing_order:
            return jsonify({'error': 'La mesa ya tiene una orden abierta'}), 409

    # Create the order
    order = Order(
        mesa_id=mesa_id,
        salon_id=salon_id,
        status='abierta'
    )

    db.session.add(order)

    # Update mesa status if mesa_id provided
    if mesa_id:
        mesa = Mesa.query.get(mesa_id)
        if mesa:
            mesa.status = 'ocupada'

    db.session.commit()
    return jsonify(order.to_dict(include_items=True)), 201


@bp.route('', methods=['GET'])
@token_required
def get_orders(current_user):
    """
    Get orders with optional filtering
    Query params: mesa_id (int, optional), salon_id (int, optional), status (str, default='abierta')
    """
    mesa_id = request.args.get('mesa_id', type=int)
    salon_id = request.args.get('salon_id', type=int)
    status = request.args.get('status', 'abierta')

    query = Order.query

    if mesa_id:
        query = query.filter(Order.mesa_id == mesa_id)
    if salon_id:
        query = query.filter(Order.salon_id == salon_id)
    if status:
        query = query.filter(Order.status == status)

    orders = query.order_by(Order.created_at.desc()).all()

    return jsonify({
        'orders': [order.to_dict(include_items=True) for order in orders],
        'total': len(orders)
    }), 200


@bp.route('/<int:order_id>', methods=['GET'])
@token_required
def get_order(current_user, order_id):
    """Get a specific order with all its items"""
    order = Order.query.get_or_404(order_id)
    return jsonify(order.to_dict(include_items=True)), 200


@bp.route('/<int:order_id>/items', methods=['POST'])
@token_required
def add_order_item(current_user, order_id):
    """
    Add or update an item in an order
    Body: { "product_variant_id": int, "quantity": int, "notes": str (optional) }
    """
    order = Order.query.get_or_404(order_id)
    data = request.get_json() or {}

    product_variant_id = data.get('product_variant_id')
    quantity = data.get('quantity')
    notes = data.get('notes')

    if not product_variant_id or not quantity:
        return jsonify({'error': 'product_variant_id y quantity son requeridos'}), 400

    # Fetch ProductVariant
    variant = ProductVariant.query.get(product_variant_id)
    if not variant:
        return jsonify({'error': f'ProductVariant {product_variant_id} no encontrado'}), 404

    # Check if OrderItem with same product_variant_id already exists
    existing_item = OrderItem.query.filter_by(
        order_id=order_id,
        product_variant_id=product_variant_id
    ).first()

    if existing_item:
        # Increment quantity
        existing_item.quantity += int(quantity)
    else:
        # Create new OrderItem
        new_item = OrderItem(
            order_id=order_id,
            product_variant_id=product_variant_id,
            quantity=int(quantity),
            unit_price=variant.price,
            notes=notes
        )
        db.session.add(new_item)

    db.session.commit()
    return jsonify(order.to_dict(include_items=True)), 201


@bp.route('/<int:order_id>/items/<int:item_id>', methods=['PUT'])
@token_required
def update_order_item(current_user, order_id, item_id):
    """
    Update an order item
    Body: { "quantity": int (optional), "notes": str (optional) }
    """
    order = Order.query.get_or_404(order_id)
    item = OrderItem.query.get_or_404(item_id)

    # Verify item belongs to this order
    if item.order_id != order_id:
        return jsonify({'error': 'Item no pertenece a esta orden'}), 404

    data = request.get_json() or {}

    if 'quantity' in data:
        quantity = int(data['quantity'])
        if quantity <= 0:
            # Delete the item if quantity is 0 or negative
            db.session.delete(item)
        else:
            item.quantity = quantity

    if 'notes' in data:
        item.notes = data['notes']

    db.session.commit()
    return jsonify(order.to_dict(include_items=True)), 200


@bp.route('/<int:order_id>/items/<int:item_id>', methods=['DELETE'])
@token_required
def delete_order_item(current_user, order_id, item_id):
    """Delete an item from an order"""
    order = Order.query.get_or_404(order_id)
    item = OrderItem.query.get_or_404(item_id)

    # Verify item belongs to this order
    if item.order_id != order_id:
        return jsonify({'error': 'Item no pertenece a esta orden'}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify(order.to_dict(include_items=True)), 200


@bp.route('/<int:order_id>/cobrar', methods=['POST'])
@token_required
def cobrar_order(current_user, order_id):
    """
    Close and finalize an order, converting it to a Sale
    Body: { "medio_pago": str (optional, default="Efectivo") }
    """
    order = Order.query.get_or_404(order_id)
    data = request.get_json() or {}
    medio_pago = data.get('medio_pago', 'Efectivo')

    # Validate order exists and status == 'abierta'
    if order.status != 'abierta':
        return jsonify({'error': 'La orden no está abierta'}), 409

    # Validate order has at least 1 item
    items_list = order.items.all()
    if not items_list:
        return jsonify({'error': 'La orden no tiene items'}), 400

    try:
        # Prepare items list for stock deduction
        stock_items = [
            {
                'product_variant_id': oi.product_variant_id,
                'quantity': oi.quantity
            }
            for oi in items_list
        ]

        # Call stock_service to reduce inventory
        deduct_stock_for_sale(stock_items)

        # Create Sale
        sale = Sale(
            mesa_id=order.mesa_id,
            source='galia',
            medio_pago=medio_pago,
            fecha=datetime.utcnow().date(),
            creacion=datetime.utcnow(),
            cerrada=datetime.utcnow(),
            estado='Cerrada',
            tipo_venta='Local',
            total=Decimal(0)
        )

        # Calculate total and create SaleItems
        total = Decimal(0)
        for oi in items_list:
            subtotal = Decimal(str(oi.unit_price)) * oi.quantity
            total += subtotal

            sale_item = SaleItem(
                sale=sale,
                product_variant_id=oi.product_variant_id,
                quantity=oi.quantity,
                unit_price=oi.unit_price,
                subtotal=subtotal
            )
            db.session.add(sale_item)

        sale.total = total
        db.session.add(sale)

        # Update order status
        order.status = 'cerrada'
        order.closed_at = datetime.utcnow()
        order.closed_by = current_user.id

        # Update mesa status if mesa_id exists
        if order.mesa_id:
            mesa = Mesa.query.get(order.mesa_id)
            if mesa:
                mesa.status = 'libre'

        db.session.commit()

        return jsonify({
            'order': order.to_dict(include_items=True),
            'sale': sale.to_dict()
        }), 200

    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error procesando cobro: {str(e)}'}), 500


@bp.route('/<int:order_id>', methods=['DELETE'])
@token_required
@admin_required
def cancel_order(current_user, order_id):
    """
    Cancel an order (admin only)
    Sets status to 'cancelada' and frees the mesa if applicable
    """
    order = Order.query.get_or_404(order_id)

    # Set status to cancelada
    order.status = 'cancelada'

    # Update mesa status if mesa_id exists
    if order.mesa_id:
        mesa = Mesa.query.get(order.mesa_id)
        if mesa:
            mesa.status = 'libre'

    db.session.commit()
    return jsonify(order.to_dict(include_items=True)), 200
