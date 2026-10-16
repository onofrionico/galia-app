"""Resuelve el Supplier y la ExpenseCategory de Galia para un proveedor/categoría de Fudo."""
import re

from app.extensions import db
from app.models.expense import ExpenseCategory, infer_expense_type
from app.models.supplier import Supplier

DEFAULT_CATEGORY_NAME = 'Sin categoría'
MAX_LISTED = 50


def normalize_name(value):
    return ' '.join((value or '').split()).casefold()


def normalize_cuit(value):
    digits = re.sub(r'\D', '', value or '')
    return digits or None


def add_capped(items, item, limit=MAX_LISTED):
    if len(items) < limit:
        items.append(item)


def new_link_stats():
    return {'suppliers_created': 0, 'suppliers_linked': 0, 'categories_created': 0,
            'categories_linked': 0, 'warnings': []}


class Linker:
    """Caché por corrida: un mismo id de Fudo resuelve siempre al mismo objeto. Solo hace flush."""

    def __init__(self, stats):
        self.stats = stats
        self.reset()

    def reset(self):
        self._suppliers = {}
        self._categories = {}
        self._default_category = None

    def supplier_for(self, ref):
        if ref is None:
            return None
        if ref.fudo_id not in self._suppliers:
            self._suppliers[ref.fudo_id] = self._resolve_supplier(ref)
        return self._suppliers[ref.fudo_id]

    def category_for(self, ref):
        if ref is None:
            return self._default()
        if ref.fudo_id not in self._categories:
            self._categories[ref.fudo_id] = self._resolve_category(ref)
        return self._categories[ref.fudo_id]

    def _resolve_supplier(self, ref):
        supplier = Supplier.query.filter_by(fudo_provider_id=ref.fudo_id).first()
        if supplier:
            return supplier

        cuit = normalize_cuit(ref.cuit)
        name = normalize_name(ref.name)
        unlinked = Supplier.query.filter(Supplier.fudo_provider_id.is_(None)).all()
        match = next((s for s in unlinked if cuit and normalize_cuit(s.cuit) == cuit), None)
        if match is None and name:
            match = next((s for s in unlinked if normalize_name(s.name) == name), None)
        if match:
            match.fudo_provider_id = ref.fudo_id
            self.stats['suppliers_linked'] += 1
            db.session.flush()
            return match

        new_cuit = ref.cuit
        if cuit and any(normalize_cuit(s.cuit) == cuit for s in Supplier.query.filter(Supplier.cuit.isnot(None))):
            new_cuit = None
            add_capped(self.stats['warnings'],
                       f'El CUIT {ref.cuit} del proveedor de Fudo {ref.fudo_id} ya pertenece a otro proveedor; '
                       'se creó sin CUIT')
        supplier = Supplier(name=(ref.name or '').strip() or f'Proveedor Fudo {ref.fudo_id}',
                            cuit=new_cuit, fudo_provider_id=ref.fudo_id)
        db.session.add(supplier)
        db.session.flush()
        self.stats['suppliers_created'] += 1
        return supplier

    def _resolve_category(self, ref):
        category = ExpenseCategory.query.filter_by(fudo_category_id=ref.fudo_id).first()
        if category:
            return category

        name = (ref.name or '').strip() or f'Categoría Fudo {ref.fudo_id}'
        wanted = normalize_name(name)
        all_categories = ExpenseCategory.query.all()
        match = next((c for c in all_categories if c.fudo_category_id is None and normalize_name(c.name) == wanted), None)
        if match:
            match.fudo_category_id = ref.fudo_id
            self.stats['categories_linked'] += 1
            db.session.flush()
            return match

        if any(normalize_name(c.name) == wanted for c in all_categories):
            add_capped(self.stats['warnings'],
                       f'Ya existe una categoría "{name}" vinculada a otra de Fudo; se creó "{name} (Fudo {ref.fudo_id})"')
            name = f'{name} (Fudo {ref.fudo_id})'
        category = ExpenseCategory(name=name, expense_type=infer_expense_type(name), is_active=True,
                                   fudo_category_id=ref.fudo_id)
        db.session.add(category)
        db.session.flush()
        self.stats['categories_created'] += 1
        return category

    def _default(self):
        if self._default_category is None:
            category = ExpenseCategory.query.filter_by(name=DEFAULT_CATEGORY_NAME).first()
            if category is None:
                category = ExpenseCategory(name=DEFAULT_CATEGORY_NAME, expense_type='indirecto', is_active=True)
                db.session.add(category)
                db.session.flush()
            self._default_category = category
        return self._default_category
