# Carta: categorías desde Fudo + grupos — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Las categorías de la carta pasan a venir de Fudo (y cada ítem toma la suya automáticamente), la sync crea ítems ocultos por cada producto nuevo, y se agregan "grupos" de presentación con carta pública en dos niveles y título de categoría opcional.

**Architecture:** Se extiende el feature "Carta digital" ya mergeado. Backend Flask: migración nueva, `menu_sync_service` crea/actualiza categorías e ítems, nuevas rutas de grupos/merge/ignore, snapshot `menu.json` v2 agrupado. Admin React: pestaña Grupos, lista agrupada, modal de ítem sin categoría editable, bandeja "Nuevos y alertas". `menu-site`: acepta v1 y v2, navegación por grupos.

**Tech Stack:** Flask + SQLAlchemy + Alembic + pytest (backend); React 18 + Vite + Tailwind (frontend admin, sin tests/ESLint → verificar con `npm run build`); React + Vite + Vitest (`menu-site/`).

**Spec:** `docs/superpowers/specs/2026-10-08-carta-grupos-fudo-design.md`
**Branch:** `feature/carta-grupos-fudo` (sale de `main` con el PR #3 mergeado)

**Convenciones del repo (ya usadas en el feature anterior):**
- Tests backend: `cd backend && python -m pytest <archivos> -q -p no:cacheprovider`. Fixtures en `backend/tests/conftest.py`: `menu_app` (SQLite en memoria + app context), `menu_client`, `storage` (FakeStorage), `admin_headers`, `employee_headers`. Fakes en `backend/tests/menu_fakes.py`: `FakeFudoClient(products, categories)`, `fudo_product(id, name, price, active=True, category_id='1')`, `fudo_category(id, name)`.
- Suite completa: baseline preexistente **29 failed / 44 errors** (ajenos); no debe empeorar.
- Commits terminan con línea en blanco + `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Nunca `git add` de las carpetas `backend/*` sin trackear (artefactos de pip).

---

## File map

**Backend (modificar):** `backend/app/models/menu.py`, `backend/app/services/menu_sync_service.py`, `backend/app/services/menu_publish_service.py`, `backend/app/routes/menu.py`, tests `backend/tests/test_menu_{models,sync,publish,routes,routes_ops,routes_validation,routes_missing,tasks}.py`, `backend/tests/menu_fakes.py`
**Backend (crear):** `backend/migrations/versions/carta_grupos_fudo.py`, `backend/tests/test_menu_groups.py`, `backend/tests/test_menu_items_merge.py`
**Backend (borrar):** `backend/seed_menu.py`, `backend/data/menu_seed.json`, `backend/tests/test_seed_menu.py`
**Admin (modificar):** `frontend/src/services/menuService.js`, `frontend/src/pages/Menu.jsx`, `frontend/src/pages/MenuInbox.jsx`, `frontend/src/components/menu/{CategoryCard,CategoryFormModal,MenuItemModal}.jsx`, `frontend/src/components/layout/Sidebar.jsx`
**Admin (crear):** `frontend/src/components/menu/GroupsPanel.jsx`, `frontend/src/components/menu/ItemPicker.jsx`
**menu-site (modificar):** `menu-site/src/lib/{loadMenu,filterMenu}.js` (+tests), `menu-site/src/App.jsx`, `menu-site/src/components/{CategoryNav,CategorySection}.jsx`, `menu-site/public/menu.sample.json`
**menu-site (crear):** `menu-site/src/components/GroupSection.jsx`

---

## Phase A — Backend

### Task 1: Modelos y migración

**Files:** Modify `backend/app/models/menu.py`, `backend/app/models/__init__.py`; Create `backend/migrations/versions/carta_grupos_fudo.py`; Test `backend/tests/test_menu_models.py`

- [ ] **Step 1: Tests (agregar a `backend/tests/test_menu_models.py`)**

```python
from app.models.menu import MenuGroup


def test_group_and_category_fields(menu_app):
    group = MenuGroup(name='Desayuno', slug='desayuno', sort_order=0)
    db.session.add(group)
    db.session.flush()
    category = MenuCategory(name='Cafetería', slug='cafeteria', fudo_category_id='10', group_id=group.id)
    db.session.add(category)
    db.session.commit()

    data = category.to_dict()
    assert data['fudo_category_id'] == '10'
    assert data['group_id'] == group.id
    assert data['show_title'] is True
    assert data['fudo_status'] is None
    assert group.to_dict() == {'id': group.id, 'name': 'Desayuno', 'slug': 'desayuno', 'sort_order': 0}


def test_deleting_group_leaves_categories_ungrouped(menu_app):
    group = MenuGroup(name='Bebidas', slug='bebidas')
    db.session.add(group)
    db.session.flush()
    category = MenuCategory(name='Licuados', slug='licuados', group_id=group.id)
    db.session.add(category)
    db.session.commit()

    db.session.delete(group)
    db.session.commit()
    assert db.session.get(MenuCategory, category.id).group_id is None


def test_item_reviewed_flag(menu_app):
    category = MenuCategory(name='X', slug='x')
    db.session.add(category)
    db.session.flush()
    item = MenuItem(category_id=category.id, name='Latte')
    db.session.add(item)
    db.session.commit()
    assert item.to_dict()['reviewed'] is False
```

Además, en `test_fudo_product_to_dict` agregar `'fudo_category_id': None` al dict esperado.

Run: `cd backend && python -m pytest tests/test_menu_models.py -q -p no:cacheprovider` → FAIL (`ImportError: cannot import name 'MenuGroup'`).

- [ ] **Step 2: Modelos** (`backend/app/models/menu.py`)

Agregar antes de `MenuCategory`:

```python
class MenuGroup(db.Model):
    """Sección de presentación de la carta pública (agrupa categorías). No afecta productos."""
    __tablename__ = 'menu_groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), nullable=False, unique=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Sin passive_deletes: al borrar el grupo SQLAlchemy pone group_id = NULL (también en SQLite).
    categories = db.relationship('MenuCategory', backref='group')

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'slug': self.slug, 'sort_order': self.sort_order}
```

En `MenuCategory` agregar columnas:

```python
    fudo_category_id = db.Column(db.String(20), unique=True)
    group_id = db.Column(db.Integer, db.ForeignKey('menu_groups.id', ondelete='SET NULL'), index=True)
    show_title = db.Column(db.Boolean, nullable=False, default=True)
    fudo_status = db.Column(db.String(20))  # None | 'missing'
```

y en `MenuCategory.to_dict` agregar `'fudo_category_id'`, `'group_id'`, `'show_title'`, `'fudo_status'`.

> SQLite no aplica `ON DELETE SET NULL` sin `PRAGMA foreign_keys`; por eso la relación no usa `passive_deletes` y SQLAlchemy hace el `UPDATE ... SET group_id = NULL` al borrar el grupo.

En `MenuItem` agregar `reviewed_at = db.Column(db.DateTime)` y en su `to_dict` `'reviewed': self.reviewed_at is not None`.

En `FudoProduct` agregar `fudo_category_id = db.Column(db.String(20))` y en su `to_dict` `'fudo_category_id': self.fudo_category_id`.

En `backend/app/models/__init__.py` exportar `MenuGroup` (import y `__all__`).

- [ ] **Step 3: Migración** `backend/migrations/versions/carta_grupos_fudo.py`

Verificar head: `cd backend && FLASK_APP=run.py python -m flask db heads` → debe ser `add_menu_tables (head)`; si no, usar el head que muestre.

```python
"""Carta: categorías desde Fudo y grupos de presentación

Revision ID: carta_grupos_fudo
Revises: add_menu_tables
Create Date: 2026-10-08

"""
from alembic import op
import sqlalchemy as sa


revision = 'carta_grupos_fudo'
down_revision = 'add_menu_tables'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'menu_groups',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(120), nullable=False, unique=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    with op.batch_alter_table('menu_categories') as batch:
        batch.add_column(sa.Column('fudo_category_id', sa.String(20), nullable=True))
        batch.add_column(sa.Column('group_id', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('show_title', sa.Boolean(), nullable=False, server_default=sa.true()))
        batch.add_column(sa.Column('fudo_status', sa.String(20), nullable=True))
        batch.create_unique_constraint('uq_menu_categories_fudo_category_id', ['fudo_category_id'])
        batch.create_foreign_key('fk_menu_categories_group_id', 'menu_groups', ['group_id'], ['id'], ondelete='SET NULL')
        batch.create_index('ix_menu_categories_group_id', ['group_id'])
    with op.batch_alter_table('menu_items') as batch:
        batch.add_column(sa.Column('reviewed_at', sa.DateTime(), nullable=True))
    with op.batch_alter_table('fudo_products') as batch:
        batch.add_column(sa.Column('fudo_category_id', sa.String(20), nullable=True))
    # Lo existente se considera revisado (lo creó una persona).
    op.execute('UPDATE menu_items SET reviewed_at = updated_at')


def downgrade():
    with op.batch_alter_table('fudo_products') as batch:
        batch.drop_column('fudo_category_id')
    with op.batch_alter_table('menu_items') as batch:
        batch.drop_column('reviewed_at')
    with op.batch_alter_table('menu_categories') as batch:
        batch.drop_index('ix_menu_categories_group_id')
        batch.drop_constraint('fk_menu_categories_group_id', type_='foreignkey')
        batch.drop_constraint('uq_menu_categories_fudo_category_id', type_='unique')
        batch.drop_column('fudo_status')
        batch.drop_column('show_title')
        batch.drop_column('group_id')
        batch.drop_column('fudo_category_id')
    op.drop_table('menu_groups')
```

- [ ] **Step 4: Tests verdes + validar migración**

Run: `python -m pytest tests/test_menu_models.py -q -p no:cacheprovider` → pasan.

Validar upgrade/downgrade contra Postgres local en un schema temporal **sin tocar `alembic_version` de la base de dev** (está stampeada con una revisión de otra rama): script en el scratchpad que crea `CREATE SCHEMA menu_migtest`, `SET search_path`, corre `upgrade()` de `add_menu_tables` y luego de `carta_grupos_fudo` (cargando los módulos con importlib y parcheando su `op` con `alembic.operations.Operations(MigrationContext.configure(conn))`), verifica columnas con `sqlalchemy.inspect`, corre `downgrade()` de la nueva, verifica que se fueron, y `DROP SCHEMA ... CASCADE` en `finally`.

- [ ] **Step 5: Commit** — `feat(menu): add menu groups and Fudo category fields`

---

### Task 2: Sync crea categorías e ítems ocultos

**Files:** Modify `backend/app/services/menu_sync_service.py`; Test `backend/tests/test_menu_sync.py`

- [ ] **Step 1: Tests** — reemplazar `test_sync_never_creates_or_deletes_menu_items` y agregar los siguientes en `backend/tests/test_menu_sync.py`:

```python
from app.models.menu import MenuCategory


def _categories():
    return [fudo_category(1, 'Cafetería'), fudo_category(2, 'Pastelería')]


def test_sync_creates_categories_from_fudo(menu_app):
    stats = sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'Latte', 6900)], categories=_categories()))
    cats = {c.fudo_category_id: c for c in MenuCategory.query.all()}
    assert set(cats) == {'1', '2'}
    assert cats['1'].name == 'Cafetería' and cats['1'].is_visible and cats['1'].group_id is None
    assert stats['categories_created'] == 2


def test_sync_renames_and_flags_missing_categories(menu_app):
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'Latte', 1)], categories=_categories()))
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'Latte', 1)], categories=[fudo_category(1, 'Cafés')]))
    cafe = MenuCategory.query.filter_by(fudo_category_id='1').one()
    pasteleria = MenuCategory.query.filter_by(fudo_category_id='2').one()
    assert cafe.name == 'Cafés' and cafe.slug == 'cafes'
    assert pasteleria.is_visible is False and pasteleria.fudo_status == 'missing'


def test_sync_creates_hidden_items_for_new_products(menu_app):
    stats = sync_fudo_products(FakeFudoClient(
        products=[fudo_product(1, 'Latte', 6900, category_id='1'), fudo_product(2, 'Medialuna', 2500, category_id='2')],
        categories=_categories(),
    ))
    latte = MenuItem.query.filter_by(name='Latte').one()
    assert latte.is_visible is False and latte.reviewed_at is None
    assert latte.category.fudo_category_id == '1'
    assert [(v.fudo_product_id, v.price, v.fudo_status) for v in latte.variants] == [('1', Decimal('6900'), 'ok')]
    assert stats['items_created'] == 2

    again = sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'Latte', 6900, category_id='1')], categories=_categories()))
    assert again['items_created'] == 0
    assert MenuItem.query.filter_by(name='Latte').count() == 1


def test_sync_skips_ignored_and_inactive_products(menu_app):
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'A', 1)], categories=_categories()))
    item = MenuItem.query.one()
    db.session.get(FudoProduct, '1').ignored = True
    db.session.delete(item)
    db.session.commit()

    stats = sync_fudo_products(FakeFudoClient(
        products=[fudo_product(1, 'A', 1), fudo_product(2, 'B', 1, active=False)], categories=_categories(),
    ))
    assert stats['items_created'] == 0
    assert MenuItem.query.count() == 0


def test_sync_moves_item_when_fudo_category_changes(menu_app):
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'Latte', 1, category_id='1')], categories=_categories()))
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'Latte', 1, category_id='2')], categories=_categories()))
    assert MenuItem.query.one().category.fudo_category_id == '2'


def test_sync_puts_products_without_category_in_sin_categoria(menu_app):
    product = fudo_product(1, 'Raro', 1)
    product['relationships'] = {}
    sync_fudo_products(FakeFudoClient(products=[product], categories=_categories()))
    assert MenuItem.query.one().category.name == 'Sin categoría'
    assert MenuItem.query.one().category.fudo_category_id == '__none__'


def test_hidden_new_items_do_not_create_unpublished_changes(menu_app, storage):
    from app.services.menu_publish_service import publish, has_unpublished_changes
    publish(storage)
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'Latte', 1)], categories=_categories()))
    assert has_unpublished_changes() is False
```

Los tests existentes que usan `_item_with_variant` crean una categoría a mano sin `fudo_category_id`: seguir funcionando (la recategorización sólo mueve si existe la categoría Fudo del producto; si el producto no trae categoría conocida, ver regla en Step 2). Ajustar `test_unassigned_excludes_linked_ignored_and_inactive` → se elimina (la función `unassigned_products` desaparece) y reemplazar por `test_new_items_lists_unreviewed`:

```python
def test_new_items_lists_unreviewed(menu_app):
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'A', 1), fudo_product(2, 'B', 1)], categories=_categories()))
    reviewed = MenuItem.query.filter_by(name='A').one()
    reviewed.reviewed_at = datetime.utcnow()
    db.session.commit()
    assert [i.name for i in new_items()] == ['B']
```

(importar `new_items` desde el servicio y `datetime`).

Run → FAIL.

- [ ] **Step 2: Implementación** — reescribir `backend/app/services/menu_sync_service.py`:

```python
from datetime import datetime
from decimal import Decimal

from app.extensions import db
from app.models.menu import FudoProduct, MenuCategory, MenuItem, MenuItemVariant
from app.utils.slug import unique_slug

NO_CATEGORY_ID = '__none__'
NO_CATEGORY_NAME = 'Sin categoría'


def _category_id(product):
    relationship = (product.get('relationships') or {}).get('productCategory') or {}
    data = relationship.get('data') or {}
    return str(data['id']) if data.get('id') is not None else None


def _next_category_order():
    current = db.session.query(db.func.max(MenuCategory.sort_order)).filter(MenuCategory.group_id.is_(None)).scalar()
    return 0 if current is None else current + 1


def _next_item_order(category_id):
    current = db.session.query(db.func.max(MenuItem.sort_order)).filter(MenuItem.category_id == category_id).scalar()
    return 0 if current is None else current + 1


def _upsert_category(by_fudo_id, fudo_category_id, name, stats):
    category = by_fudo_id.get(fudo_category_id)
    if category is None:
        category = MenuCategory(
            fudo_category_id=fudo_category_id, name=name[:100], slug=unique_slug(MenuCategory, name),
            is_visible=True, show_title=True, sort_order=_next_category_order(),
        )
        db.session.add(category)
        db.session.flush()
        by_fudo_id[fudo_category_id] = category
        stats['categories_created'] += 1
    else:
        if category.name != name[:100]:
            category.name = name[:100]
            category.slug = unique_slug(MenuCategory, name, exclude_id=category.id)
        category.fudo_status = None
    return category


def _sync_categories(raw_categories, stats):
    by_fudo_id = {c.fudo_category_id: c for c in MenuCategory.query.filter(MenuCategory.fudo_category_id.isnot(None))}
    seen = set()
    for raw in raw_categories:
        fudo_category_id = str(raw['id'])
        seen.add(fudo_category_id)
        _upsert_category(by_fudo_id, fudo_category_id, (raw.get('attributes') or {}).get('name') or 'Sin nombre', stats)
    for fudo_category_id, category in by_fudo_id.items():
        if fudo_category_id not in seen and fudo_category_id != NO_CATEGORY_ID:
            category.is_visible = False
            category.fudo_status = 'missing'
    return by_fudo_id


def _category_for_product(product, categories, stats):
    """Categoría de la carta para un FudoProduct; crea 'Sin categoría' si hace falta."""
    category = categories.get(product.fudo_category_id) if product.fudo_category_id else None
    if category is None:
        category = _upsert_category(categories, NO_CATEGORY_ID, NO_CATEGORY_NAME, stats)
    return category


def assign_fudo_category(item, products_by_id=None, categories=None):
    """Pone al ítem en la categoría de Fudo de su primer precio vinculado con producto existente."""
    categories = categories if categories is not None else {
        c.fudo_category_id: c for c in MenuCategory.query.filter(MenuCategory.fudo_category_id.isnot(None))
    }
    for variant in sorted(item.variants, key=lambda v: (v.sort_order, v.id or 0)):
        if not variant.fudo_product_id:
            continue
        product = (products_by_id or {}).get(variant.fudo_product_id) or db.session.get(FudoProduct, variant.fudo_product_id)
        if product is None:
            continue
        stats = {'categories_created': 0}
        category = _category_for_product(product, categories, stats)
        if item.category_id != category.id:
            item.sort_order = _next_item_order(category.id)
            item.category_id = category.id
        return True
    return False


def sync_fudo_products(client):
    """Sincroniza categorías, productos, precios y crea ítems ocultos para productos nuevos."""
    raw_products = client.get_all_products()
    if not raw_products:
        raise ValueError('Fudo no devolvió productos; no se sincronizó nada')

    stats = {'categories_created': 0, 'items_created': 0}
    categories = _sync_categories(client.get_all_product_categories(), stats)
    category_names = {fid: c.name for fid, c in categories.items()}

    existing = {p.fudo_id: p for p in FudoProduct.query.all()}
    now = datetime.utcnow()
    by_id = {}
    for raw in raw_products:
        fudo_id = str(raw['id'])
        attrs = raw.get('attributes') or {}
        product = by_id.get(fudo_id) or existing.get(fudo_id)
        if product is None:
            product = FudoProduct(fudo_id=fudo_id, ignored=False)
            db.session.add(product)
        product.name = (attrs.get('name') or '')[:100]
        product.price = Decimal(str(attrs.get('price') or 0)).quantize(Decimal('0.01'))
        product.is_active = bool(attrs.get('active', True))
        product.fudo_category_id = _category_id(raw)
        product.category_name = category_names.get(product.fudo_category_id)
        product.synced_at = now
        by_id[fudo_id] = product
    for fudo_id, product in existing.items():
        if fudo_id not in by_id:
            db.session.delete(product)

    price_changes = 0
    alerts = 0
    for variant in MenuItemVariant.query.filter(MenuItemVariant.fudo_product_id.isnot(None)).all():
        product = by_id.get(variant.fudo_product_id)
        if product is None:
            variant.fudo_status = 'missing'
        elif not product.is_active:
            variant.fudo_status = 'inactive'
        else:
            variant.fudo_status = 'ok'
            if Decimal(variant.price) != product.price:
                variant.price = product.price
                price_changes += 1
        if variant.fudo_status != 'ok':
            alerts += 1

    linked_items = MenuItem.query.join(MenuItemVariant).filter(MenuItemVariant.fudo_product_id.isnot(None)).distinct().all()
    for item in linked_items:
        assign_fudo_category(item, by_id, categories)

    linked = linked_fudo_ids()
    for product in by_id.values():
        if not product.is_active or product.ignored or product.fudo_id in linked:
            continue
        category = _category_for_product(product, categories, stats)
        item = MenuItem(
            category_id=category.id, name=product.name[:200] or 'Sin nombre', is_visible=False,
            sort_order=_next_item_order(category.id),
        )
        item.variants = [MenuItemVariant(fudo_product_id=product.fudo_id, price=product.price, fudo_status='ok', sort_order=0)]
        db.session.add(item)
        db.session.flush()
        linked.add(product.fudo_id)
        stats['items_created'] += 1

    db.session.commit()
    return {'products': len(by_id), 'price_changes': price_changes, 'alerts': alerts, **stats}


def linked_fudo_ids():
    rows = db.session.query(MenuItemVariant.fudo_product_id).filter(MenuItemVariant.fudo_product_id.isnot(None))
    return {fudo_id for (fudo_id,) in rows}


def new_items():
    return MenuItem.query.filter(MenuItem.reviewed_at.is_(None)).order_by(MenuItem.category_id, MenuItem.name).all()


def alert_variants():
    return MenuItemVariant.query.filter(MenuItemVariant.fudo_status.in_(['inactive', 'missing'])).all()


def alert_categories():
    return MenuCategory.query.filter(MenuCategory.fudo_status == 'missing').all()
```

Nota: `assign_fudo_category` sobre ítems de tests viejos cuyo producto no tiene `fudo_category_id` los manda a "Sin categoría" sólo si el producto existe en Fudo. Si algún test existente de `test_menu_sync.py` verifica la categoría de esos ítems, ajustar el test (no la lógica) y anotarlo en el reporte.

- [ ] **Step 3:** Run `python -m pytest tests/test_menu_sync.py tests/test_menu_tasks.py -q -p no:cacheprovider` → pasan. (`test_menu_tasks` usa sync: si alguno falla por los ítems nuevos creados, revisar: los ítems nuevos son ocultos y no deben cambiar el hash.)

- [ ] **Step 4: Commit** — `feat(menu): sync Fudo categories and auto-create hidden items`

---

### Task 3: Snapshot `menu.json` v2 agrupado

**Files:** Modify `backend/app/services/menu_publish_service.py`; Test `backend/tests/test_menu_publish.py`

- [ ] **Step 1: Tests** — actualizar `test_build_snapshot_shape` a v2 y agregar:

```python
from app.models.menu import MenuGroup


def test_snapshot_without_groups_is_single_untitled_group(menu_app):
    _seed()
    snapshot = build_snapshot()
    assert snapshot['version'] == 2
    assert [g['slug'] for g in snapshot['groups']] == ['_carta']
    assert snapshot['groups'][0]['name'] is None
    assert [c['slug'] for c in snapshot['groups'][0]['categories']] == ['tortas', 'cafes']
    assert 'categories' not in snapshot


def test_snapshot_groups_order_otros_and_empty_groups(menu_app):
    _seed()
    dulces = MenuGroup(name='Dulces', slug='dulces', sort_order=0)
    vacio = MenuGroup(name='Vacío', slug='vacio', sort_order=1)
    db.session.add_all([dulces, vacio])
    db.session.flush()
    MenuCategory.query.filter_by(slug='tortas').one().group_id = dulces.id
    MenuCategory.query.filter_by(slug='cafes').one().show_title = False
    db.session.commit()

    groups = build_snapshot()['groups']
    assert [(g['slug'], g['name']) for g in groups] == [('dulces', 'Dulces'), ('_otros', 'Otros')]
    assert groups[1]['categories'][0]['show_title'] is False
```

En `test_build_snapshot_shape` reemplazar el acceso `snapshot['categories']` por `snapshot['groups'][0]['categories']` y `assert snapshot['version'] == 2`. En `test_publish_uploads_json_and_clears_pending_flag` y similares, ajustar los paths al JSON si leen `categories`.

- [ ] **Step 2: Implementación** — en `menu_publish_service.py`:
  - `SNAPSHOT_VERSION = 2`; importar `MenuGroup`.
  - En `_build`, cada categoría agrega `'show_title': bool(category.show_title)`; armar `category_dicts` como hoy (sólo visibles con ítems) **conservando** `category.group_id` para agrupar (no incluirlo en el dict publicado). Luego:

```python
    groups = MenuGroup.query.order_by(MenuGroup.sort_order, MenuGroup.id).all()
    if not groups:
        grouped = [{'slug': '_carta', 'name': None, 'categories': [c for _, c in built]}]
    else:
        grouped = [
            {'slug': g.slug, 'name': g.name, 'categories': [c for gid, c in built if gid == g.id]}
            for g in groups
        ]
        grouped.append({'slug': '_otros', 'name': 'Otros', 'categories': [c for gid, c in built if gid is None]})
    grouped = [g for g in grouped if g['categories']]
```

  donde `built` es la lista de tuplas `(category.group_id, category_dict)` en orden `(sort_order, id)`. El dict final reemplaza `'categories'` por `'groups': grouped`.
  - El warning de `publish()` sobre `MENU_PUBLIC_BASE_URL` recorre `snapshot['groups'][*]['categories'][*]['items']`.

- [ ] **Step 3:** Run `python -m pytest tests/test_menu_publish.py tests/test_menu_tasks.py tests/test_menu_routes_ops.py -q -p no:cacheprovider`. Ajustar en `test_menu_routes_ops.py::test_publish_endpoint` el path al JSON (`['groups'][0]['categories'][0]['items'][0]['name']`).

- [ ] **Step 4: Commit** — `feat(menu): publish grouped menu.json v2`

---

### Task 4: API de grupos y categorías

**Files:** Modify `backend/app/routes/menu.py`; Create `backend/tests/test_menu_groups.py`; Modify tests que creaban categorías por API

- [ ] **Step 1: Helper de tests** — en `backend/tests/menu_fakes.py` agregar:

```python
def make_category(name='Cafés', fudo_category_id=None, **kwargs):
    """Por defecto crea una categoría 'heredada' (sin vínculo a Fudo); pasar fudo_category_id único para una de Fudo."""
    from app.extensions import db
    from app.models.menu import MenuCategory
    from app.utils.slug import unique_slug
    category = MenuCategory(name=name, slug=unique_slug(MenuCategory, name), fudo_category_id=fudo_category_id, **kwargs)
    db.session.add(category)
    db.session.commit()
    return category
```

Ojo: en categorías heredadas, un ítem con precios vinculados se mueve solo a la categoría Fudo de su producto (o a "Sin categoría" si el `FudoProduct` del test no tiene `fudo_category_id`); ajustar las aserciones de categoría de esos tests en consecuencia y anotarlo en el reporte.

Reemplazar en `test_menu_routes.py`, `test_menu_routes_validation.py`, `test_menu_routes_missing.py`, `test_menu_routes_ops.py` todo uso de `POST /api/v1/menu/categories` por `make_category(...)` (devolver `category.to_dict()` donde el test esperaba el JSON). Eliminar los tests de crear categoría por API (`test_category_slugs_are_unique`, `test_category_requires_name`, validaciones de nombre de categoría) y reemplazar `test_update_category` por la versión del Step 2.

- [ ] **Step 2: Tests** — `backend/tests/test_menu_groups.py`:

```python
from app.extensions import db
from app.models.menu import MenuCategory, MenuGroup
from menu_fakes import make_category


def test_group_crud_and_reorder(menu_client, admin_headers):
    a = menu_client.post('/api/v1/menu/groups', json={'name': 'Desayuno'}, headers=admin_headers).get_json()
    b = menu_client.post('/api/v1/menu/groups', json={'name': 'Almuerzos'}, headers=admin_headers).get_json()
    assert (a['slug'], a['sort_order'], b['sort_order']) == ('desayuno', 0, 1)
    assert menu_client.post('/api/v1/menu/groups', json={'name': ' '}, headers=admin_headers).status_code == 400

    renamed = menu_client.put(f"/api/v1/menu/groups/{a['id']}", json={'name': 'Desayuno y merienda'}, headers=admin_headers).get_json()
    assert renamed['slug'] == 'desayuno-y-merienda'

    assert menu_client.put('/api/v1/menu/groups/reorder', json={'ids': [b['id'], a['id']]}, headers=admin_headers).status_code == 200
    groups = menu_client.get('/api/v1/menu', headers=admin_headers).get_json()['groups']
    assert [g['name'] for g in groups] == ['Almuerzos', 'Desayuno y merienda']
    assert menu_client.put('/api/v1/menu/groups/reorder', json={'ids': [a['id']]}, headers=admin_headers).status_code == 400


def test_delete_group_ungroups_categories(menu_client, admin_headers):
    group = menu_client.post('/api/v1/menu/groups', json={'name': 'Bebidas'}, headers=admin_headers).get_json()
    category = make_category('Licuados')
    menu_client.put(f'/api/v1/menu/categories/{category.id}', json={'group_id': group['id']}, headers=admin_headers)
    assert menu_client.delete(f"/api/v1/menu/groups/{group['id']}", headers=admin_headers).status_code == 200
    assert db.session.get(MenuCategory, category.id).group_id is None


def test_update_category_fields(menu_client, admin_headers):
    group = menu_client.post('/api/v1/menu/groups', json={'name': 'Bebidas'}, headers=admin_headers).get_json()
    category = make_category('Licuados')
    data = menu_client.put(f'/api/v1/menu/categories/{category.id}', json={
        'group_id': group['id'], 'show_title': False, 'is_visible': False, 'description': 'Con leche o agua',
    }, headers=admin_headers).get_json()
    assert (data['group_id'], data['show_title'], data['is_visible'], data['description']) == (group['id'], False, False, 'Con leche o agua')
    assert data['sort_order'] == 0  # al final del grupo nuevo

    assert menu_client.put(f'/api/v1/menu/categories/{category.id}', json={'name': 'Otro'}, headers=admin_headers).status_code == 400
    assert menu_client.put(f'/api/v1/menu/categories/{category.id}', json={'group_id': 999}, headers=admin_headers).status_code == 400
    assert menu_client.put(f'/api/v1/menu/categories/{category.id}', json={'group_id': None}, headers=admin_headers).get_json()['group_id'] is None


def test_reorder_categories_within_group(menu_client, admin_headers):
    a = make_category('A', '1')
    b = make_category('B', '2')
    ok = menu_client.put('/api/v1/menu/categories/reorder', json={'group_id': None, 'ids': [b.id, a.id]}, headers=admin_headers)
    assert ok.status_code == 200
    assert [c.name for c in MenuCategory.query.order_by(MenuCategory.sort_order)] == ['B', 'A']
    assert menu_client.put('/api/v1/menu/categories/reorder', json={'group_id': None, 'ids': [a.id]}, headers=admin_headers).status_code == 400


def test_categories_cannot_be_created_and_only_legacy_empty_can_be_deleted(menu_client, admin_headers):
    assert menu_client.post('/api/v1/menu/categories', json={'name': 'X'}, headers=admin_headers).status_code == 405
    fudo_cat = make_category('Fudo', '1')
    legacy = make_category('Manual', None)
    assert menu_client.delete(f'/api/v1/menu/categories/{fudo_cat.id}', headers=admin_headers).status_code == 409
    assert menu_client.delete(f'/api/v1/menu/categories/{legacy.id}', headers=admin_headers).status_code == 200
```

Run → FAIL.

- [ ] **Step 3: Implementación** en `backend/app/routes/menu.py`:
  - Importar `MenuGroup`.
  - `get_menu`: categorías ordenadas por `(group_id is null, group sort, sort_order, id)` no es necesario: devolver `MenuCategory.query.order_by(MenuCategory.sort_order, MenuCategory.id)` y agregar `'groups': [g.to_dict() for g in MenuGroup.query.order_by(MenuGroup.sort_order, MenuGroup.id)]`. El front agrupa.
  - **Eliminar** la ruta `POST /categories` (`create_category`).
  - `reorder_categories`: leer `group_id` del body (`None` o int); `scope = MenuCategory.group_id.is_(None) if group_id is None else MenuCategory.group_id == group_id`; si `group_id` no es None ni int → 400; usar `_apply_order(MenuCategory, ids, scope)`.
  - `update_category`: si `'name' in data` y `category.fudo_category_id` → `_error('El nombre de la categoría viene de Fudo')`; si es heredada (sin fudo id) mantener la lógica de nombre actual. Agregar:

```python
    if 'show_title' in data:
        category.show_title = bool(data['show_title'])
    if 'group_id' in data:
        group_id = data['group_id']
        if group_id is not None and (not _is_int(group_id) or db.session.get(MenuGroup, group_id) is None):
            return _error('Grupo inexistente')
        if category.group_id != group_id:
            scope = MenuCategory.group_id.is_(None) if group_id is None else MenuCategory.group_id == group_id
            category.sort_order = _next_order(MenuCategory.sort_order, scope)
            category.group_id = group_id
```

  - `delete_category`: si `category.fudo_category_id` → `_error('Las categorías de Fudo no se borran: ocultala', 409)`; luego la regla de "tiene ítems" actual.
  - Grupos:

```python
@bp.route('/groups', methods=['POST'])
@token_required
@admin_required
def create_group(current_user):
    name, error = _required_text((request.get_json() or {}).get('name'), 100)
    if error:
        return _error(error)
    group = MenuGroup(name=name, slug=unique_slug(MenuGroup, name), sort_order=_next_order(MenuGroup.sort_order))
    db.session.add(group)
    db.session.commit()
    return jsonify(group.to_dict()), 201


@bp.route('/groups/reorder', methods=['PUT'])
@token_required
@admin_required
def reorder_groups(current_user):
    if not _apply_order(MenuGroup, (request.get_json() or {}).get('ids')):
        return _error('La lista de grupos no es válida')
    return jsonify({'message': 'Orden actualizado'}), 200


@bp.route('/groups/<int:group_id>', methods=['PUT'])
@token_required
@admin_required
def update_group(current_user, group_id):
    group = db.get_or_404(MenuGroup, group_id)
    name, error = _required_text((request.get_json() or {}).get('name'), 100)
    if error:
        return _error(error)
    group.name = name
    group.slug = unique_slug(MenuGroup, name, exclude_id=group.id)
    db.session.commit()
    return jsonify(group.to_dict()), 200


@bp.route('/groups/<int:group_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_group(current_user, group_id):
    group = db.get_or_404(MenuGroup, group_id)
    start = _next_order(MenuCategory.sort_order, MenuCategory.group_id.is_(None))
    for offset, category in enumerate(sorted(group.categories, key=lambda c: (c.sort_order, c.id))):
        category.group_id = None
        category.sort_order = start + offset
    db.session.delete(group)
    db.session.commit()
    return jsonify({'message': 'Grupo eliminado'}), 200
```

- [ ] **Step 4:** Run `python -m pytest tests/test_menu_groups.py tests/test_menu_routes.py tests/test_menu_routes_validation.py tests/test_menu_routes_missing.py tests/test_menu_routes_ops.py -q -p no:cacheprovider` → pasan.

- [ ] **Step 5: Commit** — `feat(menu): groups API and Fudo-owned categories`

---

### Task 5: Ítems — categoría automática, merge, ignore, bandeja

**Files:** Modify `backend/app/routes/menu.py`; Create `backend/tests/test_menu_items_merge.py`; Modify `backend/tests/test_menu_routes_ops.py`, `test_menu_routes.py`

- [ ] **Step 1: Tests** — `backend/tests/test_menu_items_merge.py`:

```python
from decimal import Decimal

from app.extensions import db
from app.models.menu import FudoProduct, MenuItem
from app.services.menu_sync_service import sync_fudo_products
from menu_fakes import FakeFudoClient, fudo_category, fudo_product, make_category

CATS = [fudo_category(1, 'Tortas'), fudo_category(2, 'Cafés')]


def _sync(*products):
    sync_fudo_products(FakeFudoClient(products=list(products), categories=CATS))


def test_merge_moves_variants_and_deletes_source(menu_client, admin_headers):
    _sync(fudo_product(1, 'Torta Galia porción', 11200), fudo_product(2, 'Torta Galia entera', 12600))
    target = MenuItem.query.filter_by(name='Torta Galia porción').one()
    source = MenuItem.query.filter_by(name='Torta Galia entera').one()

    response = menu_client.post(f'/api/v1/menu/items/{target.id}/merge', json={'source_item_id': source.id}, headers=admin_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert [v['fudo_product_id'] for v in data['variants']] == ['1', '2']
    assert data['reviewed'] is True
    assert db.session.get(MenuItem, source.id) is None

    assert menu_client.post(f'/api/v1/menu/items/{target.id}/merge', json={'source_item_id': target.id}, headers=admin_headers).status_code == 400
    assert menu_client.post(f'/api/v1/menu/items/{target.id}/merge', json={'source_item_id': 999}, headers=admin_headers).status_code == 400


def test_ignore_deletes_item_and_marks_products(menu_client, admin_headers):
    _sync(fudo_product(1, 'Envío', 500))
    item = MenuItem.query.one()
    assert menu_client.post(f'/api/v1/menu/items/{item.id}/ignore', headers=admin_headers).status_code == 200
    assert MenuItem.query.count() == 0
    assert db.session.get(FudoProduct, '1').ignored is True
    _sync(fudo_product(1, 'Envío', 500))
    assert MenuItem.query.count() == 0


def test_update_marks_reviewed_and_ignores_category_for_linked_items(menu_client, admin_headers):
    _sync(fudo_product(1, 'Latte', 6900, category_id='2'))
    item = MenuItem.query.one()
    other = make_category('Manual', None)
    data = menu_client.put(f'/api/v1/menu/items/{item.id}', json={'is_visible': True, 'category_id': other.id}, headers=admin_headers).get_json()
    assert data['reviewed'] is True and data['is_visible'] is True
    assert db.session.get(MenuItem, item.id).category.fudo_category_id == '2'


def test_create_item_only_for_manual_prices(menu_client, admin_headers):
    _sync(fudo_product(1, 'Latte', 6900))
    category = make_category('Extras', None)
    linked = menu_client.post('/api/v1/menu/items', json={'category_id': category.id, 'name': 'X', 'variants': [{'fudo_product_id': '1'}]}, headers=admin_headers)
    assert linked.status_code == 400
    manual = menu_client.post('/api/v1/menu/items', json={'category_id': category.id, 'name': 'Agua', 'variants': [{'label': 'Sin gas', 'price': 2900}]}, headers=admin_headers)
    assert manual.status_code == 201 and manual.get_json()['reviewed'] is True


def test_inbox_lists_new_items_and_alerts(menu_client, admin_headers):
    _sync(fudo_product(1, 'Latte', 1, category_id='1'), fudo_product(2, 'Moka', 1, category_id='2'))
    sync_fudo_products(FakeFudoClient(products=[fudo_product(1, 'Latte', 1, category_id='1')], categories=[fudo_category(1, 'Tortas')]))
    data = menu_client.get('/api/v1/menu/inbox', headers=admin_headers).get_json()
    assert sorted(i['name'] for i in data['new_items']) == ['Latte', 'Moka']
    assert {a['type'] for a in data['alerts']} == {'variant', 'category'}
    status = menu_client.get('/api/v1/menu', headers=admin_headers).get_json()['status']
    assert status['new_count'] == 2 and status['alerts_count'] == 2
```

En `test_menu_routes_ops.py`: borrar `test_fudo_products_list_marks_linked_and_filters` (la parte `unassigned=true`), `test_ignore_fudo_product` y `test_inbox`; mantener un test de `GET /fudo-products` sin `unassigned` (lista activa + `linked`). En `test_menu_routes.py::test_get_menu_tree_and_status` actualizar el `status` esperado a las claves `has_unpublished_changes, last_published_at, new_count, alerts_count`.

Run → FAIL.

- [ ] **Step 2: Implementación** en `backend/app/routes/menu.py`:
  - Importar `datetime` y `from app.services.menu_sync_service import assign_fudo_category`.
  - `_status()` → `'new_count': len(menu_sync_service.new_items())`, `'alerts_count': len(menu_sync_service.alert_variants()) + len(menu_sync_service.alert_categories())` (quitar `unassigned_count`).
  - En `_apply_item_payload`, al final (después de variantes): `assign_fudo_category(item)` (si tiene precios vinculados, pisa cualquier `category_id` recibido).
  - `create_item`: antes de construir, si alguna variante del payload trae `fudo_product_id` → `_error('Los ítems con productos de Fudo se crean solos al sincronizar')`; setear `item.reviewed_at = datetime.utcnow()`.
  - `update_item`: tras aplicar sin error, `item.reviewed_at = datetime.utcnow()`.
  - Nuevas rutas:

```python
@bp.route('/items/<int:item_id>/merge', methods=['POST'])
@token_required
@admin_required
def merge_item(current_user, item_id):
    target = db.get_or_404(MenuItem, item_id)
    source_id = (request.get_json() or {}).get('source_item_id')
    source = db.session.get(MenuItem, source_id) if _is_int(source_id) else None
    if source is None or source.id == target.id:
        return _error('Elegí otro ítem para unir')
    offset = len(target.variants)
    for position, variant in enumerate(sorted(source.variants, key=lambda v: (v.sort_order, v.id))):
        variant.item = target
        variant.sort_order = offset + position
    db.session.flush()
    db.session.delete(source)
    assign_fudo_category(target)
    target.reviewed_at = datetime.utcnow()
    db.session.commit()
    return jsonify(target.to_dict()), 200


@bp.route('/items/<int:item_id>/ignore', methods=['POST'])
@token_required
@admin_required
def ignore_item(current_user, item_id):
    item = db.get_or_404(MenuItem, item_id)
    for variant in item.variants:
        product = db.session.get(FudoProduct, variant.fudo_product_id) if variant.fudo_product_id else None
        if product is not None:
            product.ignored = True
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Ítem ignorado'}), 200
```

  - `list_fudo_products`: quitar la rama `unassigned`. **Eliminar** `ignore_fudo_product`.
  - `get_inbox`:

```python
    alerts = []
    for variant in menu_sync_service.alert_variants():
        product = db.session.get(FudoProduct, variant.fudo_product_id)
        alerts.append({**variant.to_dict(), 'type': 'variant', 'item_id': variant.item_id,
                       'item_name': variant.item.name, 'fudo_name': product.name if product else None})
    for category in menu_sync_service.alert_categories():
        alerts.append({'type': 'category', 'id': category.id, 'category_name': category.name, 'fudo_status': category.fudo_status})
    new_items = [{**item.to_dict(), 'category_name': item.category.name} for item in menu_sync_service.new_items()]
    return jsonify({'new_items': new_items, 'alerts': alerts}), 200
```

- [ ] **Step 3:** Run todos los tests de la carta: `python -m pytest tests/test_menu_*.py tests/test_fudo_client_products.py -q -p no:cacheprovider` → pasan.

- [ ] **Step 4: Commit** — `feat(menu): automatic item categories, merge, ignore and new-items inbox`

---

### Task 6: Quitar el seed del PDF

- [ ] **Step 1:** `git rm backend/seed_menu.py backend/data/menu_seed.json backend/tests/test_seed_menu.py`
- [ ] **Step 2:** `grep -rn "seed_menu\|menu_seed" backend frontend menu-site render.yaml build.sh docs/superpowers/plans/2026-10-08*` → sin resultados en código (docs viejos pueden mencionarlo).
- [ ] **Step 3:** Suite completa `cd backend && python -m pytest tests/ -q -p no:cacheprovider` → 29 failed / 44 errors (baseline), el resto pasa.
- [ ] **Step 4: Commit** — `chore(menu): remove PDF seed (menu now built from Fudo)`

---

## Phase B — Admin (`frontend/`)

Verificación: `cd frontend && npm run build` + prueba manual en Task 10.

### Task 7: Servicio, pestaña Grupos y lista agrupada

**Files:** Modify `frontend/src/services/menuService.js`, `frontend/src/pages/Menu.jsx`, `frontend/src/components/menu/CategoryCard.jsx`, `frontend/src/components/menu/CategoryFormModal.jsx`; Create `frontend/src/components/menu/GroupsPanel.jsx`

- [ ] **Step 1: `menuService.js`** — eliminar `createCategory`, `ignoreFudoProduct`; cambiar `reorderCategories` y agregar:

```js
  async reorderCategories(groupId, ids) {
    return (await api.put('/menu/categories/reorder', { group_id: groupId, ids })).data
  },

  async createGroup(data) {
    return (await api.post('/menu/groups', data)).data
  },

  async updateGroup(id, data) {
    return (await api.put(`/menu/groups/${id}`, data)).data
  },

  async deleteGroup(id) {
    return (await api.delete(`/menu/groups/${id}`)).data
  },

  async reorderGroups(ids) {
    return (await api.put('/menu/groups/reorder', { ids })).data
  },

  async mergeItem(targetId, sourceId) {
    return (await api.post(`/menu/items/${targetId}/merge`, { source_item_id: sourceId })).data
  },

  async ignoreItem(id) {
    return (await api.post(`/menu/items/${id}/ignore`)).data
  },
```

- [ ] **Step 2: `GroupsPanel.jsx`** (nuevo):

```jsx
import { useState } from 'react'
import { ChevronUp, ChevronDown, Pencil, Trash2, Plus, Check, X } from 'lucide-react'
import menuService from '../../services/menuService'
import { swap, errorMessage } from '../../utils/menuFormat'

const GroupRow = ({ group, index, total, onMove, onChanged, onError }) => {
  const [editing, setEditing] = useState(false)
  const [name, setName] = useState(group.name)

  const save = async () => {
    try {
      await menuService.updateGroup(group.id, { name })
      setEditing(false)
      onChanged()
    } catch (err) {
      onError(errorMessage(err, 'Error al renombrar el grupo'))
    }
  }

  const remove = async () => {
    if (!window.confirm(`¿Borrar el grupo "${group.name}"? Sus categorías quedan sin grupo.`)) return
    try {
      await menuService.deleteGroup(group.id)
      onChanged()
    } catch (err) {
      onError(errorMessage(err, 'Error al borrar el grupo'))
    }
  }

  return (
    <li className="flex items-center gap-2 py-2">
      {editing ? (
        <>
          <input value={name} onChange={(e) => setName(e.target.value)} className="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm" />
          <button type="button" onClick={save} className="p-1.5 text-rose-700" aria-label="Guardar"><Check className="h-4 w-4" /></button>
          <button type="button" onClick={() => { setEditing(false); setName(group.name) }} className="p-1.5 text-gray-500" aria-label="Cancelar"><X className="h-4 w-4" /></button>
        </>
      ) : (
        <>
          <span className="flex-1 font-medium text-gray-900">{group.name}</span>
          <button type="button" disabled={index === 0} onClick={() => onMove(index, -1)} className="p-1.5 text-gray-500 disabled:opacity-30" aria-label="Subir"><ChevronUp className="h-4 w-4" /></button>
          <button type="button" disabled={index === total - 1} onClick={() => onMove(index, 1)} className="p-1.5 text-gray-500 disabled:opacity-30" aria-label="Bajar"><ChevronDown className="h-4 w-4" /></button>
          <button type="button" onClick={() => setEditing(true)} className="p-1.5 text-gray-500" aria-label="Renombrar"><Pencil className="h-4 w-4" /></button>
          <button type="button" onClick={remove} className="p-1.5 text-gray-500 hover:text-red-600" aria-label="Borrar"><Trash2 className="h-4 w-4" /></button>
        </>
      )}
    </li>
  )
}

const GroupsPanel = ({ groups, onChanged }) => {
  const [name, setName] = useState('')
  const [error, setError] = useState('')

  const add = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await menuService.createGroup({ name })
      setName('')
      onChanged()
    } catch (err) {
      setError(errorMessage(err, 'Error al crear el grupo'))
    }
  }

  const move = async (index, direction) => {
    const ids = swap(groups.map((g) => g.id), index, index + direction)
    if (!ids) return
    try {
      await menuService.reorderGroups(ids)
      onChanged()
    } catch (err) {
      setError(errorMessage(err, 'Error al reordenar'))
    }
  }

  return (
    <section className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
      <div>
        <h2 className="font-semibold text-gray-900">Grupos de la carta</h2>
        <p className="text-sm text-gray-600">Organizan las secciones de la carta pública. Asigná cada categoría a un grupo desde la pestaña "Carta".</p>
      </div>
      {error && <div className="p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}
      <ul className="divide-y divide-gray-100">
        {groups.length === 0 && <li className="py-2 text-sm text-gray-500">Sin grupos: la carta se muestra por categorías.</li>}
        {groups.map((group, index) => (
          <GroupRow key={`${group.id}-${group.name}`} group={group} index={index} total={groups.length} onMove={move} onChanged={onChanged} onError={setError} />
        ))}
      </ul>
      <form onSubmit={add} className="flex gap-2">
        <input value={name} onChange={(e) => setName(e.target.value)} required placeholder="Nuevo grupo (ej: Desayuno y merienda)" className="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm" />
        <button type="submit" className="inline-flex items-center gap-1 px-3 py-1.5 text-sm bg-rose-600 text-white rounded hover:bg-rose-700"><Plus className="h-4 w-4" /> Agregar</button>
      </form>
    </section>
  )
}

export default GroupsPanel
```

- [ ] **Step 3: `CategoryCard.jsx`** — cambios:
  - Nuevas props `groups` y `onChangeGroup(category, groupId)`.
  - En el header, debajo/junto al nombre: badge `de Fudo` (gris) si `category.fudo_category_id`, `manual` (ámbar) si no; badge rojo `No está en Fudo` si `category.fudo_status === 'missing'`; si `!category.show_title` mostrar texto chico `título oculto`.
  - Agregar `<select>` compacto con opciones `Sin grupo` (value `''`) + `groups`; `onChange={(e) => onChangeGroup(category, e.target.value === '' ? null : Number(e.target.value))}`; value `category.group_id ?? ''`.
  - Quitar el botón de "Agregar ítem" (los ítems salen de Fudo); dejarlo sólo si `!category.fudo_category_id` (categorías heredadas/manuales).
  - Los tooltips de ↑↓ cambian a "Subir en el grupo"/"Bajar en el grupo".

- [ ] **Step 4: `CategoryFormModal.jsx`** — sólo edición: título "Editar categoría"; campos: nombre **solo lectura** con nota "Viene de Fudo" (editable sólo si `!category.fudo_category_id`), nota (`description`), checkboxes `Visible en la carta` y `Mostrar título en la carta` (`show_title`); botón "Borrar" sólo si `!category.fudo_category_id`. El submit envía `{description, is_visible, show_title}` (+ `name` sólo si es manual) a `updateCategory`.

- [ ] **Step 5: `Menu.jsx`** — cambios:
  - Pestañas `[['carta','Carta'],['grupos','Grupos'],['config','Configuración']]`; `grupos` renderiza `<GroupsPanel groups={menu.groups} onChanged={load} />`.
  - Estado: reemplazar el link de `unassigned_count` por "N nuevos por revisar" (`status.new_count > 0`) + alertas, link a `/menu/inbox`.
  - Construir secciones:

```jsx
  const sections = useMemo(() => {
    if (!menu) return []
    const byGroup = (groupId) => menu.categories.filter((c) => (c.group_id ?? null) === groupId)
    return [
      ...menu.groups.map((g) => ({ key: `g${g.id}`, groupId: g.id, title: g.name, categories: byGroup(g.id) })),
      { key: 'none', groupId: null, title: menu.groups.length ? 'Sin grupo' : null, categories: byGroup(null) },
    ].filter((s) => s.categories.length > 0 || s.groupId !== null)
  }, [menu])
```

  y renderizar cada sección con un encabezado (`title` en mayúsculas, gris) y sus `CategoryCard` (el `index/total` de ↑↓ es dentro de la sección).
  - `moveCategory(section, index, direction)` → `swap(section.categories.map((c) => c.id), …)` y `menuService.reorderCategories(section.groupId, ids)`.
  - `onChangeGroup={(category, groupId) => run('group', () => menuService.updateCategory(category.id, { group_id: groupId }))}`.
  - Quitar el botón "+ Categoría" y el `CategoryFormModal` de creación (sólo edición).
  - Aviso si hay categorías heredadas: `const legacy = menu.categories.filter((c) => !c.fudo_category_id)`; si `legacy.length` mostrar caja ámbar: "Hay {n} categorías creadas a mano (no vienen de Fudo). Mové sus ítems o borralas." 

- [ ] **Step 6:** `cd frontend && npm run build` → OK.
- [ ] **Step 7: Commit** — `feat(menu-admin): groups tab and grouped category list`

---

### Task 8: Modal de ítem y bandeja "Nuevos y alertas"

**Files:** Create `frontend/src/components/menu/ItemPicker.jsx`; Modify `frontend/src/components/menu/MenuItemModal.jsx`, `frontend/src/pages/MenuInbox.jsx`, `frontend/src/components/layout/Sidebar.jsx`

- [ ] **Step 1: `ItemPicker.jsx`** (selector con buscador de ítems):

```jsx
import { useState } from 'react'
import { normalizeText, variantSummary } from '../../utils/menuFormat'

// items: [{ id, name, categoryName, variants }]
const ItemPicker = ({ items, excludeId, onSelect, onCancel }) => {
  const [query, setQuery] = useState('')
  const needle = normalizeText(query.trim())
  const visible = items
    .filter((i) => i.id !== excludeId)
    .filter((i) => !needle || normalizeText(`${i.name} ${i.categoryName}`).includes(needle))
    .slice(0, 50)

  return (
    <div className="mt-2 border border-gray-200 rounded p-2 bg-gray-50">
      <input autoFocus value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Buscar ítem…" className="w-full px-3 py-2 border border-gray-300 rounded text-sm" />
      <ul className="max-h-56 overflow-y-auto mt-2 divide-y divide-gray-200">
        {visible.length === 0 && <li className="p-2 text-sm text-gray-500">Sin resultados.</li>}
        {visible.map((i) => (
          <li key={i.id}>
            <button type="button" onClick={() => onSelect(i)} className="w-full text-left p-2 text-sm hover:bg-white">
              {i.name} <span className="text-gray-500">· {i.categoryName} · {variantSummary(i.variants)}</span>
            </button>
          </li>
        ))}
      </ul>
      <button type="button" onClick={onCancel} className="mt-2 text-sm text-gray-600 hover:text-gray-900">Cancelar</button>
    </div>
  )
}

export default ItemPicker
```

- [ ] **Step 2: `MenuItemModal.jsx`** — cambios:
  - Nueva prop `allItems` (lista plana `{id, name, categoryName, variants}`).
  - `const isLinked = variants.some((v) => v.fudo_product_id)`. Si `isLinked`: en lugar del `<select>` de categoría mostrar `<p className="text-sm text-gray-700">Categoría: <strong>{categoryName}</strong> <span className="text-xs text-gray-500">(de Fudo)</span></p>` donde `categoryName = categories.find((c) => c.id === form.category_id)?.name`. Si no, el select actual. En el payload enviar `category_id` sólo si `!isLinked`.
  - Si `item` existe, en el footer agregar (antes de Cancelar): botón **"Unir con otro ítem"** que muestra `<ItemPicker items={allItems} excludeId={item.id} onSelect={handleMerge} …/>` en el cuerpo del modal, y botón **"Ignorar"**.

```jsx
  const handleMerge = async (target) => {
    if (!window.confirm(`¿Unir "${item.name}" dentro de "${target.name}"? Sus precios pasan a ese ítem y este se elimina.`)) return
    setSaving(true)
    try {
      await menuService.mergeItem(target.id, item.id)
      onSaved()
    } catch (err) {
      setError(errorMessage(err, 'Error al unir los ítems'))
      setSaving(false)
    }
  }

  const handleIgnore = async () => {
    if (!window.confirm(`¿Ignorar "${item.name}"? Se quita de la carta y no se vuelve a crear al sincronizar.`)) return
    setSaving(true)
    try {
      await menuService.ignoreItem(item.id)
      onSaved()
    } catch (err) {
      setError(errorMessage(err, 'Error al ignorar el ítem'))
      setSaving(false)
    }
  }
```

  - Quitar el uso de `prefill` (ya no se crean ítems desde productos Fudo); el botón "Nuevo ítem" sólo existe en categorías manuales (Task 7).
  - En `Menu.jsx` y `MenuInbox.jsx`, pasar `allItems` (aplanar `menu.categories` → `{...item, categoryName: c.name}`).

- [ ] **Step 3: `MenuInbox.jsx`** — reescribir el contenido:
  - Título "Nuevos y alertas".
  - Sección **Nuevos por revisar ({inbox.new_items.length})**: por ítem: nombre, `category_name`, `variantSummary(item.variants)`, badge "oculto"; acciones: **Editar** (abre `MenuItemModal`), **Mostrar en la carta** (`updateItem(id, {is_visible: true})` → recarga; esto lo marca revisado), **Unir con…** (`ItemPicker` inline → `mergeItem(target.id, item.id)`), **Ignorar** (`ignoreItem`).
  - Sección **Alertas**: `type === 'variant'` → como hoy (Editar ítem); `type === 'category'` → "La categoría {category_name} ya no existe en Fudo (quedó oculta)" con link "Ver en la carta" a `/menu`.
  - Quitar todo lo de `unassigned`, `ignoreFudoProduct`, `prefill`.

- [ ] **Step 4: `Sidebar.jsx`** — renombrar el subítem `'Sin asignar'` → `'Nuevos y alertas'`.
- [ ] **Step 5:** `cd frontend && npm run build` → OK.
- [ ] **Step 6: Commit** — `feat(menu-admin): merge/ignore items and new-items inbox`

---

## Phase C — Carta pública (`menu-site/`)

### Task 9: Datos v2 (normalización y filtro anidado)

**Files:** Modify `menu-site/src/lib/loadMenu.js`, `menu-site/src/lib/filterMenu.js` y sus tests

- [ ] **Step 1: Tests** — en `loadMenu.test.js`:

```js
  it('convierte un menú v1 en un único grupo sin título', async () => {
    const v1 = { version: 1, settings: {}, tags: [], categories: [{ slug: 'cafes', name: 'Cafés', items: [] }] }
    const { menu } = await loadMenu({ url: 'u', fetchImpl: okFetch(v1), storage: memoryStorage() })
    expect(menu.version).toBe(2)
    expect(menu.groups).toEqual([{ slug: '_carta', name: null, categories: [{ slug: 'cafes', name: 'Cafés', show_title: true, items: [] }] }])
  })

  it('acepta v2 y completa show_title', async () => {
    const v2 = { version: 2, groups: [{ slug: 'g', name: 'G', categories: [{ slug: 'c', name: 'C', items: [{ id: 1, name: 'X' }] }] }] }
    const { menu } = await loadMenu({ url: 'u', fetchImpl: okFetch(v2), storage: memoryStorage() })
    expect(menu.groups[0].categories[0].show_title).toBe(true)
    expect(menu.groups[0].categories[0].items[0].tags).toEqual([])
  })
```

  (los tests existentes que usan `validMenu` v1 siguen válidos; los que comparan `menu` con `validMenu` deben comparar contra la versión normalizada: ajustar a `expect(result.source)` + `expect(result.menu.groups[0].categories)` según corresponda.)

  En `filterMenu.test.js`, cambiar el fixture a grupos:

```js
const groups = [
  { slug: 'g1', name: 'Desayuno', categories: [
    { slug: 'cafes', name: 'Cafés', items: [
      { id: 1, name: 'Café con leche', description: null, tags: [] },
      { id: 2, name: 'Latte', description: 'Con leche de almendras', tags: ['vegano'] },
    ] },
  ] },
  { slug: 'g2', name: 'Dulces', categories: [
    { slug: 'tortas', name: 'Tortas', items: [{ id: 3, name: 'Torta Galia', description: 'Masa de nuez', tags: ['sin-tacc', 'vegano'] }] },
  ] },
]
const ids = (result) => result.flatMap((g) => g.categories.flatMap((c) => c.items.map((i) => i.id)))
```

  y reescribir los 4 tests con `filterMenu(groups, …)`, verificando además que `filterMenu(groups, { query: 'CAFE' }).map((g) => g.slug)` es `['g1']` (oculta grupos vacíos).

  Run `cd menu-site && npm test` → FAIL.

- [ ] **Step 2: Implementación**
  - `loadMenu.js`: `isValidMenu` acepta `version === 1 && Array.isArray(categories)` o `version === 2 && Array.isArray(groups)`. `normalizeMenu`:

```js
function normalizeCategory(category) {
  return {
    ...category,
    show_title: category.show_title !== false,
    items: (Array.isArray(category.items) ? category.items : []).map((item) => ({
      ...item,
      tags: Array.isArray(item.tags) ? item.tags : [],
      variants: Array.isArray(item.variants) ? item.variants : [],
    })),
  }
}

function normalizeMenu(menu) {
  const groups = menu.version === 1
    ? [{ slug: '_carta', name: null, categories: menu.categories }]
    : menu.groups
  const { categories, ...rest } = menu
  return {
    ...rest,
    version: 2,
    tags: Array.isArray(menu.tags) ? menu.tags : [],
    settings: menu.settings && typeof menu.settings === 'object' ? menu.settings : {},
    groups: groups.map((group) => ({
      ...group,
      name: group.name ?? null,
      categories: (Array.isArray(group.categories) ? group.categories : []).map(normalizeCategory),
    })),
  }
}
```

  - `filterMenu.js`: `filterMenu(groups, opts)` aplica el filtro actual a las categorías de cada grupo y descarta grupos sin categorías (si no hay filtro, devuelve `groups` tal cual).

- [ ] **Step 3:** `npm test` → pasan.
- [ ] **Step 4: Commit** — `feat(menu-site): accept grouped menu v2 and filter nested groups`

---

### Task 10: UI en dos niveles

**Files:** Create `menu-site/src/components/GroupSection.jsx`; Modify `CategoryNav.jsx`, `CategorySection.jsx`, `App.jsx`, `public/menu.sample.json`

- [ ] **Step 1:** `CategoryNav.jsx` → navegar por grupos: renombrar props a `groups`, `sectionId = (slug) => \`grupo-${slug}\``, chips con `g.name`. Si hay un solo grupo y `name` es null, el nav muestra las **categorías** de ese grupo (comportamiento actual) con `sectionId` de categoría `cat-${slug}`. Implementarlo pasando desde `App` una lista `navEntries = [{slug, label, targetId}]`:

```jsx
  const navEntries = useMemo(() => {
    if (groups.length === 1 && groups[0].name === null) {
      return groups[0].categories.map((c) => ({ slug: c.slug, label: c.name, targetId: `cat-${c.slug}` }))
    }
    return groups.map((g) => ({ slug: g.slug, label: g.name, targetId: `grupo-${g.slug}` }))
  }, [groups])
```

  y `CategoryNav` pasa a recibir `entries` (usa `entry.targetId` para medir y para el `href`).

- [ ] **Step 2:** `GroupSection.jsx`:

```jsx
import CategorySection from './CategorySection'

export default function GroupSection({ group, tagsBySlug, onOpenPhoto }) {
  return (
    <section id={`grupo-${group.slug}`} className="scroll-mt-48 py-4">
      {group.name && <h2 className="font-display text-4xl uppercase tracking-wide">{group.name}</h2>}
      {group.categories.map((category) => (
        <CategorySection key={category.slug} category={category} nested={Boolean(group.name)} tagsBySlug={tagsBySlug} onOpenPhoto={onOpenPhoto} />
      ))}
    </section>
  )
}
```

- [ ] **Step 3:** `CategorySection.jsx` — prop `nested`; `id={\`cat-${category.slug}\`}` (mantener `scroll-mt-48`); título sólo si `category.show_title`: `nested ? <h3 className="mt-4 font-display text-2xl uppercase tracking-wide text-plum-light">` : el `<h2>` actual; la `description` se muestra si tiene texto aunque el título esté oculto.
- [ ] **Step 4:** `App.jsx` — usar `menu.groups` en vez de `menu.categories`; `filterMenu(menu.groups, …)`; renderizar `GroupSection` por grupo; `CategoryNav entries={navEntries}`.
- [ ] **Step 5:** `public/menu.sample.json` en v2 a mano: 2 grupos ("Desayuno y merienda" con Cafetería y Laminados; "Dulces" con Pastelería con `show_title: false` y descripción) + `"_otros"`/"Otros" con una categoría, usando ítems y precios reales de la carta actual (≥ 3 ítems por categoría, Torta Galia `featured` con tag `recomendado`, Cheesecake con tag `sin-tacc`).
- [ ] **Step 6:** `npm test && npm run build` → OK.
- [ ] **Step 7: Commit** — `feat(menu-site): two-level grouped menu with optional category titles`

---

## Phase D — Verificación

### Task 11: Prueba funcional local + revisión final

- [ ] **Step 1:** Base SQLite temporal nueva en el scratchpad (`create_all`), admin de prueba (credenciales en archivo del scratchpad, no en el chat), insertar categorías y productos Fudo falsos llamando a `sync_fudo_products(FakeFudoClient(...))` desde un script (≥ 3 categorías, 8 productos, uno sin categoría).
- [ ] **Step 2:** Levantar `backend-e2e`, `frontend`, `menu-site` (`.claude/launch.json`) y verificar en el navegador:
  1. `/menu/inbox` lista los 8 nuevos; "Mostrar en la carta" saca uno de la lista.
  2. "Unir con…" Porción + Entera → un ítem con dos precios.
  3. "Ignorar" → desaparece.
  4. Pestaña Grupos: crear 2, reordenar; en "Carta" asignar categorías; ocultar el título de una.
  5. `GET /api/v1/menu` + `build_snapshot()` (script) → JSON v2 con grupos en orden y `show_title`.
  6. Copiar ese snapshot a `menu-site/public/menu.sample.json` temporalmente (no commitear) y ver la carta en 375px: chips por grupo, subtítulos, categoría sin título.
- [ ] **Step 3:** Revisión final de todo el branch (subagente) → corregir lo que marque.
- [ ] **Step 4:** Push + PR (`gh pr create`), con checklist de deploy: la migración `carta_grupos_fudo` corre en `build.sh`; **deployar `menu-site` antes o junto con el backend** (acepta v1 y v2); después del deploy: "Sincronizar Fudo" (creará un ítem oculto por producto), revisar en "Nuevos y alertas", crear grupos y publicar.
