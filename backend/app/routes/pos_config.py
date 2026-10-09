"""Configuración del POS: salones, mesas, modificadores, medios de pago y plantillas."""
import logging
from decimal import Decimal

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import DataError, IntegrityError

from app.extensions import db
from app.models import Product, Supply
from app.models.pos import (ACTIVE_SALE_STATUSES, DISCOUNT_KINDS, DISCOUNT_SCOPES, PAYMENT_KINDS, DiscountTemplate,
                            ModifierGroup, ModifierOption, PaymentMethod, PosSale, PosTable, ProductModifierGroup,
                            Salon)
from app.services.pos.pricing import money
from app.services.pos.errors import PosError, bad_request, not_found
from app.utils.decorators import admin_required, module_required
from app.utils.jwt_utils import token_required
from app.utils.validation import clean_str, json_object, parse_decimal

logger = logging.getLogger(__name__)
bp = Blueprint('pos_config', __name__, url_prefix='/api/v1/pos/config')


def _run(action, status=200):
    try:
        result = action()
        db.session.commit()
    except PosError as exc:
        db.session.rollback()
        return jsonify({'error': exc.message, **exc.extra}), exc.status
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Ya existe un registro con esos datos'}), 409
    except DataError:
        db.session.rollback()
        return jsonify({'error': 'Algún valor es demasiado grande'}), 400
    except Exception:
        db.session.rollback()
        logger.exception('Error inesperado en la configuración del POS')
        return jsonify({'error': 'Error interno, probá de nuevo'}), 500
    return jsonify(result), status


def _body():
    data = json_object()
    if data is None:
        raise bad_request('El cuerpo tiene que ser un objeto JSON')
    return data


def _int(value, label, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise bad_request(f'{label} es inválido')
    return value


def _name(data, max_len):
    name = clean_str(data.get('name'), max_len)
    if not name:
        raise bad_request('El nombre es obligatorio')
    return name


def _has_active_sales(table_ids):
    return bool(table_ids) and PosSale.query.filter(PosSale.table_id.in_(table_ids),
                                                    PosSale.status.in_(ACTIVE_SALE_STATUSES)).first() is not None


# Salones y mesas

@bp.route('/salons', methods=['GET'])
@token_required
@module_required('POS')
def list_salons(current_user):
    return jsonify({'salons': [s.to_dict() for s in Salon.query.order_by(Salon.position, Salon.id).all()]}), 200


@bp.route('/salons', methods=['POST'])
@token_required
@module_required('POS')
def create_salon(current_user):
    def action():
        data = _body()
        salon = Salon(name=_name(data, 100), position=_int(data.get('position', 0), 'La posición'))
        db.session.add(salon)
        db.session.flush()
        return salon.to_dict()
    return _run(action, 201)


@bp.route('/salons/<int:salon_id>', methods=['PUT'])
@token_required
@module_required('POS')
def update_salon(current_user, salon_id):
    def action():
        salon = db.session.get(Salon, salon_id)
        if salon is None:
            raise not_found('El salón no existe')
        data = _body()
        if 'name' in data:
            salon.name = _name(data, 100)
        if 'position' in data:
            salon.position = _int(data['position'], 'La posición')
        if 'is_active' in data:
            if data['is_active'] is False and _has_active_sales([t.id for t in salon.tables]):
                raise PosError('El salón tiene mesas con ventas abiertas')
            salon.is_active = bool(data['is_active'])
        db.session.flush()
        return salon.to_dict()
    return _run(action)


@bp.route('/tables', methods=['GET'])
@token_required
@module_required('POS')
def list_tables(current_user):
    query = PosTable.query
    salon_id = request.args.get('salon_id', type=int)
    if salon_id:
        query = query.filter_by(salon_id=salon_id)
    return jsonify({'tables': [t.to_dict() for t in query.order_by(PosTable.salon_id, PosTable.number).all()]}), 200


_TABLE_FLOATS = ('pos_x', 'pos_y', 'width', 'height')


def _apply_table(table, data):
    if 'number' in data:
        table.number = _int(data['number'], 'El número', minimum=1)
    if 'name' in data:
        table.name = clean_str(data['name'], 50)
    if 'capacity' in data:
        table.capacity = None if data['capacity'] is None else _int(data['capacity'], 'La capacidad', minimum=1)
    for field in _TABLE_FLOATS:
        if field in data:
            setattr(table, field, float(parse_decimal(data[field], field, minimum=Decimal('0'),
                                                      maximum=Decimal('100000'))))


@bp.route('/tables', methods=['POST'])
@token_required
@module_required('POS')
def create_table(current_user):
    def action():
        data = _body()
        salon = db.session.get(Salon, _int(data.get('salon_id'), 'El salón', minimum=1))
        if salon is None:
            raise not_found('El salón no existe')
        if 'number' not in data:
            raise bad_request('El número es obligatorio')
        table = PosTable(salon_id=salon.id)
        _apply_table(table, data)
        db.session.add(table)
        db.session.flush()
        return table.to_dict()
    return _run(action, 201)


@bp.route('/tables/<int:table_id>', methods=['PUT'])
@token_required
@module_required('POS')
def update_table(current_user, table_id):
    def action():
        table = db.session.get(PosTable, table_id)
        if table is None:
            raise not_found('La mesa no existe')
        data = _body()
        _apply_table(table, data)
        if 'is_active' in data:
            if data['is_active'] is False and _has_active_sales([table.id]):
                raise PosError('La mesa tiene una venta abierta')
            table.is_active = bool(data['is_active'])
        db.session.flush()
        return table.to_dict()
    return _run(action)


# Modificadores

def _apply_options(group, options):
    if not isinstance(options, list) or not options:
        raise bad_request('El grupo necesita al menos una opción')
    existing = {o.id: o for o in group.options}
    kept = set()
    for position, data in enumerate(options):
        if not isinstance(data, dict):
            raise bad_request('Opción inválida')
        option = existing.get(data.get('id')) if data.get('id') is not None else None
        if data.get('id') is not None and option is None:
            raise bad_request('La opción no pertenece a este grupo')
        if option is None:
            option = ModifierOption(group=group)
            db.session.add(option)
        option.name = _name(data, 100)
        option.price_delta = money(parse_decimal(data.get('price_delta', 0), 'El recargo',
                                                 maximum=Decimal('100000000')))
        option.position = position
        option.is_active = True
        supply_id = data.get('supply_id')
        if supply_id is None:
            option.supply_id = None
            option.supply_quantity = None
        else:
            supply = db.session.get(Supply, _int(supply_id, 'El insumo', minimum=1))
            if supply is None:
                raise bad_request('El insumo no existe')
            option.supply_id = supply.id
            option.supply_quantity = parse_decimal(data.get('supply_quantity'), 'La cantidad de insumo',
                                                   minimum=Decimal('0.0001'), maximum=Decimal('1000000'))
        if option.id is not None:
            kept.add(option.id)
    for option_id, option in existing.items():
        if option_id not in kept:
            option.is_active = False


def _apply_group(group, data, creating):
    if creating or 'name' in data:
        group.name = _name(data, 100)
    if creating or 'min_select' in data:
        group.min_select = _int(data.get('min_select', 0), 'El mínimo')
    if creating or 'max_select' in data:
        group.max_select = _int(data.get('max_select', 1), 'El máximo', minimum=1)
    if group.min_select > group.max_select:
        raise bad_request('El mínimo no puede superar al máximo')
    if 'is_active' in data:
        group.is_active = bool(data['is_active'])
    if creating or 'options' in data:
        _apply_options(group, data.get('options'))


@bp.route('/modifier-groups', methods=['GET'])
@token_required
@module_required('Products', 'POS')
def list_modifier_groups(current_user):
    groups = ModifierGroup.query.order_by(ModifierGroup.name).all()
    return jsonify({'modifier_groups': [g.to_dict(include_inactive=True) for g in groups]}), 200


@bp.route('/modifier-groups', methods=['POST'])
@token_required
@module_required('Products')
def create_modifier_group(current_user):
    def action():
        group = ModifierGroup()
        db.session.add(group)
        _apply_group(group, _body(), creating=True)
        db.session.flush()
        return group.to_dict()
    return _run(action, 201)


@bp.route('/modifier-groups/<int:group_id>', methods=['PUT'])
@token_required
@module_required('Products')
def update_modifier_group(current_user, group_id):
    def action():
        group = db.session.get(ModifierGroup, group_id)
        if group is None:
            raise not_found('El grupo no existe')
        _apply_group(group, _body(), creating=False)
        db.session.flush()
        return group.to_dict(include_inactive=True)
    return _run(action)


@bp.route('/products/<int:product_id>/modifier-groups', methods=['PUT'])
@token_required
@module_required('Products')
def assign_modifier_groups(current_user, product_id):
    def action():
        product = db.session.get(Product, product_id)
        if product is None:
            raise not_found('El producto no existe')
        group_ids = _body().get('group_ids')
        if not isinstance(group_ids, list) or len(set(group_ids)) != len(group_ids):
            raise bad_request('Lista de grupos inválida')
        for group_id in group_ids:
            if db.session.get(ModifierGroup, _int(group_id, 'El grupo', minimum=1)) is None:
                raise bad_request('El grupo no existe')
        ProductModifierGroup.query.filter_by(product_id=product.id).delete()
        for position, group_id in enumerate(group_ids):
            db.session.add(ProductModifierGroup(product_id=product.id, group_id=group_id, position=position))
        db.session.flush()
        return {'product_id': product.id, 'group_ids': group_ids}
    return _run(action)


# Medios de pago y plantillas (solo admin)

def _apply_payment_method(method, data, creating):
    if creating or 'name' in data:
        method.name = _name(data, 50)
    if creating or 'kind' in data:
        if data.get('kind') not in PAYMENT_KINDS:
            raise bad_request('Tipo de medio de pago inválido')
        method.kind = data['kind']
    if 'position' in data:
        method.position = _int(data['position'], 'La posición')
    if 'is_active' in data:
        method.is_active = bool(data['is_active'])


@bp.route('/payment-methods', methods=['GET'])
@token_required
@admin_required
def list_payment_methods(current_user):
    methods = PaymentMethod.query.order_by(PaymentMethod.position, PaymentMethod.id).all()
    return jsonify({'payment_methods': [m.to_dict() for m in methods]}), 200


@bp.route('/payment-methods', methods=['POST'])
@token_required
@admin_required
def create_payment_method(current_user):
    def action():
        method = PaymentMethod()
        _apply_payment_method(method, _body(), creating=True)
        db.session.add(method)
        db.session.flush()
        return method.to_dict()
    return _run(action, 201)


@bp.route('/payment-methods/<int:method_id>', methods=['PUT'])
@token_required
@admin_required
def update_payment_method(current_user, method_id):
    def action():
        method = db.session.get(PaymentMethod, method_id)
        if method is None:
            raise not_found('El medio de pago no existe')
        _apply_payment_method(method, _body(), creating=False)
        db.session.flush()
        return method.to_dict()
    return _run(action)


def _apply_template(template, data, creating):
    if creating or 'name' in data:
        template.name = _name(data, 100)
    if creating or 'kind' in data:
        if data.get('kind') not in DISCOUNT_KINDS:
            raise bad_request('Tipo de descuento inválido')
        template.kind = data['kind']
    if creating or 'scope' in data:
        if data.get('scope') not in DISCOUNT_SCOPES:
            raise bad_request('Alcance inválido')
        template.scope = data['scope']
    if creating or 'value' in data:
        value = money(parse_decimal(data.get('value'), 'El valor', minimum=Decimal('0.01'),
                                    maximum=Decimal('100000000')))
        if value < Decimal('0.01'):
            raise bad_request('El valor es inválido')
        template.value = value
    if template.kind == 'percent' and Decimal(template.value) > 100:
        raise bad_request('El porcentaje no puede superar 100')
    if 'restricted' in data:
        template.restricted = bool(data['restricted'])
    elif creating:
        template.restricted = False
    if 'is_active' in data:
        template.is_active = bool(data['is_active'])


@bp.route('/discount-templates', methods=['GET'])
@token_required
@admin_required
def list_discount_templates(current_user):
    templates = DiscountTemplate.query.order_by(DiscountTemplate.name).all()
    return jsonify({'discount_templates': [t.to_dict() for t in templates]}), 200


@bp.route('/discount-templates', methods=['POST'])
@token_required
@admin_required
def create_discount_template(current_user):
    def action():
        template = DiscountTemplate()
        _apply_template(template, _body(), creating=True)
        db.session.add(template)
        db.session.flush()
        return template.to_dict()
    return _run(action, 201)


@bp.route('/discount-templates/<int:template_id>', methods=['PUT'])
@token_required
@admin_required
def update_discount_template(current_user, template_id):
    def action():
        template = db.session.get(DiscountTemplate, template_id)
        if template is None:
            raise not_found('La plantilla no existe')
        _apply_template(template, _body(), creating=False)
        db.session.flush()
        return template.to_dict()
    return _run(action)
