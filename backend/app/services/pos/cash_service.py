"""Caja: sesiones, movimientos de efectivo y arqueo.

Lo esperado por medio de pago en una sesión = pagos registrados en ella − pagos anulados en ella. Así una
anulación posterior al cierre afecta a la sesión en la que ocurre y una sesión cerrada nunca cambia. Los
movimientos (fondo, gastos, retiros, ingresos) se aplican al primer medio de efectivo por `position`.
"""
from collections import namedtuple
from datetime import datetime, time, timedelta
from decimal import Decimal
from math import ceil

import pytz
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Expense, ExpenseCategory, Supplier, User
from app.models.pos import (ACTIVE_SALE_STATUSES, CashEvent, CashMovement, CashRegister, CashSession,
                            CashSessionCount, PaymentMethod, PosPayment, PosSale)
from app.services import cutover
from app.services.pos import pricing
from app.services.pos.audit import _jsonable
from app.services.pos.common import MAX_MONEY, display_name, now, parse_id, require_reason
from app.services.pos.errors import PosError, bad_request, forbidden, not_found
from app.utils.timezone_utils import ARGENTINA_TZ, get_current_date_argentina
from app.utils.validation import clean_str, parse_decimal

MOVEMENT_KINDS = ('expense', 'withdrawal', 'deposit')
CASH_SIGN = {'opening_float': 1, 'deposit': 1, 'expense': -1, 'withdrawal': -1}
ZERO = Decimal('0.00')

Line = namedtuple('Line', 'method collected cancelled expected')


def _money(value, label, minimum):
    return pricing.money(parse_decimal(value, label, minimum=minimum, maximum=MAX_MONEY))


def _event(register_id, session_id, user, event_kind, **payload):
    db.session.add(CashEvent(register_id=register_id, session_id=session_id, user_id=user.id, kind=event_kind,
                             payload=_jsonable(payload), created_at=now()))


def _require_admin(user, message):
    if user.role != 'admin':
        raise forbidden(message)


def current_session_id(practice=False):
    """La única sesión abierta (real o de práctica, según `practice`), o None si no hay ninguna o hay más de una.

    Un pago real nunca se cuelga de una caja de práctica ni al revés.

    Toma un lock compartido (FOR SHARE) sobre la sesión: un cierre concurrente (FOR UPDATE) espera a que el cobro
    o la anulación termine, y si el cierre ganó, la fila se reevalúa ya cerrada y no se adjunta. SQLite lo ignora.
    """
    rows = (db.session.query(CashSession.id).filter_by(status='open', is_practice=bool(practice))
            .with_for_update(read=True).limit(2).all())
    ids = [row.id for row in rows]
    return ids[0] if len(ids) == 1 else None


def _load_register(register_id, lock=False):
    query = CashRegister.query.filter_by(id=parse_id(register_id, 'La caja'))
    if lock:
        query = query.with_for_update().populate_existing()
    register = query.first()
    if register is None:
        raise not_found('La caja no existe')
    return register


def load_session(session_id, lock=False):
    query = CashSession.query.filter_by(id=parse_id(session_id, 'La sesión de caja'))
    if lock:
        query = query.with_for_update().populate_existing()
    session = query.first()
    if session is None:
        raise not_found('La sesión de caja no existe')
    return session


def open_session(user, register_id, opening_float):
    amount = _money(opening_float, 'El fondo inicial', Decimal('0'))
    register = _load_register(register_id, lock=True)
    if not register.is_active:
        raise bad_request('La caja no está activa')
    if CashSession.query.filter_by(register_id=register.id, status='open').first() is not None:
        raise PosError('La caja ya está abierta')
    session = CashSession(register_id=register.id, status='open', opened_at=now(), opened_by=user.id,
                          opening_float=amount, is_practice=cutover.practice_mode())
    db.session.add(session)
    db.session.flush()
    db.session.add(CashMovement(session_id=session.id, kind='opening_float', amount=amount, created_by=user.id,
                                created_at=now()))
    _event(register.id, session.id, user, 'opened', opening_float=amount)
    db.session.commit()
    return session


def _create_expense(user, session, amount, reason, category_id, supplier_id):
    category = db.session.get(ExpenseCategory, parse_id(category_id, 'La categoría'))
    if category is None or not category.is_active:
        raise bad_request('La categoría de gasto no existe')
    supplier = None
    if supplier_id is not None:
        supplier = db.session.get(Supplier, parse_id(supplier_id, 'El proveedor'))
        if supplier is None:
            raise bad_request('El proveedor no existe')
    expense = Expense(fecha=get_current_date_argentina(), importe=amount, comentario=reason,
                      category_id=category.id, supplier_id=supplier.id if supplier else None,
                      proveedor=supplier.name[:200] if supplier else None, de_caja=True,
                      caja=session.register.name[:100], medio_pago='Efectivo', estado_pago='Pagado',
                      creado_por=user.email[:100], cancelado=False)
    db.session.add(expense)
    db.session.flush()
    return expense


def add_movement(user, session_id, kind, amount, reason, category_id=None, supplier_id=None):
    if kind not in MOVEMENT_KINDS:
        raise bad_request('El tipo de movimiento es inválido')
    session = load_session(session_id, lock=True)
    if session.status != 'open':
        raise PosError('La caja está cerrada')
    amount = _money(amount, 'El monto', Decimal('0.01'))
    reason = require_reason(reason)
    movement = CashMovement(session_id=session.id, kind=kind, amount=amount, reason=reason, created_by=user.id,
                            created_at=now())
    if kind == 'expense' and not session.is_practice:  # un gasto de práctica no crea un gasto real
        movement.expense_id = _create_expense(user, session, amount, reason, category_id, supplier_id).id
    db.session.add(movement)
    db.session.flush()
    _event(session.register_id, session.id, user, 'movement_added', movement_id=movement.id, kind=kind,
           amount=amount, reason=reason)
    db.session.commit()
    db.session.refresh(session)
    return session


def cancel_movement(user, movement_id, reason):
    _require_admin(user, 'Solo un administrador anula movimientos de caja')
    reason = require_reason(reason)
    movement = db.session.get(CashMovement, parse_id(movement_id, 'El movimiento'))
    if movement is None:
        raise not_found('El movimiento no existe')
    session = load_session(movement.session_id, lock=True)
    db.session.refresh(movement)
    if movement.kind == 'opening_float':
        raise PosError('El fondo inicial no se anula')
    if session.status != 'open':
        raise PosError('La caja está cerrada; reabrila para anular el movimiento')
    if movement.cancelled_at is not None:
        raise PosError('El movimiento ya está anulado')
    movement.cancelled_at = now()
    movement.cancelled_by = user.id
    movement.cancel_reason = reason
    if movement.expense_id is not None:
        db.session.get(Expense, movement.expense_id).cancelado = True
    _event(session.register_id, session.id, user, 'movement_cancelled', movement_id=movement.id, reason=reason)
    db.session.commit()
    db.session.refresh(session)
    return session


def _payments_by_method(session_id, column):
    rows = (db.session.query(PosPayment.payment_method_id, func.sum(PosPayment.amount))
            .filter(column == session_id).group_by(PosPayment.payment_method_id).all())
    return {method_id: pricing.money(Decimal(str(total or 0))) for method_id, total in rows}


def _movement_totals(session):
    totals = {kind: ZERO for kind in CASH_SIGN}
    for movement in session.movements:
        if movement.cancelled_at is None:
            totals[movement.kind] += movement.amount
    return totals


def expected_lines(session):
    """Una línea por medio de pago activo o con pagos en la sesión. El efectivo suma los movimientos."""
    collected = _payments_by_method(session.id, PosPayment.cash_session_id)
    cancelled = _payments_by_method(session.id, PosPayment.cancel_cash_session_id)
    used = set(collected) | set(cancelled)
    methods = [m for m in PaymentMethod.query.order_by(PaymentMethod.position, PaymentMethod.id).all()
               if m.is_active or m.id in used]
    totals = _movement_totals(session)
    movement_net = sum((CASH_SIGN[kind] * amount for kind, amount in totals.items()), ZERO)
    lines, cash_done = [], False
    for method in methods:
        got, back = collected.get(method.id, ZERO), cancelled.get(method.id, ZERO)
        expected = got - back
        if method.kind == 'cash' and not cash_done:
            expected += movement_net
            cash_done = True
        lines.append(Line(method, got, back, pricing.money(expected)))
    return lines


def open_sales_count():
    return PosSale.query.filter(PosSale.status.in_(ACTIVE_SALE_STATUSES)).count()


def session_summary(session):
    lines = expected_lines(session)
    totals = _movement_totals(session)
    cash = next((line for line in lines if line.method.kind == 'cash'), None)
    sales = cash.collected if cash else ZERO
    back = cash.cancelled if cash else ZERO
    expected_cash = (totals['opening_float'] + sales - back - totals['expense'] - totals['withdrawal']
                     + totals['deposit'])
    return {
        'methods': [{'payment_method_id': line.method.id, 'method_name': line.method.name, 'kind': line.method.kind,
                     'collected': float(line.collected), 'cancelled': float(line.cancelled),
                     'expected': float(line.expected)} for line in lines],
        'cash': {'payment_method_id': cash.method.id if cash else None,
                 'opening_float': float(totals['opening_float']), 'sales': float(sales), 'cancelled': float(back),
                 'expenses': float(totals['expense']), 'withdrawals': float(totals['withdrawal']),
                 'deposits': float(totals['deposit']), 'expected': float(pricing.money(expected_cash))},
        'collected_net': float(sum((line.collected - line.cancelled for line in lines), ZERO)),
        'open_sales': open_sales_count(),
    }


def close_session(user, session_id, counts, note):
    session = load_session(session_id, lock=True)
    if session.status != 'open':
        raise PosError('La caja ya está cerrada')
    open_sales = open_sales_count()
    if open_sales:
        raise PosError(f'Hay {open_sales} ventas abiertas. Cobralas o anulalas antes de cerrar', open_sales=open_sales)
    if not isinstance(counts, list):
        raise bad_request('Los conteos son inválidos')
    lines = {line.method.id: line for line in expected_lines(session)}
    counted = {}
    for entry in counts:
        if not isinstance(entry, dict):
            raise bad_request('Los conteos son inválidos')
        method_id = parse_id(entry.get('payment_method_id'), 'El medio de pago')
        if method_id not in lines:
            method = db.session.get(PaymentMethod, method_id)
            if method is None:
                raise bad_request('El medio de pago no existe')
            lines[method_id] = Line(method, ZERO, ZERO, ZERO)
        counted[method_id] = _money(entry.get('counted'), f'Lo contado en {lines[method_id].method.name}',
                                    Decimal('0'))
    cash = next((line for line in lines.values() if line.method.kind == 'cash'), None)
    if cash is not None and cash.method.id not in counted:
        raise bad_request('Cargá lo contado en efectivo')
    note = clean_str(note, 500)
    rows = []
    for method_id, line in lines.items():
        value = counted.get(method_id, line.expected)
        if line.expected == 0 and value == 0 and method_id not in counted and line.method.kind != 'cash':
            continue
        rows.append(CashSessionCount(payment_method_id=method_id, method_name=line.method.name,
                                     expected=line.expected, counted=value, difference=value - line.expected))
    if any(row.difference != 0 for row in rows) and not note:
        raise bad_request('Explicá la diferencia en la nota')
    session.counts = rows
    session.status = 'closed'
    session.closed_at = now()
    session.closed_by = user.id
    session.closing_note = note
    _event(session.register_id, session.id, user, 'closed',
           differences={row.method_name: row.difference for row in rows}, note=note)
    db.session.commit()
    db.session.refresh(session)
    return session


def reopen_session(user, session_id, reason):
    _require_admin(user, 'Solo un administrador reabre una caja')
    reason = require_reason(reason)
    session = load_session(session_id, lock=True)
    if session.status != 'closed':
        raise PosError('La caja no está cerrada')
    other = (CashSession.query.filter(CashSession.register_id == session.register_id, CashSession.status == 'open',
                                      CashSession.id != session.id).first())
    if other is not None:
        raise PosError('La caja ya tiene otra sesión abierta')
    session.counts.clear()
    session.status = 'open'
    session.closed_at = None
    session.closed_by = None
    session.closing_note = None
    _event(session.register_id, session.id, user, 'reopened', reason=reason)
    db.session.commit()
    db.session.refresh(session)
    return session


def argentina_day_bounds(from_date, to_date):
    """Desde el inicio de `from_date` hasta el inicio del día siguiente a `to_date`, en hora argentina, en UTC."""
    def to_utc(day):
        local = ARGENTINA_TZ.localize(datetime.combine(day, time.min))
        return local.astimezone(pytz.utc).replace(tzinfo=None)
    return to_utc(from_date), to_utc(to_date + timedelta(days=1))


def _person(user):
    return {'id': user.id, 'name': display_name(user)} if user is not None else None


def _net_by_session(session_ids):
    if not session_ids:
        return {}
    got = dict(db.session.query(PosPayment.cash_session_id, func.sum(PosPayment.amount))
               .filter(PosPayment.cash_session_id.in_(session_ids)).group_by(PosPayment.cash_session_id).all())
    back = dict(db.session.query(PosPayment.cancel_cash_session_id, func.sum(PosPayment.amount))
                .filter(PosPayment.cancel_cash_session_id.in_(session_ids))
                .group_by(PosPayment.cancel_cash_session_id).all())
    return {sid: pricing.money(Decimal(str(got.get(sid) or 0)) - Decimal(str(back.get(sid) or 0)))
            for sid in session_ids}


def list_sessions(from_date, to_date, register_id=None, page=1, per_page=50):
    start, end = argentina_day_bounds(from_date, to_date)
    query = CashSession.query.filter(CashSession.opened_at >= start, CashSession.opened_at < end,
                                     CashSession.is_practice.is_(False))
    if register_id is not None:
        query = query.filter(CashSession.register_id == register_id)
    total = query.count()
    sessions = (query.options(selectinload(CashSession.counts), selectinload(CashSession.register))
                .order_by(CashSession.opened_at.desc(), CashSession.id.desc())
                .offset((page - 1) * per_page).limit(per_page).all())
    net = _net_by_session([s.id for s in sessions])
    rows = []
    for session in sessions:
        cash_count = next((c for c in session.counts
                           if db.session.get(PaymentMethod, c.payment_method_id).kind == 'cash'), None)
        rows.append({
            'id': session.id, 'register': {'id': session.register.id, 'name': session.register.name},
            'status': session.status, 'opened_at': session.opened_at.isoformat(), 'opened_by': _person(session.opener),
            'closed_at': session.closed_at.isoformat() if session.closed_at else None,
            'closed_by': _person(session.closer), 'collected_net': float(net.get(session.id, ZERO)),
            'cash_difference': float(cash_count.difference) if cash_count is not None else None,
        })
    return {'sessions': rows, 'total': total, 'page': page, 'pages': max(1, ceil(total / per_page))}


def unassigned_payments(from_date, to_date):
    start, end = argentina_day_bounds(from_date, to_date)
    payments = (PosPayment.query.options(selectinload(PosPayment.sale))
                .join(PosSale, PosPayment.sale_id == PosSale.id)
                .filter(PosPayment.cash_session_id.is_(None), PosPayment.created_at >= start,
                        PosPayment.created_at < end, PosSale.is_practice.is_(False))
                .order_by(PosPayment.created_at, PosPayment.id).all())
    rows = []
    for payment in payments:
        sale = payment.sale
        creator = db.session.get(User, payment.created_by)
        rows.append({
            'id': payment.id, 'sale_id': sale.id, 'sale_number': sale.number,
            'table': sale.table.label if sale.table else None, 'method_name': payment.method_name,
            'amount': float(payment.amount), 'created_by': _person(creator), 'created_at': payment.created_at.isoformat(),
            'cancelled': payment.cancelled_at is not None,
        })
    return rows
