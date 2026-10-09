"""Operaciones sobre ventas del POS.

Cada función pública es una transacción completa: valida, aplica, audita y hace commit. Si
algo falla levanta PosError (o ValueError por datos inválidos) antes del commit; la ruta
hace rollback.
"""
from collections import defaultdict
from decimal import Decimal

from sqlalchemy import func

from app.extensions import db
from app.models import ProductVariant, User
from app.models.pos import (ACTIVE_SALE_STATUSES, ModifierGroup, ModifierOption, PosSale, PosSaleItem,
                            PosSaleItemModifier, PosTable, ProductModifierGroup)
from app.services.pos import audit, pricing
from app.services.pos.common import (MAX_QUANTITY, load_sale, now, parse_id, recalc, require_module,
                                     require_status)
from app.services.pos.errors import PosError, bad_request, not_found
from app.utils.timezone_utils import get_current_date_argentina
from app.utils.validation import clean_str, parse_decimal


def assign_number(sale):
    """Asigna el siguiente número del día. Si otra venta toma el mismo número al mismo tiempo,
    el UNIQUE(business_date, number) hace fallar el commit y la ruta responde 409."""
    last = db.session.query(func.max(PosSale.number)).filter(PosSale.business_date == sale.business_date).scalar()
    sale.number = (last or 0) + 1
    db.session.add(sale)
    db.session.flush()


def open_sale(user, sale_type, table_id=None, people=None, customer_name=None, comment=None, waiter_id=None):
    if sale_type not in ('salon', 'counter'):
        raise bad_request('Tipo de venta inválido')
    customer_name = clean_str(customer_name, 100)
    comment = clean_str(comment, 500)
    table = None
    if sale_type == 'salon':
        table_id = parse_id(table_id, 'La mesa')
        table = PosTable.query.filter_by(id=table_id).with_for_update().first()
        if table is None or not table.is_active:
            raise not_found('La mesa no existe')
        if isinstance(people, bool) or not isinstance(people, int) or not 1 <= people <= 100:
            raise bad_request('Indicá la cantidad de personas')
        existing = PosSale.query.filter(PosSale.table_id == table.id,
                                        PosSale.status.in_(ACTIVE_SALE_STATUSES)).first()
        if existing is not None:
            raise PosError('La mesa ya tiene una venta abierta', 409, sale_id=existing.id)
    else:
        require_module(user, 'POS', 'Solo la caja puede abrir ventas de mostrador')
        people = None
    waiter = user.id
    if waiter_id is not None:
        require_module(user, 'POS', 'Solo la caja puede asignar el mozo')
        waiter_id = parse_id(waiter_id, 'El mozo')
        if db.session.get(User, waiter_id) is None:
            raise bad_request('El mozo no existe')
        waiter = waiter_id
    sale = PosSale(business_date=get_current_date_argentina(), sale_type=sale_type,
                   table_id=table.id if table else None, people=people, customer_name=customer_name,
                   comment=comment, waiter_id=waiter, status='open', opened_at=now(), opened_by=user.id)
    assign_number(sale)
    audit.record(sale, user, 'opened', sale_type=sale_type, table_id=sale.table_id, people=people)
    db.session.commit()
    return sale


def _validate_modifiers(product_id, option_ids):
    if option_ids is None:
        option_ids = []
    if not isinstance(option_ids, list) or any(isinstance(i, bool) or not isinstance(i, int) for i in option_ids):
        raise bad_request('Modificadores inválidos')
    if len(set(option_ids)) != len(option_ids):
        raise bad_request('Hay modificadores repetidos')
    assigned = [a.group_id for a in ProductModifierGroup.query.filter_by(product_id=product_id).all()]
    groups = (ModifierGroup.query.filter(ModifierGroup.id.in_(assigned), ModifierGroup.is_active.is_(True)).all()
              if assigned else [])
    group_ids = {g.id for g in groups}
    options = ModifierOption.query.filter(ModifierOption.id.in_(option_ids)).all() if option_ids else []
    if len(options) != len(option_ids):
        raise bad_request('Modificador inexistente')
    chosen = defaultdict(int)
    for option in options:
        if not option.is_active or option.group_id not in group_ids:
            raise bad_request(f'El modificador "{option.name}" no corresponde a este producto')
        chosen[option.group_id] += 1
    for group in groups:
        count = chosen.get(group.id, 0)
        if count < group.min_select:
            raise bad_request(f'Elegí al menos {group.min_select} en "{group.name}"')
        if count > group.max_select:
            raise bad_request(f'Podés elegir hasta {group.max_select} en "{group.name}"')
    order = {group_id: index for index, group_id in enumerate(assigned)}
    return sorted(options, key=lambda o: (order.get(o.group_id, 0), o.position, o.id))


def _parse_quantity(value):
    quantity = parse_decimal(value, 'La cantidad', minimum=Decimal('0.001'), maximum=MAX_QUANTITY)
    return quantity.quantize(Decimal('0.001'))


def add_item(user, sale_id, product_variant_id, quantity=1, modifier_option_ids=None, note=None):
    sale = load_sale(sale_id)
    require_status(sale, ('open',), 'Solo se agregan ítems a una venta abierta')
    variant_id = parse_id(product_variant_id, 'El producto')
    variant = db.session.get(ProductVariant, variant_id)
    if variant is None or not variant.is_active or not variant.product.is_active:
        raise bad_request('El producto no está disponible')
    quantity = _parse_quantity(quantity)
    note = clean_str(note, 255)
    options = _validate_modifiers(variant.product_id, modifier_option_ids)
    modifiers_total = sum((Decimal(o.price_delta) for o in options), Decimal('0'))
    item = PosSaleItem(product_variant_id=variant.id, product_name=variant.product.name, variant_name=variant.name,
                       unit_price=variant.price, quantity=quantity, modifiers_total=modifiers_total, note=note,
                       line_total=pricing.line_total(quantity, variant.price, modifiers_total), status='pending',
                       created_by=user.id, created_at=now())
    for option in options:
        item.modifiers.append(PosSaleItemModifier(
            option_id=option.id, group_name=option.group.name, option_name=option.name,
            price_delta=option.price_delta, supply_id=option.supply_id, supply_quantity=option.supply_quantity))
    sale.items.append(item)
    recalc(sale)
    audit.record(sale, user, 'item_added', item=item, product=item.product_name, variant=item.variant_name,
                 quantity=quantity, modifiers=[o.name for o in options], note=note)
    db.session.commit()
    return sale


def _find_item(sale, item_id):
    item_id = parse_id(item_id, 'El ítem')
    item = next((i for i in sale.items if i.id == item_id), None)
    if item is None:
        raise not_found('El ítem no existe en esta venta')
    return item


def delete_item(user, sale_id, item_id):
    sale = load_sale(sale_id)
    require_status(sale, ('open',), 'Solo se borran ítems de una venta abierta')
    item = _find_item(sale, item_id)
    if item.status != 'pending':
        raise PosError('El ítem ya fue confirmado; para quitarlo hay que anularlo')
    audit.record(sale, user, 'item_deleted', item_id=item.id, product=item.product_name, variant=item.variant_name,
                 quantity=item.quantity, modifiers=[m.option_name for m in item.modifiers], note=item.note)
    sale.items.remove(item)
    recalc(sale)
    db.session.commit()
    return sale
