from app.extensions import db
from app.models.expense import ExpenseCategory
from app.models.supplier import Supplier
from app.services.expense_fudo_linking import Linker, new_link_stats, normalize_cuit, normalize_name
from app.services.expense_fudo_parsing import CategoryRef, ProviderRef


def _linker():
    stats = new_link_stats()
    return Linker(stats), stats


def test_normalizers():
    assert normalize_name('  Molino   SUR ') == 'molino sur'
    assert normalize_name(None) == ''
    assert normalize_cuit('30-71234567-8') == '30712345678'
    assert normalize_cuit('') is None
    assert normalize_cuit(None) is None


def test_supplier_already_linked(menu_app):
    supplier = Supplier(name='Otro nombre', fudo_provider_id='7')
    db.session.add(supplier)
    db.session.commit()
    linker, stats = _linker()

    assert linker.supplier_for(ProviderRef('7', 'Molino Sur', None)) is supplier
    assert stats['suppliers_created'] == stats['suppliers_linked'] == 0


def test_supplier_matched_by_cuit_before_name(menu_app):
    by_name = Supplier(name='Molino Sur')
    by_cuit = Supplier(name='Molino del Sur SRL', cuit='30712345678')
    db.session.add_all([by_name, by_cuit])
    db.session.commit()
    linker, stats = _linker()

    result = linker.supplier_for(ProviderRef('7', 'Molino Sur', '30-71234567-8'))

    assert result is by_cuit
    assert by_cuit.fudo_provider_id == '7'
    assert stats['suppliers_linked'] == 1


def test_supplier_matched_by_normalized_name(menu_app):
    existing = Supplier(name='Molino Sur')
    db.session.add(existing)
    db.session.commit()
    linker, stats = _linker()

    assert linker.supplier_for(ProviderRef('7', '  molino   SUR ', None)) is existing
    assert existing.fudo_provider_id == '7'


def test_linked_supplier_is_not_stolen_by_name(menu_app):
    db.session.add(Supplier(name='Molino Sur', fudo_provider_id='1'))
    db.session.commit()
    linker, stats = _linker()

    created = linker.supplier_for(ProviderRef('7', 'Molino Sur', None))

    assert created.fudo_provider_id == '7'
    assert Supplier.query.count() == 2
    assert stats['suppliers_created'] == 1


def test_supplier_created_once_per_run(menu_app):
    linker, stats = _linker()

    first = linker.supplier_for(ProviderRef('7', 'Molino Sur', '30-71234567-8'))
    second = linker.supplier_for(ProviderRef('7', 'Molino Sur', '30-71234567-8'))

    assert first is second
    assert first.cuit == '30-71234567-8'
    assert Supplier.query.count() == 1
    assert stats['suppliers_created'] == 1


def test_supplier_cuit_conflict_creates_without_cuit(menu_app):
    db.session.add(Supplier(name='Molino Sur', cuit='30712345678', fudo_provider_id='1'))
    db.session.commit()
    linker, stats = _linker()

    created = linker.supplier_for(ProviderRef('7', 'Molino Norte', '30-71234567-8'))

    assert created.cuit is None
    assert created.name == 'Molino Norte'
    assert len(stats['warnings']) == 1


def test_supplier_without_name_gets_placeholder(menu_app):
    linker, _ = _linker()
    assert linker.supplier_for(ProviderRef('99', None, None)).name == 'Proveedor Fudo 99'


def test_no_provider(menu_app):
    linker, _ = _linker()
    assert linker.supplier_for(None) is None


def test_category_linked_matched_or_created(menu_app):
    linked = ExpenseCategory(name='Lo que sea', fudo_category_id='1')
    by_name = ExpenseCategory(name='Alquiler')
    db.session.add_all([linked, by_name])
    db.session.commit()
    linker, stats = _linker()

    assert linker.category_for(CategoryRef('1', 'Otro')) is linked
    assert linker.category_for(CategoryRef('2', 'ALQUILER ')) is by_name
    created = linker.category_for(CategoryRef('3', 'Materia prima'))

    assert by_name.fudo_category_id == '2'
    assert created.fudo_category_id == '3'
    assert created.expense_type == 'directo'
    assert stats['categories_linked'] == 1
    assert stats['categories_created'] == 1


def test_inactive_category_with_same_name_is_linked(menu_app):
    inactive = ExpenseCategory(name='Bebidas', is_active=False)
    db.session.add(inactive)
    db.session.commit()
    linker, _ = _linker()

    assert linker.category_for(CategoryRef('5', 'Bebidas')) is inactive
    assert inactive.is_active is False


def test_category_name_conflict_gets_suffix(menu_app):
    db.session.add(ExpenseCategory(name='Bebidas', fudo_category_id='1'))
    db.session.commit()
    linker, stats = _linker()

    created = linker.category_for(CategoryRef('5', 'Bebidas'))

    assert created.name == 'Bebidas (Fudo 5)'
    assert len(stats['warnings']) == 1


def test_missing_category_uses_default(menu_app):
    linker, _ = _linker()

    default = linker.category_for(None)

    assert default.name == 'Sin categoría'
    assert linker.category_for(None) is default
    assert ExpenseCategory.query.count() == 1
