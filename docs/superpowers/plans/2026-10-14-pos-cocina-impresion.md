# Cocina e impresión (sub-proyecto 3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Comandas automáticas por estación al confirmar cada tanda, anulaciones, precuenta, ticket y reimpresión, impresas en térmicas mediante una cola en el backend y una página de impresión con QZ Tray.

**Architecture:**
- **Backend:** el backend arma documentos JSON y los encola en `print_jobs`; `print_service` crea las comandas desde `sale_service`.
- **Página de impresión:** `/pos/impresion` toma los trabajos de su punto de impresión, los convierte a ESC/POS (`escpos.js`, puro) y los imprime con QZ Tray.
- **POS:** muestra el estado de la cola y las acciones de impresión de cada venta.

**Tech Stack:** Flask, SQLAlchemy 2.0, Alembic, pytest, `cryptography` (firma QZ). React 18, React Query 5, Tailwind, Vitest, `qz-tray` 2.2.4.

**Spec:** `docs/superpowers/specs/2026-10-13-pos-cocina-impresion-design.md`

## Global Constraints

- **Worktree:** `C:\Users\onofr\Desktop\galia-app\.claude\worktrees\pos-base`, rama `feature/pos-cocina-impresion` (sale de `main` en `78960e1`). Las rutas del plan son relativas a esa raíz.
- **Python** (`PY`): `C:\Users\onofr\Desktop\galia-app\backend\venv\Scripts\python.exe` (Python 3.10). Los tests corren con cwd = `backend/`: `PY -m pytest -q -p no:cacheprovider <archivos>`.
- **Node:** con cwd = `frontend/` (`npm test`, `npm run build`, `npx vitest run <archivo>`). Nunca correr vitest desde la raíz.
- **Encoding:** UTF-8 con acentos. Editar solo con Edit/Write.
- **Línea base del backend:** `PY scripts/compare_baseline.py <salida> ../docs/superpowers/plans/2026-10-08-pos-base-test-baseline.txt`. Criterio: `Sin fallas nuevas.`
- **Lint:** no hay ESLint. El frontend se verifica con `npm test` y `npm run build`.
- **Vitest:** entorno `node` y sin Testing Library. Solo lógica pura, con imports relativos.
- **Migración:** `b3a0_add_print_stations`, con `down_revision = 'b2b0_products_fudo_link'`.
- **Errores:**
  - `PosError` (409 por defecto), `bad_request` (400), `forbidden` (403) y `not_found` (404), de `app.services.pos.errors`;
  - mensajes en castellano rioplatense.
- **Fechas:**
  - se guardan en UTC naive (`common.now()`);
  - los documentos muestran hora de Argentina con formato `%d/%m/%Y %H:%M`.
- **Montos en documentos:** strings con 2 decimales (`'1234.50'`), calculados por el backend. El frontend solo les da formato (`$ 1.234,50`).
- **Constantes de la cola:**
  - `CLAIM_LIMIT = 10`;
  - un `printing` vence a los 60 s;
  - un `failed` se reintenta después de 15 s, hasta `MAX_ATTEMPTS = 5`;
  - "con problemas" y "punto caído" a los 30 s.
- **Permisos:**
  - precuenta, ticket, reimpresión, trabajos de una venta y estaciones (lectura): `POS` o `Camarero`;
  - estaciones (lectura): también `Products`;
  - cola, estado, puntos de impresión, prueba y firma QZ: `POS`;
  - configuración de estaciones e impresoras: admin.
- **La caja (1b), el celular (1c) y la caja y arqueo (2)** no cambian de comportamiento, salvo las acciones de impresión que se agregan.
- **Commits:** terminan con la línea de atribución que pida el harness.

## Review Focus

1. **Una tanda con un ítem de una estación sin impresora y otro de una estación con impresora:** se imprime solo la segunda, y la primera no rompe la confirmación. Lo cubre la Task 2 (`test_station_without_printer_is_skipped`).
2. **Dos pestañas de impresión del mismo punto:** nunca imprimen el mismo trabajo. Lo cubren la Task 4 (PostgreSQL) y la Task 3 (un trabajo ya `printing` no se vuelve a entregar).
3. **El punto de impresión se cae a mitad de un trabajo:** el trabajo vuelve a la cola a los 60 s y se imprime una sola vez cuando vuelve. Lo cubre la Task 3 (`test_stale_printing_returns_to_queue`).
4. **Acentos y ñ en los nombres de productos:** no rompen el ancho de línea ni el corte de renglones. Lo cubre la Task 5 (`renderText` con nombres acentuados largos).
5. **Reimprimir una comanda cuya estación cambió de impresora o se quedó sin impresora:** va a la impresora actual, o responde 409 con un mensaje claro. Lo cubre la Task 3.

## Mapa de archivos

**Backend**
- Create:
  - `backend/app/models/pos/printing.py`: `PrintStation`, `Printer`, `PrintJob`, `PrintPoint`;
  - `backend/migrations/versions/b3a0_add_print_stations.py`;
  - `backend/app/services/pos/print_documents.py`, `backend/app/services/pos/print_service.py`;
  - `backend/app/routes/pos_print.py`;
  - `docs/pos/impresion-qz.md`.
- Modify:
  - `backend/app/models/pos/__init__.py`, `backend/app/models/product_category.py` (`station_id`);
  - `backend/app/routes/product_categories.py` (`station_id`);
  - `backend/app/services/pos/sale_service.py` (llamadas a `print_service`);
  - `backend/app/routes/pos_config.py` (CRUD de estaciones e impresoras);
  - `backend/app/__init__.py` (blueprint);
  - `backend/requirements.txt` (`cryptography`).
- Tests:
  - `backend/tests/print_helpers.py`;
  - `test_pos_print_config.py`, `test_pos_print_jobs.py`, `test_pos_print_queue.py`, `test_pos_print_api.py`, `test_pos_print_concurrency_pg.py`;
  - `test_migration_chain.py`.

**Frontend**
- Create:
  - `frontend/src/pos/print/escpos.js` (+ test), `printStatus.js` (+ test), `qz.js`;
  - `PrintPage.jsx`, `PrintStatusBadge.jsx`, `PrintJobsList.jsx`.
- Modify:
  - `frontend/src/pos/api/posApi.js` (`posPrintApi` y claves de config), `frontend/src/pos/hooks/keys.js`;
  - `frontend/src/pos/utils/permissions.js` (`printBill`, `printReceipt`);
  - `frontend/src/pos/ui/Toasts.jsx` (`info` con acción);
  - `frontend/src/pos/sale/SaleFooter.jsx`, `SalePanel.jsx`;
  - `frontend/src/pos/modals/PaymentModal.jsx`;
  - `frontend/src/pos/layout/PosTopBar.jsx`;
  - `frontend/src/components/pos-settings/CatalogEditor.jsx` (select numérico);
  - `frontend/src/pages/admin/PosSettings.jsx`, `frontend/src/pages/ProductCategories.jsx`;
  - `frontend/src/App.jsx`, `frontend/package.json`.

---

### Task 1: Modelos, migración y estación de las categorías

**Files:**
- Create: `backend/app/models/pos/printing.py`, `backend/migrations/versions/b3a0_add_print_stations.py`, `backend/tests/print_helpers.py`
- Modify: `backend/app/models/pos/__init__.py`, `backend/app/models/product_category.py`, `backend/app/routes/product_categories.py`
- Test: `backend/tests/test_pos_print_config.py`, `backend/tests/test_migration_chain.py`

**Interfaces:**
- Produces:
  - **Modelos:**
    - `PrintStation(id, name, position, is_active)` con `to_dict()`;
    - `Printer(id, name, connection, host, port, os_name, paper_width, print_point, station_id, is_cashier, is_active)` con `to_dict()` y la relación `station`;
    - `PrintJob(id, kind, printer_id, sale_id, station_id, batch, document, status, attempts, error, claimed_by, claimed_at, printed_at, failed_at, reprint_of, created_by, created_at)` con las relaciones `printer`, `sale`, `station`;
    - `PrintPoint(name, last_seen_at)`;
    - constantes `PRINT_JOB_KINDS`, `PRINT_JOB_STATUSES`, `PRINTER_CONNECTIONS`, `PAPER_WIDTHS`.
  - **Categorías:** `ProductCategory.station_id`, que `to_dict()` incluye.
  - **Helpers de test:**
    - `make_station(name='Cocina') -> PrintStation`;
    - `make_printer(name, station=None, cashier=False, point='Caja', connection='network', width=80, active=True) -> Printer`, que también crea el `PrintPoint` del punto si no existe;
    - `make_kitchen_product() -> SimpleNamespace(category, product, variant)` con la categoría "Platos", el producto "Tostado" y la variante "Unidad" a $3000.

- [ ] **Step 1: Tests que fallan.** Crear `backend/tests/print_helpers.py`:

```python
"""Fábricas compartidas por los tests de impresión."""
from decimal import Decimal
from types import SimpleNamespace

from app.extensions import db
from app.models import Product, ProductCategory, ProductVariant
from app.models.pos import PrintPoint, PrintStation, Printer


def make_station(name='Cocina'):
    station = PrintStation(name=name)
    db.session.add(station)
    db.session.commit()
    return station


def make_printer(name, station=None, cashier=False, point='Caja', connection='network', width=80, active=True):
    printer = Printer(name=name, connection=connection, host='192.168.0.50' if connection == 'network' else None,
                      port=9100, os_name='EPSON TM-T20' if connection == 'usb' else None, paper_width=width,
                      print_point=point, station_id=station.id if station else None, is_cashier=cashier,
                      is_active=active)
    db.session.add(printer)
    if db.session.get(PrintPoint, point) is None:
        db.session.add(PrintPoint(name=point))
    db.session.commit()
    return printer


def make_kitchen_product():
    category = ProductCategory(name='Platos')
    db.session.add(category)
    db.session.flush()
    product = Product(name='Tostado', category_id=category.id, has_recipe=False)
    db.session.add(product)
    db.session.flush()
    variant = ProductVariant(product_id=product.id, name='Unidad', price=Decimal('3000'), stock_quantity=0,
                             min_stock=0)
    db.session.add(variant)
    db.session.commit()
    return SimpleNamespace(category=category, product=product, variant=variant)
```

Crear `backend/tests/test_pos_print_config.py`:

```python
from collections import defaultdict

from app.extensions import db
from app.models import ProductCategory
from app.services.product_sync_service import sync_product_categories
from pos_helpers import auth_headers, make_user, pos_app  # noqa: F401
from print_helpers import make_station


def test_category_station_via_api(pos_app):
    client = pos_app.test_client()
    headers = auth_headers(client, make_user('prod@test.com', modules=('Products',)))
    cocina = make_station('Cocina')
    created = client.post('/api/v1/product-categories', json={'name': 'Platos', 'station_id': cocina.id},
                          headers=headers)
    assert created.status_code == 201 and created.get_json()['station_id'] == cocina.id
    category_id = created.get_json()['id']
    cleared = client.put(f'/api/v1/product-categories/{category_id}', json={'station_id': None}, headers=headers)
    assert cleared.status_code == 200 and cleared.get_json()['station_id'] is None
    assert client.put(f'/api/v1/product-categories/{category_id}', json={'station_id': 999},
                      headers=headers).status_code == 400
    assert client.put(f'/api/v1/product-categories/{category_id}', json={'station_id': 'x'},
                      headers=headers).status_code == 400


def test_inactive_station_is_rejected(pos_app):
    client = pos_app.test_client()
    headers = auth_headers(client, make_user('prod@test.com', modules=('Products',)))
    station = make_station('Barra')
    station.is_active = False
    db.session.commit()
    response = client.post('/api/v1/product-categories', json={'name': 'Bebidas', 'station_id': station.id},
                           headers=headers)
    assert response.status_code == 400


def test_station_can_be_set_on_fudo_category_and_sync_keeps_it(pos_app):
    client = pos_app.test_client()
    headers = auth_headers(client, make_user('prod@test.com', modules=('Products',)))
    cocina = make_station('Cocina')
    category = ProductCategory(name='Platos', fudo_category_id='7')
    db.session.add(category)
    db.session.commit()
    response = client.put(f'/api/v1/product-categories/{category.id}', json={'station_id': cocina.id},
                          headers=headers)
    assert response.status_code == 200
    sync_product_categories([{'id': 7, 'attributes': {'name': 'Platos calientes'}}], defaultdict(int))
    db.session.commit()
    db.session.refresh(category)
    assert category.name == 'Platos calientes' and category.station_id == cocina.id
```

En `backend/tests/test_migration_chain.py` agregar al final:

```python
def test_print_stations_follows_products_fudo_link():
    assert _revisions()['b3a0_add_print_stations'] == ['b2b0_products_fudo_link']
```

- [ ] **Step 2: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_pos_print_config.py tests/test_migration_chain.py`
Expected: ImportError (`PrintPoint`) y `KeyError: 'b3a0_add_print_stations'`.

- [ ] **Step 3: Modelos.** Crear `backend/app/models/pos/printing.py`:

```python
from app.extensions import db

PRINT_JOB_KINDS = ('order', 'void', 'bill', 'receipt', 'test')
PRINT_JOB_STATUSES = ('pending', 'printing', 'printed', 'failed')
PRINTER_CONNECTIONS = ('network', 'usb')
PAPER_WIDTHS = (58, 80)


class PrintStation(db.Model):
    __tablename__ = 'print_stations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False, unique=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'position': self.position, 'is_active': self.is_active}


class Printer(db.Model):
    __tablename__ = 'printers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False, unique=True)
    connection = db.Column(db.String(10), nullable=False)
    host = db.Column(db.String(100), nullable=True)
    port = db.Column(db.Integer, nullable=False, default=9100)
    os_name = db.Column(db.String(120), nullable=True)
    paper_width = db.Column(db.Integer, nullable=False, default=80)
    print_point = db.Column(db.String(60), nullable=False)
    station_id = db.Column(db.Integer, db.ForeignKey('print_stations.id'), nullable=True)
    is_cashier = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    station = db.relationship('PrintStation')

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'connection': self.connection, 'host': self.host,
                'port': self.port, 'os_name': self.os_name, 'paper_width': self.paper_width,
                'print_point': self.print_point, 'station_id': self.station_id,
                'station_name': self.station.name if self.station else None, 'is_cashier': self.is_cashier,
                'is_active': self.is_active}


class PrintJob(db.Model):
    __tablename__ = 'print_jobs'
    __table_args__ = (db.Index('ix_print_jobs_printer_status', 'printer_id', 'status', 'id'),)

    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(10), nullable=False)
    printer_id = db.Column(db.Integer, db.ForeignKey('printers.id'), nullable=False, index=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('pos_sales.id'), nullable=True, index=True)
    station_id = db.Column(db.Integer, db.ForeignKey('print_stations.id'), nullable=True)
    batch = db.Column(db.Integer, nullable=True)
    document = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(10), nullable=False, default='pending')
    attempts = db.Column(db.Integer, nullable=False, default=0)
    error = db.Column(db.String(255), nullable=True)
    claimed_by = db.Column(db.String(60), nullable=True)
    claimed_at = db.Column(db.DateTime, nullable=True)
    printed_at = db.Column(db.DateTime, nullable=True)
    failed_at = db.Column(db.DateTime, nullable=True)
    reprint_of = db.Column(db.Integer, db.ForeignKey('print_jobs.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

    printer = db.relationship('Printer')
    sale = db.relationship('PosSale')
    station = db.relationship('PrintStation')


class PrintPoint(db.Model):
    """Punto de impresión (una PC con la página /pos/impresion). Se crea al configurar impresoras."""
    __tablename__ = 'print_points'

    name = db.Column(db.String(60), primary_key=True)
    last_seen_at = db.Column(db.DateTime, nullable=True)
```

En `backend/app/models/pos/__init__.py`, agregar:

```python
from app.models.pos.printing import (PAPER_WIDTHS, PRINT_JOB_KINDS, PRINT_JOB_STATUSES, PRINTER_CONNECTIONS,
                                     PrintJob, PrintPoint, PrintStation, Printer)
```

y sumar a `__all__`: `'PrintStation', 'Printer', 'PrintJob', 'PrintPoint', 'PRINT_JOB_KINDS', 'PRINT_JOB_STATUSES', 'PRINTER_CONNECTIONS', 'PAPER_WIDTHS'`.

En `backend/app/models/product_category.py`:
- después de `fudo_status`, agregar la columna:

```python
    # Estación de producción (comandas). Campo de Galia: la sincronización con Fudo no lo toca.
    station_id = db.Column(db.Integer, db.ForeignKey('print_stations.id'), nullable=True)
```

- en `to_dict`, después de `'fudo_status': self.fudo_status,`, agregar `'station_id': self.station_id,`.

- [ ] **Step 4: Migración.** Crear `backend/migrations/versions/b3a0_add_print_stations.py`:

```python
"""add print stations, printers, print jobs and points; station on product categories

Revision ID: b3a0_add_print_stations
Revises: b2b0_products_fudo_link
Create Date: 2026-10-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b3a0_add_print_stations'
down_revision = 'b2b0_products_fudo_link'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'print_stations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=60), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_table(
        'printers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=60), nullable=False),
        sa.Column('connection', sa.String(length=10), nullable=False),
        sa.Column('host', sa.String(length=100), nullable=True),
        sa.Column('port', sa.Integer(), nullable=False, server_default='9100'),
        sa.Column('os_name', sa.String(length=120), nullable=True),
        sa.Column('paper_width', sa.Integer(), nullable=False, server_default='80'),
        sa.Column('print_point', sa.String(length=60), nullable=False),
        sa.Column('station_id', sa.Integer(), sa.ForeignKey('print_stations.id'), nullable=True),
        sa.Column('is_cashier', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_table(
        'print_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kind', sa.String(length=10), nullable=False),
        sa.Column('printer_id', sa.Integer(), sa.ForeignKey('printers.id'), nullable=False),
        sa.Column('sale_id', sa.Integer(), sa.ForeignKey('pos_sales.id'), nullable=True),
        sa.Column('station_id', sa.Integer(), sa.ForeignKey('print_stations.id'), nullable=True),
        sa.Column('batch', sa.Integer(), nullable=True),
        sa.Column('document', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=10), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error', sa.String(length=255), nullable=True),
        sa.Column('claimed_by', sa.String(length=60), nullable=True),
        sa.Column('claimed_at', sa.DateTime(), nullable=True),
        sa.Column('printed_at', sa.DateTime(), nullable=True),
        sa.Column('failed_at', sa.DateTime(), nullable=True),
        sa.Column('reprint_of', sa.Integer(), sa.ForeignKey('print_jobs.id'), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_print_jobs_printer_id', 'print_jobs', ['printer_id'])
    op.create_index('ix_print_jobs_sale_id', 'print_jobs', ['sale_id'])
    op.create_index('ix_print_jobs_printer_status', 'print_jobs', ['printer_id', 'status', 'id'])
    op.create_table(
        'print_points',
        sa.Column('name', sa.String(length=60), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('name'),
    )
    with op.batch_alter_table('product_categories') as batch:
        batch.add_column(sa.Column('station_id', sa.Integer(), nullable=True))
        batch.create_foreign_key('fk_product_categories_station_id', 'print_stations', ['station_id'], ['id'])


def downgrade():
    with op.batch_alter_table('product_categories') as batch:
        batch.drop_constraint('fk_product_categories_station_id', type_='foreignkey')
        batch.drop_column('station_id')
    op.drop_table('print_points')
    op.drop_index('ix_print_jobs_printer_status', table_name='print_jobs')
    op.drop_index('ix_print_jobs_sale_id', table_name='print_jobs')
    op.drop_index('ix_print_jobs_printer_id', table_name='print_jobs')
    op.drop_table('print_jobs')
    op.drop_table('printers')
    op.drop_table('print_stations')
```

- [ ] **Step 5: Estación en la API de categorías.** En `backend/app/routes/product_categories.py`:

Agregar los imports (junto a los existentes):

```python
from app.extensions import db
from app.models.pos import PrintStation
```

(si `db` ya está importado, no duplicarlo). Agregar este helper después de los imports:

```python
def _station_id(value):
    """None o el id de una estación activa. ValueError si no es válida (la ruta responde 400)."""
    if value in (None, ''):
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError('La estación es inválida')
    station = db.session.get(PrintStation, value)
    if station is None or not station.is_active:
        raise ValueError('La estación no existe')
    return station.id
```

En `create_category`, dentro del `try` que limpia los campos, agregar:

```python
        station_id = _station_id(data.get('station_id'))
```

y crear la categoría con `ProductCategory(name=name, description=description, color=color, icon=icon, station_id=station_id)`.

En `update_category`, dentro del `try` que arma `updates`, después del `for field, max_len in limits.items(): …`, agregar:

```python
        if 'station_id' in data:
            updates['station_id'] = _station_id(data['station_id'])
```

- [ ] **Step 6: Correr**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_pos_print_config.py tests/test_migration_chain.py tests/test_product_sync.py tests/test_products_fudo_lock.py tests/test_pos_models.py`
Expected: todos pasan.

- [ ] **Step 7: Commit**

```bash
git add backend/app/models backend/migrations/versions/b3a0_add_print_stations.py backend/app/routes/product_categories.py backend/tests/print_helpers.py backend/tests/test_pos_print_config.py backend/tests/test_migration_chain.py
git commit -m "feat(pos): print stations, printers and print jobs models"
```

---

### Task 2: Documentos y comandas automáticas

**Files:**
- Create: `backend/app/services/pos/print_documents.py`, `backend/app/services/pos/print_service.py`
- Modify: `backend/app/services/pos/sale_service.py` (`confirm_pending`, `cancel_item`, `cancel_sale_rows`)
- Test: `backend/tests/test_pos_print_jobs.py`

**Interfaces:**
- Consumes: modelos y helpers de la Task 1; `common.now`, `common.display_name`; `ARGENTINA_TZ`.
- Produces:
  - **`print_documents`:**
    - `order_document(sale, station, batch, items)`, `void_document(sale, station, items, reason)`;
    - `bill_document(sale)`, `receipt_document(sale)`;
    - `test_document(printer)`, `mark_reprint(document)`;
    - `NOT_FISCAL = 'No válido como factura'`.
    - Cada documento es `{'title', 'header': [str], 'lines': [{'qty', 'text', 'amount', 'details': [str], 'strike'}], 'totals': [{'label', 'amount'}], 'footer': [str]}`, con montos como string `'1234.50'`.
  - **`print_service`:**
    - `jobs_for_batch(sale, items, user) -> list[PrintJob]`;
    - `jobs_for_void(sale, items, user, reason) -> list[PrintJob]`;
    - `station_printer(station_id) -> Printer | None`, `cashier_printer() -> Printer | None`;
    - `add_job(kind, printer, user, document, sale=None, station_id=None, batch=None, reprint_of=None) -> PrintJob`.
    - Las funciones de `print_service` no hacen commit.

- [ ] **Step 1: Tests que fallan.** Crear `backend/tests/test_pos_print_jobs.py`:

```python
import pytest

from app.extensions import db
from app.models.pos import PrintJob
from app.services.pos import payment_service, sale_service
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401
from print_helpers import make_kitchen_product, make_printer, make_station


@pytest.fixture
def ctx(pos_app):
    user = make_user('caja@test.com', modules=('POS', 'Anular', 'Camarero'))
    cat = make_catalog()
    kitchen = make_kitchen_product()
    _salon, t1, _t2 = make_floor()
    cocina, barra = make_station('Cocina'), make_station('Barra')
    kitchen.category.station_id = cocina.id
    cat.category.station_id = barra.id
    db.session.commit()
    make_printer('Térmica cocina', station=cocina)
    make_printer('Térmica barra', station=barra)
    return user, cat, kitchen, t1, cocina, barra


def _jobs(kind='order'):
    return PrintJob.query.filter_by(kind=kind).order_by(PrintJob.id).all()


def test_batch_is_split_by_station_with_details(ctx):
    user, cat, kitchen, t1, cocina, barra = ctx
    sale = sale_service.open_sale(user, 'salon', table_id=t1.id, people=2)
    sale_service.add_item(user, sale.id, kitchen.variant.id, quantity=2, note='sin sal')
    sale_service.add_item(user, sale.id, cat.taza.id, modifier_option_ids=[cat.entera.id])
    sale_service.confirm_batch(user, sale.id)
    jobs = _jobs()
    assert [(j.station_id, j.batch, j.sale_id) for j in jobs] == [(cocina.id, 1, sale.id), (barra.id, 1, sale.id)]
    kitchen_doc, bar_doc = jobs[0].document, jobs[1].document
    assert kitchen_doc['title'] == 'COCINA'
    assert kitchen_doc['header'][0] == 'Mesa 1' and 'Tanda 1' in kitchen_doc['header']
    assert kitchen_doc['lines'] == [{'qty': '2', 'text': 'Tostado', 'amount': None, 'details': ['Nota: sin sal'],
                                     'strike': False}]
    assert bar_doc['title'] == 'BARRA'
    assert bar_doc['lines'][0]['text'] == 'Cortado' and bar_doc['lines'][0]['details'] == ['Entera']
    assert all(j.status == 'pending' and j.printer.station_id == j.station_id for j in jobs)


def test_category_without_station_prints_nothing(ctx):
    user, cat, _kitchen, t1, _cocina, _barra = ctx
    cat.category.station_id = None
    db.session.commit()
    sale = sale_service.open_sale(user, 'salon', table_id=t1.id, people=1)
    sale_service.add_item(user, sale.id, cat.unidad.id)
    sale_service.confirm_batch(user, sale.id)
    assert _jobs() == []


def test_station_without_printer_is_skipped(ctx):
    user, cat, kitchen, t1, cocina, _barra = ctx
    for printer in cocina_printers(cocina):
        printer.is_active = False
    db.session.commit()
    sale = sale_service.open_sale(user, 'salon', table_id=t1.id, people=1)
    sale_service.add_item(user, sale.id, kitchen.variant.id)
    sale_service.add_item(user, sale.id, cat.unidad.id)
    sale = sale_service.confirm_batch(user, sale.id)
    assert [j.document['title'] for j in _jobs()] == ['BARRA']
    assert all(i.status == 'confirmed' for i in sale.items)


def cocina_printers(station):
    from app.models.pos import Printer
    return Printer.query.filter_by(station_id=station.id).all()


def test_second_batch_gets_its_number(ctx):
    user, cat, _kitchen, t1, _cocina, _barra = ctx
    sale = sale_service.open_sale(user, 'salon', table_id=t1.id, people=1)
    sale_service.add_item(user, sale.id, cat.unidad.id)
    sale_service.confirm_batch(user, sale.id)
    sale_service.add_item(user, sale.id, cat.unidad.id)
    sale_service.confirm_batch(user, sale.id)
    assert [j.batch for j in _jobs()] == [1, 2]
    assert 'Tanda 2' in _jobs()[1].document['header']


def test_waiter_confirm_route_and_counter_payment_print(ctx, pos_app):
    user, cat, _kitchen, t1, _cocina, _barra = ctx
    client = pos_app.test_client()
    headers = auth_headers(client, make_user('mozo@test.com', modules=('Camarero',)))
    sale = client.post('/api/v1/pos/sales', json={'sale_type': 'salon', 'table_id': t1.id, 'people': 1},
                       headers=headers).get_json()
    client.post(f"/api/v1/pos/sales/{sale['id']}/items", json={'product_variant_id': cat.unidad.id}, headers=headers)
    assert client.post(f"/api/v1/pos/sales/{sale['id']}/confirm", headers=headers).status_code == 200
    counter = sale_service.open_sale(user, 'counter')
    sale_service.add_item(user, counter.id, cat.unidad.id)
    payment_service.add_payment(user, counter.id, cat.efectivo.id, 900)
    jobs = _jobs()
    assert len(jobs) == 2 and jobs[1].document['header'][0] == f'Mostrador #{counter.number}'


def test_cancelling_items_and_sales_prints_voids(ctx):
    user, cat, kitchen, t1, cocina, barra = ctx
    sale = sale_service.open_sale(user, 'salon', table_id=t1.id, people=1)
    sale_service.add_item(user, sale.id, kitchen.variant.id)
    sale_service.add_item(user, sale.id, cat.unidad.id)
    sale_service.add_item(user, sale.id, cat.unidad.id)
    sale = sale_service.confirm_batch(user, sale.id)
    sale_service.add_item(user, sale.id, cat.unidad.id)
    pending = sale.items[-1]
    sale_service.delete_item(user, sale.id, pending.id)
    assert _jobs('void') == []
    bar_item = next(i for i in sale.items if i.product_name == 'Medialuna')
    sale_service.cancel_item(user, sale.id, bar_item.id, 'Error de carga')
    voids = _jobs('void')
    assert [(v.station_id, v.document['title']) for v in voids] == [(barra.id, 'ANULACIÓN · BARRA')]
    assert voids[0].document['lines'][0]['strike'] is True
    assert 'Motivo: Error de carga' in voids[0].document['footer']
    sale_service.cancel_sale(user, sale.id, 'Se fueron')
    assert sorted(v.station_id for v in _jobs('void')[1:]) == sorted([cocina.id, barra.id])
```

- [ ] **Step 2: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_pos_print_jobs.py`
Expected: fallan porque no hay trabajos (`[] == [...]`).

- [ ] **Step 3: Documentos.** Crear `backend/app/services/pos/print_documents.py`:

```python
"""Documentos de impresión del POS: comanda, anulación, precuenta, ticket y prueba.

Un documento es JSON: {title, header: [str], lines: [{qty, text, amount, details: [str], strike}],
totals: [{label, amount}], footer: [str]}. Los montos van como string con 2 decimales, calculados acá;
el frontend solo los imprime. El mismo documento le sirve a una futura pantalla de cocina.
"""
import copy
from decimal import Decimal

import pytz

from app.extensions import db
from app.models import ProductVariant
from app.services.pos.common import display_name, now
from app.utils.timezone_utils import ARGENTINA_TZ

NOT_FISCAL = 'No válido como factura'
REPRINT = 'REIMPRESIÓN'


def _when(moment=None):
    return pytz.utc.localize(moment or now()).astimezone(ARGENTINA_TZ).strftime('%d/%m/%Y %H:%M')


def _money(value):
    return f'{Decimal(value):.2f}'


def _qty(value):
    value = Decimal(value)
    return str(int(value)) if value == value.to_integral_value() else format(value.normalize(), 'f')


def _place(sale):
    return sale.table.label if sale.table is not None else f'Mostrador #{sale.number}'


def _waiter(sale):
    return f'Mozo: {display_name(sale.waiter) or "—"}'


def _text(item):
    variant = db.session.get(ProductVariant, item.product_variant_id)
    several = variant is not None and variant.product.variants.filter_by(is_active=True).count() > 1
    return f'{item.product_name} ({item.variant_name})' if several else item.product_name


def _details(item):
    details = [modifier.option_name for modifier in item.modifiers]
    if item.note:
        details.append(f'Nota: {item.note}')
    return details


def _line(item, amount=None, strike=False):
    return {'qty': _qty(item.quantity), 'text': _text(item), 'amount': amount, 'details': _details(item),
            'strike': strike}


def _document(title, header, lines, totals=None, footer=None):
    return {'title': title, 'header': header, 'lines': lines, 'totals': totals or [], 'footer': footer or []}


def order_document(sale, station, batch, items):
    return _document(station.name.upper(), [_place(sale), _waiter(sale), f'Tanda {batch}', _when()],
                     [_line(item) for item in items])


def void_document(sale, station, items, reason):
    return _document(f'ANULACIÓN · {station.name.upper()}', [_place(sale), _waiter(sale), _when()],
                     [_line(item, strike=True) for item in items], footer=[f'Motivo: {reason}'])


def _sale_header(sale):
    header = [_place(sale)]
    if sale.people:
        header.append(f'Personas: {sale.people}')
    header += [_waiter(sale), f'Venta #{sale.number}', _when()]
    return header


def _sale_lines(sale):
    return [_line(item, amount=_money(item.line_total)) for item in sale.items if item.status == 'confirmed']


def _sale_totals(sale):
    totals = [{'label': 'Subtotal', 'amount': _money(sale.subtotal)}]
    for discount in sale.discounts:
        if discount.cancelled_at is None:
            label = f'Descuento · {discount.reason}' if discount.reason else 'Descuento'
            totals.append({'label': label, 'amount': _money(-discount.amount)})
    totals.append({'label': 'TOTAL', 'amount': _money(sale.total)})
    return totals


def bill_document(sale):
    return _document('PRECUENTA', _sale_header(sale), _sale_lines(sale), _sale_totals(sale), [NOT_FISCAL])


def receipt_document(sale):
    totals = _sale_totals(sale)
    for payment in sale.payments:
        if payment.cancelled_at is None:
            totals.append({'label': payment.method_name, 'amount': _money(payment.amount)})
            if payment.change:
                totals.append({'label': 'Vuelto', 'amount': _money(payment.change)})
    return _document('TICKET', _sale_header(sale), _sale_lines(sale), totals, [NOT_FISCAL, '¡Gracias!'])


def test_document(printer):
    return _document('PRUEBA', [printer.name, f'Papel {printer.paper_width} mm', _when()],
                     [{'qty': '1', 'text': 'Café con leche y medialuna de manteca (ñandú)', 'amount': '1234.50',
                       'details': ['Acentos: áéíóú ÁÉÍÓÚ ü ñ Ñ ¿? ¡!'], 'strike': False}],
                     [{'label': 'TOTAL', 'amount': '1234.50'}], ['Si los acentos y la ñ se ven bien, está OK'])


def mark_reprint(document):
    copied = copy.deepcopy(document)
    copied['header'] = list(copied.get('header', [])) + [REPRINT]
    return copied
```

(La función `test_document` empieza con `test_`; pytest no la toma porque el módulo está en `app/`, no en `tests/`.)

- [ ] **Step 4: Servicio.** Crear `backend/app/services/pos/print_service.py`:

```python
"""Cola de impresión del POS: comandas por estación, precuenta, ticket, reimpresión y estado.

Las funciones de creación (jobs_for_batch, jobs_for_void, add_job) no hacen commit: corren dentro de la
transacción de la venta. Las acciones de la cola hacen commit.
"""
from collections import OrderedDict

from app.extensions import db
from app.models import ProductVariant
from app.models.pos import PrintJob, PrintStation, Printer
from app.services.pos import print_documents as documents
from app.services.pos.common import now


def station_printer(station_id):
    if station_id is None:
        return None
    return Printer.query.filter_by(station_id=station_id, is_active=True).order_by(Printer.id).first()


def cashier_printer():
    return Printer.query.filter_by(is_cashier=True, is_active=True).order_by(Printer.id).first()


def add_job(kind, printer, user, document, sale=None, station_id=None, batch=None, reprint_of=None):
    job = PrintJob(kind=kind, printer_id=printer.id, sale_id=sale.id if sale is not None else None,
                   station_id=station_id, batch=batch, document=document, status='pending', attempts=0,
                   created_by=user.id, created_at=now(), reprint_of=reprint_of)
    db.session.add(job)
    return job


def _station_of(item):
    variant = db.session.get(ProductVariant, item.product_variant_id)
    category = variant.product.category if variant is not None else None
    return category.station_id if category is not None else None


def _by_station(items):
    groups = OrderedDict()
    for item in items:
        station_id = _station_of(item)
        if station_id is not None:
            groups.setdefault(station_id, []).append(item)
    return groups


def _station_jobs(kind, sale, items, user, build):
    jobs = []
    for station_id, group in _by_station(items).items():
        station = db.session.get(PrintStation, station_id)
        printer = station_printer(station_id)
        if station is None or not station.is_active or printer is None:
            continue
        jobs.append(add_job(kind, printer, user, build(station, group), sale, station_id, group[0].batch))
    return jobs


def jobs_for_batch(sale, items, user):
    """Una comanda por estación con los ítems recién confirmados. Sin estación o sin impresora: nada."""
    return _station_jobs('order', sale, items, user,
                         lambda station, group: documents.order_document(sale, station, group[0].batch, group))


def jobs_for_void(sale, items, user, reason):
    """Una comanda de anulación por estación con los ítems confirmados que se anularon."""
    return _station_jobs('void', sale, items, user,
                         lambda station, group: documents.void_document(sale, station, group, reason))
```

- [ ] **Step 5: Engancharlo en las ventas.** En `backend/app/services/pos/sale_service.py`:
  - agregar `from app.services.pos import print_service` junto a los otros imports de `app.services.pos`;
  - en `confirm_pending`, antes de `return pending`:

```python
    print_service.jobs_for_batch(sale, pending, user)
```

  - en `cancel_item`, después de `_cancel_item_row(item, user, reason, reason_id)`:

```python
    print_service.jobs_for_void(sale, [item], user, reason)
```

  - en `cancel_sale_rows`, después de `stock_hooks.restore(confirmed)`:

```python
    print_service.jobs_for_void(sale, confirmed, user, reason)
```

  - comprobar que no hay import circular: `print_service` no importa `sale_service`.

- [ ] **Step 6: Correr**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_pos_print_jobs.py tests/test_pos_batches.py tests/test_pos_cancellations.py tests/test_pos_move_split.py tests/test_pos_payments.py tests/test_pos_cash_payments.py`
Expected: todos pasan.

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/pos/print_documents.py backend/app/services/pos/print_service.py backend/app/services/pos/sale_service.py backend/tests/test_pos_print_jobs.py
git commit -m "feat(pos): kitchen order and void print jobs per station"
```

---

### Task 3: Precuenta, ticket, reimpresión, cola y firma QZ

**Files:**
- Modify: `backend/app/services/pos/print_service.py`, `backend/requirements.txt`
- Test: `backend/tests/test_pos_print_queue.py`

**Interfaces:**
- Consumes: `add_job`, `station_printer`, `cashier_printer`, `documents.*` (Task 2); `common.load_sale`, `common.parse_id`, `common.now`; `clean_str`.
- Produces (`print_service`):
  - **Trabajos:**
    - `print_bill(user, sale_id) -> PrintJob`, `print_receipt(user, sale_id) -> PrintJob`;
    - `reprint(user, job_id) -> PrintJob`, `test_print(user, printer_id) -> PrintJob`.
  - **Cola:**
    - `claim(print_point) -> list[PrintJob]`;
    - `mark_done(job_id)`, `mark_failed(job_id, error)`, `retry(job_id)`, `mark_printed(job_id)`, cada una `-> PrintJob`.
  - **Estado:**
    - `status() -> {'problems': [job_dict], 'points': [{'name', 'last_seen_at', 'down'}], 'pending': int}`;
    - `sale_jobs(sale_id) -> list[PrintJob]`;
    - `print_points() -> [{'name', 'printers': [printer_dict]}]`.
  - **Serialización:** `job_to_dict(job, with_printer=False) -> dict` con `{'id', 'kind', 'status', 'printer': {'id', 'name'} (más 'connection', 'host', 'port', 'os_name', 'paper_width' si with_printer), 'sale_id', 'sale_number', 'place', 'station_name', 'batch', 'attempts', 'error', 'created_at', 'printed_at', 'reprint_of', 'document'}`.
  - **Firma QZ:** `qz_certificate() -> str` y `sign_qz(message) -> str` (base64).
  - **Constantes:** `CLAIM_LIMIT = 10`, `STALE_PRINTING = timedelta(seconds=60)`, `RETRY_AFTER = timedelta(seconds=15)`, `MAX_ATTEMPTS = 5`, `PROBLEM_AGE = timedelta(seconds=30)`, `POINT_DOWN = timedelta(seconds=30)`.

- [ ] **Step 1: Dependencia**

En `backend/requirements.txt`, agregar la línea `cryptography==42.0.8`.
Run: `PY -m pip install cryptography==42.0.8`
Expected: se instala sin errores.

- [ ] **Step 2: Tests que fallan.** Crear `backend/tests/test_pos_print_queue.py`:

```python
import base64
from datetime import datetime, timedelta

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID

from app.extensions import db
from app.models.pos import PrintJob, PrintPoint
from app.services.pos import payment_service, print_service, sale_service
from app.services.pos.errors import PosError
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401
from print_helpers import make_printer, make_station


@pytest.fixture
def ctx(pos_app):
    user = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    _salon, t1, _t2 = make_floor()
    barra = make_station('Barra')
    cat.category.station_id = barra.id
    db.session.commit()
    bar_printer = make_printer('Térmica barra', station=barra, point='Caja')
    cashier = make_printer('Térmica caja', cashier=True, point='Caja', width=58)
    return user, cat, t1, barra, bar_printer, cashier


def _billed(user, cat, table):
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=2)
    sale_service.add_item(user, sale.id, cat.unidad.id, quantity=2)
    sale_service.confirm_batch(user, sale.id)
    return sale_service.request_bill(user, sale.id)


def test_bill_and_receipt_go_to_cashier_printer(ctx):
    user, cat, t1, _barra, _bp, cashier = ctx
    sale = _billed(user, cat, t1)
    bill = print_service.print_bill(user, sale.id)
    assert bill.kind == 'bill' and bill.printer_id == cashier.id
    doc = bill.document
    assert doc['title'] == 'PRECUENTA' and doc['lines'][0]['amount'] == '1800.00'
    assert doc['totals'][-1] == {'label': 'TOTAL', 'amount': '1800.00'} and doc['footer'] == ['No válido como factura']
    assert 'Personas: 2' in doc['header']
    with pytest.raises(PosError) as error:
        print_service.print_receipt(user, sale.id)
    assert error.value.status == 409
    payment_service.add_payment(user, sale.id, cat.efectivo.id, 1800, tendered=2000)
    receipt = print_service.print_receipt(user, sale.id)
    labels = [t['label'] for t in receipt.document['totals']]
    assert receipt.document['title'] == 'TICKET' and labels[-2:] == ['Efectivo', 'Vuelto']
    assert receipt.document['totals'][-1]['amount'] == '200.00'


def test_bill_requires_confirmed_items_and_a_cashier_printer(ctx):
    user, cat, t1, _barra, _bp, cashier = ctx
    sale = sale_service.open_sale(user, 'salon', table_id=t1.id, people=1)
    with pytest.raises(PosError) as error:
        print_service.print_bill(user, sale.id)
    assert error.value.status == 409
    sale_service.add_item(user, sale.id, cat.unidad.id)
    sale_service.confirm_batch(user, sale.id)
    cashier.is_active = False
    db.session.commit()
    with pytest.raises(PosError) as error:
        print_service.print_bill(user, sale.id)
    assert error.value.status == 409 and error.value.message == 'No hay impresora de caja configurada'


def test_reprint_copies_with_mark_and_follows_current_printer(ctx):
    user, cat, t1, barra, bar_printer, _cashier = ctx
    _billed(user, cat, t1)
    order = PrintJob.query.filter_by(kind='order').one()
    bar_printer.is_active = False
    db.session.commit()
    with pytest.raises(PosError) as error:
        print_service.reprint(user, order.id)
    assert error.value.status == 409
    new_printer = make_printer('Térmica barra 2', station=barra, point='Caja')
    copy = print_service.reprint(user, order.id)
    assert copy.reprint_of == order.id and copy.printer_id == new_printer.id
    assert copy.document['header'][-1] == 'REIMPRESIÓN' and order.document['header'][-1] != 'REIMPRESIÓN'


def test_claim_filters_by_point_and_marks_printing(ctx):
    user, cat, t1, _barra, bar_printer, _cashier = ctx
    make_printer('Térmica oficina', cashier=False, point='Oficina')
    _billed(user, cat, t1)
    assert print_service.claim('Oficina') == []
    jobs = print_service.claim('Caja')
    assert [(j.kind, j.status, j.claimed_by) for j in jobs] == [('order', 'printing', 'Caja')]
    assert print_service.claim('Caja') == []
    assert db.session.get(PrintPoint, 'Caja').last_seen_at is not None
    done = print_service.mark_done(jobs[0].id)
    assert done.status == 'printed' and done.printed_at is not None


def test_failed_jobs_retry_until_max_then_wait_for_manual(ctx):
    user, cat, t1, _barra, _bp, _cashier = ctx
    _billed(user, cat, t1)
    job = print_service.claim('Caja')[0]
    for attempt in range(1, print_service.MAX_ATTEMPTS + 1):
        failed = print_service.mark_failed(job.id, 'Sin papel')
        assert failed.status == 'failed' and failed.attempts == attempt and failed.error == 'Sin papel'
        failed.failed_at = datetime.utcnow() - timedelta(seconds=20)
        db.session.commit()
        claimed = print_service.claim('Caja')
        if attempt < print_service.MAX_ATTEMPTS:
            assert [j.id for j in claimed] == [job.id]
        else:
            assert claimed == []
    retried = print_service.retry(job.id)
    assert retried.status == 'pending' and retried.attempts == 0
    marked = print_service.mark_printed(job.id)
    assert marked.status == 'printed' and marked.claimed_by == 'manual'
    with pytest.raises(PosError):
        print_service.retry(job.id)


def test_stale_printing_returns_to_queue(ctx):
    user, cat, t1, _barra, _bp, _cashier = ctx
    _billed(user, cat, t1)
    job = print_service.claim('Caja')[0]
    job.claimed_at = datetime.utcnow() - timedelta(seconds=61)
    db.session.commit()
    again = print_service.claim('Caja')
    assert [j.id for j in again] == [job.id]


def test_status_reports_problems_and_down_points(ctx):
    user, cat, t1, _barra, _bp, _cashier = ctx
    status = print_service.status()
    assert status == {'problems': [], 'points': [{'name': 'Caja', 'last_seen_at': None, 'down': True}],
                      'pending': 0}
    _billed(user, cat, t1)
    job = PrintJob.query.one()
    job.created_at = datetime.utcnow() - timedelta(seconds=31)
    db.session.commit()
    print_service.claim('Caja')
    status = print_service.status()
    assert [p['id'] for p in status['problems']] == [job.id] and status['pending'] == 1
    assert status['points'][0]['down'] is False
    assert status['problems'][0]['place'] == 'Mesa 1' and status['problems'][0]['station_name'] == 'Barra'


def test_test_print_and_print_points(ctx):
    user, _cat, _t1, _barra, bar_printer, cashier = ctx
    job = print_service.test_print(user, cashier.id)
    assert job.kind == 'test' and job.sale_id is None and job.document['title'] == 'PRUEBA'
    points = print_service.print_points()
    assert [p['name'] for p in points] == ['Caja']
    assert sorted(p['name'] for p in points[0]['printers']) == sorted([bar_printer.name, cashier.name])


def test_job_dict_with_printer_connection(ctx):
    user, cat, t1, _barra, bar_printer, _cashier = ctx
    _billed(user, cat, t1)
    job = print_service.claim('Caja')[0]
    data = print_service.job_to_dict(job, with_printer=True)
    assert data['printer'] == {'id': bar_printer.id, 'name': 'Térmica barra', 'connection': 'network',
                               'host': '192.168.0.50', 'port': 9100, 'os_name': None, 'paper_width': 80}
    assert data['document']['title'] == 'BARRA' and data['sale_number'] == 1


def _key_pair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'galia-test')])
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(1).not_valid_before(datetime(2026, 1, 1)).not_valid_after(datetime(2036, 1, 1))
            .sign(key, hashes.SHA256()))
    key_pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption()).decode()
    return cert, cert.public_bytes(serialization.Encoding.PEM).decode(), key_pem


def test_qz_signing(pos_app, monkeypatch):
    monkeypatch.delenv('QZ_CERTIFICATE', raising=False)
    monkeypatch.delenv('QZ_PRIVATE_KEY', raising=False)
    with pytest.raises(PosError) as error:
        print_service.qz_certificate()
    assert error.value.status == 404
    cert, cert_pem, key_pem = _key_pair()
    monkeypatch.setenv('QZ_CERTIFICATE', cert_pem.replace('\n', '\\n'))
    monkeypatch.setenv('QZ_PRIVATE_KEY', key_pem.replace('\n', '\\n'))
    assert print_service.qz_certificate() == cert_pem
    signature = base64.b64decode(print_service.sign_qz('mensaje de QZ'))
    cert.public_key().verify(signature, b'mensaje de QZ', padding.PKCS1v15(), hashes.SHA512())
```

- [ ] **Step 3: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_pos_print_queue.py`
Expected: `AttributeError: module 'app.services.pos.print_service' has no attribute 'print_bill'` (y equivalentes).

- [ ] **Step 4: Implementar.** En `backend/app/services/pos/print_service.py`:

Cambiar los imports de arriba a:

```python
import base64
import os
from collections import OrderedDict
from datetime import timedelta

from sqlalchemy import and_, or_

from app.extensions import db
from app.models import ProductVariant
from app.models.pos import PrintJob, PrintPoint, PrintStation, Printer
from app.services.pos import print_documents as documents
from app.services.pos.common import load_sale, now, parse_id
from app.services.pos.errors import PosError, bad_request, not_found
from app.utils.validation import clean_str

CLAIM_LIMIT = 10
STALE_PRINTING = timedelta(seconds=60)
RETRY_AFTER = timedelta(seconds=15)
MAX_ATTEMPTS = 5
PROBLEM_AGE = timedelta(seconds=30)
POINT_DOWN = timedelta(seconds=30)
```

Agregar al final del archivo:

```python
def _require_cashier():
    printer = cashier_printer()
    if printer is None:
        raise PosError('No hay impresora de caja configurada')
    return printer


def print_bill(user, sale_id):
    sale = load_sale(sale_id)
    if sale.status not in ('open', 'billing') or not any(i.status == 'confirmed' for i in sale.items):
        raise PosError('La venta no tiene ítems confirmados para la precuenta')
    job = add_job('bill', _require_cashier(), user, documents.bill_document(sale), sale)
    db.session.commit()
    return job


def print_receipt(user, sale_id):
    sale = load_sale(sale_id)
    if sale.status != 'closed':
        raise PosError('Solo se imprime el ticket de una venta cerrada')
    job = add_job('receipt', _require_cashier(), user, documents.receipt_document(sale), sale)
    db.session.commit()
    return job


def _load_job(job_id, lock=True):
    query = PrintJob.query.filter_by(id=parse_id(job_id, 'El trabajo'))
    if lock:
        query = query.with_for_update().populate_existing()
    job = query.first()
    if job is None:
        raise not_found('El trabajo de impresión no existe')
    return job


def reprint(user, job_id):
    original = _load_job(job_id, lock=False)
    if original.kind in ('order', 'void'):
        printer = station_printer(original.station_id)
        if printer is None:
            raise PosError('La estación no tiene una impresora activa')
    elif original.kind == 'test':
        printer = original.printer
    else:
        printer = _require_cashier()
    job = add_job(original.kind, printer, user, documents.mark_reprint(original.document), original.sale,
                  original.station_id, original.batch, reprint_of=original.id)
    db.session.commit()
    return job


def test_print(user, printer_id):
    printer = db.session.get(Printer, parse_id(printer_id, 'La impresora'))
    if printer is None or not printer.is_active:
        raise not_found('La impresora no existe')
    job = add_job('test', printer, user, documents.test_document(printer))
    db.session.commit()
    return job


def _recover():
    """Devuelve a la cola lo que quedó imprimiendo sin respuesta y los fallidos que pueden reintentarse."""
    moment = now()
    PrintJob.query.filter(PrintJob.status == 'printing', PrintJob.claimed_at < moment - STALE_PRINTING).update(
        {'status': 'pending', 'claimed_by': None, 'claimed_at': None}, synchronize_session=False)
    PrintJob.query.filter(PrintJob.status == 'failed', PrintJob.attempts < MAX_ATTEMPTS,
                          PrintJob.failed_at < moment - RETRY_AFTER).update(
        {'status': 'pending', 'claimed_by': None, 'claimed_at': None}, synchronize_session=False)


def claim(print_point):
    point = clean_str(print_point, 60)
    if not point:
        raise bad_request('Indicá el punto de impresión')
    _recover()
    # El punto existe desde que se configuró una impresora: solo se actualiza (sin inserts concurrentes).
    PrintPoint.query.filter_by(name=point).update({'last_seen_at': now()}, synchronize_session=False)
    printer_ids = [p.id for p in Printer.query.filter_by(print_point=point, is_active=True)]
    jobs = []
    if printer_ids:
        query = (PrintJob.query.filter(PrintJob.printer_id.in_(printer_ids), PrintJob.status == 'pending')
                 .order_by(PrintJob.id).limit(CLAIM_LIMIT))
        if db.engine.dialect.name == 'postgresql':
            query = query.with_for_update(skip_locked=True)
        jobs = query.all()
        for job in jobs:
            job.status = 'printing'
            job.claimed_by = point
            job.claimed_at = now()
    db.session.commit()
    return jobs


def mark_done(job_id):
    job = _load_job(job_id)
    job.status = 'printed'
    job.printed_at = now()
    job.error = None
    db.session.commit()
    return job


def mark_failed(job_id, error):
    job = _load_job(job_id)
    if job.status == 'printed':
        db.session.commit()
        return job
    job.attempts += 1
    job.status = 'failed'
    job.error = (error if isinstance(error, str) else '').strip()[:255] or 'Error desconocido'
    job.failed_at = now()
    job.claimed_by = None
    job.claimed_at = None
    db.session.commit()
    return job


def retry(job_id):
    job = _load_job(job_id)
    if job.status == 'printed':
        raise PosError('El trabajo ya se imprimió')
    job.status = 'pending'
    job.attempts = 0
    job.error = None
    job.claimed_by = None
    job.claimed_at = None
    db.session.commit()
    return job


def mark_printed(job_id):
    job = _load_job(job_id)
    job.status = 'printed'
    job.printed_at = now()
    job.claimed_by = 'manual'
    db.session.commit()
    return job


def _place(job):
    sale = job.sale
    if sale is None:
        return None
    return sale.table.label if sale.table is not None else f'Mostrador #{sale.number}'


def job_to_dict(job, with_printer=False):
    printer = {'id': job.printer.id, 'name': job.printer.name}
    if with_printer:
        printer.update({'connection': job.printer.connection, 'host': job.printer.host, 'port': job.printer.port,
                        'os_name': job.printer.os_name, 'paper_width': job.printer.paper_width})
    return {
        'id': job.id, 'kind': job.kind, 'status': job.status, 'printer': printer, 'sale_id': job.sale_id,
        'sale_number': job.sale.number if job.sale else None, 'place': _place(job),
        'station_name': job.station.name if job.station else None, 'batch': job.batch, 'attempts': job.attempts,
        'error': job.error, 'created_at': job.created_at.isoformat(),
        'printed_at': job.printed_at.isoformat() if job.printed_at else None, 'reprint_of': job.reprint_of,
        'document': job.document,
    }


def _active_points():
    names = sorted({p.print_point for p in Printer.query.filter_by(is_active=True)})
    return [db.session.get(PrintPoint, name) or PrintPoint(name=name) for name in names]


def status():
    moment = now()
    problems = (PrintJob.query.filter(or_(PrintJob.status == 'failed',
                                          and_(PrintJob.status.in_(('pending', 'printing')),
                                               PrintJob.created_at < moment - PROBLEM_AGE)))
                .order_by(PrintJob.id).limit(50).all())
    points = [{'name': p.name, 'last_seen_at': p.last_seen_at.isoformat() if p.last_seen_at else None,
               'down': p.last_seen_at is None or p.last_seen_at < moment - POINT_DOWN} for p in _active_points()]
    pending = PrintJob.query.filter(PrintJob.status.in_(('pending', 'printing'))).count()
    return {'problems': [job_to_dict(j) for j in problems], 'points': points, 'pending': pending}


def sale_jobs(sale_id):
    return PrintJob.query.filter_by(sale_id=parse_id(sale_id, 'La venta')).order_by(PrintJob.id).all()


def print_points():
    printers = Printer.query.filter_by(is_active=True).order_by(Printer.print_point, Printer.name).all()
    grouped = OrderedDict()
    for printer in printers:
        grouped.setdefault(printer.print_point, []).append(printer.to_dict())
    return [{'name': name, 'printers': items} for name, items in grouped.items()]


def _env_pem(name):
    value = os.getenv(name)
    if not value:
        raise not_found('La firma de QZ Tray no está configurada')
    return value.replace('\\n', '\n')


def qz_certificate():
    return _env_pem('QZ_CERTIFICATE')


def sign_qz(message):
    """Firma el pedido de QZ Tray con RSA y SHA-512 (lo que espera qz.security con setSignatureAlgorithm('SHA512'))."""
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    key_pem = _env_pem('QZ_PRIVATE_KEY')
    if not isinstance(message, str) or not message:
        raise bad_request('Falta el texto a firmar')
    key = serialization.load_pem_private_key(key_pem.encode(), password=None)
    return base64.b64encode(key.sign(message.encode(), padding.PKCS1v15(), hashes.SHA512())).decode()
```

`test_print` empieza con `test_`; pytest no lo recoge porque vive en `app/`.

- [ ] **Step 5: Correr**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_pos_print_queue.py tests/test_pos_print_jobs.py`
Expected: todos pasan.

- [ ] **Step 6: Commit**

```bash
git add backend/requirements.txt backend/app/services/pos/print_service.py backend/tests/test_pos_print_queue.py
git commit -m "feat(pos): bill, receipt, reprint, print queue and QZ signing"
```

---

### Task 4: API de impresión y configuración

**Files:**
- Create: `backend/app/routes/pos_print.py`, `backend/tests/test_pos_print_api.py`, `backend/tests/test_pos_print_concurrency_pg.py`
- Modify: `backend/app/routes/pos_config.py`, `backend/app/__init__.py`

**Interfaces:**
- Consumes: todo `print_service` (Tasks 2 y 3).
- Produces (prefijo `/api/v1/pos`):
  - **Ventas** (`POS` o `Camarero`):
    - `POST /sales/<id>/print/bill` y `POST /sales/<id>/print/receipt` → `job_to_dict`;
    - `POST /print/jobs/<id>/reprint` → `job_to_dict`;
    - `GET /sales/<id>/print-jobs` → `{"jobs": [...]}`.
  - **Estaciones:** `GET /print/stations` (`POS`, `Camarero` o `Products`) → `{"stations": [...]}` con las activas.
  - **Cola** (`POS`):
    - `POST /print/claim {print_point}` → `{"jobs": [job_to_dict con with_printer]}`;
    - `POST /print/jobs/<id>/done`, `/failed {error}`, `/retry`, `/mark-printed` → `job_to_dict`;
    - `GET /print/status` → `status()`;
    - `GET /print/points` → `{"points": [...]}`;
    - `POST /print/printers/<id>/test` → `job_to_dict`;
    - `GET /print/qz-certificate` → `{"certificate": "..."}`;
    - `POST /print/qz-sign {request}` → `{"signature": "..."}`.
  - **Configuración** (admin, en `/api/v1/pos/config`):
    - `GET` y `POST /print-stations`, `PUT /print-stations/<id>` (listas con la clave `print_stations`);
    - `GET` y `POST /printers`, `PUT /printers/<id>` (lista con la clave `printers`).

- [ ] **Step 1: Tests que fallan.** Crear `backend/tests/test_pos_print_api.py`:

```python
from app.extensions import db
from app.models.pos import PrintPoint
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401
from print_helpers import make_printer, make_station

BASE = '/api/v1/pos'


def _billed_sale(client, headers, table, cat):
    sale = client.post(f'{BASE}/sales', json={'sale_type': 'salon', 'table_id': table.id, 'people': 1},
                       headers=headers).get_json()
    client.post(f"{BASE}/sales/{sale['id']}/items", json={'product_variant_id': cat.unidad.id}, headers=headers)
    client.post(f"{BASE}/sales/{sale['id']}/confirm", headers=headers)
    client.post(f"{BASE}/sales/{sale['id']}/request-bill", headers=headers)
    return sale


def test_waiter_prints_bill_but_cannot_touch_the_queue(pos_app):
    client = pos_app.test_client()
    cat = make_catalog()
    _salon, t1, _t2 = make_floor()
    make_printer('Térmica caja', cashier=True)
    waiter = auth_headers(client, make_user('mozo@test.com', modules=('Camarero',)))
    sale = _billed_sale(client, waiter, t1, cat)
    bill = client.post(f"{BASE}/sales/{sale['id']}/print/bill", headers=waiter)
    assert bill.status_code == 200 and bill.get_json()['kind'] == 'bill'
    jobs = client.get(f"{BASE}/sales/{sale['id']}/print-jobs", headers=waiter).get_json()['jobs']
    assert [j['kind'] for j in jobs] == ['bill']
    assert client.post(f"{BASE}/print/jobs/{jobs[0]['id']}/reprint", headers=waiter).status_code == 200
    assert client.post(f'{BASE}/print/claim', json={'print_point': 'Caja'}, headers=waiter).status_code == 403
    assert client.get(f'{BASE}/print/status', headers=waiter).status_code == 403


def test_queue_flow_through_the_api(pos_app):
    client = pos_app.test_client()
    cat = make_catalog()
    _salon, t1, _t2 = make_floor()
    printer = make_printer('Térmica caja', cashier=True)
    headers = auth_headers(client, make_user('caja@test.com', modules=('POS',)))
    sale = _billed_sale(client, headers, t1, cat)
    client.post(f"{BASE}/sales/{sale['id']}/print/bill", headers=headers)
    claimed = client.post(f'{BASE}/print/claim', json={'print_point': 'Caja'}, headers=headers).get_json()['jobs']
    assert claimed[0]['printer']['host'] == '192.168.0.50' and claimed[0]['status'] == 'printing'
    failed = client.post(f"{BASE}/print/jobs/{claimed[0]['id']}/failed", json={'error': 'Sin papel'}, headers=headers)
    assert failed.get_json()['status'] == 'failed'
    assert client.post(f"{BASE}/print/jobs/{claimed[0]['id']}/retry", headers=headers).get_json()['status'] == 'pending'
    marked = client.post(f"{BASE}/print/jobs/{claimed[0]['id']}/mark-printed", headers=headers).get_json()
    assert marked['status'] == 'printed'
    status = client.get(f'{BASE}/print/status', headers=headers).get_json()
    assert status['pending'] == 0 and status['points'][0]['name'] == 'Caja'
    points = client.get(f'{BASE}/print/points', headers=headers).get_json()['points']
    assert points[0]['printers'][0]['id'] == printer.id
    test_job = client.post(f'{BASE}/print/printers/{printer.id}/test', headers=headers).get_json()
    assert test_job['kind'] == 'test'
    assert client.post(f'{BASE}/print/claim', json={}, headers=headers).status_code == 400


def test_receipt_conflict_and_qz_not_configured(pos_app, monkeypatch):
    monkeypatch.delenv('QZ_CERTIFICATE', raising=False)
    monkeypatch.delenv('QZ_PRIVATE_KEY', raising=False)
    client = pos_app.test_client()
    cat = make_catalog()
    _salon, t1, _t2 = make_floor()
    headers = auth_headers(client, make_user('caja@test.com', modules=('POS',)))
    sale = _billed_sale(client, headers, t1, cat)
    response = client.post(f"{BASE}/sales/{sale['id']}/print/receipt", headers=headers)
    assert response.status_code == 409
    assert client.get(f'{BASE}/print/qz-certificate', headers=headers).status_code == 404
    assert client.post(f'{BASE}/print/qz-sign', json={'request': 'x'}, headers=headers).status_code == 404


def test_stations_lookup_for_products_users(pos_app):
    client = pos_app.test_client()
    make_station('Cocina')
    inactive = make_station('Vieja')
    inactive.is_active = False
    db.session.commit()
    headers = auth_headers(client, make_user('prod@test.com', modules=('Products',)))
    stations = client.get(f'{BASE}/print/stations', headers=headers).get_json()['stations']
    assert [s['name'] for s in stations] == ['Cocina']


def test_config_is_admin_only_and_validates_printers(pos_app):
    client = pos_app.test_client()
    cashier_headers = auth_headers(client, make_user('caja@test.com', modules=('POS',)))
    assert client.get(f'{BASE}/config/printers', headers=cashier_headers).status_code == 403
    admin = auth_headers(client, make_user('admin@test.com', role='admin'))
    station = client.post(f'{BASE}/config/print-stations', json={'name': 'Cocina'}, headers=admin)
    assert station.status_code == 201
    station_id = station.get_json()['id']
    ok = client.post(f'{BASE}/config/printers', json={
        'name': 'Térmica cocina', 'connection': 'network', 'host': '192.168.0.60', 'port': 9100, 'paper_width': 80,
        'print_point': 'Caja', 'station_id': station_id, 'is_cashier': False, 'is_active': True}, headers=admin)
    assert ok.status_code == 201 and ok.get_json()['station_name'] == 'Cocina'
    assert db.session.get(PrintPoint, 'Caja') is not None
    bad_cases = [
        {'name': 'A', 'connection': 'network', 'paper_width': 80, 'print_point': 'Caja'},
        {'name': 'B', 'connection': 'usb', 'paper_width': 80, 'print_point': 'Caja'},
        {'name': 'C', 'connection': 'network', 'host': 'h', 'paper_width': 70, 'print_point': 'Caja'},
        {'name': 'D', 'connection': 'network', 'host': 'h', 'paper_width': 80, 'print_point': ''},
        {'name': 'E', 'connection': 'network', 'host': 'h', 'paper_width': 80, 'print_point': 'Caja',
         'station_id': station_id},
        {'name': 'F', 'connection': 'network', 'host': 'h', 'paper_width': 80, 'print_point': 'Caja',
         'station_id': station_id, 'is_cashier': True},
    ]
    for body in bad_cases:
        assert client.post(f'{BASE}/config/printers', json=body, headers=admin).status_code == 400, body
    cashier = client.post(f'{BASE}/config/printers', json={
        'name': 'Térmica caja', 'connection': 'usb', 'os_name': 'EPSON', 'paper_width': 58, 'print_point': 'Caja',
        'is_cashier': True}, headers=admin)
    assert cashier.status_code == 201
    second = client.post(f'{BASE}/config/printers', json={
        'name': 'Otra caja', 'connection': 'usb', 'os_name': 'X', 'paper_width': 58, 'print_point': 'Caja',
        'is_cashier': True}, headers=admin)
    assert second.status_code == 400
    printer_id = ok.get_json()['id']
    updated = client.put(f'{BASE}/config/printers/{printer_id}', json={'print_point': 'Oficina'}, headers=admin)
    assert updated.status_code == 200 and updated.get_json()['print_point'] == 'Oficina'
    assert db.session.get(PrintPoint, 'Oficina') is not None
    listed = client.get(f'{BASE}/config/printers', headers=admin).get_json()['printers']
    assert len(listed) == 2
    stations = client.get(f'{BASE}/config/print-stations', headers=admin).get_json()['print_stations']
    assert [s['name'] for s in stations] == ['Cocina']
```

Crear `backend/tests/test_pos_print_concurrency_pg.py`:

```python
import os
import threading

import pytest

from app import create_app
from app.config import Config, config
from app.extensions import db
from app.models import User
from app.services.pos import print_service
from pos_helpers import make_user
from print_helpers import make_printer

PG_URL = os.getenv('POS_PG_TEST_URL')
pytestmark = pytest.mark.skipif(not PG_URL, reason='POS_PG_TEST_URL no configurada')
if PG_URL and 'test' not in PG_URL.rsplit('/', 1)[-1]:
    pytestmark = pytest.mark.skip(
        reason='POS_PG_TEST_URL tiene que apuntar a una base de test (el nombre debe contener "test")')


class PgTestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = PG_URL


@pytest.fixture
def pg_app():
    config['pos_pg_test'] = PgTestConfig
    app = create_app('pos_pg_test')
    with app.app_context():
        db.drop_all()
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_two_print_tabs_never_get_the_same_job(pg_app):
    with pg_app.app_context():
        user = make_user('caja@test.com', modules=('POS',))
        printer = make_printer('Térmica caja', cashier=True)
        for _ in range(15):
            print_service.test_print(user, printer.id)

    barrier = threading.Barrier(2)
    results = [None, None]

    def run(index):
        with pg_app.app_context():
            barrier.wait()
            results[index] = [job.id for job in print_service.claim('Caja')]
            db.session.remove()

    threads = [threading.Thread(target=run, args=(i,)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    first, second = results
    assert not set(first) & set(second)
    assert len(first) + len(second) == 15 or len(first) == 10 or len(second) == 10
```

- [ ] **Step 2: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_pos_print_api.py`
Expected: 404 en las rutas nuevas.

- [ ] **Step 3: Rutas de impresión.** Crear `backend/app/routes/pos_print.py`:

```python
"""API de impresión del POS: precuenta, ticket, reimpresión, cola del punto de impresión y firma de QZ Tray."""
import logging

from flask import Blueprint, jsonify
from sqlalchemy.exc import DataError, IntegrityError

from app.extensions import db
from app.models.pos import PrintStation
from app.services.pos import print_service
from app.services.pos.errors import PosError, bad_request
from app.utils.decorators import module_required
from app.utils.jwt_utils import token_required
from app.utils.validation import json_object

logger = logging.getLogger(__name__)
bp = Blueprint('pos_print', __name__, url_prefix='/api/v1/pos')


def _body():
    data = json_object()
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise bad_request('El cuerpo tiene que ser un objeto JSON')
    return data


def _run(action):
    try:
        payload = action()
    except PosError as exc:
        db.session.rollback()
        return jsonify({'error': exc.message, **exc.extra}), exc.status
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Otra operación modificó la impresión al mismo tiempo, probá de nuevo'}), 409
    except DataError:
        db.session.rollback()
        return jsonify({'error': 'Algún valor es demasiado grande'}), 400
    except Exception:
        db.session.rollback()
        logger.exception('Error inesperado en la impresión')
        return jsonify({'error': 'Error interno, probá de nuevo'}), 500
    return jsonify(payload), 200


def _job(job):
    return print_service.job_to_dict(job)


@bp.route('/sales/<int:sale_id>/print/bill', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def print_bill(current_user, sale_id):
    return _run(lambda: _job(print_service.print_bill(current_user, sale_id)))


@bp.route('/sales/<int:sale_id>/print/receipt', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def print_receipt(current_user, sale_id):
    return _run(lambda: _job(print_service.print_receipt(current_user, sale_id)))


@bp.route('/print/jobs/<int:job_id>/reprint', methods=['POST'])
@token_required
@module_required('POS', 'Camarero')
def reprint(current_user, job_id):
    return _run(lambda: _job(print_service.reprint(current_user, job_id)))


@bp.route('/sales/<int:sale_id>/print-jobs', methods=['GET'])
@token_required
@module_required('POS', 'Camarero')
def sale_jobs(current_user, sale_id):
    return _run(lambda: {'jobs': [_job(j) for j in print_service.sale_jobs(sale_id)]})


@bp.route('/print/stations', methods=['GET'])
@token_required
@module_required('POS', 'Camarero', 'Products')
def stations(current_user):
    rows = PrintStation.query.filter_by(is_active=True).order_by(PrintStation.position, PrintStation.id).all()
    return jsonify({'stations': [s.to_dict() for s in rows]}), 200


@bp.route('/print/claim', methods=['POST'])
@token_required
@module_required('POS')
def claim(current_user):
    def action():
        jobs = print_service.claim(_body().get('print_point'))
        return {'jobs': [print_service.job_to_dict(j, with_printer=True) for j in jobs]}
    return _run(action)


@bp.route('/print/jobs/<int:job_id>/done', methods=['POST'])
@token_required
@module_required('POS')
def job_done(current_user, job_id):
    return _run(lambda: _job(print_service.mark_done(job_id)))


@bp.route('/print/jobs/<int:job_id>/failed', methods=['POST'])
@token_required
@module_required('POS')
def job_failed(current_user, job_id):
    return _run(lambda: _job(print_service.mark_failed(job_id, _body().get('error'))))


@bp.route('/print/jobs/<int:job_id>/retry', methods=['POST'])
@token_required
@module_required('POS')
def job_retry(current_user, job_id):
    return _run(lambda: _job(print_service.retry(job_id)))


@bp.route('/print/jobs/<int:job_id>/mark-printed', methods=['POST'])
@token_required
@module_required('POS')
def job_mark_printed(current_user, job_id):
    return _run(lambda: _job(print_service.mark_printed(job_id)))


@bp.route('/print/status', methods=['GET'])
@token_required
@module_required('POS')
def print_status(current_user):
    return _run(print_service.status)


@bp.route('/print/points', methods=['GET'])
@token_required
@module_required('POS')
def print_points(current_user):
    return _run(lambda: {'points': print_service.print_points()})


@bp.route('/print/printers/<int:printer_id>/test', methods=['POST'])
@token_required
@module_required('POS')
def test_print(current_user, printer_id):
    return _run(lambda: _job(print_service.test_print(current_user, printer_id)))


@bp.route('/print/qz-certificate', methods=['GET'])
@token_required
@module_required('POS')
def qz_certificate(current_user):
    return _run(lambda: {'certificate': print_service.qz_certificate()})


@bp.route('/print/qz-sign', methods=['POST'])
@token_required
@module_required('POS')
def qz_sign(current_user):
    return _run(lambda: {'signature': print_service.sign_qz(_body().get('request'))})
```

En `backend/app/__init__.py`, agregar `pos_print` a la lista del `from app.routes import …` y, después de `app.register_blueprint(pos_cash.bp)`:

```python
    app.register_blueprint(pos_print.bp)
```

- [ ] **Step 4: Configuración.** En `backend/app/routes/pos_config.py`:
  - agregar `PAPER_WIDTHS, PRINTER_CONNECTIONS, PrintPoint, PrintStation, Printer` al import de `app.models.pos`;
  - agregar al final:

```python
# Estaciones e impresoras

@bp.route('/print-stations', methods=['GET'])
@token_required
@admin_required
def list_print_stations(current_user):
    rows = PrintStation.query.order_by(PrintStation.position, PrintStation.id).all()
    return jsonify({'print_stations': [s.to_dict() for s in rows]}), 200


def _apply_station(station, data):
    if 'name' in data or station.id is None:
        station.name = _name(data, 60)
    if 'position' in data:
        station.position = _int(data['position'], 'El orden')
    if 'is_active' in data:
        station.is_active = bool(data['is_active'])


@bp.route('/print-stations', methods=['POST'])
@token_required
@admin_required
def create_print_station(current_user):
    def action():
        station = PrintStation(position=0, is_active=True)
        _apply_station(station, _body())
        db.session.add(station)
        db.session.flush()
        return station.to_dict()
    return _run(action, 201)


@bp.route('/print-stations/<int:station_id>', methods=['PUT'])
@token_required
@admin_required
def update_print_station(current_user, station_id):
    def action():
        station = db.session.get(PrintStation, station_id)
        if station is None:
            raise not_found('La estación no existe')
        _apply_station(station, _body())
        return station.to_dict()
    return _run(action)


@bp.route('/printers', methods=['GET'])
@token_required
@admin_required
def list_printers(current_user):
    rows = Printer.query.order_by(Printer.print_point, Printer.name).all()
    return jsonify({'printers': [p.to_dict() for p in rows]}), 200


def _apply_printer(printer, data):
    creating = printer.id is None
    if 'name' in data or creating:
        printer.name = _name(data, 60)
    if 'connection' in data or creating:
        if data.get('connection') not in PRINTER_CONNECTIONS:
            raise bad_request('La conexión tiene que ser de red o USB')
        printer.connection = data['connection']
    if 'host' in data:
        printer.host = clean_str(data['host'], 100)
    if 'port' in data:
        printer.port = _int(data['port'], 'El puerto', minimum=1)
        if printer.port > 65535:
            raise bad_request('El puerto es inválido')
    if 'os_name' in data:
        printer.os_name = clean_str(data['os_name'], 120)
    if 'paper_width' in data or creating:
        if data.get('paper_width') not in PAPER_WIDTHS:
            raise bad_request('El ancho de papel tiene que ser 58 u 80 mm')
        printer.paper_width = data['paper_width']
    if 'print_point' in data or creating:
        printer.print_point = clean_str(data.get('print_point'), 60)
        if not printer.print_point:
            raise bad_request('Indicá el punto de impresión')
    if 'station_id' in data:
        value = data['station_id']
        if value in (None, ''):
            printer.station_id = None
        else:
            station = db.session.get(PrintStation, _int(value, 'La estación', minimum=1))
            if station is None or not station.is_active:
                raise bad_request('La estación no existe')
            printer.station_id = station.id
    for flag in ('is_cashier', 'is_active'):
        if flag in data:
            setattr(printer, flag, bool(data[flag]))
    if printer.connection == 'network' and not printer.host:
        raise bad_request('Una impresora de red necesita IP')
    if printer.connection == 'usb' and not printer.os_name:
        raise bad_request('Una impresora USB necesita el nombre que tiene en Windows')
    if printer.station_id and printer.is_cashier:
        raise bad_request('Una impresora de estación no puede ser la de caja')
    others = Printer.query.filter(Printer.is_active.is_(True), Printer.id != printer.id) if printer.id else \
        Printer.query.filter(Printer.is_active.is_(True))
    if printer.is_active and printer.is_cashier and others.filter(Printer.is_cashier.is_(True)).first():
        raise bad_request('Ya hay una impresora de caja activa')
    if printer.is_active and printer.station_id and others.filter(Printer.station_id == printer.station_id).first():
        raise bad_request('Esa estación ya tiene una impresora activa')
    if db.session.get(PrintPoint, printer.print_point) is None:
        db.session.add(PrintPoint(name=printer.print_point))


@bp.route('/printers', methods=['POST'])
@token_required
@admin_required
def create_printer(current_user):
    def action():
        printer = Printer(port=9100, is_cashier=False, is_active=True)
        _apply_printer(printer, _body())
        db.session.add(printer)
        db.session.flush()
        return printer.to_dict()
    return _run(action, 201)


@bp.route('/printers/<int:printer_id>', methods=['PUT'])
@token_required
@admin_required
def update_printer(current_user, printer_id):
    def action():
        printer = db.session.get(Printer, printer_id)
        if printer is None:
            raise not_found('La impresora no existe')
        with db.session.no_autoflush:
            _apply_printer(printer, _body())
        return printer.to_dict()
    return _run(action)
```

(`PrintStation(position=0, is_active=True)` deja `id` en `None` hasta el `flush`; `_apply_station` usa eso para exigir el nombre al crear.)

- [ ] **Step 5: Correr**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_pos_print_api.py tests/test_pos_print_concurrency_pg.py tests/test_pos_config_api.py tests/test_route_access_coverage.py`
Expected: pasan; el de PostgreSQL queda `skipped`.

- [ ] **Step 6: Suite completa contra la línea base** (cwd `backend/`):

```
PY -m pytest -q -p no:cacheprovider -rfE > <scratch>/pos_print_pytest.txt
PY scripts/compare_baseline.py <scratch>/pos_print_pytest.txt ../docs/superpowers/plans/2026-10-08-pos-base-test-baseline.txt
```

Expected: `Sin fallas nuevas.`

- [ ] **Step 7: Commit**

```bash
git add backend/app/routes/pos_print.py backend/app/routes/pos_config.py backend/app/__init__.py backend/tests/test_pos_print_api.py backend/tests/test_pos_print_concurrency_pg.py
git commit -m "feat(pos): printing API and stations/printers configuration"
```

---

### Task 5: Capa de datos del frontend y ESC/POS

**Files:**
- Create: `frontend/src/pos/print/escpos.js`, `frontend/src/pos/print/escpos.test.js`, `frontend/src/pos/print/printStatus.js`, `frontend/src/pos/print/printStatus.test.js`
- Modify: `frontend/src/pos/api/posApi.js`, `frontend/src/pos/hooks/keys.js`

**Interfaces:**
- Consumes: la API de la Task 4.
- Produces:
  - **`posPrintApi`:**
    - de la venta: `printBill(saleId)`, `printReceipt(saleId)`, `reprint(jobId)`, `saleJobs(saleId)`;
    - de la cola: `claim(point)`, `done(jobId)`, `failed(jobId, error)`, `retry(jobId)`, `markPrinted(jobId)`, `status()`, `points()`, `testPrint(printerId)`;
    - de QZ y configuración: `qzCertificate()`, `qzSign(request)`, `stations()`.
  - **`posConfigApi`:** el mapa `RESOURCE_KEYS` suma `'print-stations': 'print_stations'` y `printers: 'printers'`.
  - **`posKeys`:** `print: ['pos', 'print']`, `printStatus: ['pos', 'print', 'status']`, `printSaleJobs: (id) => ['pos', 'print', 'sale', id]`, `printPoints: ['pos', 'print', 'points']`, `printStations: ['pos', 'print', 'stations']`.
  - **`escpos.js`:** `columnsFor(width)`, `formatTicketMoney(amount)`, `renderText(doc, width) -> string[]`, `renderEscPos(doc, width) -> string`.
  - **`printStatus.js`:** `printHealth(status) -> 'unknown' | 'ok' | 'busy' | 'alert'`, `jobLabel(job) -> string`.

- [ ] **Step 1: Tests que fallan.** Crear `frontend/src/pos/print/escpos.test.js`:

```js
import { describe, expect, it } from 'vitest'
import { columnsFor, formatTicketMoney, renderEscPos, renderText } from './escpos'

const order = {
  title: 'COCINA',
  header: ['Mesa 1', 'Mozo: Ana', 'Tanda 1', '14/10/2026 13:05'],
  lines: [
    { qty: '2', text: 'Tostado', amount: null, details: ['Nota: sin sal'], strike: false },
    { qty: '1', text: 'Sándwich de jamón crudo, rúcula y parmesano en pan de campo', amount: null, details: [], strike: false },
  ],
  totals: [],
  footer: [],
}

const bill = {
  title: 'PRECUENTA',
  header: ['Mesa 1', 'Venta #3'],
  lines: [{ qty: '2', text: 'Medialuña', amount: '1800.00', details: [], strike: false }],
  totals: [{ label: 'Subtotal', amount: '1800.00' }, { label: 'Descuento', amount: '-180.00' }, { label: 'TOTAL', amount: '1620.00' }],
  footer: ['No válido como factura'],
}

describe('columnsFor', () => {
  it('usa 32 columnas en 58 mm y 48 en 80 mm', () => {
    expect(columnsFor(58)).toBe(32)
    expect(columnsFor(80)).toBe(48)
  })
})

describe('formatTicketMoney', () => {
  it('formatea en pesos argentinos', () => {
    expect(formatTicketMoney('1800.00')).toBe('$ 1.800')
    expect(formatTicketMoney('1234.50')).toBe('$ 1.234,50')
    expect(formatTicketMoney('-180.00')).toBe('-$ 180')
  })
})

describe('renderText', () => {
  it('nunca supera el ancho y corta renglones largos con sangría', () => {
    for (const width of [58, 80]) {
      const lines = renderText(order, width)
      expect(lines.every((l) => l.length <= columnsFor(width))).toBe(true)
    }
    const lines = renderText(order, 58)
    expect(lines).toContain('2 x Tostado')
    expect(lines).toContain('    Nota: sin sal')
    expect(lines.filter((l) => l.startsWith('1 x Sándwich')).length).toBe(1)
    expect(lines.some((l) => l.startsWith('    ') && l.includes('parmesano'))).toBe(true)
  })

  it('alinea los montos a la derecha y muestra los totales', () => {
    const lines = renderText(bill, 58)
    const item = lines.find((l) => l.startsWith('2 x Medialuña'))
    expect(item.endsWith('$ 1.800')).toBe(true)
    expect(item.length).toBe(32)
    expect(lines.find((l) => l.startsWith('TOTAL'))).toBe(`TOTAL${' '.repeat(32 - 5 - '$ 1.620'.length)}$ 1.620`)
    // Centrado: Math.floor((32 - 22) / 2) = 5 espacios a la izquierda.
    expect(lines).toContain(`${' '.repeat(5)}No válido como factura`)
  })

  it('marca los renglones anulados', () => {
    const voided = { ...order, lines: [{ ...order.lines[0], strike: true }] }
    expect(renderText(voided, 80)).toContain('XX 2 x Tostado')
  })
})

describe('renderEscPos', () => {
  it('inicializa, usa CP858, título doble, conserva acentos y corta el papel', () => {
    const data = renderEscPos(bill, 80)
    expect(data.startsWith('\x1b@\x1bt\x13')).toBe(true)
    expect(data).toContain('\x1d!\x11PRECUENTA')
    expect(data).toContain('Medialuña')
    expect(data.endsWith('\x1dV\x01')).toBe(true)
  })
})
```

Crear `frontend/src/pos/print/printStatus.test.js`:

```js
import { describe, expect, it } from 'vitest'
import { jobLabel, printHealth } from './printStatus'

describe('printHealth', () => {
  it('clasifica el estado de la cola', () => {
    expect(printHealth(undefined)).toBe('unknown')
    expect(printHealth({ problems: [], points: [{ name: 'Caja', down: false }], pending: 0 })).toBe('ok')
    expect(printHealth({ problems: [], points: [{ name: 'Caja', down: false }], pending: 2 })).toBe('busy')
    expect(printHealth({ problems: [{ id: 1 }], points: [], pending: 1 })).toBe('alert')
    expect(printHealth({ problems: [], points: [{ name: 'Caja', down: true }], pending: 0 })).toBe('alert')
  })
})

describe('jobLabel', () => {
  it('describe el trabajo', () => {
    expect(jobLabel({ kind: 'order', station_name: 'Cocina', place: 'Mesa 1' })).toBe('Comanda · Cocina · Mesa 1')
    expect(jobLabel({ kind: 'bill', station_name: null, place: 'Mostrador #3' })).toBe('Precuenta · Caja · Mostrador #3')
    expect(jobLabel({ kind: 'test', station_name: null, place: null })).toBe('Prueba · Caja')
  })
})
```

- [ ] **Step 2: Correr y ver que fallen**

Run (cwd `frontend/`): `npx vitest run src/pos/print`
Expected: FAIL (no existen los módulos).

- [ ] **Step 3: Implementar.** Crear `frontend/src/pos/print/escpos.js`:

```js
// Convierte un documento de impresión (JSON del backend) en texto de ancho fijo y en comandos ESC/POS.
// Funciones puras: las usan la página de impresión (QZ Tray), el modo simulación y los tests.
const ESC = '\x1b'
const GS = '\x1d'
const INDENT = '    '

export const columnsFor = (width) => (Number(width) === 58 ? 32 : 48)

export function formatTicketMoney(amount) {
  const value = Number(amount)
  const sign = value < 0 ? '-' : ''
  const [whole, cents] = Math.abs(value).toFixed(2).split('.')
  const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
  return `${sign}$ ${grouped}${cents === '00' ? '' : `,${cents}`}`
}

// Corta en palabras sin pasar `cols`; las palabras más largas que el renglón se parten.
function wrap(text, cols, indent = '') {
  const lines = []
  let current = ''
  for (const word of String(text).split(/\s+/).filter(Boolean)) {
    const pieces = []
    for (let rest = word; rest.length; rest = rest.slice(cols - indent.length)) pieces.push(rest.slice(0, cols - indent.length))
    for (const piece of pieces) {
      const candidate = current ? `${current} ${piece}` : piece
      const limit = lines.length ? cols - indent.length : cols
      if (candidate.length <= limit) current = candidate
      else {
        lines.push(current)
        current = piece
      }
    }
  }
  if (current || !lines.length) lines.push(current)
  return lines.map((line, i) => (i === 0 ? line : `${indent}${line}`))
}

function withAmount(left, amount, cols) {
  const right = formatTicketMoney(amount)
  const room = cols - right.length - 1
  const lines = wrap(left, room, INDENT)
  const last = lines.pop()
  return [...lines, `${last}${' '.repeat(cols - last.length - right.length)}${right}`]
}

const center = (text, cols) => {
  const pad = Math.max(0, Math.floor((cols - text.length) / 2))
  return `${' '.repeat(pad)}${text}`.trimEnd()
}

function bodyLines(doc, cols) {
  const out = []
  const rule = '-'.repeat(cols)
  for (const header of doc.header ?? []) out.push(...wrap(header, cols))
  out.push(rule)
  for (const line of doc.lines ?? []) {
    const left = `${line.strike ? 'XX ' : ''}${line.qty} x ${line.text}`
    out.push(...(line.amount != null ? withAmount(left, line.amount, cols) : wrap(left, cols, INDENT)))
    for (const detail of line.details ?? []) out.push(...wrap(`${INDENT}${detail}`, cols, INDENT))
  }
  if ((doc.totals ?? []).length) {
    out.push(rule)
    for (const total of doc.totals) out.push(...withAmount(total.label, total.amount, cols))
  }
  if ((doc.footer ?? []).length) {
    out.push('')
    for (const text of doc.footer) for (const piece of wrap(text, cols)) out.push(center(piece, cols))
  }
  return out
}

export function renderText(doc, width) {
  const cols = columnsFor(width)
  return [...wrap(doc.title ?? '', cols).map((t) => center(t, cols)), ...bodyLines(doc, cols)]
}

export function renderEscPos(doc, width) {
  const cols = columnsFor(width)
  let out = `${ESC}@${ESC}t\x13`
  out += `${ESC}a\x01${GS}!\x11${doc.title ?? ''}\n${GS}!\x00${ESC}a\x00`
  const body = bodyLines(doc, cols)
  const headerCount = body.indexOf('-'.repeat(cols))
  out += `${ESC}E\x01${body.slice(0, headerCount).join('\n')}\n${ESC}E\x00`
  out += `${body.slice(headerCount).join('\n')}\n\n\n\n${GS}V\x01`
  return out
}
```

Crear `frontend/src/pos/print/printStatus.js`:

```js
const KIND_LABELS = { order: 'Comanda', void: 'Anulación', bill: 'Precuenta', receipt: 'Ticket', test: 'Prueba' }

// Estado del indicador de impresión de la caja.
export function printHealth(status) {
  if (!status) return 'unknown'
  if ((status.problems ?? []).length || (status.points ?? []).some((p) => p.down)) return 'alert'
  return status.pending > 0 ? 'busy' : 'ok'
}

export function jobLabel(job) {
  return [KIND_LABELS[job.kind] ?? job.kind, job.station_name ?? 'Caja', job.place].filter(Boolean).join(' · ')
}
```

- [ ] **Step 4: Correr**

Run: `npx vitest run src/pos/print`
Expected: PASS.

- [ ] **Step 5: API y claves.** En `frontend/src/pos/api/posApi.js`:
  - en `RESOURCE_KEYS`, agregar `'print-stations': 'print_stations',` y `printers: 'printers',`;
  - agregar al final:

```js
export const posPrintApi = {
  printBill: (saleId) => data(api.post(`/pos/sales/${saleId}/print/bill`)),
  printReceipt: (saleId) => data(api.post(`/pos/sales/${saleId}/print/receipt`)),
  reprint: (jobId) => data(api.post(`/pos/print/jobs/${jobId}/reprint`)),
  saleJobs: (saleId) => data(api.get(`/pos/sales/${saleId}/print-jobs`)).then((d) => d.jobs),
  claim: (point) => data(api.post('/pos/print/claim', { print_point: point })).then((d) => d.jobs),
  done: (jobId) => data(api.post(`/pos/print/jobs/${jobId}/done`)),
  failed: (jobId, error) => data(api.post(`/pos/print/jobs/${jobId}/failed`, { error })),
  retry: (jobId) => data(api.post(`/pos/print/jobs/${jobId}/retry`)),
  markPrinted: (jobId) => data(api.post(`/pos/print/jobs/${jobId}/mark-printed`)),
  status: () => data(api.get('/pos/print/status')),
  points: () => data(api.get('/pos/print/points')).then((d) => d.points),
  testPrint: (printerId) => data(api.post(`/pos/print/printers/${printerId}/test`)),
  qzCertificate: () => data(api.get('/pos/print/qz-certificate')).then((d) => d.certificate),
  qzSign: (request) => data(api.post('/pos/print/qz-sign', { request })).then((d) => d.signature),
  stations: () => data(api.get('/pos/print/stations')).then((d) => d.stations),
}
```

En `frontend/src/pos/hooks/keys.js`, agregar dentro de `posKeys`:

```js
  print: ['pos', 'print'],
  printStatus: ['pos', 'print', 'status'],
  printSaleJobs: (id) => ['pos', 'print', 'sale', id],
  printPoints: ['pos', 'print', 'points'],
  printStations: ['pos', 'print', 'stations'],
```

- [ ] **Step 6: Verificar**

Run: `npm test` y `npm run build`.
Expected: todo pasa.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pos/print frontend/src/pos/api/posApi.js frontend/src/pos/hooks/keys.js
git commit -m "feat(pos): print API client and ESC/POS rendering"
```

---

### Task 6: Página de impresión con QZ Tray y modo simulación

**Files:**
- Create: `frontend/src/pos/print/qz.js`, `frontend/src/pos/print/PrintPage.jsx`
- Modify: `frontend/package.json`, `frontend/src/App.jsx`

**Interfaces:**
- Consumes: `posPrintApi`, `posKeys` y `renderEscPos`/`renderText` (Task 5); `useWakeLock` de `@/camarero/hooks/useWakeLock`; `btn`; `ToastProvider`; `PosRoute`; `ProtectedRoute`.
- Produces:
  - la ruta `/pos/impresion` (permiso `POS`), fuera de `PosLayout`;
  - `qz.js`: `connectQz() -> Promise<void>`, `qzReady() -> boolean`, `printRaw(printer, data) -> Promise<void>`.

- [ ] **Step 1: Dependencia**

Run (cwd `frontend/`): `npm install qz-tray@2.2.4`
Expected: se agrega a `dependencies`.

- [ ] **Step 2: Puente con QZ.** Crear `frontend/src/pos/print/qz.js`:

```js
import qz from 'qz-tray'
import { posPrintApi } from '../api/posApi'

let securityReady = false

// Firma los pedidos con el certificado del backend: sin certificado, QZ pide permiso en cada impresión.
function setupSecurity() {
  if (securityReady) return
  securityReady = true
  qz.security.setCertificatePromise((resolve) => {
    posPrintApi.qzCertificate().then(resolve).catch(() => resolve())
  })
  qz.security.setSignatureAlgorithm('SHA512')
  qz.security.setSignaturePromise((toSign) => (resolve) => {
    posPrintApi.qzSign(toSign).then(resolve).catch(() => resolve())
  })
}

export const qzReady = () => qz.websocket.isActive()

export async function connectQz() {
  setupSecurity()
  if (!qz.websocket.isActive()) await qz.websocket.connect({ retries: 1, delay: 1 })
}

// printer: { connection, host, port, os_name } tal como llega en el trabajo.
export async function printRaw(printer, data) {
  const target = printer.connection === 'network' ? { host: printer.host, port: printer.port } : printer.os_name
  const config = qz.configs.create(target, { encoding: 'CP858' })
  await qz.print(config, [{ type: 'raw', format: 'command', flavor: 'plain', data }])
}
```

- [ ] **Step 3: Página.** Crear `frontend/src/pos/print/PrintPage.jsx`:

```jsx
import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useWakeLock } from '@/camarero/hooks/useWakeLock'
import { posPrintApi } from '../api/posApi'
import { posKeys } from '../hooks/keys'
import { btn } from '../ui/buttons'
import { timeLabel } from '../utils/time'
import { renderEscPos, renderText } from './escpos'
import { connectQz, printRaw, qzReady } from './qz'
import { jobLabel } from './printStatus'

const POINT_KEY = 'pos.printPoint'
const SIMULATE_KEY = 'pos.printSimulate'
const TICK_MS = 2000

const read = (key) => { try { return localStorage.getItem(key) } catch { return null } }
const write = (key, value) => { try { localStorage.setItem(key, value) } catch { /* sin storage: solo esta sesión */ } }

function beep() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)()
    const osc = ctx.createOscillator()
    osc.connect(ctx.destination)
    osc.frequency.value = 880
    osc.start()
    osc.stop(ctx.currentTime + 0.25)
  } catch { /* sin audio */ }
}

// Punto de impresión: toma los trabajos de sus impresoras y los imprime con QZ Tray (o los simula).
export default function PrintPage() {
  useWakeLock()
  const [point, setPoint] = useState(() => read(POINT_KEY) ?? '')
  const [simulate, setSimulate] = useState(() => read(SIMULATE_KEY) === '1')
  const [qzState, setQzState] = useState('idle')
  const [log, setLog] = useState([])
  const [preview, setPreview] = useState(null)
  const busy = useRef(false)
  const { data: points = [] } = useQuery({ queryKey: posKeys.printPoints, queryFn: posPrintApi.points })
  const printers = points.find((p) => p.name === point)?.printers ?? []

  const addLog = useCallback((job, ok, error) => {
    setLog((current) => [{ at: new Date().toISOString(), label: jobLabel(job), printer: job.printer.name, ok, error },
      ...current].slice(0, 50))
  }, [])

  const connect = useCallback(async () => {
    setQzState('connecting')
    try {
      await connectQz()
      setQzState('ready')
    } catch {
      setQzState('error')
    }
  }, [])

  useEffect(() => {
    if (point && !simulate) connect()
  }, [point, simulate, connect])

  const handle = useCallback(async (job) => {
    const width = job.printer.paper_width
    try {
      if (simulate) setPreview({ label: jobLabel(job), text: renderText(job.document, width).join('\n') })
      else await printRaw(job.printer, renderEscPos(job.document, width))
      await posPrintApi.done(job.id)
      addLog(job, true)
    } catch (error) {
      const message = String(error?.message ?? error ?? 'Error de impresión').slice(0, 255)
      addLog(job, false, message)
      beep()
      try { await posPrintApi.failed(job.id, message) } catch { /* el backend lo recupera a los 60 s */ }
    }
  }, [simulate, addLog])

  useEffect(() => {
    if (!point) return undefined
    const tick = async () => {
      if (busy.current || (!simulate && !qzReady())) return
      busy.current = true
      try {
        const jobs = await posPrintApi.claim(point)
        for (const job of jobs) await handle(job)
      } catch {
        // Sin red o backend caído: se reintenta en el próximo ciclo.
      } finally {
        busy.current = false
      }
    }
    const id = setInterval(tick, TICK_MS)
    tick()
    return () => clearInterval(id)
  }, [point, simulate, handle])

  const choosePoint = (value) => { setPoint(value); write(POINT_KEY, value) }
  const toggleSimulate = (value) => { setSimulate(value); write(SIMULATE_KEY, value ? '1' : '0') }

  return (
    <div className="min-h-screen space-y-4 bg-galia-cream p-6">
      <header className="flex flex-wrap items-center gap-4">
        <h1 className="text-2xl font-semibold text-galia-plum">Impresión</h1>
        <label className="text-sm">Punto de impresión
          <select value={point} onChange={(e) => choosePoint(e.target.value)} className="ml-2 rounded border px-2 py-1">
            <option value="">Elegí uno</option>
            {points.map((p) => <option key={p.name} value={p.name}>{p.name}</option>)}
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={simulate} onChange={(e) => toggleSimulate(e.target.checked)} />
          Modo simulación (sin impresoras)
        </label>
        <Link to="/pos" className="ml-auto text-sm underline">Volver al POS</Link>
      </header>

      {!simulate && point && qzState !== 'ready' && (
        <div className="rounded-lg bg-amber-50 p-4 text-amber-900">
          {qzState === 'connecting' ? 'Conectando con QZ Tray…' : 'QZ Tray no está abierto.'}{' '}
          <button type="button" className="underline" onClick={connect}>Reintentar</button>{' · '}
          <a className="underline" href="https://qz.io/download/" target="_blank" rel="noreferrer">Descargar QZ Tray</a>
        </div>
      )}
      {!point && <p className="text-gray-600">Elegí el punto de impresión de esta PC para empezar.</p>}

      {point && (
        <section className="rounded-xl bg-white p-4 shadow-sm">
          <h2 className="font-semibold">Impresoras de {point}</h2>
          <ul className="mt-2 divide-y">
            {printers.map((printer) => (
              <li key={printer.id} className="flex items-center justify-between py-2 text-sm">
                <span>
                  {printer.name} · {printer.connection === 'network' ? `${printer.host}:${printer.port}` : printer.os_name}
                  {' · '}{printer.paper_width} mm · {printer.is_cashier ? 'Caja' : printer.station_name}
                </span>
                <button type="button" className={btn('secondary', 'min-h-[36px]')}
                  onClick={() => posPrintApi.testPrint(printer.id).catch(() => {})}>Imprimir prueba</button>
              </li>
            ))}
            {printers.length === 0 && <li className="py-2 text-sm text-gray-500">Este punto no tiene impresoras activas.</li>}
          </ul>
        </section>
      )}

      {simulate && preview && (
        <section className="rounded-xl bg-white p-4 shadow-sm">
          <h2 className="font-semibold">Última impresión simulada · {preview.label}</h2>
          <pre className="mt-2 overflow-x-auto rounded bg-gray-900 p-3 font-mono text-sm text-green-200">{preview.text}</pre>
        </section>
      )}

      <section className="rounded-xl bg-white p-4 shadow-sm">
        <h2 className="font-semibold">Registro</h2>
        <ul className="mt-2 space-y-1 text-sm">
          {log.map((entry, i) => (
            <li key={`${entry.at}-${i}`} className={entry.ok ? '' : 'text-red-700'}>
              {timeLabel(entry.at)} · {entry.printer} · {entry.label} · {entry.ok ? 'impreso' : `error: ${entry.error}`}
            </li>
          ))}
          {log.length === 0 && <li className="text-gray-500">Todavía no se imprimió nada.</li>}
        </ul>
      </section>
    </div>
  )
}
```

- [ ] **Step 4: Ruta.** En `frontend/src/App.jsx`:
  - agregar `import PrintPage from './pos/print/PrintPage'` e `import { ToastProvider } from './pos/ui/Toasts'` (si no está);
  - antes de `<Route path="/pos" …>`, agregar:

```jsx
          <Route path="/pos/impresion" element={<ProtectedRoute><PosRoute require="pos"><ToastProvider><PrintPage /></ToastProvider></PosRoute></ProtectedRoute>} />
```

- [ ] **Step 5: Verificar**

Run: `npm test` y `npm run build`.
Expected: todo pasa. El build incluye `qz-tray` sin errores.

- [ ] **Step 6: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/pos/print frontend/src/App.jsx
git commit -m "feat(pos): print page with QZ Tray and simulation mode"
```

---

### Task 7: Impresión desde la venta e indicador en la caja

**Files:**
- Create: `frontend/src/pos/print/PrintStatusBadge.jsx`, `frontend/src/pos/print/PrintJobsList.jsx`
- Modify:
  - `frontend/src/pos/utils/permissions.js` (+ `permissions.test.js`);
  - `frontend/src/pos/ui/Toasts.jsx`;
  - `frontend/src/pos/sale/SaleFooter.jsx`, `frontend/src/pos/sale/SalePanel.jsx`;
  - `frontend/src/pos/modals/PaymentModal.jsx`;
  - `frontend/src/pos/layout/PosTopBar.jsx`.

**Interfaces:**
- Consumes: `posPrintApi`, `posKeys`, `printHealth`, `jobLabel` (Task 5); `useToast`, `btn`, `timeLabel`, `usePosPermissions`.
- Produces:
  - `saleActions` suma `printBill` (venta `open`/`billing` con algún confirmado) y `printReceipt` (venta `closed`);
  - `toast.info(message, action?)`;
  - `PrintJobsList({ saleId })`;
  - `PrintStatusBadge()`.

- [ ] **Step 1: Test que falla.** En `frontend/src/pos/utils/permissions.test.js`, agregar dentro de `describe('saleActions', …)`:

```js
  it('ofrece imprimir precuenta con ítems confirmados y ticket con la venta cerrada', () => {
    const open = saleActions(sale({ status: 'open', items: [{ id: 1, status: 'confirmed' }] }), cashier)
    expect(open).toMatchObject({ printBill: true, printReceipt: false })
    expect(saleActions(sale({ status: 'open', items: [{ id: 1, status: 'pending' }] }), cashier).printBill).toBe(false)
    expect(saleActions(sale({ status: 'closed', items: [{ id: 1, status: 'confirmed' }] }), cashier))
      .toMatchObject({ printBill: false, printReceipt: true })
  })
```

(`sale` y `cashier` son los helpers que ya define ese archivo; si se llaman distinto, usar los existentes.)

Run: `npx vitest run src/pos/utils/permissions.test.js`
Expected: FAIL (`printBill` indefinido).

- [ ] **Step 2: Implementar las acciones.** En `frontend/src/pos/utils/permissions.js`, dentro del objeto que devuelve `saleActions`, agregar:

```js
    printBill: active && confirmed > 0,
    printReceipt: sale.status === 'closed',
```

Run: `npx vitest run src/pos/utils/permissions.test.js`
Expected: PASS.

- [ ] **Step 3: Aviso con acción.** En `frontend/src/pos/ui/Toasts.jsx`, cambiar `info: (message) => show('info', message),` por:

```js
    info: (message, action) => show('info', message, action),
```

- [ ] **Step 4: Lista de impresiones.** Crear `frontend/src/pos/print/PrintJobsList.jsx`:

```jsx
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { posPrintApi } from '../api/posApi'
import { posKeys } from '../hooks/keys'
import { useToast } from '../ui/Toasts'
import { errorMessage } from '../utils/errors'
import { timeLabel } from '../utils/time'
import { jobLabel } from './printStatus'

const STATUS = { pending: 'En cola', printing: 'Imprimiendo', printed: 'Impresa', failed: 'Con error' }

export default function PrintJobsList({ saleId }) {
  const queryClient = useQueryClient()
  const toast = useToast()
  const { data: jobs = [], isLoading, isError } = useQuery({
    queryKey: posKeys.printSaleJobs(saleId), queryFn: () => posPrintApi.saleJobs(saleId), refetchInterval: 5_000,
  })
  const reprint = useMutation({
    mutationFn: posPrintApi.reprint,
    onSuccess: () => {
      toast.success('Enviado a imprimir')
      queryClient.invalidateQueries({ queryKey: posKeys.printSaleJobs(saleId) })
    },
    onError: (error) => toast.error(errorMessage(error)),
  })
  if (isLoading) return <p className="p-4 text-sm text-gray-500">Cargando impresiones…</p>
  if (isError) return <p className="p-4 text-sm text-red-700">No se pudieron cargar las impresiones.</p>
  if (jobs.length === 0) return <p className="p-4 text-sm text-gray-500">Todavía no se imprimió nada de esta venta.</p>
  return (
    <ul className="divide-y px-4 py-2">
      {jobs.map((job) => (
        <li key={job.id} className="flex items-center justify-between gap-2 py-2 text-sm">
          <span>
            <span className="font-mono text-gray-500">{timeLabel(job.created_at)}</span> {jobLabel(job)}
            {job.batch ? ` · tanda ${job.batch}` : ''}{job.reprint_of ? ' · reimpresión' : ''}
            <span className={`ml-2 ${job.status === 'failed' ? 'text-red-700' : 'text-gray-500'}`}>{STATUS[job.status]}</span>
          </span>
          <button type="button" className="text-galia-plum underline" disabled={reprint.isPending}
            onClick={() => reprint.mutate(job.id)}>Reimprimir</button>
        </li>
      ))}
    </ul>
  )
}
```

- [ ] **Step 5: Panel de venta.** En `frontend/src/pos/sale/SalePanel.jsx`:
  - agregar `import { posPrintApi } from '../api/posApi'` e `import PrintJobsList from '../print/PrintJobsList'`;
  - en `handlers`, agregar:

```js
    printBill: () => run(sale.id, () => posPrintApi.printBill(sale.id).then(() => sale))
      .then((ok) => { if (ok) toast.success('Precuenta enviada a imprimir') }),
    printReceipt: () => run(sale.id, () => posPrintApi.printReceipt(sale.id).then(() => sale))
      .then((ok) => { if (ok) toast.success('Ticket enviado a imprimir') }),
```

(`run` escribe en la caché la venta devuelta, por eso las funciones devuelven `sale`.)

  - en el handler `requestBill`, reemplazar `if (await confirmPendingFirst()) await run(sale.id, () => posApi.requestBill(sale.id))` por:

```js
      if (!(await confirmPendingFirst())) return
      const billed = await run(sale.id, () => posApi.requestBill(sale.id))
      if (billed) toast.info('Cuenta pedida', { label: 'Imprimir precuenta', onClick: handlers.printBill })
```

  - pestañas: hacer visible la barra siempre, con "Ticket", "Historial" (solo si `actions.history`) e "Impresiones" (siempre). Reemplazar el bloque `{actions.history && ( <div className="flex border-b"> … </div> )}` por:

```jsx
      <div className="flex border-b">
        <button type="button" className={tabClass(tab === 'ticket')} onClick={() => setTab('ticket')}>Ticket</button>
        {actions.history && (
          <button type="button" className={tabClass(tab === 'history')} onClick={() => setTab('history')}>Historial</button>
        )}
        <button type="button" className={tabClass(tab === 'prints')} onClick={() => setTab('prints')}>Impresiones</button>
      </div>
```

  - y en el contenido, reemplazar la expresión `tab === 'history' && actions.history ? <SaleHistory … /> : <Ticket … />` por:

```jsx
        {tab === 'history' && actions.history && <SaleHistory saleId={sale.id} />}
        {tab === 'prints' && <PrintJobsList saleId={sale.id} />}
        {(tab === 'ticket' || (tab === 'history' && !actions.history)) && (
          <Ticket sale={sale} perms={perms} handlers={itemHandlers} busy={busy} />
        )}
```

En `frontend/src/pos/sale/SaleFooter.jsx`:
- en el array `more`, después de `actions.discount && [...]`, agregar `actions.printBill && ['Precuenta', handlers.printBill],`;
- en el bloque de venta no activa (el `return` con "Cerrada · cobrado …"), agregar, si `actions.printReceipt`, un botón "Imprimir ticket" junto al texto:

```jsx
      <div className="flex items-center justify-between gap-2 border-t bg-gray-50 px-4 py-3 text-sm text-gray-700">
        <span>{sale.status === 'closed' ? `Cerrada · cobrado ${formatMoney(sale.paid_total)}` : `Anulada: ${sale.cancel_reason ?? ''}`}</span>
        {actions.printReceipt && (
          <button type="button" className={btn('secondary', 'min-h-[40px]')} onClick={handlers.printReceipt}>Imprimir ticket</button>
        )}
      </div>
```

(reemplaza el `<div>` de ese `return`.)

- [ ] **Step 6: Ticket al cobrar.** En `frontend/src/pos/modals/PaymentModal.jsx`:
  - agregar `import { posPrintApi } from '../api/posApi'` y `import { useToast } from '../ui/Toasts'` (si no está);
  - en el componente, `const toast = useToast()` (si no existe);
  - en el `footer` del modal "Venta cerrada", reemplazar el botón único por:

```jsx
        footer={(
          <div className="grid grid-cols-2 gap-2">
            <button type="button" className={btn('secondary')} onClick={() => posPrintApi.printReceipt(sale.id)
              .then(() => toast.success('Ticket enviado a imprimir'))
              .catch((error) => toast.error(errorMessage(error)))}>Imprimir ticket</button>
            <button type="button" className={btn('primary')} onClick={onSaleClosed}>Listo</button>
          </div>
        )}
```

  - importar `errorMessage` de `../utils/errors` si no está.

- [ ] **Step 7: Indicador.** Crear `frontend/src/pos/print/PrintStatusBadge.jsx`:

```jsx
import { useState } from 'react'
import { Printer } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { posPrintApi } from '../api/posApi'
import { posKeys } from '../hooks/keys'
import { useToast } from '../ui/Toasts'
import { errorMessage } from '../utils/errors'
import { elapsedLabel } from '../utils/time'
import { jobLabel, printHealth } from './printStatus'

const TONES = { alert: 'bg-red-600 text-white', busy: 'bg-amber-200 text-amber-900', ok: 'bg-white/15 text-galia-cream', unknown: 'bg-white/15 text-galia-cream' }

export default function PrintStatusBadge() {
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()
  const toast = useToast()
  const { data: status } = useQuery({ queryKey: posKeys.printStatus, queryFn: posPrintApi.status, refetchInterval: 15_000 })
  const action = useMutation({
    mutationFn: ({ fn, id }) => fn(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: posKeys.print }),
    onError: (error) => toast.error(errorMessage(error)),
  })
  const health = printHealth(status)
  const problems = status?.problems ?? []

  return (
    <div className="relative">
      <button type="button" onClick={() => setOpen((v) => !v)} aria-expanded={open}
        className={`flex min-h-[40px] items-center gap-1 rounded-full px-3 text-xs font-medium ${TONES[health]}`}>
        <Printer size={14} /> Impresión{problems.length ? ` · ${problems.length}` : ''}
      </button>
      {open && (
        <div className="absolute right-0 z-30 mt-2 w-96 rounded-xl bg-white p-3 text-sm text-gray-800 shadow-xl">
          <p className="font-semibold">Puntos de impresión</p>
          <ul className="mb-2">
            {(status?.points ?? []).map((p) => (
              <li key={p.name} className={p.down ? 'text-red-700' : 'text-green-700'}>
                {p.name} · {p.down ? (p.last_seen_at ? `sin señal hace ${elapsedLabel(p.last_seen_at)}` : 'nunca se conectó') : 'conectado'}
              </li>
            ))}
            {(status?.points ?? []).length === 0 && <li className="text-gray-500">No hay impresoras configuradas.</li>}
          </ul>
          <p className="font-semibold">Con problemas</p>
          <ul className="divide-y">
            {problems.map((job) => (
              <li key={job.id} className="py-2">
                <p>{jobLabel(job)} · {elapsedLabel(job.created_at)}{job.error ? ` · ${job.error}` : ''}</p>
                <div className="mt-1 flex gap-3">
                  <button type="button" className="text-galia-plum underline" onClick={() => action.mutate({ fn: posPrintApi.retry, id: job.id })}>Reintentar</button>
                  <button type="button" className="text-galia-plum underline" onClick={() => action.mutate({ fn: posPrintApi.markPrinted, id: job.id })}>Marcar como impresa</button>
                </div>
              </li>
            ))}
            {problems.length === 0 && <li className="py-2 text-gray-500">Todo impreso.</li>}
          </ul>
        </div>
      )}
    </div>
  )
}
```

En `frontend/src/pos/layout/PosTopBar.jsx`:
- agregar `import PrintStatusBadge from '../print/PrintStatusBadge'`;
- junto a `<CashStatusBadge />`, agregar `{perms.pos && <PrintStatusBadge />}`.

- [ ] **Step 8: Verificar**

Run: `npm test` y `npm run build`.
Expected: todo pasa.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/pos
git commit -m "feat(pos): bill, receipt and reprint actions and print status badge"
```

---

### Task 8: Configuración en Galia y guía de instalación

**Files:**
- Modify: `frontend/src/components/pos-settings/CatalogEditor.jsx`, `frontend/src/pages/admin/PosSettings.jsx`, `frontend/src/pages/ProductCategories.jsx`
- Create: `docs/pos/impresion-qz.md`

**Interfaces:**
- Consumes: `posConfigApi` con `print-stations` y `printers` (Task 5); `posPrintApi.stations()` (Task 5).
- Produces:
  - solapas "Estaciones" e "Impresoras" en Ajustes del POS;
  - selector de estación en Categorías;
  - la guía de instalación.

- [ ] **Step 1: Select numérico en `CatalogEditor`.** En `frontend/src/components/pos-settings/CatalogEditor.jsx`:
  - cambiar el comentario de `fields` a `// fields: [{ key, label, type: 'text' | 'number' | 'select' | 'checkbox', options?: [[value, label]], numeric?: true }]`;
  - en `toValue`, antes de `return value`, agregar:

```js
  if (field.type === 'select' && field.numeric) return value === '' || value == null ? null : Number(value)
```

  - en `display`, reemplazar la rama `select` por:

```js
  if (field.type === 'select') return field.options.find(([v]) => String(v) === String(value ?? ''))?.[1] ?? value
```

  - en el `<select>` del formulario, usar `value={value ?? ''}`.

- [ ] **Step 2: Solapas.** En `frontend/src/pages/admin/PosSettings.jsx`:
  - agregar `import { useQuery } from '@tanstack/react-query'` e `import { posConfigApi } from '@/pos/api/posApi'`;
  - agregar al objeto `TABS`:

```js
  'print-stations': {
    label: 'Estaciones',
    emptyItem: { name: '', position: 0, is_active: true },
    fields: [
      { key: 'name', label: 'Nombre', type: 'text' },
      { key: 'position', label: 'Orden', type: 'number' },
      { key: 'is_active', label: 'Activa', type: 'checkbox' },
    ],
  },
  printers: {
    label: 'Impresoras',
    emptyItem: { name: '', connection: 'network', host: '', port: 9100, os_name: '', paper_width: 80, print_point: 'Caja', station_id: '', is_cashier: false, is_active: true },
    fields: [
      { key: 'name', label: 'Nombre', type: 'text' },
      { key: 'connection', label: 'Conexión', type: 'select', options: [['network', 'Red (IP)'], ['usb', 'USB (Windows)']] },
      { key: 'host', label: 'IP (red)', type: 'text' },
      { key: 'port', label: 'Puerto (red)', type: 'number' },
      { key: 'os_name', label: 'Nombre en Windows (USB)', type: 'text' },
      { key: 'paper_width', label: 'Papel', type: 'select', numeric: true, options: [[80, '80 mm'], [58, '58 mm']] },
      { key: 'print_point', label: 'Punto de impresión', type: 'text' },
      { key: 'station_id', label: 'Estación', type: 'select', numeric: true, options: [] },
      { key: 'is_cashier', label: 'Impresora de caja', type: 'checkbox' },
      { key: 'is_active', label: 'Activa', type: 'checkbox' },
    ],
  },
```

  - dentro de `PosSettings`, cargar las estaciones y completar las opciones antes de renderizar:

```js
  const { data: stations = [] } = useQuery({ queryKey: ['pos-settings', 'print-stations'], queryFn: () => posConfigApi.listResource('print-stations') })
  const current = tab === 'printers'
    ? { ...TABS.printers, fields: TABS.printers.fields.map((f) => (f.key === 'station_id'
      ? { ...f, options: [['', 'Sin estación'], ...stations.filter((s) => s.is_active).map((s) => [s.id, s.name])] }
      : f)) }
    : TABS[tab]
```

  (reemplaza la línea existente `const current = TABS[tab]`).

- [ ] **Step 3: Estación en Categorías.** En `frontend/src/pages/ProductCategories.jsx`:
  - agregar `import { posPrintApi } from '../pos/api/posApi'`;
  - agregar el estado `const [stations, setStations] = useState([])` y, en el `useEffect` inicial, `posPrintApi.stations().then(setStations).catch(() => setStations([]))`;
  - en `handleOpenModal`, sumar `station_id: category?.station_id ?? ''` a los dos `setFormData` (en el de alta, `station_id: ''`);
  - en `handleSubmit`, enviar `{ ...formData, station_id: formData.station_id === '' ? null : Number(formData.station_id) }` en lugar de `formData`, tanto al crear como al actualizar;
  - en el formulario, después del campo "Ícono", agregar:

```jsx
              <div>
                <label className="block text-sm font-medium mb-1">Estación (comandas)</label>
                <select
                  value={formData.station_id ?? ''}
                  onChange={(e) => setFormData({ ...formData, station_id: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                >
                  <option value="">Sin comanda</option>
                  {stations.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
```

  - en cada tarjeta, después de la línea del color, agregar:

```jsx
            <p className="mt-1 text-xs text-gray-600">
              Comanda: {stations.find((s) => s.id === category.station_id)?.name ?? 'sin comanda'}
            </p>
```

- [ ] **Step 4: Guía.** Crear `docs/pos/impresion-qz.md`:

````markdown
# Impresión de comandas y tickets con QZ Tray

La impresión la hace una PC del local con QZ Tray y la página **Impresión** de Galia abierta (`/pos/impresion`). El backend encola los trabajos y esa página los imprime en las térmicas de red (IP, puerto 9100) y USB (instaladas en Windows).

## 1. Instalar QZ Tray

Descargar e instalar QZ Tray desde https://qz.io/download/ en la PC de impresión (la de caja). Queda corriendo en la bandeja del sistema y arranca con Windows.

## 2. Certificado para imprimir sin confirmación

Sin certificado, QZ Tray pregunta "¿Permitir?" en cada impresión. Para evitarlo, generar un par de claves (una sola vez, en cualquier PC con OpenSSL, por ejemplo Git Bash):

```bash
openssl req -x509 -newkey rsa:2048 -keyout galia-qz-key.pem -out galia-qz-cert.pem -days 3650 -nodes -subj "/CN=Galia POS"
```

- En Render (servicio `galia-backend` → Environment), cargar:
  - `QZ_CERTIFICATE` con el contenido completo de `galia-qz-cert.pem`.
  - `QZ_PRIVATE_KEY` con el contenido completo de `galia-qz-key.pem`.
- En la PC de impresión, copiar `galia-qz-cert.pem` como `override.crt` en la carpeta de instalación de QZ Tray (por ejemplo `C:\Program Files\QZ Tray\override.crt`) y reiniciar QZ Tray.
- Guardar la clave privada en un lugar seguro y no compartirla.

## 3. Estaciones, impresoras y categorías

En Galia, como admin:

1. **Ajustes del POS → Estaciones:** crear "Cocina", "Barra" (o las que correspondan).
2. **Ajustes del POS → Impresoras:** dar de alta cada térmica:
   - **Red:** IP fija de la impresora y puerto 9100.
   - **USB:** el nombre exacto con el que figura en Windows (Configuración → Impresoras).
   - **Papel:** 58 u 80 mm.
   - **Punto de impresión:** "Caja" (el nombre que va a elegir la PC de impresión).
   - **Estación:** la que imprime esa impresora, o marcar "Impresora de caja" para precuentas y tickets.
3. **Productos → Categorías:** en cada categoría, elegir la estación. "Sin comanda" no imprime (por ejemplo, lo que se entrega directo en caja).

## 4. Dejar la página de impresión abierta

1. En la PC de impresión, entrar a Galia con un usuario con permiso POS y abrir `/pos/impresion`.
2. Elegir el punto de impresión ("Caja").
3. Fijar la pestaña en Chrome (clic derecho → Fijar) y configurarla como página de inicio, para que se abra sola al prender la PC.
4. Desactivar la suspensión de la PC durante el horario del local.

## 5. Probar

En la página de impresión, usar **Imprimir prueba** en cada impresora: tiene que salir un ticket con acentos y ñ legibles. Después, confirmar una tanda de prueba en el POS y verificar que cada estación reciba solo lo suyo.

## Si algo no imprime

- El indicador **Impresión** de la caja se pone rojo y muestra qué falló.
- "QZ Tray no está abierto": abrir QZ Tray y tocar **Reintentar** en la página de impresión.
- Impresora de red: verificar que la PC llegue a esa IP (por ejemplo, `ping 192.168.0.50`).
- Los trabajos quedan en cola: cuando se resuelve, se imprimen solos. Si ya se resolvió a mano, usar **Marcar como impresa**.
````

- [ ] **Step 5: Verificar**

Run: `npm test` y `npm run build`.
Expected: todo pasa.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/pos-settings/CatalogEditor.jsx frontend/src/pages/admin/PosSettings.jsx frontend/src/pages/ProductCategories.jsx docs/pos/impresion-qz.md
git commit -m "feat(pos): stations and printers settings, category station and QZ guide"
```

---

### Task 9: Verificación final

**Files:** ninguno (preview fuera del repo).

- [ ] **Step 1: Suites.** Backend completo contra la línea base (como en la Task 4, Step 6) y frontend con `npm test` y `npm run build`.
Expected: `Sin fallas nuevas.` y todo verde.

- [ ] **Step 2: Preview.** Base SQLite descartable con `create_all` y los datos del script de preview de caja (`prep_caja_preview.py` del scratchpad). Configurar desde la UI (como admin):
  - estaciones Cocina y Barra;
  - impresoras de red con IPs ficticias, punto "Caja";
  - la impresora de caja USB;
  - categorías asignadas a cada estación.

- [ ] **Step 3: Verificación manual** (spec, sección "Verificación manual"), con `/pos/impresion` en otra pestaña y en modo simulación:
  1. Confirmar una tanda mixta: aparece una comanda de cada estación, cada una con solo sus ítems.
  2. Anular un ítem: anulación en su estación.
  3. Precuenta (desde "Más" y desde el aviso de "Pedir cuenta") y ticket (después de cobrar) en caja.
  4. Reimprimir desde la pestaña "Impresiones", que lleva la marca "REIMPRESIÓN".
  5. Cerrar la página de impresión y confirmar una tanda: a los 30 s el indicador se pone rojo y el panel muestra la comanda pendiente y el punto sin señal. Reabrir la página: se imprime sola.
  6. "Marcar como impresa" y "Reintentar" desde el panel.
  7. El celular (`/camarero`) confirma una tanda y la comanda sale igual.
