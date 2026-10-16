"""Importa/actualiza gastos desde Fudo con proveedor y categoría vinculados (ver spec 2026-10-15)."""
import logging

from app.extensions import db
from app.models.expense import Expense
from app.services.expense_fudo_linking import Linker, add_capped, new_link_stats
from app.services.expense_fudo_parsing import index_included, parse_expense

logger = logging.getLogger(__name__)

BATCH_SIZE = 200
LINK_COUNTERS = ('suppliers_created', 'suppliers_linked', 'categories_created', 'categories_linked')
# Campos de enriquecimiento: si Fudo no los manda (None) se conserva lo que ya había (p. ej. lo del CSV).
KEEP_WHEN_MISSING = ('caja', 'de_caja', 'medio_pago', 'tipo_comprobante', 'numero_comprobante',
                     'numero_fiscal', 'proveedor')


def sync_expenses(client, start_date, end_date):
    payload = client.get_all_expenses_with_included(start_date=start_date, end_date=end_date)
    expenses = payload.get('data', [])
    index = index_included(payload.get('included', []))
    stats = {'fetched': len(expenses), 'created': 0, 'updated': 0, 'unchanged': 0, 'errors': [],
             **new_link_stats()}
    linker = Linker(stats)

    for position, raw in enumerate(expenses, start=1):
        counters = {key: stats[key] for key in LINK_COUNTERS}
        try:
            with db.session.begin_nested():
                _upsert(parse_expense(raw, index), linker, stats)
        except Exception as exc:  # un gasto roto no corta la corrida
            linker.reset()  # lo creado dentro del savepoint se deshizo
            stats.update(counters)
            logger.warning('Gasto de Fudo %s no importado: %s', raw.get('id'), exc)
            add_capped(stats['errors'], {'expense_id': raw.get('id'), 'error': str(exc)})
        if position % BATCH_SIZE == 0:
            db.session.commit()

    db.session.commit()
    return stats


def _upsert(parsed, linker, stats):
    supplier = linker.supplier_for(parsed.provider)
    category = linker.category_for(parsed.category)
    supplier_id = supplier.id if supplier else None

    expense = Expense.query.filter_by(external_id=parsed.external_id).first()
    if expense is None:
        fields = {k: v for k, v in parsed.fields.items() if not (k in KEEP_WHEN_MISSING and v is None)}
        db.session.add(Expense(external_id=parsed.external_id, source='fudo', creado_por='Fudo Sync',
                               supplier_id=supplier_id, category_id=category.id, **fields))
        db.session.flush()
        stats['created'] += 1
        return

    changed = False
    for field, value in parsed.fields.items():
        if value is None and field in KEEP_WHEN_MISSING:
            continue
        if getattr(expense, field) != value:
            setattr(expense, field, value)
            changed = True
    if not expense.supplier_overridden and expense.supplier_id != supplier_id:
        expense.supplier_id = supplier_id
        changed = True
    if not expense.category_overridden and expense.category_id != category.id:
        expense.category_id = category.id
        changed = True
    if expense.source != 'fudo':
        expense.source = 'fudo'
        changed = True
    db.session.flush()
    stats['updated' if changed else 'unchanged'] += 1
