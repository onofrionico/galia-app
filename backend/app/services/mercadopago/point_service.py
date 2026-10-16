"""Cobros con el Point Smart: crear la orden, aplicar el resultado (idempotente), refrescar y cancelar.

El resultado llega por webhook o por la consulta de respaldo del frontend; las dos vías llaman a apply(), que
bloquea la orden, consulta a MercadoPago y crea el pago una sola vez (client_request_id 'mp-order-<id>').
"""
import logging
import uuid
from datetime import timedelta
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import MpPointOrder, PosPayment, User
from app.models.mercadopago import ACTIVE_STATUSES, FINAL_STATUSES
from app.services import mercadopago
from app.services.mercadopago import MpRejected, MpUnavailable
from app.services.mercadopago import settings as mp_settings
from app.services.mercadopago.client import order_state
from app.services.pos import audit, payment_service, pricing
from app.services.pos.common import MAX_MONEY, load_sale, now, parse_id
from app.services.pos.errors import PosError, bad_request, forbidden, not_found
from app.utils.permissions import check_module_access
from app.utils.validation import parse_decimal

logger = logging.getLogger(__name__)
REFRESH_AFTER = timedelta(seconds=5)
UNAVAILABLE = 'MercadoPago no responde, probá de nuevo'
NOT_READY = 'El Point no está listo para recibir cobros: revisá que esté prendido y en modo PDV'
REJECTION_TEXT = {
    'cc_rejected_insufficient_amount': 'fondos insuficientes',
    'cc_rejected_bad_filled_security_code': 'código de seguridad incorrecto',
    'cc_rejected_call_for_authorize': 'la tarjeta pide autorización al banco',
    'cc_rejected_card_disabled': 'tarjeta inhabilitada',
    'cc_rejected_high_risk': 'rechazado por seguridad',
}


def _require_charge(user):
    if not (check_module_access(user, 'POS') or check_module_access(user, 'Cobrar')):
        raise forbidden('No tenés permiso para cobrar')


def _place(sale):
    return sale.table.label if sale.table is not None else f'Mostrador #{sale.number}'


def order_to_dict(order):
    return {'id': order.id, 'sale_id': order.sale_id, 'amount': f'{order.amount:.2f}', 'status': order.status,
            'status_detail': order.status_detail, 'error': order.error, 'mp_order_id': order.mp_order_id,
            'mp_payment_id': order.mp_payment_id, 'payment_id': order.payment_id,
            'approved_amount': f'{order.approved_amount:.2f}' if order.approved_amount is not None else None,
            'created_at': order.created_at.isoformat(), 'fake': mercadopago.fake_enabled()}


def _load(order_id, lock=False):
    query = MpPointOrder.query.filter_by(id=parse_id(order_id, 'El cobro'))
    if lock:
        query = query.with_for_update().populate_existing()
    order = query.first()
    if order is None:
        raise not_found('El cobro no existe')
    return order


def _parse_amount(value):
    try:
        return pricing.money(parse_decimal(value, 'El monto', minimum=Decimal('0.01'), maximum=MAX_MONEY))
    except ValueError as exc:
        raise bad_request(str(exc))


def start(user, sale_id, amount):
    _require_charge(user)
    settings = mp_settings.get_settings()
    mp_settings.require_ready(settings)
    client = mercadopago.get_client(settings)
    sale = load_sale(parse_id(sale_id, 'La venta'))
    if not (sale.status == 'billing' or (sale.status == 'open' and sale.sale_type == 'counter')):
        raise PosError('Pedí la cuenta antes de cobrar')
    amount = _parse_amount(amount)
    if amount > sale.balance:
        raise bad_request(f'El monto tiene que ser mayor a 0 y no superar el saldo (${sale.balance:.2f})')
    busy = MpPointOrder.query.filter(MpPointOrder.terminal_id == settings.terminal_id,
                                     MpPointOrder.status.in_(ACTIVE_STATUSES)).first()
    if busy is not None:
        raise PosError(f'El Point está cobrando {_place(busy.sale)} (${busy.amount:.2f}): esperá o cancelalo')
    key = str(uuid.uuid4())
    order = MpPointOrder(sale_id=sale.id, amount=amount, terminal_id=settings.terminal_id, status='creating',
                         external_reference=f'galia-venta-{sale.id}-{key[:8]}', idempotency_key=key,
                         created_by=user.id, created_at=now(), updated_at=now())
    db.session.add(order)
    try:
        db.session.commit()  # el índice único rechaza un segundo cobro activo en la terminal
    except IntegrityError:
        db.session.rollback()
        raise PosError('El Point está ocupado con otro cobro: esperá o cancelalo')
    response = None
    for attempt in (1, 2):  # un reintento con la misma clave de idempotencia
        try:
            response = client.create_order(order.terminal_id, order.amount, order.external_reference, key)
            break
        except MpUnavailable as exc:
            logger.warning('MercadoPago sin respuesta creando la orden %s (intento %s): %s', order.id, attempt, exc)
        except MpRejected as exc:
            logger.warning('MercadoPago rechazó la orden %s: %s', order.id, exc)
            order.status = 'failed'
            order.error = NOT_READY if exc.status in (400, 404, 409) else exc.message[:255]
            order.updated_at = now()
            db.session.commit()
            return order
    if response is None:
        order.status, order.error, order.updated_at = 'failed', UNAVAILABLE, now()
        db.session.commit()
        return order
    order.mp_order_id = str(response['id'])
    order.status = 'created'
    order.updated_at = order.last_checked_at = now()
    audit.record(order.sale, user, 'point_order_created', order_id=order.id, amount=order.amount)
    db.session.commit()
    return order


def _register_payment(order, approved_amount):
    """Crea el pago de Galia por lo aprobado, hasta el saldo. Lo que sobra queda marcado para conciliar."""
    request_id = f'mp-order-{order.id}'
    existing = PosPayment.query.filter_by(client_request_id=request_id).first()
    if existing is not None:  # otra vía ya lo registró
        order.payment_id = existing.id
        db.session.commit()
        return existing
    settings = mp_settings.get_settings()
    user = db.session.get(User, order.created_by)
    sale = order.sale
    balance = sale.balance if sale.status in ('billing', 'open') else Decimal('0')
    to_register = min(approved_amount, balance)
    if approved_amount > to_register:
        order.error = f'Cobrado de más: ${approved_amount - to_register:.2f}, revisalo en Conciliación'
        logger.error('Cobro de Point %s excede el saldo de la venta %s', order.id, sale.id)
    if to_register <= 0:
        db.session.commit()
        return None
    db.session.commit()  # persiste el estado approved antes de crear el pago (add_payment hace su propio commit)
    payment_service.add_payment(user, sale.id, settings.point_payment_method_id, to_register,
                                client_request_id=request_id)
    payment = PosPayment.query.filter_by(client_request_id=request_id).first()
    payment.mp_payment_id = order.mp_payment_id
    order.payment_id = payment.id
    db.session.commit()
    return payment


def apply(order_id):
    order = _load(order_id, lock=True)
    if order.status in FINAL_STATUSES or not order.mp_order_id:
        db.session.commit()
        return order
    client = mercadopago.get_client(mp_settings.get_settings())
    try:
        state = order_state(client.get_order(order.mp_order_id))
    except (MpUnavailable, MpRejected) as exc:
        logger.warning('No se pudo consultar la orden %s: %s', order.id, exc)
        order.last_checked_at = now()
        db.session.commit()
        return order
    order.last_checked_at = order.updated_at = now()
    order.status_detail = (state['status_detail'] or '')[:80] or None
    if state['status'] == 'approved':
        order.status = 'approved'
        order.mp_payment_id = state['mp_payment_id']
        order.approved_amount = state['approved_amount'] or order.amount
        try:
            _register_payment(order, order.approved_amount)
        except PosError as exc:
            db.session.rollback()
            order = _load(order_id, lock=True)
            order.error = f'Cobrado pero no registrado: {exc.message}. Revisalo en Conciliación'[:255]
            logger.error('Cobro de Point %s aprobado sin registrar: %s', order.id, exc.message)
            db.session.commit()
        return order
    if state['status'] == 'failed':
        reason = REJECTION_TEXT.get(state['status_detail'] or '', state['status_detail'] or 'sin detalle')
        order.status, order.error = 'failed', f'El pago fue rechazado en el Point: {reason}'[:255]
    elif state['status'] in ('canceled', 'expired'):
        order.status = state['status']
        order.error = 'Se canceló el cobro' if state['status'] == 'canceled' else 'El cobro venció sin pagarse'
    elif order.status != 'canceling':
        order.status = state['status']
    if order.status in FINAL_STATUSES:
        # Evento en la venta: el feed de cambios refresca el aviso "Cobro en Point pendiente" en las pantallas.
        audit.record(order.sale, db.session.get(User, order.created_by), 'point_order_finished',
                     order_id=order.id, status=order.status)
    db.session.commit()
    return order


def apply_by_mp_order_id(mp_order_id):
    order = MpPointOrder.query.filter_by(mp_order_id=str(mp_order_id)).first()
    return apply(order.id) if order is not None else None


def refresh(order_id):
    order = _load(order_id)
    if order.status in FINAL_STATUSES:
        return order
    if order.last_checked_at is None or order.last_checked_at < now() - REFRESH_AFTER:
        return apply(order.id)
    return order


def cancel(user, order_id):
    _require_charge(user)
    order = _load(order_id, lock=True)
    if order.status not in ('created', 'processing'):
        raise PosError('Ese cobro ya terminó' if order.status in FINAL_STATUSES else 'Ese cobro ya se está cancelando')
    client = mercadopago.get_client(mp_settings.get_settings())
    try:
        client.cancel_order(order.mp_order_id, at_terminal=order.status == 'processing')
    except MpUnavailable:
        db.session.rollback()
        raise PosError(UNAVAILABLE)
    except MpRejected:
        db.session.rollback()
        apply(order_id)
        raise PosError('El cobro ya se está procesando en el Point: esperá el resultado')
    order.status = 'canceled' if order.status == 'created' else 'canceling'
    order.error = 'Se canceló el cobro' if order.status == 'canceled' else None
    order.updated_at = now()
    audit.record(order.sale, user, 'point_order_canceled', order_id=order.id)
    db.session.commit()
    return order


def sale_orders(sale_id):
    rows = MpPointOrder.query.filter_by(sale_id=parse_id(sale_id, 'La venta')).order_by(MpPointOrder.id).all()
    return [order_to_dict(o) for o in rows]
