"""Lecturas del POS: plano de mesas, catálogo y listas para la UI."""
from collections import defaultdict

from flask import Blueprint, jsonify, request

from app.models import Product, ProductCategory
from app.models.pos import (ACTIVE_SALE_STATUSES, DiscountTemplate, ModifierGroup, PaymentMethod, PosSale, PosTable,
                            ProductModifierGroup, Salon)
from app.services.pos.serializers import sale_to_dict
from app.utils.decorators import module_required
from app.utils.jwt_utils import token_required

bp = Blueprint('pos_floor', __name__, url_prefix='/api/v1/pos')


@bp.route('/floor', methods=['GET'])
@token_required
@module_required('POS', 'Camarero')
def floor(current_user):
    salons = Salon.query.filter_by(is_active=True).order_by(Salon.position, Salon.id).all()
    salon_id = request.args.get('salon_id', type=int) or (salons[0].id if salons else None)
    tables = (PosTable.query.filter_by(salon_id=salon_id, is_active=True).order_by(PosTable.number).all()
              if salon_id else [])
    active = (PosSale.query.filter(PosSale.table_id.in_([t.id for t in tables]),
                                   PosSale.status.in_(ACTIVE_SALE_STATUSES)).order_by(PosSale.opened_at).all()
              if tables else [])
    by_table = defaultdict(list)
    for sale in active:
        by_table[sale.table_id].append(sale_to_dict(sale, include_items=False))
    return jsonify({
        'salons': [s.to_dict() for s in salons],
        'salon_id': salon_id,
        'tables': [{**t.to_dict(), 'sales': by_table.get(t.id, [])} for t in tables],
    }), 200


@bp.route('/catalog', methods=['GET'])
@token_required
@module_required('POS', 'Camarero')
def catalog(current_user):
    groups = {g.id: g for g in ModifierGroup.query.filter_by(is_active=True).all()}
    assignments = defaultdict(list)
    for assignment in ProductModifierGroup.query.order_by(ProductModifierGroup.position).all():
        if assignment.group_id in groups:
            assignments[assignment.product_id].append(groups[assignment.group_id].to_dict())
    products = []
    for product in Product.query.filter_by(is_active=True).order_by(Product.name).all():
        variants = [{'id': v.id, 'name': v.name, 'price': float(v.price)}
                    for v in product.variants if v.is_active]
        if not variants:
            continue
        products.append({'id': product.id, 'name': product.name, 'category_id': product.category_id,
                         'image_url': product.image_url, 'variants': variants,
                         'modifier_groups': assignments.get(product.id, [])})
    categories = ProductCategory.query.filter_by(is_active=True).order_by(ProductCategory.name).all()
    return jsonify({'categories': [{'id': c.id, 'name': c.name, 'color': c.color} for c in categories],
                    'products': products}), 200


@bp.route('/payment-methods', methods=['GET'])
@token_required
@module_required('POS', 'Camarero', 'Cobrar')
def payment_methods(current_user):
    methods = PaymentMethod.query.filter_by(is_active=True).order_by(PaymentMethod.position, PaymentMethod.id).all()
    return jsonify({'payment_methods': [m.to_dict() for m in methods]}), 200


@bp.route('/discount-templates', methods=['GET'])
@token_required
@module_required('POS', 'Camarero')
def discount_templates(current_user):
    templates = DiscountTemplate.query.filter_by(is_active=True).order_by(DiscountTemplate.name).all()
    return jsonify({'discount_templates': [t.to_dict() for t in templates]}), 200
