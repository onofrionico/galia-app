"""Canje de vouchers en el POS: se aplican como un descuento por monto a la venta."""
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.pos import ACTIVE_SALE_STATUSES, PosDiscount
from app.models.vouchers import Voucher
from app.services.pos import audit
from app.services.pos.closing import close_if_settled
from app.services.pos.common import load_sale, now, recalc, require_status
from app.services.pos.errors import PosError, not_found
from app.services.vouchers import batches
from app.services.vouchers.codes import normalize_code
from app.utils.timezone_utils import convert_utc_to_argentina, get_current_date_argentina


def _active_row(voucher):
    """(PosDiscount activo, PosSale) del voucher, o None si está libre."""
    return batches.active_discount_rows(voucher_ids=[voucher.id]).get(voucher.id)


def _day(value):
    return value.strftime('%d/%m/%Y')


def _pesos(amount):
    return '$' + f'{amount:,.0f}'.replace(',', '.')


def redeem_voucher(user, sale_id, code):
    sale = load_sale(sale_id)
    require_status(sale, ACTIVE_SALE_STATUSES, 'Solo se canjea un voucher en una venta abierta o en cobro')
    if sale.is_practice:
        raise PosError('No se canjea un voucher en una venta de práctica')
    normalized = normalize_code(code)
    voucher = Voucher.query.filter_by(code=normalized).first() if normalized else None
    if voucher is None:
        raise not_found('Código de voucher inválido')
    batch = voucher.batch
    if voucher.voided_at is not None:
        raise PosError('Ese voucher fue anulado')
    row = _active_row(voucher)
    if row is not None:
        discount, other = row
        if other.id == sale.id:
            raise PosError('Ese voucher ya está aplicado a esta venta')
        if other.status == 'closed':
            day = _day(convert_utc_to_argentina(discount.created_at))
            raise PosError(f'Ese voucher ya fue canjeado el {day} en la venta #{other.number}')
        raise PosError(f'Ese voucher ya está aplicado a la venta #{other.number}')
    if batch.expires_at < get_current_date_argentina():
        raise PosError(f'Ese voucher venció el {_day(batch.expires_at)}')
    if batch.min_sale_amount is not None and sale.subtotal < batch.min_sale_amount:
        raise PosError(f'La venta tiene que llegar a {_pesos(batch.min_sale_amount)} para usar este voucher')

    discount = PosDiscount(sale=sale, voucher_id=voucher.id, kind='amount', value=batch.amount, amount=0,
                           reason=f'Voucher {batch.name}', created_by=user.id, created_at=now())
    db.session.add(discount)
    try:
        db.session.flush()
    except IntegrityError:  # otra caja se quedó con el voucher en el mismo instante
        db.session.rollback()
        raise PosError('Ese voucher ya está en uso')
    recalc(sale)
    if sale.total < sale.paid_total:
        raise PosError('El total quedaría por debajo de lo ya pagado; anulá un pago primero')
    audit.record(sale, user, 'voucher_redeemed', discount_id=discount.id, voucher_id=voucher.id,
                 code=voucher.code, amount=discount.amount, batch=batch.name)
    close_if_settled(sale, user)
    db.session.commit()
    return sale
