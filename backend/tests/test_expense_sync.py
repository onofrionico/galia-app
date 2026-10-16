from datetime import date
from decimal import Decimal

from app.extensions import db
from app.models.expense import Expense, ExpenseCategory
from app.models.supplier import Supplier
from app.services import expense_sync_service
from fudo_expense_fakes import FakeExpensesClient, fudo_expense, fudo_expense_category, fudo_provider

INCLUDED = [fudo_provider(7, 'Molino Sur', cuit='30-71234567-8'), fudo_expense_category(3, 'Insumos')]


def _sync(data, included=INCLUDED):
    client = FakeExpensesClient(data=data, included=included)
    stats = expense_sync_service.sync_expenses(client, '2026-10-01', '2026-10-31')
    return stats, client


def test_creates_enriched_expenses(menu_app):
    stats, client = _sync([
        fudo_expense(101, amount='1500', provider_id=7, category_id=3),
        fudo_expense(102, amount='800', provider_id=7, category_id=3),
    ])

    assert client.calls == [('2026-10-01', '2026-10-31')]
    assert stats['fetched'] == 2
    assert stats['created'] == 2
    assert stats['suppliers_created'] == 1
    assert stats['categories_created'] == 1
    expense = Expense.query.filter_by(external_id=101).one()
    assert expense.source == 'fudo'
    assert expense.creado_por == 'Fudo Sync'
    assert expense.supplier.name == 'Molino Sur'
    assert expense.category_rel.name == 'Insumos'
    assert expense.importe == Decimal('1500.00')
    assert Supplier.query.count() == 1


def test_second_run_is_idempotent(menu_app):
    data = [fudo_expense(101, provider_id=7, category_id=3)]
    _sync(data)

    stats, _ = _sync(data)

    assert stats['created'] == 0
    assert stats['updated'] == 0
    assert stats['unchanged'] == 1
    assert Expense.query.count() == 1


def test_resync_updates_fudo_fields(menu_app):
    _sync([fudo_expense(101, amount='1000', status='PENDING', provider_id=7, category_id=3)])

    stats, _ = _sync([fudo_expense(101, amount='1200', status='CANCELLED', provider_id=7, category_id=3)])

    expense = Expense.query.filter_by(external_id=101).one()
    assert stats['updated'] == 1
    assert expense.importe == Decimal('1200.00')
    assert expense.estado_pago == 'Cancelado'
    assert expense.cancelado is True


def test_resync_respects_manual_overrides(menu_app):
    _sync([fudo_expense(101, provider_id=7, category_id=3)])
    manual_category = ExpenseCategory(name='Corregida')
    manual_supplier = Supplier(name='Proveedor corregido')
    db.session.add_all([manual_category, manual_supplier])
    db.session.flush()
    expense = Expense.query.filter_by(external_id=101).one()
    expense.category_id = manual_category.id
    expense.supplier_id = manual_supplier.id
    expense.category_overridden = True
    expense.supplier_overridden = True
    db.session.commit()

    _sync([fudo_expense(101, amount='999', provider_id=7, category_id=3)])

    expense = Expense.query.filter_by(external_id=101).one()
    assert expense.category_id == manual_category.id
    assert expense.supplier_id == manual_supplier.id
    assert expense.importe == Decimal('999.00')


def test_resync_recalculates_non_overridden_links(menu_app):
    _sync([fudo_expense(101, category_id=3)])
    other = ExpenseCategory(name='Otra')
    db.session.add(other)
    db.session.commit()
    insumos = ExpenseCategory.query.filter_by(name='Insumos').one()
    insumos.fudo_category_id = None
    db.session.flush()
    other.fudo_category_id = '3'
    db.session.commit()

    _sync([fudo_expense(101, category_id=3)])

    assert Expense.query.filter_by(external_id=101).one().category_id == other.id


def test_csv_imported_expense_is_adopted(menu_app):
    category = ExpenseCategory(name='Sin categoría')
    db.session.add(category)
    db.session.flush()
    db.session.add(Expense(external_id=101, fecha=date(2026, 10, 1), importe=Decimal('1'),
                           category_id=category.id, source='galia'))
    db.session.commit()

    stats, _ = _sync([fudo_expense(101, amount='50', provider_id=7, category_id=3)])

    expense = Expense.query.filter_by(external_id=101).one()
    assert stats['updated'] == 1
    assert expense.source == 'fudo'
    assert expense.supplier.name == 'Molino Sur'


def test_manual_expenses_are_never_touched(menu_app):
    category = ExpenseCategory(name='Alquiler')
    db.session.add(category)
    db.session.flush()
    manual = Expense(fecha=date(2026, 10, 5), importe=Decimal('300000'), category_id=category.id,
                     proveedor='Inmobiliaria', comentario='Alquiler octubre')
    db.session.add(manual)
    db.session.commit()

    _sync([fudo_expense(101, provider_id=7, category_id=3)])

    db.session.refresh(manual)
    assert manual.source == 'galia'
    assert manual.external_id is None
    assert manual.proveedor == 'Inmobiliaria'
    assert manual.supplier_id is None
    assert Expense.query.count() == 2


def test_bad_expense_is_reported_and_others_continue(menu_app):
    stats, _ = _sync([
        fudo_expense(101, amount=None, provider_id=8),
        fudo_expense(102, date=None),
        fudo_expense(103, provider_id=7, category_id=3),
    ], included=INCLUDED + [fudo_provider(8, 'Proveedor del gasto roto')])

    assert stats['created'] == 1
    assert [e['expense_id'] for e in stats['errors']] == ['101', '102']
    assert 'importe' in stats['errors'][0]['error']
    assert Expense.query.count() == 1
    assert Supplier.query.filter_by(fudo_provider_id='8').count() == 0  # se deshizo con el savepoint
    assert stats['suppliers_created'] == 1  # solo Molino Sur; el del gasto roto no cuenta


def test_supplier_cached_after_failed_expense_still_works(menu_app):
    stats, _ = _sync([
        fudo_expense(101, amount=None, provider_id=7),
        fudo_expense(102, provider_id=7, category_id=3),
    ])

    assert stats['created'] == 1
    assert Expense.query.filter_by(external_id=102).one().supplier.name == 'Molino Sur'
    assert Supplier.query.count() == 1


def test_commits_in_batches(menu_app, monkeypatch):
    commits = []
    original_commit = db.session.commit
    monkeypatch.setattr(expense_sync_service, 'BATCH_SIZE', 2)
    monkeypatch.setattr(db.session, 'commit', lambda: (commits.append(1), original_commit())[1])

    _sync([fudo_expense(i) for i in range(1, 6)])

    assert len(commits) == 3  # tras el 2, tras el 4 y el final


def test_resync_keeps_existing_values_when_fudo_does_not_send_them(menu_app):
    category = ExpenseCategory(name='Sin categoría')
    db.session.add(category)
    db.session.flush()
    db.session.add(Expense(external_id=101, fecha=date(2026, 10, 1), importe=Decimal('1'), category_id=category.id,
                           source='fudo', caja='Caja principal', de_caja=True, medio_pago='Efectivo',
                           tipo_comprobante='Factura A', numero_comprobante='0001-1', numero_fiscal='30712345678',
                           proveedor='Molino Sur'))
    db.session.commit()

    _sync([fudo_expense(101, amount='1')], included=[])

    expense = Expense.query.filter_by(external_id=101).one()
    assert expense.caja == 'Caja principal'
    assert expense.de_caja is True
    assert expense.medio_pago == 'Efectivo'
    assert expense.tipo_comprobante == 'Factura A'
    assert expense.numero_comprobante == '0001-1'
    assert expense.numero_fiscal == '30712345678'
    assert expense.proveedor == 'Molino Sur'


def test_new_expense_without_cash_flag_defaults_to_false(menu_app):
    _sync([fudo_expense(101)], included=[])

    assert Expense.query.filter_by(external_id=101).one().de_caja is False


def test_errors_total_counts_beyond_the_listed_cap(menu_app):
    stats, _ = _sync([fudo_expense(i, date=None) for i in range(1, 61)], included=[])

    assert len(stats['errors']) == 50
    assert stats['errors_total'] == 60
    assert stats['created'] == 0
