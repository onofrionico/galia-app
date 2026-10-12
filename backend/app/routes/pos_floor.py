"""Lecturas del POS: plano de mesas, catálogo y listas para la UI."""
from collections import defaultdict

from flask import Blueprint, jsonify, request
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Product, ProductCategory
from app.models.pos import (ACTIVE_SALE_STATUSES, CancelReason, DiscountTemplate, ModifierGroup, PaymentMethod, PosSale, PosSaleEvent, PosTable,
                            ProductModifierGroup, Salon)
from app.services.pos import waiters
from app.services.pos.common import display_name
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


@bp.route('/cancel-reasons', methods=['GET'])
@token_required
@module_required('POS', 'Camarero', 'Anular')
def cancel_reasons(current_user):
    reasons = (CancelReason.query.filter_by(is_active=True)
               .order_by(CancelReason.position, CancelReason.id).all())
    return jsonify({'cancel_reasons': [r.to_dict() for r in reasons]}), 200


@bp.route('/waiters', methods=['GET'])
@token_required
@module_required('POS')
def list_waiters(current_user):
    return jsonify({'waiters': [{'id': u.id, 'name': display_name(u)} for u in waiters.list_waiters()]}), 200


CHANGES_LIMIT = 500
CHANGES_OVERLAP = 50


def _changed_sale(sale, event_ids):
    table = sale.table
    return {'id': sale.id, 'table_id': sale.table_id, 'salon_id': table.salon_id if table else None,
            'sale_type': sale.sale_type, 'status': sale.status, 'event_ids': event_ids}


@bp.route('/changes', methods=['GET'])
@token_required
@module_required('POS', 'Camarero')
def changes(current_user):
    """Ventas con eventos posteriores a `since`. La UI lo consulta cada pocos segundos.

    Con varios hilos, un evento puede confirmarse después que otro de id mayor. Por eso la ventana
    arranca CHANGES_OVERLAP ids antes de `since`: devuelve también los eventos recientes ya
    informados, con sus ids (`event_ids` en total y por venta), y la UI descarta los que ya vio.
    """
    last = db.session.query(func.max(PosSaleEvent.id)).scalar() or 0
    since = request.args.get('since', type=int)
    if since is None:
        return jsonify({'last_event_id': last, 'sales': []}), 200
    if since > last:
        return jsonify({'last_event_id': last, 'reset': True, 'sales': []}), 200
    # En la ventana hay a lo sumo CHANGES_OVERLAP ids <= since; si se llena el límite, hay más de
    # CHANGES_LIMIT eventos posteriores a since.
    rows = (db.session.query(PosSaleEvent.id, PosSaleEvent.sale_id)
            .filter(PosSaleEvent.id > max(0, since - CHANGES_OVERLAP)).order_by(PosSaleEvent.id)
            .limit(CHANGES_LIMIT + CHANGES_OVERLAP + 1).all())
    if sum(1 for row in rows if row.id > since) > CHANGES_LIMIT:
        return jsonify({'last_event_id': last, 'reset': True, 'sales': []}), 200
    if not rows:
        return jsonify({'last_event_id': since, 'event_ids': [], 'sales': []}), 200
    events_by_sale = defaultdict(list)
    for row in rows:
        events_by_sale[row.sale_id].append(row.id)
    sales = (PosSale.query.options(selectinload(PosSale.table))
             .filter(PosSale.id.in_(sorted(events_by_sale))).order_by(PosSale.id).all())
    return jsonify({'last_event_id': max(since, rows[-1].id), 'event_ids': [row.id for row in rows],
                    'sales': [_changed_sale(s, events_by_sale[s.id]) for s in sales]}), 200
