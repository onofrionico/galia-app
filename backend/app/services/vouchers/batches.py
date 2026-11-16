"""Tandas de vouchers: alta con códigos, estados derivados, resumen, vencimiento y anulación."""
from datetime import date, datetime
from decimal import Decimal

from app.extensions import db
from app.models.pos import PosDiscount, PosSale
from app.models.vouchers import Voucher, VoucherBatch, VoucherChangeLog
from app.services.pos import pricing
from app.services.pos.errors import PosError, bad_request, not_found
from app.services.vouchers.codes import format_code, generate_code
from app.utils.timezone_utils import get_current_date_argentina
from app.utils.validation import clean_str, parse_decimal

MAX_BATCH_QUANTITY = 500  # tope de seguridad por tanda
MAX_AMOUNT = Decimal('100000000')  # Numeric(12, 2) con margen


def _parse_date(raw, label):
    try:
        return date.fromisoformat(raw)
    except (TypeError, ValueError):
        raise bad_request(f'{label} tiene que ser una fecha (AAAA-MM-DD)')


def _decimal(value, label, minimum):
    try:
        return pricing.money(parse_decimal(value, label, minimum=minimum, maximum=MAX_AMOUNT))
    except ValueError as exc:
        raise bad_request(str(exc))


def _text(value, label, max_len, required=False):
    try:
        text = clean_str(value, max_len)
    except ValueError as exc:
        raise bad_request(f'{label}: {exc}')
    if required and not text:
        raise bad_request(f'{label} es obligatorio')
    return text


def _unique_codes(quantity):
    codes = set()
    while len(codes) < quantity:
        codes |= {generate_code() for _ in range(quantity - len(codes))}
        taken = {c for (c,) in db.session.query(Voucher.code).filter(Voucher.code.in_(codes)).all()}
        codes -= taken
    return sorted(codes)


def create_batch(user, data):
    name = _text(data.get('name'), 'El nombre', 100, required=True)
    amount = _decimal(data.get('amount'), 'El monto', Decimal('0.01'))
    quantity = data.get('quantity')
    if isinstance(quantity, bool) or not isinstance(quantity, int) or not 1 <= quantity <= MAX_BATCH_QUANTITY:
        raise bad_request(f'La cantidad tiene que ser un entero entre 1 y {MAX_BATCH_QUANTITY}')
    expires_at = _parse_date(data.get('expires_at'), 'El vencimiento')
    if expires_at < get_current_date_argentina():
        raise bad_request('El vencimiento no puede ser anterior a hoy')
    min_raw = data.get('min_sale_amount')
    min_sale_amount = None if min_raw in (None, '') else _decimal(min_raw, 'El mínimo de consumo', Decimal('0'))
    batch = VoucherBatch(name=name, amount=amount, quantity=quantity, expires_at=expires_at,
                         min_sale_amount=min_sale_amount, terms=_text(data.get('terms'), 'Las condiciones', 2000),
                         created_by=user.id, created_at=datetime.utcnow())
    db.session.add(batch)
    db.session.flush()
    for code in _unique_codes(quantity):
        db.session.add(Voucher(batch_id=batch.id, code=code))
    db.session.commit()
    return batch


def voucher_status(voucher, discount_row, today):
    """'voided' > 'redeemed'/'in_use' (descuento activo) > 'expired' > 'available'.

    `discount_row` es (PosDiscount activo, PosSale) o None."""
    if voucher.voided_at is not None:
        return 'voided'
    if discount_row is not None:
        return 'redeemed' if discount_row[1].status == 'closed' else 'in_use'
    if voucher.batch.expires_at < today:
        return 'expired'
    return 'available'


def active_discount_rows(voucher_ids=None, batch_ids=None):
    """{voucher_id: (PosDiscount, PosSale)} de los descuentos activos, en una sola consulta."""
    query = (db.session.query(PosDiscount, PosSale).join(PosSale, PosDiscount.sale_id == PosSale.id)
             .filter(PosDiscount.cancelled_at.is_(None), PosDiscount.voucher_id.isnot(None)))
    if voucher_ids is not None:
        query = query.filter(PosDiscount.voucher_id.in_(voucher_ids))
    if batch_ids is not None:
        query = query.join(Voucher, PosDiscount.voucher_id == Voucher.id).filter(Voucher.batch_id.in_(batch_ids))
    return {discount.voucher_id: (discount, sale) for discount, sale in query.all()}


def _summary(batch, rows, today):
    counts = {'available': 0, 'in_use': 0, 'redeemed': 0, 'expired': 0, 'voided': 0}
    total = Decimal('0')
    items = []
    for voucher in batch.vouchers:
        row = rows.get(voucher.id)
        status = voucher_status(voucher, row, today)
        counts[status] += 1
        if status == 'redeemed':
            total += Decimal(row[0].amount)
        items.append({'id': voucher.id, 'code': format_code(voucher.code), 'code_raw': voucher.code,
                      'status': status, 'sale_id': row[1].id if row else None,
                      'redeemed_at': row[0].created_at.isoformat() if row else None,
                      'void_reason': voucher.void_reason})
    summary = {'id': batch.id, 'name': batch.name, 'amount': float(batch.amount),
               'min_sale_amount': float(batch.min_sale_amount) if batch.min_sale_amount is not None else None,
               'expires_at': batch.expires_at.isoformat(), 'terms': batch.terms,
               'created_at': batch.created_at.isoformat(), 'issued': len(batch.vouchers),
               'discount_total': float(total), **counts}
    return summary, items


def batch_detail(batch_id):
    batch = db.session.get(VoucherBatch, batch_id)
    if batch is None:
        raise not_found('La tanda no existe')
    summary, items = _summary(batch, active_discount_rows(batch_ids=[batch.id]), get_current_date_argentina())
    return {**summary, 'vouchers': items}


def list_batches():
    all_batches = VoucherBatch.query.order_by(VoucherBatch.id.desc()).all()
    rows = active_discount_rows(batch_ids=[b.id for b in all_batches]) if all_batches else {}
    today = get_current_date_argentina()
    return [_summary(batch, rows, today)[0] for batch in all_batches]


def extend_expiry(user, batch_id, new_date):
    batch = db.session.get(VoucherBatch, batch_id)
    if batch is None:
        raise not_found('La tanda no existe')
    new_expiry = _parse_date(new_date, 'El vencimiento')
    if new_expiry <= batch.expires_at:
        raise bad_request('El nuevo vencimiento tiene que ser posterior al actual')
    db.session.add(VoucherChangeLog(batch_id=batch.id, user_id=user.id, field='expires_at',
                                    old_value=batch.expires_at.isoformat(), new_value=new_expiry.isoformat()))
    batch.expires_at = new_expiry
    db.session.commit()
    return batch


def void_voucher(user, voucher_id, reason):
    voucher = db.session.get(Voucher, voucher_id)
    if voucher is None:
        raise not_found('El voucher no existe')
    reason = _text(reason, 'El motivo', 255, required=True)
    if voucher.voided_at is not None:
        raise PosError('El voucher ya está anulado')
    if voucher.id in active_discount_rows(voucher_ids=[voucher.id]):
        raise PosError('El voucher está aplicado a una venta; quitalo de la venta antes de anularlo')
    voucher.voided_at = datetime.utcnow()
    voucher.voided_by = user.id
    voucher.void_reason = reason
    db.session.commit()
    return voucher
