from app.services.pos.common import display_name


def _money(value):
    return float(value) if value is not None else None


def _iso(value):
    return value.isoformat() if value is not None else None


def item_to_dict(item):
    return {
        'id': item.id,
        'product_variant_id': item.product_variant_id,
        'product_name': item.product_name,
        'variant_name': item.variant_name,
        'unit_price': _money(item.unit_price),
        'quantity': float(item.quantity),
        'modifiers_total': _money(item.modifiers_total),
        'line_total': _money(item.line_total),
        'note': item.note,
        'status': item.status,
        'batch': item.batch,
        'created_at': _iso(item.created_at),
        'confirmed_at': _iso(item.confirmed_at),
        'cancelled_at': _iso(item.cancelled_at),
        'cancel_reason': item.cancel_reason,
        'modifiers': [{'option_id': m.option_id, 'group_name': m.group_name, 'option_name': m.option_name,
                       'price_delta': _money(m.price_delta)} for m in item.modifiers],
    }


def discount_to_dict(discount):
    return {
        'id': discount.id, 'item_id': discount.item_id, 'template_id': discount.template_id,
        'kind': discount.kind, 'value': _money(discount.value), 'amount': _money(discount.amount),
        'reason': discount.reason, 'is_active': discount.cancelled_at is None,
        'created_at': _iso(discount.created_at),
    }


def payment_to_dict(payment):
    return {
        'id': payment.id, 'payment_method_id': payment.payment_method_id, 'method_name': payment.method_name,
        'amount': _money(payment.amount), 'tendered': _money(payment.tendered), 'change': _money(payment.change),
        'is_active': payment.cancelled_at is None, 'cancel_reason': payment.cancel_reason,
        'created_at': _iso(payment.created_at),
    }


def sale_to_dict(sale, include_items=True):
    table = sale.table
    data = {
        'id': sale.id,
        'number': sale.number,
        'business_date': sale.business_date.isoformat(),
        'sale_type': sale.sale_type,
        'status': sale.status,
        'table': ({'id': table.id, 'number': table.number, 'label': table.label, 'salon_id': table.salon_id,
                   'salon_name': table.salon.name} if table else None),
        'people': sale.people,
        'customer_name': sale.customer_name,
        'comment': sale.comment,
        'waiter': {'id': sale.waiter.id, 'name': display_name(sale.waiter)} if sale.waiter else None,
        'opened_at': _iso(sale.opened_at),
        'billing_at': _iso(sale.billing_at),
        'closed_at': _iso(sale.closed_at),
        'cancelled_at': _iso(sale.cancelled_at),
        'cancel_reason': sale.cancel_reason,
        'subtotal': _money(sale.subtotal),
        'discount_total': _money(sale.discount_total),
        'total': _money(sale.total),
        'paid_total': _money(sale.paid_total),
        'balance': _money(sale.balance),
        'split_from_id': sale.split_from_id,
        'sale_id': sale.sale_id,
    }
    if include_items:
        data['items'] = [item_to_dict(i) for i in sale.items]
        data['discounts'] = [discount_to_dict(d) for d in sale.discounts]
        data['payments'] = [payment_to_dict(p) for p in sale.payments]
    return data
