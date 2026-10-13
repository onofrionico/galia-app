# Sincronización de Productos con Fudo — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que el catálogo de Productos del POS se cree y actualice desde Fudo (nombre, categoría, precio, activo) en la misma sincronización que ya usa la carta, con los campos de Fudo bloqueados y la posibilidad de agrupar productos de Fudo como variantes.

**Architecture:** Un servicio nuevo `product_sync_service` recibe la caché `FudoProduct` y las categorías crudas de Fudo que ya descargó `menu_sync_service.sync_fudo_products`, y hace upsert de `product_categories` / `products` / `product_variants` dentro de la misma transacción. Las rutas de Productos y Categorías rechazan con 409 los cambios a campos que vienen de Fudo, y se agregan endpoints para sincronizar, listar candidatos de Fudo y mover (attach/detach) variantes vinculadas.

**Tech Stack:** Flask + SQLAlchemy + Alembic (backend, pytest con SQLite en memoria), React 18 + Vite + Tailwind (frontend, vitest en entorno node solo para utilidades puras).

**Spec:** `docs/superpowers/specs/2026-10-13-products-fudo-sync-design.md`

## Global Constraints

- Rama `feature/products-fudo-sync`, worktree `.claude/worktrees/products-fudo-sync`. Todos los comandos se corren desde ahí.
- Python del proyecto: `/c/Users/onofr/Desktop/galia-app/backend/venv/Scripts/python.exe` (el `python` del sistema no tiene las dependencias). En los comandos se abrevia `$PY`; definirlo con `PY=/c/Users/onofr/Desktop/galia-app/backend/venv/Scripts/python.exe`.
- Tests de backend: `cd backend && $PY -m pytest <archivo> -q -p no:cacheprovider`. Línea base antes de empezar: `test_menu_sync.py test_products.py test_product_categories.py test_menu_tasks.py test_menu_routes_ops.py` → 97 passed.
- Migración nueva: `b2b0_products_fudo_link`, `down_revision = 'b2a0_add_cash_registers'`.
- Texto del 409 de campo bloqueado, exacto: `Este dato se edita en Fudo`.
- Texto del 502 de sync, exacto: `Error sincronizando con Fudo. Revisá las credenciales o probá más tarde.`
- Estados de variante: `'ok' | 'inactive' | 'missing' | None`. Estado de categoría: `None | 'missing'`. Categoría sin categoría: `fudo_category_id='__none__'`, nombre `Sin categoría`.
- Sufijo de choque de nombre de categoría: ` (Fudo)`, luego ` (Fudo 2)`, ` (Fudo 3)`…
- Las estadísticas de Productos se devuelven dentro del resultado de `sync_fudo_products` bajo la clave **`catalog`** (la clave `products` ya existe y es el conteo de productos de Fudo): `{categories_created, products_created, variants_updated, alerts}`.
- Nunca se borra una `ProductVariant` vinculada (las ventas del POS la referencian por FK).
- La sync nunca toca: `description`, `image_url`, `has_recipe`, `track_stock`, receta, `stock_quantity`, `min_stock`, modificadores, ni `color`/`icon`/`description` de categorías.
- Frontend: no se agregan dependencias. Los tests de vitest son de utilidades puras (`environment: 'node'`, `include: src/**/*.test.js`).
- Commits terminan con `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

- Nombre de categoría de Fudo que coincide (ignorando mayúsculas) con una categoría manual existente: debe adoptarse, no romper por `unique(name)`. → test `test_adopts_unlinked_category_with_same_name_ignoring_case` (Task 2).
- Formulario que reenvía el objeto completo con los mismos valores (ProductDetail guarda `name` y `category_id` siempre): no debe dar 409. → tests `test_update_linked_product_with_same_values_is_ok` y `test_update_linked_variant_same_price_as_float_is_ok` (Task 4).
- Fudo responde sin categorías (lista vacía): no hay que marcar todas como `missing` ni mover productos existentes. → tests `test_empty_categories_do_not_mark_missing` (Task 2) y `test_unknown_category_keeps_existing_product_and_sends_new_to_sin_categoria` (Task 3).
- Producto de Fudo movido con attach que deja al Producto de origen sin variantes: el origen debe quedar inactivo y no aparecer en el POS, y la siguiente sync no debe reactivarlo. → test `test_attach_moves_variant_and_deactivates_empty_source` + `test_sync_after_attach_keeps_source_inactive` (Task 5).
- Dos syncs seguidas sin cambios en Fudo: nada cambia y las estadísticas quedan en cero. → test `test_sync_is_idempotent` (Task 3).

---

### Task 1: Columnas de Fudo en categorías y variantes

**Files:**
- Create: `backend/migrations/versions/b2b0_products_fudo_link.py`
- Modify: `backend/app/models/product_category.py`
- Modify: `backend/app/models/product_variant.py`
- Test: `backend/tests/test_product_sync.py` (archivo nuevo; las Tasks 2 y 3 le agregan tests)

**Interfaces:**
- Produces: `ProductCategory.fudo_category_id: str|None` (unique), `ProductCategory.fudo_status: str|None`; `ProductVariant.fudo_product_id: str|None` (unique), `ProductVariant.fudo_status: str|None`. Las cuatro aparecen en sus `to_dict()`.

- [ ] **Step 1: Write the failing test**

Crear `backend/tests/test_product_sync.py`:

```python
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.menu import FudoProduct
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_variant import ProductVariant
from app.services import menu_sync_service
from menu_fakes import FakeFudoClient, fudo_category, fudo_product


def _manual_product(name='Medialuna', category_name='Panadería', price='1500'):
    category = ProductCategory.query.filter_by(name=category_name).first()
    if category is None:
        category = ProductCategory(name=category_name)
        db.session.add(category)
        db.session.flush()
    product = Product(name=name, category_id=category.id)
    db.session.add(product)
    db.session.flush()
    db.session.add(ProductVariant(product_id=product.id, name=name, price=Decimal(price)))
    db.session.commit()
    return product


def test_fudo_columns_in_to_dict(menu_app):
    category = ProductCategory(name='Cafés', fudo_category_id='7')
    db.session.add(category)
    db.session.flush()
    product = Product(name='Latte', category_id=category.id)
    db.session.add(product)
    db.session.flush()
    variant = ProductVariant(product_id=product.id, name='Latte', price=Decimal('6500'),
                             fudo_product_id='42', fudo_status='ok')
    db.session.add(variant)
    db.session.commit()

    assert category.to_dict()['fudo_category_id'] == '7'
    assert category.to_dict()['fudo_status'] is None
    assert variant.to_dict()['fudo_product_id'] == '42'
    assert variant.to_dict()['fudo_status'] == 'ok'


def test_fudo_product_id_is_unique(menu_app):
    product = _manual_product()
    db.session.add(ProductVariant(product_id=product.id, name='A', price=1, fudo_product_id='9'))
    db.session.add(ProductVariant(product_id=product.id, name='B', price=1, fudo_product_id='9'))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && $PY -m pytest tests/test_product_sync.py -q -p no:cacheprovider`
Expected: FAIL con `TypeError: 'fudo_category_id' is an invalid keyword argument for ProductCategory`.

- [ ] **Step 3: Add the model columns**

En `backend/app/models/product_category.py`, debajo de `is_active`:

```python
    fudo_category_id = db.Column(db.String(20), unique=True, nullable=True)
    fudo_status = db.Column(db.String(20), nullable=True)  # None | 'missing'
```

y en `to_dict()`, después de `'is_active': self.is_active,`:

```python
            'fudo_category_id': self.fudo_category_id,
            'fudo_status': self.fudo_status,
```

En `backend/app/models/product_variant.py`, debajo de `is_active`:

```python
    fudo_product_id = db.Column(db.String(20), unique=True, nullable=True)
    fudo_status = db.Column(db.String(20), nullable=True)  # 'ok' | 'inactive' | 'missing' | None (no vinculada)
```

y en `to_dict()`, después de `'is_active': self.is_active,`:

```python
            'fudo_product_id': self.fudo_product_id,
            'fudo_status': self.fudo_status,
```

- [ ] **Step 4: Write the migration**

Crear `backend/migrations/versions/b2b0_products_fudo_link.py`:

```python
"""link product categories and variants to Fudo

Revision ID: b2b0_products_fudo_link
Revises: b2a0_add_cash_registers
Create Date: 2026-10-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b2b0_products_fudo_link'
down_revision = 'b2a0_add_cash_registers'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('product_categories') as batch:
        batch.add_column(sa.Column('fudo_category_id', sa.String(20), nullable=True))
        batch.add_column(sa.Column('fudo_status', sa.String(20), nullable=True))
        batch.create_unique_constraint('uq_product_categories_fudo_category_id', ['fudo_category_id'])
    with op.batch_alter_table('product_variants') as batch:
        batch.add_column(sa.Column('fudo_product_id', sa.String(20), nullable=True))
        batch.add_column(sa.Column('fudo_status', sa.String(20), nullable=True))
        batch.create_unique_constraint('uq_product_variants_fudo_product_id', ['fudo_product_id'])


def downgrade():
    with op.batch_alter_table('product_variants') as batch:
        batch.drop_constraint('uq_product_variants_fudo_product_id', type_='unique')
        batch.drop_column('fudo_status')
        batch.drop_column('fudo_product_id')
    with op.batch_alter_table('product_categories') as batch:
        batch.drop_constraint('uq_product_categories_fudo_category_id', type_='unique')
        batch.drop_column('fudo_status')
        batch.drop_column('fudo_category_id')
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && $PY -m pytest tests/test_product_sync.py tests/test_products.py tests/test_product_categories.py -q -p no:cacheprovider`
Expected: PASS (todos).

Verificar que Alembic tiene un solo head: `cd backend && grep -rl "down_revision = 'b2b0" migrations/versions/` → sin resultados, y `grep -rl "down_revision = 'b2a0" migrations/versions/` → solo `b2b0_products_fudo_link.py`.

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/product_category.py backend/app/models/product_variant.py backend/migrations/versions/b2b0_products_fudo_link.py backend/tests/test_product_sync.py
git commit -m "feat(products): add Fudo link columns to categories and variants

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Sincronización de categorías de Productos

**Files:**
- Create: `backend/app/services/product_sync_service.py`
- Test: `backend/tests/test_product_sync.py` (agregar)

**Interfaces:**
- Consumes: columnas de la Task 1.
- Produces:
  - `NO_CATEGORY_ID = '__none__'`, `NO_CATEGORY_NAME = 'Sin categoría'`
  - `sync_product_categories(raw_categories: list[dict], stats: dict) -> dict[str, ProductCategory]` — `stats` debe traer la clave `categories_created`; devuelve el mapa `fudo_category_id → ProductCategory` (incluye las ya vinculadas que no vinieron).
  - `upsert_category(by_fudo_id: dict, fudo_category_id: str, name: str, stats: dict) -> ProductCategory` (la usa la Task 3 para "Sin categoría").

- [ ] **Step 1: Write the failing tests**

Agregar a `backend/tests/test_product_sync.py`:

```python
from app.services import product_sync_service


def _stats():
    return {'categories_created': 0}


def test_creates_categories_from_fudo(menu_app):
    stats = _stats()
    result = product_sync_service.sync_product_categories(
        [fudo_category(1, 'Cafés'), fudo_category(2, 'Pastelería')], stats)
    db.session.commit()

    assert set(result) == {'1', '2'}
    assert result['1'].name == 'Cafés'
    assert result['1'].is_active is True
    assert stats['categories_created'] == 2


def test_adopts_unlinked_category_with_same_name_ignoring_case(menu_app):
    manual = ProductCategory(name='cafés', color='#123456', icon='☕')
    db.session.add(manual)
    db.session.commit()

    stats = _stats()
    result = product_sync_service.sync_product_categories([fudo_category(1, 'Cafés')], stats)
    db.session.commit()

    assert result['1'].id == manual.id
    assert manual.fudo_category_id == '1'
    assert manual.color == '#123456' and manual.icon == '☕'
    assert stats['categories_created'] == 0
    assert ProductCategory.query.count() == 1


def test_name_clash_with_other_linked_category_gets_suffix(menu_app):
    product_sync_service.sync_product_categories([fudo_category(1, 'Bebidas')], _stats())
    result = product_sync_service.sync_product_categories(
        [fudo_category(1, 'Bebidas'), fudo_category(2, 'Bebidas')], _stats())
    db.session.commit()

    assert result['1'].name == 'Bebidas'
    assert result['2'].name == 'Bebidas (Fudo)'


def test_suffixed_name_is_stable_across_syncs(menu_app):
    raw = [fudo_category(1, 'Bebidas'), fudo_category(2, 'Bebidas')]
    product_sync_service.sync_product_categories(raw, _stats())
    result = product_sync_service.sync_product_categories(raw, _stats())
    db.session.commit()

    assert result['2'].name == 'Bebidas (Fudo)'


def test_renames_linked_category(menu_app):
    product_sync_service.sync_product_categories([fudo_category(1, 'Cafes')], _stats())
    result = product_sync_service.sync_product_categories([fudo_category(1, 'Cafés de especialidad')], _stats())
    db.session.commit()

    assert result['1'].name == 'Cafés de especialidad'


def test_missing_category_is_deactivated_and_comes_back(menu_app):
    product_sync_service.sync_product_categories([fudo_category(1, 'Cafés'), fudo_category(2, 'Té')], _stats())
    result = product_sync_service.sync_product_categories([fudo_category(1, 'Cafés')], _stats())
    db.session.commit()
    assert result['2'].is_active is False
    assert result['2'].fudo_status == 'missing'

    result = product_sync_service.sync_product_categories([fudo_category(1, 'Cafés'), fudo_category(2, 'Té')], _stats())
    db.session.commit()
    assert result['2'].is_active is True
    assert result['2'].fudo_status is None


def test_empty_categories_do_not_mark_missing(menu_app):
    product_sync_service.sync_product_categories([fudo_category(1, 'Cafés')], _stats())
    result = product_sync_service.sync_product_categories([], _stats())
    db.session.commit()

    assert result['1'].is_active is True
    assert result['1'].fudo_status is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && $PY -m pytest tests/test_product_sync.py -q -p no:cacheprovider`
Expected: FAIL con `ImportError: cannot import name 'product_sync_service'`.

- [ ] **Step 3: Implement the categories sync**

Crear `backend/app/services/product_sync_service.py`:

```python
"""Sincroniza el catálogo de Productos (POS) desde la caché de Fudo que actualiza la carta.

Durante la transición Fudo es la fuente de verdad de nombre, categoría, precio y estado.
No hace commit: lo hace quien lo llama (menu_sync_service.sync_fudo_products).
"""
from sqlalchemy import func

from app.extensions import db
from app.models.product_category import ProductCategory

NO_CATEGORY_ID = '__none__'
NO_CATEGORY_NAME = 'Sin categoría'


def _name_taken(name, exclude_id=None):
    query = ProductCategory.query.filter(func.lower(ProductCategory.name) == name.lower())
    if exclude_id is not None:
        query = query.filter(ProductCategory.id != exclude_id)
    return db.session.query(query.exists()).scalar()


def _free_name(base, exclude_id=None):
    """El nombre de Fudo, o con sufijo ' (Fudo)', ' (Fudo 2)'... si ya lo usa otra categoría."""
    base = base.strip()[:100] or 'Sin nombre'
    if not _name_taken(base, exclude_id):
        return base
    n = 1
    while True:
        suffix = ' (Fudo)' if n == 1 else f' (Fudo {n})'
        candidate = base[:100 - len(suffix)] + suffix
        if not _name_taken(candidate, exclude_id):
            return candidate
        n += 1


def upsert_category(by_fudo_id, fudo_category_id, name, stats):
    category = by_fudo_id.get(fudo_category_id)
    if category is None:
        clean = name.strip()[:100] or 'Sin nombre'
        category = ProductCategory.query.filter(
            func.lower(ProductCategory.name) == clean.lower(),
            ProductCategory.fudo_category_id.is_(None),
        ).first()
        if category is None:
            category = ProductCategory(name=_free_name(clean))
            db.session.add(category)
            stats['categories_created'] += 1
        category.fudo_category_id = fudo_category_id
        by_fudo_id[fudo_category_id] = category
    else:
        new_name = _free_name(name, exclude_id=category.id)
        if category.name != new_name:
            category.name = new_name
    category.is_active = True
    category.fudo_status = None
    db.session.flush()
    return category


def sync_product_categories(raw_categories, stats):
    """Upsert de las categorías de Fudo. Devuelve {fudo_category_id: ProductCategory}."""
    by_fudo_id = {
        c.fudo_category_id: c
        for c in ProductCategory.query.filter(ProductCategory.fudo_category_id.isnot(None))
    }
    if not raw_categories:
        return by_fudo_id
    seen = set()
    for raw in raw_categories:
        fudo_category_id = str(raw['id'])
        seen.add(fudo_category_id)
        name = (raw.get('attributes') or {}).get('name') or 'Sin nombre'
        upsert_category(by_fudo_id, fudo_category_id, name, stats)
    for fudo_category_id, category in by_fudo_id.items():
        if fudo_category_id not in seen and fudo_category_id != NO_CATEGORY_ID:
            category.is_active = False
            category.fudo_status = 'missing'
    return by_fudo_id
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && $PY -m pytest tests/test_product_sync.py -q -p no:cacheprovider`
Expected: PASS (9 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/product_sync_service.py backend/tests/test_product_sync.py
git commit -m "feat(products): sync product categories from Fudo

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Sincronización de productos y variantes, integrada a la sync de la carta

**Files:**
- Modify: `backend/app/services/product_sync_service.py`
- Modify: `backend/app/services/menu_sync_service.py:99-177` (`sync_fudo_products`)
- Test: `backend/tests/test_product_sync.py` (agregar)
- Test: `backend/tests/test_menu_tasks.py` (agregar un test)

**Interfaces:**
- Consumes: `sync_product_categories`, `upsert_category`, `NO_CATEGORY_ID`, `NO_CATEGORY_NAME` (Task 2).
- Produces:
  - `sync_products_from_cache(fudo_products: list[FudoProduct], raw_categories: list[dict]) -> dict` con claves `categories_created, products_created, variants_updated, alerts`. No hace commit.
  - `menu_sync_service.sync_fudo_products(client)` agrega `'catalog': <ese dict>` a su resultado.

- [ ] **Step 1: Write the failing tests**

Agregar a `backend/tests/test_product_sync.py`:

```python
def _sync(products, categories=None):
    return menu_sync_service.sync_fudo_products(FakeFudoClient(products=products, categories=categories or []))


def _variant(fudo_id):
    return ProductVariant.query.filter_by(fudo_product_id=str(fudo_id)).one()


def test_creates_products_from_scratch(menu_app):
    result = _sync([fudo_product(1, 'Latte', 6500), fudo_product(2, 'Té verde', 3000, active=False)],
                   [fudo_category(1, 'Cafés')])

    variant = _variant(1)
    product = db.session.get(Product, variant.product_id)
    assert product.name == 'Latte'
    assert product.category.name == 'Cafés'
    assert product.is_active is True
    assert variant.name == 'Latte'
    assert Decimal(variant.price) == Decimal('6500')
    assert variant.fudo_status == 'ok'
    assert Decimal(variant.stock_quantity) == 0
    assert ProductVariant.query.filter_by(fudo_product_id='2').count() == 0
    assert result['catalog'] == {'categories_created': 1, 'products_created': 1, 'variants_updated': 0, 'alerts': 0}


def test_updates_price_and_name(menu_app):
    _sync([fudo_product(1, 'Latte', 6500)], [fudo_category(1, 'Cafés')])
    result = _sync([fudo_product(1, 'Latte grande', 6900)], [fudo_category(1, 'Cafés')])

    variant = _variant(1)
    assert variant.name == 'Latte grande'
    assert Decimal(variant.price) == Decimal('6900')
    assert db.session.get(Product, variant.product_id).name == 'Latte grande'
    assert result['catalog']['variants_updated'] == 1


def test_inactive_in_fudo_deactivates_variant_and_product(menu_app):
    _sync([fudo_product(1, 'Latte', 6500)], [fudo_category(1, 'Cafés')])
    result = _sync([fudo_product(1, 'Latte', 6500, active=False)], [fudo_category(1, 'Cafés')])

    variant = _variant(1)
    assert variant.is_active is False
    assert variant.fudo_status == 'inactive'
    assert db.session.get(Product, variant.product_id).is_active is False
    assert result['catalog']['alerts'] == 1


def test_missing_in_fudo_keeps_variant_inactive(menu_app):
    _sync([fudo_product(1, 'Latte', 6500), fudo_product(2, 'Té', 3000)], [fudo_category(1, 'Cafés')])
    _sync([fudo_product(2, 'Té', 3000)], [fudo_category(1, 'Cafés')])

    variant = _variant(1)
    assert variant.is_active is False
    assert variant.fudo_status == 'missing'
    assert db.session.get(Product, variant.product_id) is not None


def test_reactivated_in_fudo_comes_back(menu_app):
    _sync([fudo_product(1, 'Latte', 6500)], [fudo_category(1, 'Cafés')])
    _sync([fudo_product(1, 'Latte', 6500, active=False)], [fudo_category(1, 'Cafés')])
    _sync([fudo_product(1, 'Latte', 6500)], [fudo_category(1, 'Cafés')])

    variant = _variant(1)
    assert variant.is_active is True
    assert variant.fudo_status == 'ok'
    assert db.session.get(Product, variant.product_id).is_active is True


def test_moves_product_when_fudo_category_changes(menu_app):
    categories = [fudo_category(1, 'Cafés'), fudo_category(2, 'Especiales')]
    _sync([fudo_product(1, 'Latte', 6500, category_id='1')], categories)
    _sync([fudo_product(1, 'Latte', 6500, category_id='2')], categories)

    product = db.session.get(Product, _variant(1).product_id)
    assert product.category.name == 'Especiales'


def test_product_without_category_goes_to_sin_categoria(menu_app):
    _sync([fudo_product(1, 'Agua', 1000, category_id=None)], [fudo_category(1, 'Cafés')])

    product = db.session.get(Product, _variant(1).product_id)
    assert product.category.name == 'Sin categoría'
    assert product.category.fudo_category_id == '__none__'


def test_unknown_category_keeps_existing_product_and_sends_new_to_sin_categoria(menu_app):
    _sync([fudo_product(1, 'Latte', 6500, category_id='1')], [fudo_category(1, 'Cafés')])
    _sync([fudo_product(1, 'Latte', 6500, category_id='9'), fudo_product(2, 'Té', 3000, category_id='9')], [])

    assert db.session.get(Product, _variant(1).product_id).category.name == 'Cafés'
    assert db.session.get(Product, _variant(2).product_id).category.name == 'Sin categoría'


def test_grouped_product_keeps_galia_name(menu_app):
    categories = [fudo_category(1, 'Cafés')]
    _sync([fudo_product(1, 'Café chico', 3000), fudo_product(2, 'Café grande', 3500)], categories)
    target = db.session.get(Product, _variant(1).product_id)
    _variant(2).product_id = target.id
    target.name = 'Café'
    db.session.commit()

    _sync([fudo_product(1, 'Café chico', 3200), fudo_product(2, 'Café grande', 3700)], categories)

    assert target.name == 'Café'
    assert _variant(1).name == 'Café chico'
    assert Decimal(_variant(2).price) == Decimal('3700')


def test_sync_never_touches_galia_fields(menu_app):
    _sync([fudo_product(1, 'Latte', 6500)], [fudo_category(1, 'Cafés')])
    variant = _variant(1)
    product = db.session.get(Product, variant.product_id)
    product.description = 'Con leche de almendras'
    product.image_url = 'https://cdn.test/latte.webp'
    product.has_recipe = True
    product.track_stock = True
    variant.stock_quantity = Decimal('12')
    variant.min_stock = Decimal('3')
    product.category.color = '#ff0000'
    product.category.icon = '☕'
    db.session.commit()

    _sync([fudo_product(1, 'Latte', 7000)], [fudo_category(1, 'Cafés')])

    assert product.description == 'Con leche de almendras'
    assert product.image_url == 'https://cdn.test/latte.webp'
    assert product.has_recipe is True and product.track_stock is True
    assert Decimal(variant.stock_quantity) == Decimal('12')
    assert Decimal(variant.min_stock) == Decimal('3')
    assert product.category.color == '#ff0000' and product.category.icon == '☕'


def test_manual_products_are_left_alone(menu_app):
    manual = _manual_product('Medialuna', 'Panadería')
    _sync([fudo_product(1, 'Latte', 6500)], [fudo_category(1, 'Cafés')])

    assert manual.name == 'Medialuna'
    assert manual.is_active is True
    assert manual.variants.first().fudo_product_id is None


def test_ignored_menu_products_are_still_created(menu_app):
    db.session.add(FudoProduct(fudo_id='1', name='Latte', price=Decimal('6500'), ignored=True))
    db.session.commit()

    _sync([fudo_product(1, 'Latte', 6500)], [fudo_category(1, 'Cafés')])

    assert ProductVariant.query.filter_by(fudo_product_id='1').count() == 1


def test_sync_is_idempotent(menu_app):
    products = [fudo_product(1, 'Latte', 6500), fudo_product(2, 'Té', 3000, category_id=None)]
    categories = [fudo_category(1, 'Cafés'), fudo_category(2, 'Cafés')]
    _sync(products, categories)
    snapshot = sorted((p.id, p.name, p.category_id, p.is_active) for p in Product.query.all())

    result = _sync(products, categories)

    assert result['catalog'] == {'categories_created': 0, 'products_created': 0, 'variants_updated': 0, 'alerts': 0}
    assert sorted((p.id, p.name, p.category_id, p.is_active) for p in Product.query.all()) == snapshot


def test_fudo_failure_changes_nothing(menu_app):
    _sync([fudo_product(1, 'Latte', 6500)], [fudo_category(1, 'Cafés')])
    with pytest.raises(ValueError):
        _sync([], [fudo_category(1, 'Cafés')])
    db.session.rollback()

    assert _variant(1).fudo_status == 'ok'
```

Agregar a `backend/tests/test_menu_tasks.py`:

```python
def test_nightly_sync_includes_products_catalog(menu_app, storage):
    result = sync_and_publish(FakeFudoClient(products=[fudo_product(1, 'Latte', 6900)]), storage)

    assert result['catalog']['products_created'] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && $PY -m pytest tests/test_product_sync.py tests/test_menu_tasks.py -q -p no:cacheprovider`
Expected: FAIL con `KeyError: 'catalog'` / `NoResultFound`.

- [ ] **Step 3: Implement products sync**

Agregar a `backend/app/services/product_sync_service.py` (imports arriba, funciones abajo):

```python
from decimal import Decimal

from app.models.product import Product
from app.models.product_variant import ProductVariant


def _category_for(fudo_product, categories, stats, existing=False):
    """Categoría para un producto de Fudo. None = categoría desconocida en un producto existente: no mover."""
    if fudo_product.fudo_category_id and fudo_product.fudo_category_id in categories:
        return categories[fudo_product.fudo_category_id]
    if fudo_product.fudo_category_id and existing:
        return None
    return upsert_category(categories, NO_CATEGORY_ID, NO_CATEGORY_NAME, stats)


def _sync_linked_variants(linked, by_id, stats):
    for variant in linked:
        fudo = by_id.get(variant.fudo_product_id)
        if fudo is None:
            variant.is_active = False
            variant.fudo_status = 'missing'
        else:
            name = fudo.name[:100] or 'Sin nombre'
            if variant.name != name or Decimal(str(variant.price)) != Decimal(str(fudo.price)):
                stats['variants_updated'] += 1
            variant.name = name
            variant.price = fudo.price
            variant.is_active = bool(fudo.is_active)
            variant.fudo_status = 'ok' if fudo.is_active else 'inactive'
        if variant.fudo_status != 'ok':
            stats['alerts'] += 1


def _sync_linked_products(linked, by_id, categories, stats):
    variants_by_product = {}
    for variant in linked:
        variants_by_product.setdefault(variant.product_id, []).append(variant)
    for product_id, variants in variants_by_product.items():
        product = db.session.get(Product, product_id)
        in_cache = [by_id[v.fudo_product_id] for v in variants if v.fudo_product_id in by_id]
        if in_cache:
            if len(variants) == 1:
                product.name = in_cache[0].name[:200] or 'Sin nombre'
            category = _category_for(in_cache[0], categories, stats, existing=True)
            if category is not None:
                product.category_id = category.id
        db.session.flush()
        product.is_active = product.variants.filter_by(is_active=True).count() > 0


def _create_new_products(fudo_products, linked_ids, categories, stats):
    for fudo in fudo_products:
        if not fudo.is_active or fudo.fudo_id in linked_ids:
            continue
        name = fudo.name or 'Sin nombre'
        category = _category_for(fudo, categories, stats)
        product = Product(name=name[:200], category_id=category.id, is_active=True)
        db.session.add(product)
        db.session.flush()
        db.session.add(ProductVariant(
            product_id=product.id, name=name[:100], price=fudo.price,
            fudo_product_id=fudo.fudo_id, fudo_status='ok', is_active=True,
        ))
        linked_ids.add(fudo.fudo_id)
        stats['products_created'] += 1


def sync_products_from_cache(fudo_products, raw_categories):
    """Actualiza categorías, Productos y variantes desde la caché de Fudo. No hace commit."""
    stats = {'categories_created': 0, 'products_created': 0, 'variants_updated': 0, 'alerts': 0}
    categories = sync_product_categories(raw_categories, stats)
    by_id = {p.fudo_id: p for p in fudo_products}

    linked = (
        ProductVariant.query.filter(ProductVariant.fudo_product_id.isnot(None))
        .order_by(ProductVariant.id).all()
    )
    _sync_linked_variants(linked, by_id, stats)
    _sync_linked_products(linked, by_id, categories, stats)
    _create_new_products(fudo_products, {v.fudo_product_id for v in linked}, categories, stats)
    db.session.flush()
    return stats
```

- [ ] **Step 4: Wire it into the menu sync**

En `backend/app/services/menu_sync_service.py`:

Agregar el import:

```python
from app.services import product_sync_service
```

En `sync_fudo_products`, reemplazar

```python
    categories = _sync_categories(client.get_all_product_categories(), stats)
```

por

```python
    raw_categories = client.get_all_product_categories()
    categories = _sync_categories(raw_categories, stats)
```

y reemplazar el final

```python
    db.session.commit()
    return {'products': len(by_id), 'price_changes': price_changes, 'alerts': alerts, **stats}
```

por

```python
    catalog = product_sync_service.sync_products_from_cache(list(by_id.values()), raw_categories)
    db.session.commit()
    return {'products': len(by_id), 'price_changes': price_changes, 'alerts': alerts, **stats, 'catalog': catalog}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && $PY -m pytest tests/test_product_sync.py tests/test_menu_tasks.py tests/test_menu_sync.py tests/test_menu_routes_ops.py -q -p no:cacheprovider`
Expected: PASS. Si algún test existente de `test_menu_sync.py` compara el dict completo del resultado y falla por la clave `catalog`, actualizar esa aserción para incluir `'catalog': ANY` (de `unittest.mock`) — no cambiar el comportamiento.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/product_sync_service.py backend/app/services/menu_sync_service.py backend/tests/test_product_sync.py backend/tests/test_menu_tasks.py backend/tests/test_menu_sync.py
git commit -m "feat(products): create and update POS catalog from Fudo during menu sync

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Bloqueo de campos de Fudo en la API

**Files:**
- Create: `backend/app/services/product_fudo_info.py`
- Modify: `backend/app/routes/products.py` (`list_products`, `get_product`, `update_product`, `delete_product`, `update_variant`, `delete_variant`)
- Modify: `backend/app/routes/product_categories.py` (`update_category`, `delete_category`)
- Test: `backend/tests/test_products_fudo_lock.py`

**Interfaces:**
- Consumes: columnas de la Task 1.
- Produces (en `app.services.product_fudo_info`):
  - `FUDO_LOCKED_ERROR = 'Este dato se edita en Fudo'`
  - `LOCKED_VARIANT_FIELDS = ('name', 'price', 'is_active')`, `LOCKED_CATEGORY_FIELDS = ('name', 'is_active')`
  - `fudo_info(product_ids: list[int]) -> dict[int, {'linked': int, 'alerts': int}]` (solo Productos con variantes vinculadas)
  - `locked_product_fields(entry: dict|None) -> list[str]` → `[]`, o `['category_id', 'is_active']`, o `['name', 'category_id', 'is_active']` si `entry['linked'] == 1`
  - `fudo_payload(entry: dict|None) -> {'fudo_linked': bool, 'fudo_locked_fields': list[str], 'fudo_alerts': int}`
  - `changes_locked(data: dict, fields: Iterable[str], obj) -> bool`
  - `product_detail(product: Product) -> dict` (formato de `GET /products/<id>`; la Task 5 lo reutiliza)
- `GET /products` y `GET /products/<id>` agregan `fudo_linked`, `fudo_locked_fields`, `fudo_alerts` a cada producto. `GET /products?fudo_alerts=true` devuelve solo Productos (activos o no) con alguna variante `missing` o `inactive`.

- [ ] **Step 1: Write the failing tests**

Crear `backend/tests/test_products_fudo_lock.py`:

```python
from decimal import Decimal

from app.extensions import db
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_variant import ProductVariant
from app.services import menu_sync_service
from menu_fakes import FakeFudoClient, fudo_category, fudo_product


def _linked(products=None):
    menu_sync_service.sync_fudo_products(FakeFudoClient(
        products=products or [fudo_product(1, 'Latte', 6500)], categories=[fudo_category(1, 'Cafés')]))
    variant = ProductVariant.query.filter_by(fudo_product_id='1').one()
    return db.session.get(Product, variant.product_id), variant


def test_get_product_reports_locked_fields(menu_client, admin_headers):
    product, _ = _linked()
    data = menu_client.get(f'/api/v1/products/{product.id}', headers=admin_headers).get_json()

    assert data['fudo_linked'] is True
    assert data['fudo_locked_fields'] == ['name', 'category_id', 'is_active']
    assert data['fudo_alerts'] == 0
    assert data['variants'][0]['fudo_product_id'] == '1'


def test_list_reports_fudo_fields(menu_client, admin_headers):
    _linked()
    data = menu_client.get('/api/v1/products', headers=admin_headers).get_json()

    assert data['products'][0]['fudo_linked'] is True


def test_update_linked_product_locked_fields_is_409(menu_client, admin_headers):
    product, _ = _linked()
    other = ProductCategory(name='Otra')
    db.session.add(other)
    db.session.commit()
    url = f'/api/v1/products/{product.id}'

    for body in ({'name': 'Otro'}, {'category_id': other.id}, {'is_active': False}):
        response = menu_client.put(url, json=body, headers=admin_headers)
        assert response.status_code == 409, body
        assert response.get_json()['error'] == 'Este dato se edita en Fudo'
    assert product.name == 'Latte'


def test_update_linked_product_with_same_values_is_ok(menu_client, admin_headers):
    product, _ = _linked()
    response = menu_client.put(f'/api/v1/products/{product.id}', json={
        'name': ' Latte ', 'category_id': product.category_id, 'description': 'Rico', 'image_url': '',
        'has_recipe': True, 'track_stock': True,
    }, headers=admin_headers)

    assert response.status_code == 200
    assert response.get_json()['description'] == 'Rico'


def test_grouped_product_name_is_editable(menu_client, admin_headers):
    product, _ = _linked([fudo_product(1, 'Café chico', 3000), fudo_product(2, 'Café grande', 3500)])
    ProductVariant.query.filter_by(fudo_product_id='2').one().product_id = product.id
    db.session.commit()

    data = menu_client.get(f'/api/v1/products/{product.id}', headers=admin_headers).get_json()
    assert data['fudo_locked_fields'] == ['category_id', 'is_active']
    response = menu_client.put(f'/api/v1/products/{product.id}', json={'name': 'Café'}, headers=admin_headers)
    assert response.status_code == 200


def test_delete_linked_product_is_409(menu_client, admin_headers):
    product, _ = _linked()
    response = menu_client.delete(f'/api/v1/products/{product.id}', headers=admin_headers)

    assert response.status_code == 409
    assert product.is_active is True


def test_update_linked_variant_locked_fields_is_409(menu_client, admin_headers):
    product, variant = _linked()
    url = f'/api/v1/products/{product.id}/variants/{variant.id}'

    for body in ({'name': 'Otro'}, {'price': 1}, {'is_active': False}):
        assert menu_client.put(url, json=body, headers=admin_headers).status_code == 409, body


def test_update_linked_variant_stock_is_ok(menu_client, admin_headers):
    product, variant = _linked()
    response = menu_client.put(f'/api/v1/products/{product.id}/variants/{variant.id}',
                               json={'stock_quantity': 5, 'min_stock': 1}, headers=admin_headers)

    assert response.status_code == 200
    assert Decimal(str(variant.stock_quantity)) == Decimal('5')


def test_update_linked_variant_same_price_as_float_is_ok(menu_client, admin_headers):
    product, variant = _linked()
    response = menu_client.put(f'/api/v1/products/{product.id}/variants/{variant.id}',
                               json={'price': 6500.0, 'name': 'Latte'}, headers=admin_headers)

    assert response.status_code == 200


def test_delete_linked_variant_is_409(menu_client, admin_headers):
    product, variant = _linked()
    response = menu_client.delete(f'/api/v1/products/{product.id}/variants/{variant.id}', headers=admin_headers)

    assert response.status_code == 409
    assert variant.is_active is True


def test_manual_variant_on_linked_product_is_editable(menu_client, admin_headers):
    product, _ = _linked()
    created = menu_client.post(f'/api/v1/products/{product.id}/variants',
                               json={'name': 'Extra shot', 'price': 800}, headers=admin_headers)
    assert created.status_code == 201
    variant_id = created.get_json()['id']

    response = menu_client.put(f'/api/v1/products/{product.id}/variants/{variant_id}',
                               json={'price': 900}, headers=admin_headers)
    assert response.status_code == 200
    assert menu_client.delete(f'/api/v1/products/{product.id}/variants/{variant_id}',
                              headers=admin_headers).status_code == 200


def test_linked_category_locks_name_and_active(menu_client, admin_headers):
    product, _ = _linked()
    url = f'/api/v1/product-categories/{product.category_id}'

    assert menu_client.put(url, json={'name': 'Otra'}, headers=admin_headers).status_code == 409
    assert menu_client.put(url, json={'is_active': False}, headers=admin_headers).status_code == 409
    assert menu_client.delete(url, headers=admin_headers).status_code == 409
    response = menu_client.put(url, json={'name': 'Cafés', 'color': '#00ff00', 'icon': '☕', 'description': 'x'},
                               headers=admin_headers)
    assert response.status_code == 200
    assert response.get_json()['color'] == '#00ff00'


def test_fudo_alerts_filter(menu_client, admin_headers):
    _linked([fudo_product(1, 'Latte', 6500), fudo_product(2, 'Té', 3000)])
    menu_sync_service.sync_fudo_products(FakeFudoClient(
        products=[fudo_product(1, 'Latte', 6500)], categories=[fudo_category(1, 'Cafés')]))

    data = menu_client.get('/api/v1/products?fudo_alerts=true', headers=admin_headers).get_json()

    assert [p['name'] for p in data['products']] == ['Té']
    assert data['products'][0]['fudo_alerts'] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && $PY -m pytest tests/test_products_fudo_lock.py -q -p no:cacheprovider`
Expected: FAIL (`KeyError: 'fudo_linked'`, 200 en lugar de 409).

- [ ] **Step 3: Implement the info helpers**

Crear `backend/app/services/product_fudo_info.py`:

```python
"""Qué datos de un Producto vienen de Fudo y, por lo tanto, no se editan en Galia."""
from decimal import Decimal, InvalidOperation

from app.extensions import db
from app.models.product_recipe_item import ProductRecipeItem
from app.models.product_variant import ProductVariant

FUDO_LOCKED_ERROR = 'Este dato se edita en Fudo'
LOCKED_VARIANT_FIELDS = ('name', 'price', 'is_active')
LOCKED_CATEGORY_FIELDS = ('name', 'is_active')
ALERT_STATUSES = ('missing', 'inactive')


def fudo_info(product_ids):
    """{product_id: {'linked': n, 'alerts': n}} para los Productos con variantes vinculadas a Fudo."""
    if not product_ids:
        return {}
    rows = (
        db.session.query(ProductVariant.product_id, ProductVariant.fudo_status)
        .filter(ProductVariant.product_id.in_(product_ids), ProductVariant.fudo_product_id.isnot(None))
        .all()
    )
    info = {}
    for product_id, status in rows:
        entry = info.setdefault(product_id, {'linked': 0, 'alerts': 0})
        entry['linked'] += 1
        if status in ALERT_STATUSES:
            entry['alerts'] += 1
    return info


def locked_product_fields(entry):
    if not entry:
        return []
    fields = ['category_id', 'is_active']
    if entry['linked'] == 1:
        fields.insert(0, 'name')
    return fields


def fudo_payload(entry):
    return {
        'fudo_linked': bool(entry),
        'fudo_locked_fields': locked_product_fields(entry),
        'fudo_alerts': entry['alerts'] if entry else 0,
    }


def _normalize(field, value):
    if field == 'price':
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
    if field == 'is_active':
        return bool(value)
    if isinstance(value, str):
        return value.strip()
    return value


def changes_locked(data, fields, obj):
    """True si el body intenta cambiar algún campo bloqueado respecto de su valor actual."""
    for field in fields:
        if field not in data:
            continue
        new = _normalize(field, data[field])
        if new is None or new != _normalize(field, getattr(obj, field)):
            return True
    return False


def product_detail(product):
    """Formato de GET /products/<id>: todas las variantes, receta si tiene y datos de Fudo."""
    data = product.to_dict()
    variants = ProductVariant.query.filter_by(product_id=product.id).order_by(ProductVariant.id).all()
    data['variants'] = [v.to_dict() for v in variants]
    if product.has_recipe:
        data['recipe'] = [r.to_dict() for r in ProductRecipeItem.query.filter_by(product_id=product.id).all()]
    data.update(fudo_payload(fudo_info([product.id]).get(product.id)))
    return data
```

- [ ] **Step 4: Apply the locks in `routes/products.py`**

Imports nuevos:

```python
from app.services.product_fudo_info import (
    FUDO_LOCKED_ERROR, LOCKED_VARIANT_FIELDS, changes_locked, fudo_info, fudo_payload,
    locked_product_fields, product_detail,
)
```

Helper junto a `_bad_body`:

```python
def _fudo_locked():
    return jsonify({'error': FUDO_LOCKED_ERROR}), 409
```

`list_products`: reemplazar el bloque desde `query = Product.query` hasta antes de `paginated = ...` por:

```python
    fudo_alerts = request.args.get('fudo_alerts', 'false').lower() == 'true'

    query = Product.query
    if fudo_alerts:
        alert_ids = db.session.query(ProductVariant.product_id).filter(
            ProductVariant.fudo_status.in_(['missing', 'inactive']))
        query = query.filter(Product.id.in_(alert_ids))
    elif not include_inactive:
        query = query.filter(Product.is_active == True)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
```

y después del `for p in products:` que carga variantes, agregar:

```python
    info = fudo_info([p['id'] for p in products])
    for p in products:
        p.update(fudo_payload(info.get(p['id'])))
```

`get_product`: reemplazar el cuerpo después de `get_or_404` por:

```python
    return jsonify(product_detail(product)), 200
```

`update_product`: inmediatamente después de `if data is None: return _bad_body()`, agregar:

```python
    locked = locked_product_fields(fudo_info([product.id]).get(product.id))
    if changes_locked(data, locked, product):
        return _fudo_locked()
```

y cambiar el `return` final por `return jsonify(product_detail(product)), 200`.

`delete_product`: después del `get_or_404`:

```python
    if fudo_info([product.id]):
        return _fudo_locked()
```

`update_variant`: después de `if data is None: return _bad_body()`:

```python
    if variant.fudo_product_id and changes_locked(data, LOCKED_VARIANT_FIELDS, variant):
        return _fudo_locked()
```

`delete_variant`: después del `first_or_404()`:

```python
    if variant.fudo_product_id:
        return _fudo_locked()
```

- [ ] **Step 5: Apply the locks in `routes/product_categories.py`**

Import:

```python
from app.services.product_fudo_info import FUDO_LOCKED_ERROR, LOCKED_CATEGORY_FIELDS, changes_locked
```

`update_category`: después de `if data is None: return ... 400`:

```python
    if category.fudo_category_id and changes_locked(data, LOCKED_CATEGORY_FIELDS, category):
        return jsonify({'error': FUDO_LOCKED_ERROR}), 409
```

`delete_category`: después del `get_or_404`:

```python
    if category.fudo_category_id:
        return jsonify({'error': FUDO_LOCKED_ERROR}), 409
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && $PY -m pytest tests/test_products_fudo_lock.py tests/test_products.py tests/test_product_categories.py -q -p no:cacheprovider`
Expected: PASS. (`test_products.py` tiene tests que comparan la respuesta de `PUT /products/<id>`; ahora la respuesta trae además `variants` y los campos `fudo_*`. Si alguno compara igualdad del dict completo, ajustar a comparar las claves que verifica.)

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/product_fudo_info.py backend/app/routes/products.py backend/app/routes/product_categories.py backend/tests/test_products_fudo_lock.py backend/tests/test_products.py
git commit -m "feat(products): lock Fudo-owned fields and report Fudo status

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Endpoints de sync, candidatos, attach y detach

**Files:**
- Modify: `backend/app/routes/products.py`
- Test: `backend/tests/test_products_attach.py`

**Interfaces:**
- Consumes: `menu_sync_service.sync_fudo_products` (Task 3), `product_detail`, `fudo_info` (Task 4).
- Produces:
  - `POST /api/v1/products/sync` → 200 con el resultado completo de `sync_fudo_products` (incluye `catalog`); 502 con el texto global ante cualquier excepción.
  - `GET /api/v1/products/fudo-candidates` → `{"products": [{fudo_id, name, price, category_name, is_active, ignored, fudo_category_id, product_id, product_name}]}` ordenado por nombre.
  - `POST /api/v1/products/<id>/variants/attach` body `{"fudo_product_id": str}` → 200 con `product_detail(product)`.
  - `POST /api/v1/products/<id>/variants/<vid>/detach` → 201 con `product_detail(nuevo)`.

- [ ] **Step 1: Write the failing tests**

Crear `backend/tests/test_products_attach.py`:

```python
from app.extensions import db
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.services import menu_sync_service
from menu_fakes import FakeFudoClient, fudo_category, fudo_product

CATEGORIES = [fudo_category(1, 'Cafés')]
PRODUCTS = [fudo_product(1, 'Café chico', 3000), fudo_product(2, 'Café grande', 3500)]


def _sync(products=PRODUCTS):
    menu_sync_service.sync_fudo_products(FakeFudoClient(products=products, categories=CATEGORIES))


def _product_of(fudo_id):
    variant = ProductVariant.query.filter_by(fudo_product_id=str(fudo_id)).one()
    return db.session.get(Product, variant.product_id)


def test_sync_endpoint(menu_client, admin_headers, monkeypatch):
    monkeypatch.setattr('app.routes.products.FudoClient', lambda: FakeFudoClient(products=PRODUCTS, categories=CATEGORIES))
    response = menu_client.post('/api/v1/products/sync', headers=admin_headers)

    assert response.status_code == 200
    assert response.get_json()['catalog']['products_created'] == 2


def test_sync_endpoint_reports_fudo_errors(menu_client, admin_headers, monkeypatch):
    def broken_client():
        raise RuntimeError('credenciales inválidas')
    monkeypatch.setattr('app.routes.products.FudoClient', broken_client)
    response = menu_client.post('/api/v1/products/sync', headers=admin_headers)

    assert response.status_code == 502
    assert response.get_json()['error'] == 'Error sincronizando con Fudo. Revisá las credenciales o probá más tarde.'


def test_sync_endpoint_requires_products_module(menu_client, employee_headers):
    assert menu_client.post('/api/v1/products/sync', headers=employee_headers).status_code == 403


def test_fudo_candidates(menu_client, admin_headers):
    _sync()
    data = menu_client.get('/api/v1/products/fudo-candidates', headers=admin_headers).get_json()

    by_id = {p['fudo_id']: p for p in data['products']}
    assert by_id['1']['product_id'] == _product_of(1).id
    assert by_id['1']['product_name'] == 'Café chico'
    assert by_id['2']['price'] == 3500


def test_attach_moves_variant_and_deactivates_empty_source(menu_client, admin_headers):
    _sync()
    target, source = _product_of(1), _product_of(2)

    response = menu_client.post(f'/api/v1/products/{target.id}/variants/attach',
                                json={'fudo_product_id': '2'}, headers=admin_headers)

    assert response.status_code == 200
    body = response.get_json()
    assert sorted(v['fudo_product_id'] for v in body['variants']) == ['1', '2']
    assert body['fudo_locked_fields'] == ['category_id', 'is_active']
    assert source.is_active is False


def test_sync_after_attach_keeps_source_inactive(menu_client, admin_headers):
    _sync()
    target, source = _product_of(1), _product_of(2)
    menu_client.post(f'/api/v1/products/{target.id}/variants/attach',
                     json={'fudo_product_id': '2'}, headers=admin_headers)
    menu_client.put(f'/api/v1/products/{target.id}', json={'name': 'Café'}, headers=admin_headers)

    _sync()

    assert source.is_active is False
    assert target.name == 'Café'
    assert ProductVariant.query.filter_by(fudo_product_id='2').one().product_id == target.id
    assert Product.query.count() == 2


def test_attach_creates_variant_for_unlinked_fudo_product(menu_client, admin_headers):
    _sync([fudo_product(1, 'Café chico', 3000), fudo_product(3, 'Café XL', 4000, active=False)])
    target = _product_of(1)

    response = menu_client.post(f'/api/v1/products/{target.id}/variants/attach',
                                json={'fudo_product_id': '3'}, headers=admin_headers)

    assert response.status_code == 200
    variant = ProductVariant.query.filter_by(fudo_product_id='3').one()
    assert variant.product_id == target.id
    assert variant.is_active is False
    assert variant.fudo_status == 'inactive'


def test_attach_errors(menu_client, admin_headers):
    _sync()
    target = _product_of(1)
    url = f'/api/v1/products/{target.id}/variants/attach'

    assert menu_client.post(url, json={}, headers=admin_headers).status_code == 400
    assert menu_client.post(url, json={'fudo_product_id': 2}, headers=admin_headers).status_code == 400
    assert menu_client.post(url, json={'fudo_product_id': '999'}, headers=admin_headers).status_code == 404
    assert menu_client.post(url, json={'fudo_product_id': '1'}, headers=admin_headers).status_code == 409
    assert menu_client.post('/api/v1/products/9999/variants/attach', json={'fudo_product_id': '2'},
                            headers=admin_headers).status_code == 404


def test_detach_creates_product(menu_client, admin_headers):
    _sync()
    target = _product_of(1)
    menu_client.post(f'/api/v1/products/{target.id}/variants/attach',
                     json={'fudo_product_id': '2'}, headers=admin_headers)
    variant = ProductVariant.query.filter_by(fudo_product_id='2').one()

    response = menu_client.post(f'/api/v1/products/{target.id}/variants/{variant.id}/detach', headers=admin_headers)

    assert response.status_code == 201
    body = response.get_json()
    assert body['name'] == 'Café grande'
    assert body['category_id'] == target.category_id
    assert variant.product_id == body['id']
    assert target.is_active is True


def test_detach_errors(menu_client, admin_headers):
    _sync()
    target = _product_of(1)
    only = ProductVariant.query.filter_by(fudo_product_id='1').one()
    manual = menu_client.post(f'/api/v1/products/{target.id}/variants', json={'name': 'Extra', 'price': 100},
                              headers=admin_headers).get_json()

    assert menu_client.post(f'/api/v1/products/{target.id}/variants/{manual["id"]}/detach',
                            headers=admin_headers).status_code == 409
    db.session.delete(db.session.get(ProductVariant, manual['id']))
    db.session.commit()
    assert menu_client.post(f'/api/v1/products/{target.id}/variants/{only.id}/detach',
                            headers=admin_headers).status_code == 409
    assert menu_client.post(f'/api/v1/products/{target.id}/variants/9999/detach',
                            headers=admin_headers).status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && $PY -m pytest tests/test_products_attach.py -q -p no:cacheprovider`
Expected: FAIL (404/405 en las rutas nuevas, `AttributeError` en el monkeypatch de `FudoClient`).

- [ ] **Step 3: Implement the endpoints**

Imports nuevos en `backend/app/routes/products.py`:

```python
from app.models.menu import FudoProduct
from app.services import menu_sync_service
from app.utils.fudo_client import FudoClient
```

Agregar al final del archivo:

```python
@bp.route('/sync', methods=['POST'])
@token_required
@module_required('Products')
def sync_fudo(current_user):
    try:
        stats = menu_sync_service.sync_fudo_products(FudoClient())
    except Exception:
        db.session.rollback()
        current_app.logger.exception('Error sincronizando productos con Fudo')
        return jsonify({'error': 'Error sincronizando con Fudo. Revisá las credenciales o probá más tarde.'}), 502
    return jsonify(stats), 200


@bp.route('/fudo-candidates', methods=['GET'])
@token_required
@authenticated_only
def fudo_candidates(current_user):
    rows = (
        db.session.query(FudoProduct, Product.id, Product.name)
        .outerjoin(ProductVariant, ProductVariant.fudo_product_id == FudoProduct.fudo_id)
        .outerjoin(Product, Product.id == ProductVariant.product_id)
        .order_by(FudoProduct.name)
        .all()
    )
    return jsonify({'products': [
        {**fudo.to_dict(), 'product_id': product_id, 'product_name': product_name}
        for fudo, product_id, product_name in rows
    ]}), 200


def _deactivate_if_empty(product):
    db.session.flush()
    if product.variants.filter_by(is_active=True).count() == 0:
        product.is_active = False


@bp.route('/<int:product_id>/variants/attach', methods=['POST'])
@token_required
@module_required('Products')
def attach_fudo_variant(current_user, product_id):
    product = Product.query.get_or_404(product_id)
    data = json_object()
    if data is None:
        return _bad_body()
    fudo_id = data.get('fudo_product_id')
    if not isinstance(fudo_id, str) or not fudo_id.strip():
        return jsonify({'error': 'fudo_product_id es requerido'}), 400
    fudo = db.session.get(FudoProduct, fudo_id.strip())
    if fudo is None:
        return jsonify({'error': 'Producto de Fudo no encontrado'}), 404

    variant = ProductVariant.query.filter_by(fudo_product_id=fudo.fudo_id).first()
    if variant is not None and variant.product_id == product.id:
        return jsonify({'error': 'Ese producto de Fudo ya está en este producto'}), 409
    if variant is None:
        db.session.add(ProductVariant(
            product_id=product.id, name=(fudo.name or 'Sin nombre')[:100], price=fudo.price,
            fudo_product_id=fudo.fudo_id, is_active=bool(fudo.is_active),
            fudo_status='ok' if fudo.is_active else 'inactive',
        ))
    else:
        source = db.session.get(Product, variant.product_id)
        variant.product_id = product.id
        _deactivate_if_empty(source)
    db.session.commit()
    return jsonify(product_detail(product)), 200


@bp.route('/<int:product_id>/variants/<int:variant_id>/detach', methods=['POST'])
@token_required
@module_required('Products')
def detach_variant(current_user, product_id, variant_id):
    product = Product.query.get_or_404(product_id)
    variant = ProductVariant.query.filter_by(id=variant_id, product_id=product_id).first_or_404()
    if not variant.fudo_product_id:
        return jsonify({'error': 'Solo se pueden separar variantes vinculadas a Fudo'}), 409
    if product.variants.count() == 1:
        return jsonify({'error': 'Es la única variante del producto'}), 409

    new_product = Product(name=variant.name[:200], category_id=product.category_id, is_active=variant.is_active)
    db.session.add(new_product)
    db.session.flush()
    variant.product_id = new_product.id
    _deactivate_if_empty(product)
    db.session.commit()
    return jsonify(product_detail(new_product)), 201
```

Nota: `/sync` y `/fudo-candidates` no chocan con `/<int:product_id>` porque el conversor `int` no acepta texto.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && $PY -m pytest tests/test_products_attach.py tests/test_products_fudo_lock.py tests/test_product_sync.py tests/test_products.py -q -p no:cacheprovider`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routes/products.py backend/tests/test_products_attach.py
git commit -m "feat(products): add Fudo sync, candidates, attach and detach endpoints

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Servicio, utilidades y selector de Fudo en el frontend

**Files:**
- Modify: `frontend/src/services/productsService.js`
- Create: `frontend/src/utils/fudoLock.js`
- Create: `frontend/src/utils/fudoLock.test.js`
- Modify: `frontend/src/components/menu/FudoProductPicker.jsx`

**Interfaces:**
- Consumes: endpoints de las Tasks 4 y 5.
- Produces:
  - `productsService.syncFudo() -> Promise<result>`, `getFudoCandidates() -> Promise<candidate[]>`, `attachFudoVariant(productId, fudoProductId) -> Promise<product>`, `detachVariant(productId, variantId) -> Promise<product>`.
  - `fudoLock.js`: `isFudoLocked(product, field) -> bool`, `variantFudoStatus(variant) -> 'ok'|'inactive'|'missing'|null`, `FUDO_STATUS_LABELS`, `syncSummary(result) -> string`, `candidateLegend(candidate, productId) -> string|null`.
  - `FudoProductPicker` acepta props opcionales `isDisabled(p) -> bool`, `describe(p) -> string|null`, `emptyLabel: string`. Sin esas props se comporta igual que hoy.

- [ ] **Step 1: Install frontend deps in the worktree**

Run: `cd frontend && npm ci`
Expected: termina sin errores (el worktree no tiene `node_modules`).

- [ ] **Step 2: Write the failing test**

Crear `frontend/src/utils/fudoLock.test.js`:

```js
import { candidateLegend, isFudoLocked, syncSummary, variantFudoStatus } from './fudoLock'

describe('isFudoLocked', () => {
  it('is true only for listed fields', () => {
    const product = { fudo_locked_fields: ['name', 'category_id'] }
    expect(isFudoLocked(product, 'name')).toBe(true)
    expect(isFudoLocked(product, 'description')).toBe(false)
    expect(isFudoLocked(null, 'name')).toBe(false)
    expect(isFudoLocked({}, 'name')).toBe(false)
  })
})

describe('variantFudoStatus', () => {
  it('returns null for manual variants and ok by default for linked ones', () => {
    expect(variantFudoStatus({ fudo_product_id: null })).toBe(null)
    expect(variantFudoStatus({ fudo_product_id: '1', fudo_status: null })).toBe('ok')
    expect(variantFudoStatus({ fudo_product_id: '1', fudo_status: 'missing' })).toBe('missing')
  })
})

describe('syncSummary', () => {
  it('summarizes the catalog stats', () => {
    expect(syncSummary({ catalog: { variants_updated: 12, products_created: 3, alerts: 1 } }))
      .toBe('Fudo sincronizado: 12 variantes actualizadas · 3 productos nuevos · 1 alerta')
    expect(syncSummary({ catalog: { variants_updated: 0, products_created: 0, alerts: 0 } }))
      .toBe('Fudo sincronizado: 0 variantes actualizadas · 0 productos nuevos')
    expect(syncSummary({ catalog: { variants_updated: 1, products_created: 1, alerts: 2 } }))
      .toBe('Fudo sincronizado: 1 variante actualizada · 1 producto nuevo · 2 alertas')
  })
})

describe('candidateLegend', () => {
  it('explains where the candidate is', () => {
    expect(candidateLegend({ product_id: 5, product_name: 'Café' }, 5)).toBe('ya en este producto')
    expect(candidateLegend({ product_id: 7, product_name: 'Café grande' }, 5)).toBe('se moverá desde «Café grande»')
    expect(candidateLegend({ product_id: null, is_active: false }, 5)).toBe('inactivo en Fudo')
    expect(candidateLegend({ product_id: null, is_active: true }, 5)).toBe(null)
  })
})
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/utils/fudoLock.test.js`
Expected: FAIL con `Failed to resolve import "./fudoLock"`.

- [ ] **Step 4: Implement the utilities**

Crear `frontend/src/utils/fudoLock.js`:

```js
// Datos de Productos que vienen de Fudo durante la transición (ver spec 2026-10-13-products-fudo-sync).

export const FUDO_LOCK_HINT = 'Se edita en Fudo'

export const FUDO_STATUS_LABELS = {
  ok: 'Fudo',
  inactive: 'Inactiva en Fudo',
  missing: 'Ya no existe en Fudo',
}

export const isFudoLocked = (product, field) => Boolean(product?.fudo_locked_fields?.includes(field))

export const variantFudoStatus = (variant) =>
  variant?.fudo_product_id ? variant.fudo_status || 'ok' : null

const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`

export const syncSummary = (result) => {
  const c = result?.catalog || {}
  const parts = [
    plural(c.variants_updated || 0, 'variante actualizada', 'variantes actualizadas'),
    plural(c.products_created || 0, 'producto nuevo', 'productos nuevos'),
  ]
  if (c.alerts) parts.push(plural(c.alerts, 'alerta', 'alertas'))
  return `Fudo sincronizado: ${parts.join(' · ')}`
}

export const candidateLegend = (candidate, productId) => {
  if (candidate.product_id === productId) return 'ya en este producto'
  if (candidate.product_id) return `se moverá desde «${candidate.product_name}»`
  return candidate.is_active === false ? 'inactivo en Fudo' : null
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/utils/fudoLock.test.js`
Expected: PASS.

- [ ] **Step 6: Add the service methods**

En `frontend/src/services/productsService.js`, antes de `uploadProductImage`:

```js
  async syncFudo() {
    const response = await api.post('/products/sync')
    return response.data
  },

  async getFudoCandidates() {
    const response = await api.get('/products/fudo-candidates')
    return response.data.products
  },

  async attachFudoVariant(productId, fudoProductId) {
    const response = await api.post(`/products/${productId}/variants/attach`, {
      fudo_product_id: fudoProductId,
    })
    return response.data
  },

  async detachVariant(productId, variantId) {
    const response = await api.post(`/products/${productId}/variants/${variantId}/detach`)
    return response.data
  },
```

- [ ] **Step 7: Generalize the picker**

En `frontend/src/components/menu/FudoProductPicker.jsx`:

Reemplazar la firma y el comentario de props por:

```jsx
// products: [{ fudo_id, name, price, category_name, linked }]
// allowedIds: ids que se pueden elegir aunque estén vinculados (los del propio ítem)
// excludedIds: ids ya usados en otras variantes de este formulario
// isDisabled(p) / describe(p): reemplazan la lógica de la carta (p. ej. Productos); describe devuelve la leyenda o null
const FudoProductPicker = ({
  products,
  allowedIds = new Set(),
  excludedIds = new Set(),
  onSelect,
  onCancel,
  isDisabled,
  describe,
  emptyLabel = 'No hay productos: tocá "Sincronizar Fudo" primero.',
}) => {
```

Reemplazar `{products.length === 0 && <li className="p-2 text-sm text-gray-500">No hay productos: tocá "Sincronizar Fudo" primero.</li>}` por:

```jsx
        {products.length === 0 && <li className="p-2 text-sm text-gray-500">{emptyLabel}</li>}
```

Dentro del `visible.map`, reemplazar la línea `const taken = ...` por:

```jsx
          const taken = isDisabled
            ? isDisabled(p)
            : (p.linked && !allowedIds.has(p.fudo_id)) || excludedIds.has(p.fudo_id)
          const legend = describe ? describe(p) : taken ? 'ya en la carta' : null
```

y reemplazar `{taken && <span className="text-gray-500"> · ya en la carta</span>}` por:

```jsx
                  {legend && <span className="text-gray-500"> · {legend}</span>}
```

- [ ] **Step 8: Run the frontend test suite and build**

Run: `cd frontend && npx vitest run && npm run build`
Expected: todos los tests PASS y el build termina sin errores.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/services/productsService.js frontend/src/utils/fudoLock.js frontend/src/utils/fudoLock.test.js frontend/src/components/menu/FudoProductPicker.jsx
git commit -m "feat(products): frontend Fudo helpers, service calls and reusable picker

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Listado de Productos y Categorías con Fudo

**Files:**
- Modify: `frontend/src/pages/Products.jsx`
- Modify: `frontend/src/pages/ProductCategories.jsx`

**Interfaces:**
- Consumes: `productsService.syncFudo`, `syncSummary`, `FUDO_LOCK_HINT` (Task 6); campos `fudo_linked`, `fudo_alerts` en `GET /products` y `fudo_category_id`, `fudo_status` en categorías (Tasks 1 y 4); `useAuth().hasModuleAccess`.

- [ ] **Step 1: Products.jsx — sync button, badges and filter**

Imports: cambiar la primera línea de `lucide-react` por

```jsx
import { Plus, Edit2, Trash2, Search, RefreshCw, AlertTriangle } from 'lucide-react'
```

y agregar

```jsx
import { useAuth } from '../context/AuthContext'
import { syncSummary } from '../utils/fudoLock'
```

Estado nuevo (debajo de `const [error, setError] = useState('')`):

```jsx
  const { hasModuleAccess } = useAuth()
  const [fudoAlerts, setFudoAlerts] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [notice, setNotice] = useState('')
```

En el `useEffect` de `fetchProducts`, agregar `fudoAlerts` a las dependencias: `[page, search, categoryFilter, fudoAlerts]`. En `fetchProducts`, después de `if (categoryFilter) {...}`:

```jsx
      if (fudoAlerts) {
        params.fudo_alerts = true
      }
```

Handler nuevo (después de `handleCategoryFilter`):

```jsx
  const handleSyncFudo = async () => {
    setSyncing(true)
    setNotice('')
    try {
      const result = await productsService.syncFudo()
      setNotice(syncSummary(result))
      setError('')
      fetchCategories()
      fetchProducts()
    } catch (error) {
      setError(error.response?.data?.error || 'Error sincronizando con Fudo')
    } finally {
      setSyncing(false)
    }
  }
```

Encabezado: reemplazar el `<button onClick={() => navigate('/products/new')} ...>` por un contenedor con los dos botones:

```jsx
        <div className="flex gap-2">
          {hasModuleAccess('Products') && (
            <button
              onClick={handleSyncFudo}
              disabled={syncing}
              className="flex items-center gap-2 border border-gray-300 px-4 py-2 rounded hover:bg-gray-50 disabled:opacity-50"
            >
              <RefreshCw size={18} className={syncing ? 'animate-spin' : ''} /> Sincronizar con Fudo
            </button>
          )}
          <button
            onClick={() => navigate('/products/new')}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            <Plus size={20} /> Nuevo Producto
          </button>
        </div>
```

Debajo del bloque `{error && (...)}`:

```jsx
      {notice && (
        <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded mb-4">
          {notice}
        </div>
      )}
```

En la barra de filtros, después del `<select>` de categorías:

```jsx
          <label className="flex items-center gap-2 text-sm whitespace-nowrap">
            <input
              type="checkbox"
              checked={fudoAlerts}
              onChange={(e) => {
                setFudoAlerts(e.target.checked)
                setPage(1)
              }}
              className="w-4 h-4"
            />
            Con alertas de Fudo
          </label>
```

En la celda del nombre, después del span "Receta":

```jsx
                    {product.fudo_linked && (
                      <span className="ml-2 text-xs bg-emerald-100 text-emerald-800 px-2 py-1 rounded">
                        Fudo
                      </span>
                    )}
                    {product.fudo_alerts > 0 && (
                      <span
                        className="ml-2 inline-flex items-center gap-1 text-xs bg-amber-100 text-amber-800 px-2 py-1 rounded"
                        title="Alguna variante está inactiva o ya no existe en Fudo"
                      >
                        <AlertTriangle size={12} /> {product.fudo_alerts}
                      </span>
                    )}
```

En la celda de acciones, mostrar el botón Desactivar solo si no está vinculado: envolver el `<button onClick={() => handleDelete(product.id)} ...>` en `{!product.fudo_linked && ( ... )}`.

- [ ] **Step 2: ProductCategories.jsx — badge and locked name**

En la tarjeta, después de `<h3 className="font-bold text-lg">{category.name}</h3>`:

```jsx
                {category.fudo_category_id && (
                  <span className="text-xs bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded">Fudo</span>
                )}
                {category.fudo_status === 'missing' && (
                  <span className="text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded">Ya no existe en Fudo</span>
                )}
```

Envolver el botón de borrar (`onClick={() => handleDelete(category.id)}`) en `{!category.fudo_category_id && ( ... )}`.

En el modal, al input de Nombre agregarle:

```jsx
                  disabled={Boolean(editingCategory?.fudo_category_id)}
                  title={editingCategory?.fudo_category_id ? FUDO_LOCK_HINT : undefined}
```

y debajo del input:

```jsx
                {editingCategory?.fudo_category_id && (
                  <p className="text-xs text-gray-500 mt-1">El nombre se edita en Fudo.</p>
                )}
```

con el import `import { FUDO_LOCK_HINT } from '../utils/fudoLock'`. Agregar `disabled:bg-gray-100` a las clases del input para que se vea bloqueado.

- [ ] **Step 3: Build**

Run: `cd frontend && npm run build`
Expected: sin errores.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Products.jsx frontend/src/pages/ProductCategories.jsx
git commit -m "feat(products): Fudo sync button, badges and alerts filter in product lists

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Detalle de Producto con campos bloqueados y variantes de Fudo

**Files:**
- Modify: `frontend/src/pages/ProductDetail.jsx`

**Interfaces:**
- Consumes: `isFudoLocked`, `variantFudoStatus`, `FUDO_STATUS_LABELS`, `FUDO_LOCK_HINT`, `candidateLegend` (Task 6); `productsService.getFudoCandidates`, `attachFudoVariant`, `detachVariant`; `FudoProductPicker` con `isDisabled`/`describe`/`emptyLabel`; `GET /products/<id>` con `fudo_linked`, `fudo_locked_fields` y variantes con `fudo_product_id`/`fudo_status` (Tasks 4 y 5).

- [ ] **Step 1: Imports and state**

Cambiar el import de `lucide-react` por:

```jsx
import { Save, X, Plus, Trash2, ArrowLeft, Lock, Link2, Unlink } from 'lucide-react'
```

y agregar:

```jsx
import FudoProductPicker from '../components/menu/FudoProductPicker'
import {
  FUDO_LOCK_HINT,
  FUDO_STATUS_LABELS,
  candidateLegend,
  isFudoLocked,
  variantFudoStatus,
} from '../utils/fudoLock'
```

Estado nuevo, debajo de `suppliesForbidden`:

```jsx
  const [fudoCandidates, setFudoCandidates] = useState(null)
```

- [ ] **Step 2: Handlers**

Después de `handleUpdateVariant`:

```jsx
  const openFudoPicker = async () => {
    try {
      setFudoCandidates(await productsService.getFudoCandidates())
    } catch (error) {
      setError(error.response?.data?.error || 'Error al cargar productos de Fudo')
    }
  }

  const handleAttachFudo = async (candidate) => {
    if (candidate.product_id && !window.confirm(`«${candidate.name}» se moverá desde «${candidate.product_name}». ¿Continuar?`)) {
      return
    }
    try {
      const updated = await productsService.attachFudoVariant(product.id, candidate.fudo_id)
      setFudoCandidates(null)
      setProduct(updated)
      setVariants(updated.variants || [])
      setError('')
    } catch (error) {
      setError(error.response?.data?.error || 'Error al agregar la variante de Fudo')
    }
  }

  const handleDetachVariant = async (variant) => {
    if (!window.confirm(`¿Separar «${variant.name}» en un producto propio?`)) return
    try {
      await productsService.detachVariant(product.id, variant.id)
      fetchProduct()
    } catch (error) {
      setError(error.response?.data?.error || 'Error al separar la variante')
    }
  }
```

En `fetchProduct`, la respuesta ya trae `fudo_*`; no hay cambios.

- [ ] **Step 3: Banner and locked inputs (tab Información)**

Debajo del bloque `{error && (...)}` del encabezado:

```jsx
      {product?.fudo_linked && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-900 px-4 py-3 rounded mb-4 flex items-center gap-2">
          <Lock size={16} /> Nombre, categoría, precios y estado se editan en Fudo.
        </div>
      )}
```

Al input de Nombre agregarle:

```jsx
                  disabled={isFudoLocked(product, 'name')}
                  title={isFudoLocked(product, 'name') ? FUDO_LOCK_HINT : undefined}
```

y al `<select>` de Categoría:

```jsx
                  disabled={isFudoLocked(product, 'category_id')}
                  title={isFudoLocked(product, 'category_id') ? FUDO_LOCK_HINT : undefined}
```

Agregar `disabled:bg-gray-100` a las clases de ambos. En las dos etiquetas (`Nombre *`, `Categoría *`), agregar después del texto:

```jsx
                  {isFudoLocked(product, 'name') && <Lock size={12} className="inline ml-1 text-gray-500" />}
```

(usar `'category_id'` en la de Categoría).

- [ ] **Step 4: Variants table**

Agregar una columna de encabezado `Fudo` después de `Nombre`. Reemplazar el cuerpo de cada fila (`variants.map((variant) => (...))`) por:

```jsx
                  {variants.map((variant) => {
                    const status = variantFudoStatus(variant)
                    const linked = status !== null
                    return (
                      <tr key={variant.id} className={`border-b ${variant.is_active ? '' : 'opacity-60'}`}>
                        <td className="px-4 py-2">{variant.name}</td>
                        <td className="px-4 py-2">
                          {linked && (
                            <span
                              className={`text-xs px-2 py-1 rounded ${
                                status === 'ok' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                              }`}
                            >
                              {FUDO_STATUS_LABELS[status]}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-2">
                          {linked ? (
                            <span title={FUDO_LOCK_HINT}>${variant.price}</span>
                          ) : (
                            <EditableNumberInput
                              value={variant.price}
                              onCommit={(raw) => handleUpdateVariant(variant.id, 'price', raw)}
                              className="w-20 border rounded px-2 py-1"
                              step="0.01"
                            />
                          )}
                        </td>
                        <td className="px-4 py-2">
                          <EditableNumberInput
                            value={variant.stock_quantity}
                            onCommit={(raw) => handleUpdateVariant(variant.id, 'stock_quantity', raw)}
                            className="w-20 border rounded px-2 py-1"
                            disabled={formData.has_recipe}
                          />
                        </td>
                        <td className="px-4 py-2">
                          <EditableNumberInput
                            value={variant.min_stock}
                            onCommit={(raw) => handleUpdateVariant(variant.id, 'min_stock', raw)}
                            className="w-20 border rounded px-2 py-1"
                            disabled={formData.has_recipe}
                          />
                        </td>
                        <td className="px-4 py-2">
                          {linked ? (
                            variants.length > 1 && (
                              <button
                                onClick={() => handleDetachVariant(variant)}
                                className="flex items-center gap-1 text-sm text-gray-700 hover:bg-gray-100 px-2 py-1 rounded"
                                title="Separar en un producto propio"
                              >
                                <Unlink size={16} /> Separar
                              </button>
                            )
                          ) : (
                            <button
                              onClick={() => handleDeleteVariant(variant.id)}
                              className="text-red-600 hover:bg-red-50 p-1 rounded"
                            >
                              <Trash2 size={18} />
                            </button>
                          )}
                        </td>
                      </tr>
                    )
                  })}
```

- [ ] **Step 5: "Agregar variante desde Fudo"**

Inmediatamente antes de `<div className="border-t pt-4"><h3 className="font-medium mb-3">Agregar Variante</h3>`:

```jsx
              <div className="mb-6">
                {fudoCandidates === null ? (
                  <button
                    onClick={openFudoPicker}
                    className="flex items-center gap-2 border border-emerald-300 text-emerald-800 px-3 py-2 rounded text-sm hover:bg-emerald-50"
                  >
                    <Link2 size={16} /> Agregar variante desde Fudo
                  </button>
                ) : (
                  <FudoProductPicker
                    products={fudoCandidates}
                    isDisabled={(p) => p.product_id === product.id}
                    describe={(p) => candidateLegend(p, product.id)}
                    emptyLabel='No hay productos de Fudo: tocá "Sincronizar con Fudo" en Productos.'
                    onSelect={handleAttachFudo}
                    onCancel={() => setFudoCandidates(null)}
                  />
                )}
              </div>
```

Y cambiar el título `Agregar Variante` por `Agregar variante manual`.

- [ ] **Step 6: Build and tests**

Run: `cd frontend && npx vitest run && npm run build`
Expected: PASS y build sin errores.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/ProductDetail.jsx
git commit -m "feat(products): lock Fudo fields and manage Fudo variants in product detail

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Verificación integral

**Files:**
- Modify (si hace falta): `.claude/launch.json` del repo principal (`C:\Users\onofr\Desktop\galia-app\.claude\launch.json`) para agregar configs `products-fudo-backend` y `products-fudo-frontend` apuntando a este worktree.

- [ ] **Step 1: Full backend suite**

Run: `cd backend && $PY -m pytest -q -p no:cacheprovider`
Expected: sin fallas nuevas respecto de `main`. Si algún test falla, comprobar si también falla en `main`: crear un worktree temporal con `git worktree add ../../tmp-main-check a6884dd`, correr ese mismo archivo de test ahí (`cd ../../tmp-main-check/backend && $PY -m pytest <archivo> -q -p no:cacheprovider`) y después borrarlo con `git worktree remove ../../tmp-main-check`. Las fallas que también ocurren en `main` se reportan pero no se corrigen; las nuevas se corrigen.

- [ ] **Step 2: Full frontend suite and build**

Run: `cd frontend && npx vitest run && npm run build`
Expected: PASS.

- [ ] **Step 3: Manual check in the browser preview (SQLite)**

Levantar el backend del worktree con una base SQLite en el scratchpad (como las configs `pos-caja-*` del `launch.json`) y el frontend con `npm run dev`. Sin credenciales de Fudo, sembrar la caché con un script en el scratchpad que llame a `menu_sync_service.sync_fudo_products(FakeFudoClient(...))` (importando `tests/menu_fakes.py`) para crear productos vinculados. Verificar:
- `/products`: insignia "Fudo", filtro "Con alertas de Fudo", sin botón Desactivar en vinculados.
- `/products/<id>`: banner, Nombre y Categoría deshabilitados, precio en solo lectura, "Agregar variante desde Fudo" mueve una variante con confirmación, "Separar" la devuelve.
- `/product-categories`: insignia y nombre bloqueado.
- El botón "Sincronizar con Fudo" muestra el error 502 en rojo (sin credenciales).

Sacar captura de `/products/<id>` para el usuario.

- [ ] **Step 4: Migration on PostgreSQL (pendiente del usuario si Docker no arranca)**

Contra una base Postgres de prueba en el head `b2a0_add_cash_registers`:

```bash
cd backend && $PY -m flask --app run.py db upgrade && $PY -m flask --app run.py db downgrade b2a0_add_cash_registers && $PY -m flask --app run.py db upgrade
```

Expected: las tres operaciones terminan sin error. Si no hay Postgres disponible, dejarlo anotado como pendiente en el PR.

- [ ] **Step 5: Commit any fixes**

```bash
git add -A backend frontend
git commit -m "fix(products): address issues found in Fudo sync verification

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

(Solo si hubo cambios.)
