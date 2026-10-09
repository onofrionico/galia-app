"""Descuentos del POS: por venta o por ítem, libres o desde plantillas."""
from decimal import Decimal

from app.extensions import db
from app.models.pos import DiscountTemplate, PosDiscount
from app.models.pos import ACTIVE_SALE_STATUSES
from app.services.pos import audit, pricing
from app.services.pos.closing import close_if_settled
from app.services.pos.common import load_sale, now, parse_id, recalc, require_module, require_status
from app.services.pos.errors import PosError, bad_request, not_found
from app.utils.validation import clean_str, parse_decimal

MAX_PERCENT = Decimal('100')
MAX_AMOUNT = Decimal('100000000')  # Numeric(10, 2)


def add_discount(user, sale_id, item_id=None, template_id=None, kind=None, value=None, reason=None):
    sale = load_sale(sale_id)
    require_status(sale, ACTIVE_SALE_STATUSES, 'Solo se descuenta en una venta abierta o en cobro')
    item = None
    if item_id is not None:
        item_id = parse_id(item_id, 'El ítem')
        item = next((i for i in sale.items if i.id == item_id), None)
        if item is None or item.status != 'confirmed':
            raise bad_request('Solo se descuentan ítems confirmados de esta venta')
    reason = clean_str(reason, 255)
    template = None
    if template_id is not None:
        template = db.session.get(DiscountTemplate, parse_id(template_id, 'La plantilla'))
        if template is None or not template.is_active:
            raise bad_request('La plantilla no existe')
        if (template.scope == 'item') != (item is not None):
            raise bad_request('Esa plantilla se aplica a ítems' if template.scope == 'item'
                              else 'Esa plantilla se aplica a la venta')
        if template.restricted:
            require_module(user, 'Descuentos', 'No tenés permiso para usar esa plantilla')
        kind, value = template.kind, Decimal(template.value)
        reason = reason or template.name
    else:
        require_module(user, 'Descuentos', 'No tenés permiso para hacer descuentos libres')
        if kind not in ('percent', 'amount'):
            raise bad_request('Tipo de descuento inválido')
        value = parse_decimal(value, 'El descuento', minimum=Decimal('0.01'), maximum=MAX_AMOUNT)
        value = pricing.money(value)
        if value < Decimal('0.01'):
            raise bad_request('El descuento no puede ser menor a 0.01')
        if kind == 'percent' and value > MAX_PERCENT:
            raise bad_request('El porcentaje no puede superar 100')
        if not reason:
            raise bad_request('Indicá el motivo del descuento')
    discount = PosDiscount(sale=sale, item=item, template_id=template.id if template else None, kind=kind,
                           value=value, amount=Decimal('0'), reason=reason, created_by=user.id, created_at=now())
    db.session.add(discount)
    recalc(sale)
    if sale.total < sale.paid_total:
        raise PosError('El total quedaría por debajo de lo ya pagado; anulá un pago primero')
    audit.record(sale, user, 'discount_added', item=item, discount_id=discount.id, kind=kind, value=value,
                 amount=discount.amount, reason=reason, template_id=discount.template_id)
    close_if_settled(sale, user)
    db.session.commit()
    return sale


def cancel_discount(user, discount_id):
    discount = db.session.get(PosDiscount, parse_id(discount_id, 'El descuento'))
    if discount is None:
        raise not_found('El descuento no existe')
    sale = load_sale(discount.sale_id)
    require_status(sale, ACTIVE_SALE_STATUSES, 'Solo se modifica una venta abierta o en cobro')
    db.session.refresh(discount)
    if discount.cancelled_at is not None:
        raise PosError('El descuento ya está anulado')
    if discount.template is None or discount.template.restricted:
        require_module(user, 'Descuentos', 'No tenés permiso para quitar ese descuento')
    discount.cancelled_at = now()
    discount.cancelled_by = user.id
    recalc(sale)
    audit.record(sale, user, 'discount_cancelled', item_id=discount.item_id, discount_id=discount.id)
    db.session.commit()
    return sale
