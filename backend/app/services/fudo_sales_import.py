"""Importación de toda la historia de ventas de Fudo, mes por mes, con control por mes.

Idempotente (las ventas se identifican por su id de Fudo y sus ítems se reemplazan) y reanudable
(cada mes se commitea; los meses `done` se saltean, salvo los dos últimos, que pueden seguir cambiando).
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal

import pytz

from app.extensions import db
from app.models import FudoImportMonth, Sale
from app.services.sales_sync_service import apply_fudo_sales
from app.utils.timezone_utils import ARGENTINA_TZ, get_current_date_argentina

STATES = ('CLOSED', 'CANCELED')
ZERO = Decimal('0.00')


def current_month():
    return get_current_date_argentina().replace(day=1)


def _next_month(month):
    return date(month.year + (month.month == 12), month.month % 12 + 1, 1)


def _start_utc(day):
    """00:00 del día en Argentina, en UTC."""
    return ARGENTINA_TZ.localize(datetime.combine(day, time.min)).astimezone(pytz.utc)


def _month_bounds(month):
    """(inicio, fin) del mes de Argentina en UTC ISO, para filtrar por createdAt."""
    fmt = '%Y-%m-%dT%H:%M:%SZ'
    end = _start_utc(_next_month(month)) - timedelta(seconds=1)
    return _start_utc(month).strftime(fmt), end.strftime(fmt)


def _total(value):
    return Decimal(str(value or 0)).quantize(Decimal('0.01'))


def import_month(client, month, run_id=None):
    """Trae de Fudo las ventas cerradas y anuladas del mes y las aplica en `sales`/`sale_items`."""
    month = month.replace(day=1)
    start, end = _month_bounds(month)
    payload = client.get_all_sales_with_included(start_date=start, end_date=end, states=STATES)
    raw_sales = payload.get('data') or []

    ids = []
    for raw in raw_sales:
        try:
            ids.append(int(raw.get('id')))
        except (TypeError, ValueError):
            continue
    before = {s.external_id: (_total(s.total), s.estado) for s in Sale.query.filter(Sale.external_id.in_(ids or [0]))}

    results = apply_fudo_sales(payload, update_existing=True)

    after = {s.external_id: (_total(s.total), s.estado) for s in Sale.query.filter(Sale.external_id.in_(ids or [0]))}
    changed = sum(1 for external_id, values in before.items() if after.get(external_id) != values)

    closed = [raw for raw in raw_sales if (raw.get('attributes') or {}).get('saleState') == 'CLOSED']
    closed_ids = []
    for raw in closed:
        try:
            closed_ids.append(int(raw.get('id')))
        except (TypeError, ValueError):
            continue
    fudo_total = sum((_total((raw.get('attributes') or {}).get('total')) for raw in closed), ZERO)
    stored = Sale.query.filter(Sale.external_id.in_(closed_ids or [0]), Sale.estado == 'Cerrada').all()
    galia_total = sum((_total(s.total) for s in stored), ZERO)

    record = db.session.get(FudoImportMonth, month) or FudoImportMonth(month=month)
    record.status = 'done'
    record.fudo_count, record.fudo_total = len(closed), fudo_total
    record.galia_count, record.galia_total = len(stored), galia_total
    record.changed = changed
    record.errors = results['errors']
    record.imported_at = datetime.utcnow()
    record.run_id = run_id
    db.session.add(record)
    db.session.commit()
    return {**record.to_dict(), 'created': results['imported'], 'updated': results['updated']}


def import_range(client, start, end, run_id=None):
    """Importa cada mes que toca el rango [start, end]."""
    months, month = [], start.replace(day=1)
    while month <= end:
        months.append(import_month(client, month, run_id))
        month = _next_month(month)
    return {'months': months, 'errors': sum(len(m['errors']) for m in months),
            'changed_months': [m['month'] for m in months if m['changed']]}


def import_history(client, from_month=None, force=False, run_id=None):
    """Desde `from_month` (o la primera venta de Fudo) hasta el mes actual."""
    last = current_month()
    if from_month is None:
        first = client.first_sale_date()
        if first is None:
            return {'months': [], 'errors': 0, 'changed_months': []}
        from_month = first
    month = from_month.replace(day=1)
    recent = {last, (last - timedelta(days=1)).replace(day=1)}
    # Un mes `done` se saltea solo si coincidió con Fudo y no tuvo errores; si no, se reintenta.
    settled = {m.month for m in FudoImportMonth.query.filter_by(status='done') if m.matches and not m.errors}
    months = []
    while month <= last:
        if force or month in recent or month not in settled:
            months.append(import_month(client, month, run_id))
            if run_id is not None:
                from app.services import fudo_sync_runs
                fudo_sync_runs.heartbeat(run_id)
        month = _next_month(month)
    return {'months': months, 'errors': sum(len(m['errors']) for m in months),
            'changed_months': [m['month'] for m in months if m['changed']]}
