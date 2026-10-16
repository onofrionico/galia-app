"""Conciliación diaria: movimientos de la cuenta de MercadoPago contra pagos de Galia con medios de MercadoPago."""
import logging
from datetime import datetime, time, timedelta
from decimal import Decimal

import pytz

from app.extensions import db
from app.models import MpFetchDay, MpMovement, MpPointOrder, MpReconciliation, PaymentMethod, PosPayment
from app.models.mercadopago import RESOLUTION_KINDS
from app.services import mercadopago
from app.services.mercadopago import MpRejected, MpUnavailable
from app.services.mercadopago import settings as mp_settings
from app.services.mercadopago.client import movement_fields
from app.services.pos import payment_service
from app.services.pos.common import now, parse_id, require_module
from app.services.pos.errors import PosError, bad_request, not_found
from app.utils.timezone_utils import ARGENTINA_TZ
from app.utils.validation import clean_str

logger = logging.getLogger(__name__)
MAX_PER_DAY = 1000
SUGGEST_WINDOW = timedelta(minutes=15)
MONEY_STATUSES = ('approved', 'refunded', 'charged_back', 'partially_refunded', 'in_mediation')
ZERO = Decimal('0.00')


def _require(user):
    require_module(user, 'Conciliar', 'No tenés permiso para conciliar')


def _begin(day):
    return ARGENTINA_TZ.localize(datetime.combine(day, time.min)).astimezone(pytz.utc).replace(tzinfo=None)


def day_bounds(day):
    """(inicio, fin) del día de Argentina en UTC naive (fin al último segundo)."""
    begin = _begin(day)
    return begin, begin + timedelta(days=1) - timedelta(seconds=1)


def fetch(user, day):
    _require(user)
    client = mercadopago.get_client(mp_settings.get_settings())
    begin, end = day_bounds(day)
    fetched, offset, truncated = 0, 0, False
    try:
        while True:
            page = client.search_payments(begin, end, offset)
            results = page.get('results') or []
            for payment in results:
                fields = movement_fields(payment)
                movement = MpMovement.query.filter_by(mp_payment_id=fields['mp_payment_id']).first()
                if movement is None:
                    movement = MpMovement(mp_payment_id=fields['mp_payment_id'])
                    db.session.add(movement)
                for key, value in fields.items():
                    setattr(movement, key, value)
                movement.fetched_at = now()
                fetched += 1
            offset += len(results)
            total = (page.get('paging') or {}).get('total', 0)
            if not results or offset >= total:
                break
            if offset >= MAX_PER_DAY:
                truncated = True
                break
    except MpUnavailable:
        db.session.rollback()
        raise PosError('MercadoPago no responde, probá de nuevo')
    except MpRejected as exc:
        db.session.rollback()
        raise PosError(f'MercadoPago respondió: {exc.message}')
    mark = db.session.get(MpFetchDay, day) or MpFetchDay(business_date=day)
    mark.fetched_at, mark.fetched_by, mark.count, mark.truncated = now(), user.id, fetched, truncated
    db.session.add(mark)
    db.session.commit()
    return {'fetched': fetched, 'truncated': truncated}


def _galia_payments(day):
    method_ids = [m.id for m in PaymentMethod.query.filter_by(is_mercadopago=True)]
    if not method_ids:
        return []
    return PosPayment.query.filter(PosPayment.payment_method_id.in_(method_ids),
                                   PosPayment.created_at >= _begin(day),
                                   PosPayment.created_at < _begin(day + timedelta(days=1))).order_by(PosPayment.id).all()


def _money(value):
    return f'{value:.2f}'


def _payment_row(payment):
    sale = payment.sale
    return {'payment_id': payment.id, 'sale_id': payment.sale_id, 'sale_number': sale.number if sale else None,
            'method_name': payment.method_name, 'amount': _money(payment.amount),
            'created_at': payment.created_at.isoformat(), 'is_active': payment.cancelled_at is None,
            'mp_payment_id': payment.mp_payment_id}


def _movement_row(movement):
    return {'movement_id': movement.id, 'mp_payment_id': movement.mp_payment_id,
            'date_created': movement.date_created.isoformat(), 'amount': _money(movement.amount),
            'refunded_amount': _money(movement.refunded_amount), 'status': movement.status,
            'channel': movement.channel, 'payment_method': movement.payment_method,
            'description': movement.description, 'external_reference': movement.external_reference}


def _resolution_row(resolution):
    return {'id': resolution.id, 'kind': resolution.kind, 'note': resolution.note,
            'created_at': resolution.created_at.isoformat()}


def _matched_row(movement, payment, resolution):
    difference = ZERO
    if movement is not None and payment is not None:
        galia = payment.amount if payment.cancelled_at is None else ZERO
        difference = movement.amount - movement.refunded_amount - galia
    return {'movement': _movement_row(movement) if movement else None,
            'payment': _payment_row(payment) if payment else None,
            'resolution': _resolution_row(resolution) if resolution else None, 'difference': _money(difference)}


def day(day):
    movements = MpMovement.query.filter_by(business_date=day).order_by(MpMovement.date_created).all()
    fetched = db.session.get(MpFetchDay, day) is not None or bool(movements)
    money = [m for m in movements if m.status in MONEY_STATUSES]
    rejected = [m for m in movements if m.status not in MONEY_STATUSES]
    payments = _galia_payments(day)
    by_mp_id = {p.mp_payment_id: p for p in payments if p.mp_payment_id}
    references = [m.external_reference for m in money if m.external_reference]
    by_reference = {o.external_reference: o.payment for o in MpPointOrder.query.filter(
        MpPointOrder.external_reference.in_(references or ['']), MpPointOrder.payment_id.isnot(None))}
    movement_ids = [m.id for m in movements] or [0]
    payment_ids = [p.id for p in payments] or [0]
    resolutions = {r.mp_movement_id: r for r in MpReconciliation.query.filter(
        MpReconciliation.mp_movement_id.in_(movement_ids))}
    payment_resolutions = {r.payment_id: r for r in MpReconciliation.query.filter(
        MpReconciliation.payment_id.in_(payment_ids))}

    matched, only_mp, used = [], [], set()
    for movement in money:
        resolution = resolutions.get(movement.id)
        if resolution is not None and resolution.payment_id is not None:
            payment = db.session.get(PosPayment, resolution.payment_id)
        else:
            payment = by_mp_id.get(movement.mp_payment_id) or by_reference.get(movement.external_reference or '')
        if payment is not None:
            used.add(payment.id)
            matched.append(_matched_row(movement, payment, resolution))
        elif resolution is not None:  # not_a_sale
            matched.append(_matched_row(movement, None, resolution))
        else:
            only_mp.append(movement)

    free = [p for p in payments if p.id not in used and p.cancelled_at is None]
    only_galia = []
    for payment in free:
        resolution = payment_resolutions.get(payment.id)
        if resolution is not None and resolution.kind == 'reviewed':
            matched.append(_matched_row(None, payment, resolution))
        else:
            only_galia.append(payment)
    only_mp_rows = []
    for movement in only_mp:
        suggestions = [_payment_row(p) for p in only_galia if p.amount == movement.amount and not p.mp_payment_id
                       and abs(p.created_at - movement.date_created) <= SUGGEST_WINDOW]
        only_mp_rows.append({**_movement_row(movement), 'suggestions': suggestions})

    pending = len(only_mp_rows) + len(only_galia)
    status = 'sin_traer' if not fetched else ('conciliado' if pending == 0 else 'con_diferencias')
    by_channel = {}
    for movement in money:
        by_channel[movement.channel] = by_channel.get(movement.channel, ZERO) + movement.amount
    totals = {
        'matched': _money(sum((Decimal(r['movement']['amount']) for r in matched if r['movement']), ZERO)),
        'only_mp': _money(sum((m.amount for m in only_mp), ZERO)),
        'only_galia': _money(sum((p.amount for p in only_galia), ZERO)),
        'by_channel': {channel: _money(amount) for channel, amount in by_channel.items()},
    }
    return {'day': day.isoformat(), 'status': status, 'pending': pending, 'matched': matched,
            'only_mp': only_mp_rows, 'only_galia': [_payment_row(p) for p in only_galia],
            'rejected': [_movement_row(m) for m in rejected], 'totals': totals}


def summary(date_from, date_to):
    if date_to < date_from or (date_to - date_from).days > 62:
        raise bad_request('El rango de fechas es inválido')
    days, current = [], date_from
    while current <= date_to:
        data = day(current)
        days.append({'day': current.isoformat(), 'status': data['status'], 'pending': data['pending']})
        current += timedelta(days=1)
    return days


def _already_resolved(movement, payment):
    if movement is not None and MpReconciliation.query.filter_by(mp_movement_id=movement.id).first():
        return True
    if payment is not None and MpReconciliation.query.filter_by(payment_id=payment.id).first():
        return True
    return payment is not None and bool(payment.mp_payment_id)


def resolve(user, kind, movement_id=None, payment_id=None, sale_id=None, payment_method_id=None, note=None):
    _require(user)
    if kind not in RESOLUTION_KINDS:
        raise bad_request('La resolución es inválida')
    note = clean_str(note, 255)
    movement = db.session.get(MpMovement, parse_id(movement_id, 'El movimiento')) if movement_id else None
    payment = db.session.get(PosPayment, parse_id(payment_id, 'El pago')) if payment_id else None
    if movement_id and movement is None:
        raise not_found('El movimiento no existe')
    if payment_id and payment is None:
        raise not_found('El pago no existe')
    if kind == 'reviewed':
        movement = None
    else:
        if movement is None:
            raise bad_request('Elegí el movimiento de MercadoPago')
        if kind != 'matched_manual':
            payment = None
    if _already_resolved(movement, payment):
        raise PosError('Ya está conciliado')
    if kind == 'matched_manual':
        if payment is None:
            raise bad_request('Elegí el pago de Galia')
        payment.mp_payment_id = movement.mp_payment_id
    elif kind == 'payment_created':
        if not sale_id or not payment_method_id:
            raise bad_request('Elegí la venta y el medio de pago')
        method = db.session.get(PaymentMethod, parse_id(payment_method_id, 'El medio de pago'))
        if method is None or not method.is_mercadopago:
            raise bad_request('Elegí un medio de pago de MercadoPago')
        request_id = f'mp-mov-{movement.id}'
        try:
            payment_service.add_payment(user, parse_id(sale_id, 'La venta'), method.id,
                                        movement.amount - movement.refunded_amount, client_request_id=request_id)
        except ValueError as exc:
            raise bad_request(str(exc))
        payment = PosPayment.query.filter_by(client_request_id=request_id).first()
        payment.mp_payment_id = movement.mp_payment_id
    elif kind == 'not_a_sale':
        if not note:
            raise bad_request('Contá en la nota qué es ese movimiento')
    elif kind == 'reviewed':
        if payment is None:
            raise bad_request('Elegí el pago de Galia')
        if not note:
            raise bad_request('Contá en la nota qué revisaste')
    resolution = MpReconciliation(mp_movement_id=movement.id if movement else None,
                                  payment_id=payment.id if payment else None, kind=kind, note=note,
                                  created_by=user.id, created_at=now())
    db.session.add(resolution)
    db.session.commit()
    return _resolution_row(resolution)


def undo(user, resolution_id):
    """Deshace la resolución. Un pago creado desde la conciliación no se anula: se anula aparte."""
    _require(user)
    resolution = db.session.get(MpReconciliation, parse_id(resolution_id, 'La resolución'))
    if resolution is None:
        raise not_found('La resolución no existe')
    if resolution.kind in ('matched_manual', 'payment_created') and resolution.payment_id:
        payment = db.session.get(PosPayment, resolution.payment_id)
        payment.mp_payment_id = None
    db.session.delete(resolution)
    db.session.commit()
