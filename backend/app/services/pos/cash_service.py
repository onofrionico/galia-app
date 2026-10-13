"""Caja: sesiones, movimientos de efectivo y arqueo.

Lo esperado por medio de pago en una sesión = pagos registrados en ella − pagos anulados en ella. Así una
anulación posterior al cierre afecta a la sesión en la que ocurre y una sesión cerrada nunca cambia. Los
movimientos (fondo, gastos, retiros, ingresos) se aplican al primer medio de efectivo por `position`.
"""
from collections import namedtuple
from decimal import Decimal

from sqlalchemy import func

from app.extensions import db
from app.models import Expense, ExpenseCategory, Supplier
from app.models.pos import (ACTIVE_SALE_STATUSES, CashEvent, CashMovement, CashRegister, CashSession,
                            PaymentMethod, PosPayment, PosSale)
from app.services.pos import pricing
from app.services.pos.audit import _jsonable
from app.services.pos.common import MAX_MONEY, now, parse_id, require_reason
from app.services.pos.errors import PosError, bad_request, forbidden, not_found
from app.utils.timezone_utils import get_current_date_argentina
from app.utils.validation import parse_decimal

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


def current_session_id():
    """La única sesión abierta, o None si no hay ninguna o hay más de una (varias cajas abiertas)."""
    ids = [row.id for row in db.session.query(CashSession.id).filter_by(status='open').limit(2).all()]
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
                          opening_float=amount)
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
    if kind == 'expense':
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
