# Gastos sincronizados con Fudo — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que los gastos importados desde Fudo lleguen vinculados a un `Supplier` y a una `ExpenseCategory` de Galia (matcheando o creando), con medio de pago y comprobante legibles, respetando correcciones manuales y con el resultado de cada corrida visible en el modal.

**Architecture:** La lógica sale de `routes/fudo_sync.py` y se reparte en tres módulos de servicio: parseo puro del JSON:API de Fudo (`expense_fudo_parsing.py`), resolución de vínculos proveedor/categoría (`expense_fudo_linking.py`) y orquestación con upsert por `external_id` (`expense_sync_service.py`). Cada corrida queda registrada en `fudo_sync_runs` (`fudo_sync_runs.py` arranca/cierra la corrida y corre el hilo); la ruta valida, crea la corrida, lanza el hilo y devuelve 202 con `run_id`; el modal consulta la corrida hasta que termina.

**Tech Stack:** Flask + Flask-SQLAlchemy 3 (SQLAlchemy 2.0.20), Alembic, pytest (SQLite en memoria), React + Vite, vitest (entorno node, solo `src/**/*.test.js`).

**Spec:** `docs/superpowers/specs/2026-10-15-expenses-fudo-sync-design.md`

## Global Constraints

- Migración nueva: `b5a0_expenses_fudo_link`, `down_revision = 'b4a0_add_fiscal_invoicing'` (la cadena tiene una sola cabeza; `test_migration_chain.py` lo verifica).
- `suppliers.fudo_provider_id` y `expense_categories.fudo_category_id`: `String(50)`, nullable, unique.
- `expenses.source`: `String(10)`, not null, default `'galia'`; valores `'fudo'` / `'galia'`; backfill `'fudo'` donde `external_id IS NOT NULL`.
- `expenses.category_overridden`, `expenses.supplier_overridden`: Boolean, not null, default false.
- Rango de sync: `start_date` y `end_date` obligatorias, `YYYY-MM-DD`, `start ≤ end`, rango ≤ 366 días → si no, 400.
- Corrida `running` de < 30 min → 409 con `run_id`; una más vieja se marca `error` ("corrida abandonada") y no bloquea.
- Commit cada 200 gastos; `warnings` y `errors` de las stats se cortan en 50 elementos.
- Stats: `fetched, created, updated, unchanged, suppliers_created, suppliers_linked, categories_created, categories_linked, warnings, errors`.
- Conflicto de nombre de categoría → `"<nombre> (Fudo <id>)"`. Conflicto de CUIT → supplier sin CUIT + warning.
- Textos de UI y mensajes de error en español rioplatense, como el resto de la app.
- Python de los tests: `backend/venv/Scripts/python.exe` (correr desde `backend/`). La suite completa tiene fallas preexistentes (employee_documents, sales_date_filter, schedule_management, social_security_documents, payroll_deletion, permissions): correr solo los archivos que se nombran en cada tarea.

## Review Focus

- **Importe en formato raro** (`"15000.5"`, `15000.499`, `null`, `""`): se guarda como Decimal con 2 decimales; `null`/vacío va a `errors`, nunca se importa como 0. → test en Tarea 3.
- **Fecha faltante o inválida en un gasto**: va a `errors` y el gasto no se crea (el código viejo ponía la fecha de hoy en silencio). → test en Tarea 3.
- **Mismo proveedor en muchos gastos de una corrida, o nombre con otro case / espacios dobles que un Supplier existente** (`"  molino   SUR "` vs `"Molino Sur"`): se crea o vincula **un solo** Supplier. → tests en Tarea 4.
- **Categoría de Galia desactivada con el mismo nombre que una de Fudo**: se vincula, no explota por el unique de `name`. → test en Tarea 4.
- **Gastos cargados a mano en Galia** (`external_id` null, `source='galia'`): la sync nunca los toca, y un gasto que falla no deja proveedores/categorías huérfanos a medio crear en la caché. → tests en Tarea 5.

---

## File Structure

| Archivo | Acción | Responsabilidad |
|---|---|---|
| `backend/scripts/inspect_fudo_expenses.py` | Crear | Imprime los nombres de atributos/relaciones reales de Fudo (sin valores) |
| `backend/tests/fudo_expense_fakes.py` | Crear | Builders de payloads JSON:API y cliente fake |
| `backend/migrations/versions/b5a0_expenses_fudo_link.py` | Crear | Columnas nuevas, backfill, tabla `fudo_sync_runs` |
| `backend/app/models/fudo_sync_run.py` | Crear | Modelo `FudoSyncRun` |
| `backend/app/models/expense.py` | Modificar | Columnas nuevas, `infer_expense_type`, `to_dict`, `source` en CSV |
| `backend/app/models/supplier.py` | Modificar | `fudo_provider_id` + `to_dict` |
| `backend/app/models/__init__.py` | Modificar | Exportar `FudoSyncRun` |
| `backend/app/utils/fudo_client.py` | Modificar | `get_all_expenses_with_included` |
| `backend/app/services/expense_fudo_parsing.py` | Crear | Payload de Fudo → `ParsedExpense` (puro) |
| `backend/app/services/expense_fudo_linking.py` | Crear | `Linker`: proveedor → Supplier, categoría → ExpenseCategory |
| `backend/app/services/expense_sync_service.py` | Crear | `sync_expenses(client, start, end) -> stats` |
| `backend/app/services/fudo_sync_runs.py` | Crear | `start_run`, `finish_run`, `run_expenses_sync`, `SyncInProgress` |
| `backend/app/routes/fudo_sync.py` | Modificar | Nuevo POST de gastos, GET de corridas; borrar parseo viejo |
| `backend/app/routes/expenses.py` | Modificar | Marcar banderas de corrección en PUT y classify |
| `backend/app/routes/reports.py` | Modificar | Re-vincular `fudo_category_id` en PUT de categoría |
| `frontend/src/services/fudoService.js` | Modificar | `syncExpenses(start, end)`, `getSyncRun`, `getSyncRuns` |
| `frontend/src/components/fudo/syncRunSummary.js` (+ `.test.js`) | Crear | Helpers puros del modal |
| `frontend/src/components/fudo/FudoSyncExpensesModal.jsx` | Reescribir | Rango → sincronizar → seguimiento → resumen |
| `frontend/src/pages/Expenses.jsx` | Modificar | Botón "Sync Fudo", montar modal, badge "Fudo" |
| `frontend/src/pages/ExpenseCategories.jsx` | Modificar | Selector de categoría de Fudo vinculada |

---

### Task 1: Confirmar la forma real de la API y armar los fakes

**Files:**
- Create: `backend/scripts/inspect_fudo_expenses.py`
- Create: `backend/tests/fudo_expense_fakes.py`

**Interfaces:**
- Produces (en `tests/fudo_expense_fakes.py`):
  - `fudo_expense(expense_id, amount='1000.00', date='2026-10-01', provider_id=None, category_id=None, payment_method_id=None, receipt_type_id=None, status='PAID', **attributes) -> dict`
  - `fudo_provider(provider_id, name, cuit=None) -> dict`
  - `fudo_expense_category(category_id, name) -> dict`
  - `fudo_payment_method(method_id, name) -> dict`
  - `fudo_receipt_type(type_id, name) -> dict`
  - `class FakeExpensesClient(data=None, included=None, error=None)` con `get_all_expenses_with_included(start_date=None, end_date=None) -> {'data': [...], 'included': [...]}` y atributo `calls: list[tuple]`.

Los nombres de atributos que usa este plan son un **supuesto** (Fudo expone JSON:API, docs no accesibles). Esta tarea los confirma.

- [ ] **Step 1: Escribir el script de inspección**

```python
#!/usr/bin/env python3
"""Muestra los NOMBRES de atributos y relaciones de /expenses (sin valores) para validar el parseo.

Uso: cd backend && venv/Scripts/python.exe scripts/inspect_fudo_expenses.py
"""
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from dotenv import load_dotenv

load_dotenv()

from app.utils.fudo_client import FudoClient


def main():
    client = FudoClient()
    response = client.get_expenses(page_size=50, page_number=1)
    expense_attrs, expense_rels = set(), set()
    statuses = set()
    for expense in response.get('data', []):
        expense_attrs.update(expense.get('attributes', {}).keys())
        expense_rels.update(expense.get('relationships', {}).keys())
        statuses.add(expense.get('attributes', {}).get('status'))
    included = defaultdict(set)
    for item in response.get('included', []):
        included[item.get('type')].update(item.get('attributes', {}).keys())

    print('Expense attributes:', sorted(expense_attrs))
    print('Expense relationships:', sorted(expense_rels))
    print('Expense status values:', sorted(str(s) for s in statuses))
    for kind, keys in sorted(included.items()):
        print(f'included[{kind}] attributes:', sorted(keys))


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Correrlo si hay credenciales**

Run: `cd backend && venv/Scripts/python.exe scripts/inspect_fudo_expenses.py`

- Si `FUDO_API_KEY`/`FUDO_API_SECRET` no están en `backend/.env`, pedírselas al usuario (que las cargue él en el `.env`; nunca pegarlas en el chat ni commitearlas). Si no las puede dar ahora, seguir con los nombres supuestos y anotarlo como pendiente en la descripción del PR.
- Comparar la salida con las constantes `ATTR`, `REL`, `PROVIDER_ATTR` y `STATUS_MAP` de la Tarea 3 y con los `type` de los builders de abajo (`Expense`, `Provider`, `ExpenseCategory`, `PaymentMethod`, `ReceiptType`). Si difieren, **corregir esos valores en este plan antes de seguir** (Tareas 1 y 3 son las únicas que los nombran).

- [ ] **Step 3: Escribir los fakes**

```python
"""Builders de payloads JSON:API de gastos de Fudo y cliente fake para los tests de sync."""


def _rel(kind, rel_id):
    return {'data': {'id': str(rel_id), 'type': kind}} if rel_id is not None else {'data': None}


def fudo_expense(expense_id, amount='1000.00', date='2026-10-01', provider_id=None, category_id=None,
                 payment_method_id=None, receipt_type_id=None, status='PAID', **attributes):
    attrs = {'amount': amount, 'date': date, 'status': status, 'description': None}
    attrs.update(attributes)
    return {
        'id': str(expense_id),
        'type': 'Expense',
        'attributes': attrs,
        'relationships': {
            'provider': _rel('Provider', provider_id),
            'expenseCategory': _rel('ExpenseCategory', category_id),
            'paymentMethod': _rel('PaymentMethod', payment_method_id),
            'receiptType': _rel('ReceiptType', receipt_type_id),
        },
    }


def fudo_provider(provider_id, name, cuit=None):
    return {'id': str(provider_id), 'type': 'Provider', 'attributes': {'name': name, 'fiscalNumber': cuit}}


def fudo_expense_category(category_id, name):
    return {'id': str(category_id), 'type': 'ExpenseCategory', 'attributes': {'name': name}}


def fudo_payment_method(method_id, name):
    return {'id': str(method_id), 'type': 'PaymentMethod', 'attributes': {'name': name}}


def fudo_receipt_type(type_id, name):
    return {'id': str(type_id), 'type': 'ReceiptType', 'attributes': {'name': name}}


class FakeExpensesClient:
    def __init__(self, data=None, included=None, error=None):
        self.data = data or []
        self.included = included or []
        self.error = error
        self.calls = []

    def get_all_expenses_with_included(self, start_date=None, end_date=None):
        self.calls.append((start_date, end_date))
        if self.error:
            raise self.error
        return {'data': self.data, 'included': self.included}
```

- [ ] **Step 4: Commit**

```bash
git add backend/scripts/inspect_fudo_expenses.py backend/tests/fudo_expense_fakes.py
git commit -m "test: fakes de gastos de Fudo y script de inspección de la API"
```

---

### Task 2: Migración y modelos

**Files:**
- Create: `backend/migrations/versions/b5a0_expenses_fudo_link.py`
- Create: `backend/app/models/fudo_sync_run.py`
- Modify: `backend/app/models/expense.py`
- Modify: `backend/app/models/supplier.py`
- Modify: `backend/app/models/__init__.py`
- Test: `backend/tests/test_expense_fudo_models.py`, `backend/tests/test_migration_chain.py`

**Interfaces:**
- Produces:
  - `Supplier.fudo_provider_id: str | None`; `Supplier.to_dict()['fudo_provider_id']`
  - `ExpenseCategory.fudo_category_id: str | None`; `to_dict()['fudo_category_id']`
  - `Expense.source: str` (`'galia'` por defecto), `Expense.category_overridden: bool`, `Expense.supplier_overridden: bool`; las tres en `to_dict()`
  - `app.models.expense.infer_expense_type(name: str) -> str` (`'directo'` | `'indirecto'`)
  - `app.models.fudo_sync_run.FudoSyncRun` (columnas: `id, kind, status, started_at, finished_at, params, stats, error, triggered_by`) con `to_dict()`

- [ ] **Step 1: Escribir los tests que fallan**

`backend/tests/test_expense_fudo_models.py`:

```python
from datetime import date, datetime
from decimal import Decimal

from app.extensions import db
from app.models.expense import Expense, ExpenseCategory, infer_expense_type
from app.models.fudo_sync_run import FudoSyncRun
from app.models.supplier import Supplier


def test_expense_defaults_and_to_dict(menu_app):
    category = ExpenseCategory(name='Insumos', fudo_category_id='3')
    supplier = Supplier(name='Molino Sur', fudo_provider_id='7')
    db.session.add_all([category, supplier])
    db.session.flush()
    expense = Expense(fecha=date(2026, 10, 1), importe=Decimal('10.00'),
                      category_id=category.id, supplier_id=supplier.id)
    db.session.add(expense)
    db.session.commit()

    data = expense.to_dict()
    assert data['source'] == 'galia'
    assert data['category_overridden'] is False
    assert data['supplier_overridden'] is False
    assert category.to_dict()['fudo_category_id'] == '3'
    assert supplier.to_dict()['fudo_provider_id'] == '7'


def test_infer_expense_type():
    assert infer_expense_type('Mercadería') == 'directo'
    assert infer_expense_type('Materia prima panadería') == 'directo'
    assert infer_expense_type('Alquiler') == 'indirecto'
    assert infer_expense_type('') == 'indirecto'


def test_csv_row_with_id_is_marked_fudo(menu_app):
    expense = Expense.from_csv_row({'Id': '55', 'Fecha': '01/10/2026', 'Importe': '100', 'Categoría': 'Alquiler'})
    assert expense.source == 'fudo'
    manual = Expense.from_csv_row({'Id': '', 'Fecha': '01/10/2026', 'Importe': '100', 'Categoría': 'Alquiler'})
    assert manual.source == 'galia'


def test_sync_run_to_dict(menu_app):
    run = FudoSyncRun(kind='expenses', status='running', started_at=datetime(2026, 10, 15, 12, 0),
                      params={'start_date': '2026-10-01', 'end_date': '2026-10-15'})
    db.session.add(run)
    db.session.commit()

    data = run.to_dict()
    assert data['kind'] == 'expenses'
    assert data['status'] == 'running'
    assert data['started_at'] == '2026-10-15T12:00:00'
    assert data['finished_at'] is None
    assert data['params'] == {'start_date': '2026-10-01', 'end_date': '2026-10-15'}
    assert data['stats'] is None
```

Agregar al final de `backend/tests/test_migration_chain.py`:

```python
def test_expenses_fudo_link_follows_fiscal_invoicing():
    assert _revisions()['b5a0_expenses_fudo_link'] == ['b4a0_add_fiscal_invoicing']
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `cd backend && venv/Scripts/python.exe -m pytest tests/test_expense_fudo_models.py tests/test_migration_chain.py -v`
Expected: FAIL (`ImportError: cannot import name 'infer_expense_type'` / `No module named 'app.models.fudo_sync_run'` / `KeyError: 'b5a0_expenses_fudo_link'`).

- [ ] **Step 3: Migración**

`backend/migrations/versions/b5a0_expenses_fudo_link.py`:

```python
"""link expenses, suppliers and expense categories to Fudo; add fudo_sync_runs

Revision ID: b5a0_expenses_fudo_link
Revises: b4a0_add_fiscal_invoicing
Create Date: 2026-10-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b5a0_expenses_fudo_link'
down_revision = 'b4a0_add_fiscal_invoicing'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('suppliers') as batch:
        batch.add_column(sa.Column('fudo_provider_id', sa.String(50), nullable=True))
        batch.create_unique_constraint('uq_suppliers_fudo_provider_id', ['fudo_provider_id'])
    with op.batch_alter_table('expense_categories') as batch:
        batch.add_column(sa.Column('fudo_category_id', sa.String(50), nullable=True))
        batch.create_unique_constraint('uq_expense_categories_fudo_category_id', ['fudo_category_id'])
    with op.batch_alter_table('expenses') as batch:
        batch.add_column(sa.Column('source', sa.String(10), nullable=False, server_default='galia'))
        batch.add_column(sa.Column('category_overridden', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column('supplier_overridden', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.execute("UPDATE expenses SET source = 'fudo' WHERE external_id IS NOT NULL")
    op.create_table(
        'fudo_sync_runs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('kind', sa.String(20), nullable=False),
        sa.Column('status', sa.String(10), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('params', sa.JSON(), nullable=True),
        sa.Column('stats', sa.JSON(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('triggered_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
    )
    op.create_index('ix_fudo_sync_runs_kind_started_at', 'fudo_sync_runs', ['kind', 'started_at'])


def downgrade():
    op.drop_index('ix_fudo_sync_runs_kind_started_at', table_name='fudo_sync_runs')
    op.drop_table('fudo_sync_runs')
    with op.batch_alter_table('expenses') as batch:
        batch.drop_column('supplier_overridden')
        batch.drop_column('category_overridden')
        batch.drop_column('source')
    with op.batch_alter_table('expense_categories') as batch:
        batch.drop_constraint('uq_expense_categories_fudo_category_id', type_='unique')
        batch.drop_column('fudo_category_id')
    with op.batch_alter_table('suppliers') as batch:
        batch.drop_constraint('uq_suppliers_fudo_provider_id', type_='unique')
        batch.drop_column('fudo_provider_id')
```

- [ ] **Step 4: Modelo `FudoSyncRun`**

`backend/app/models/fudo_sync_run.py`:

```python
from datetime import datetime

from app.extensions import db


class FudoSyncRun(db.Model):
    """Una corrida de sincronización con Fudo (por ahora solo kind='expenses')."""
    __tablename__ = 'fudo_sync_runs'
    __table_args__ = (db.Index('ix_fudo_sync_runs_kind_started_at', 'kind', 'started_at'),)

    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(10), nullable=False)  # running | ok | error
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)
    params = db.Column(db.JSON, nullable=True)
    stats = db.Column(db.JSON, nullable=True)
    error = db.Column(db.Text, nullable=True)
    triggered_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'kind': self.kind,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'params': self.params,
            'stats': self.stats,
            'error': self.error,
            'triggered_by': self.triggered_by,
        }
```

En `backend/app/models/__init__.py`, al lado de `from app.models.expense import Expense, ExpenseCategory`, agregar `from app.models.fudo_sync_run import FudoSyncRun` y sumar `'FudoSyncRun'` a la lista `__all__`.

- [ ] **Step 5: Columnas en `Supplier` y `Expense`**

En `backend/app/models/supplier.py`, después de `is_active`:

```python
    fudo_provider_id = db.Column(db.String(50), nullable=True, unique=True)
```

y en `to_dict`, después de `'is_active'`: `'fudo_provider_id': self.fudo_provider_id,`.

En `backend/app/models/expense.py`:

1. Arriba: `import sqlalchemy as sa`.
2. Antes de `class ExpenseCategory`, la función compartida:

```python
DIRECT_EXPENSE_KEYWORDS = ('mercaderia', 'mercadería', 'insumo', 'materia prima', 'producto', 'stock')


def infer_expense_type(name):
    """'directo' si el nombre de la categoría sugiere costo de producción, si no 'indirecto'."""
    lowered = (name or '').lower()
    return 'directo' if any(keyword in lowered for keyword in DIRECT_EXPENSE_KEYWORDS) else 'indirecto'
```

3. En `ExpenseCategory`, después de `is_active`: `fudo_category_id = db.Column(db.String(50), nullable=True, unique=True)`; en su `to_dict`: `'fudo_category_id': self.fudo_category_id,`.
4. En `Expense`, después de `cancelado`:

```python
    source = db.Column(db.String(10), nullable=False, default='galia', server_default='galia')  # 'fudo' | 'galia'
    category_overridden = db.Column(db.Boolean, nullable=False, default=False, server_default=sa.false())
    supplier_overridden = db.Column(db.Boolean, nullable=False, default=False, server_default=sa.false())
```

y en `Expense.to_dict`, después de `'cancelado'`:

```python
            'source': self.source,
            'category_overridden': self.category_overridden,
            'supplier_overridden': self.supplier_overridden,
```

5. En `from_csv_row`, reemplazar las dos líneas

```python
                direct_keywords = ['mercaderia', 'mercadería', 'insumo', 'materia prima', 'producto', 'stock']
                expense_type = 'directo' if any(kw in categoria_name.lower() for kw in direct_keywords) else 'indirecto'
```

por `expense_type = infer_expense_type(categoria_name)`, y en el `cls(...)` final agregar `source='fudo' if external_id else 'galia',` (las filas del CSV con `Id` son exportaciones de Fudo).

6. Bug preexistente: `from_csv_row` llama dos veces a `db.add(category)`, que no existe en Flask-SQLAlchemy (`AttributeError` al importar un CSV con una categoría nueva). Reemplazar ambas por `db.session.add(category)`. `test_csv_row_with_id_is_marked_fudo` pasa por ese camino.

- [ ] **Step 6: Correr los tests**

Run: `cd backend && venv/Scripts/python.exe -m pytest tests/test_expense_fudo_models.py tests/test_migration_chain.py tests/test_suppliers.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/migrations/versions/b5a0_expenses_fudo_link.py backend/app/models backend/tests/test_expense_fudo_models.py backend/tests/test_migration_chain.py
git commit -m "feat(expenses): vínculos con Fudo en gastos, proveedores y categorías + fudo_sync_runs"
```

---

### Task 3: Cliente y parseo puro de gastos

**Files:**
- Modify: `backend/app/utils/fudo_client.py` (método `get_all_expenses`, líneas ~183-226)
- Create: `backend/app/services/expense_fudo_parsing.py`
- Test: `backend/tests/test_expense_fudo_parsing.py`

**Interfaces:**
- Consumes: builders de `tests/fudo_expense_fakes.py` (Tarea 1).
- Produces:
  - `FudoClient.get_all_expenses_with_included(start_date=None, end_date=None) -> {'data': list[dict], 'included': list[dict]}` (included deduplicado por `(type, id)`); `get_all_expenses` sigue devolviendo solo la lista.
  - `expense_fudo_parsing.ParseError(ValueError)`
  - `ProviderRef(fudo_id: str, name: str | None, cuit: str | None)`, `CategoryRef(fudo_id: str, name: str | None)` (dataclasses frozen)
  - `ParsedExpense(external_id: int, fields: dict, provider: ProviderRef | None, category: CategoryRef | None)`
  - `FUDO_FIELDS: tuple[str, ...]` — claves de `fields`: `fecha, fecha_vencimiento, importe, comentario, estado_pago, cancelado, de_caja, caja, medio_pago, tipo_comprobante, numero_comprobante, numero_fiscal, proveedor`
  - `index_included(included: list[dict]) -> dict[(str, str), dict]`
  - `parse_expense(raw: dict, index: dict) -> ParsedExpense`

- [ ] **Step 1: Escribir los tests que fallan**

`backend/tests/test_expense_fudo_parsing.py`:

```python
from datetime import date
from decimal import Decimal

import pytest

from app.services.expense_fudo_parsing import (
    FUDO_FIELDS, CategoryRef, ParseError, ProviderRef, index_included, parse_expense,
)
from app.utils.fudo_client import FudoClient
from fudo_expense_fakes import (
    fudo_expense, fudo_expense_category, fudo_payment_method, fudo_provider, fudo_receipt_type,
)

INCLUDED = [
    fudo_provider(7, 'Molino Sur', cuit='30-71234567-8'),
    fudo_expense_category(3, 'Insumos'),
    fudo_payment_method(1, 'Transferencia'),
    fudo_receipt_type(2, 'Factura A'),
]


def test_parse_full_expense():
    raw = fudo_expense(101, amount='15000.5', date='2026-10-01', provider_id=7, category_id=3,
                       payment_method_id=1, receipt_type_id=2, status='PAID',
                       dueDate='2026-10-15', description='Harina 000', receiptNumber='0001-00001234')

    parsed = parse_expense(raw, index_included(INCLUDED))

    assert parsed.external_id == 101
    assert parsed.provider == ProviderRef('7', 'Molino Sur', '30-71234567-8')
    assert parsed.category == CategoryRef('3', 'Insumos')
    assert set(parsed.fields) == set(FUDO_FIELDS)
    assert parsed.fields['fecha'] == date(2026, 10, 1)
    assert parsed.fields['fecha_vencimiento'] == date(2026, 10, 15)
    assert parsed.fields['importe'] == Decimal('15000.50')
    assert parsed.fields['comentario'] == 'Harina 000'
    assert parsed.fields['estado_pago'] == 'Pagado'
    assert parsed.fields['cancelado'] is False
    assert parsed.fields['medio_pago'] == 'Transferencia'
    assert parsed.fields['tipo_comprobante'] == 'Factura A'
    assert parsed.fields['numero_comprobante'] == '0001-00001234'
    assert parsed.fields['numero_fiscal'] == '30-71234567-8'
    assert parsed.fields['proveedor'] == 'Molino Sur'


def test_parse_without_relations():
    parsed = parse_expense(fudo_expense(5, status='PENDING'), index_included([]))

    assert parsed.provider is None
    assert parsed.category is None
    assert parsed.fields['proveedor'] is None
    assert parsed.fields['medio_pago'] is None
    assert parsed.fields['estado_pago'] == 'Pendiente'


def test_relation_not_in_included_keeps_id_without_name():
    parsed = parse_expense(fudo_expense(5, provider_id=99), index_included([]))
    assert parsed.provider == ProviderRef('99', None, None)


@pytest.mark.parametrize('status', ['CANCELLED', 'CANCELED'])
def test_cancelled_status(status):
    parsed = parse_expense(fudo_expense(5, status=status), {})
    assert parsed.fields['cancelado'] is True
    assert parsed.fields['estado_pago'] == 'Cancelado'


@pytest.mark.parametrize('amount, expected', [
    ('15000.5', Decimal('15000.50')), (15000.499, Decimal('15000.50')), (0, Decimal('0.00')), ('1200', Decimal('1200.00')),
])
def test_amount_is_quantized(amount, expected):
    assert parse_expense(fudo_expense(5, amount=amount), {}).fields['importe'] == expected


@pytest.mark.parametrize('amount', [None, '', 'abc'])
def test_invalid_amount_raises(amount):
    with pytest.raises(ParseError, match='importe'):
        parse_expense(fudo_expense(5, amount=amount), {})


@pytest.mark.parametrize('value', [None, '', '01/10/2026'])
def test_invalid_date_raises(value):
    with pytest.raises(ParseError, match='fecha'):
        parse_expense(fudo_expense(5, date=value), {})


def test_invalid_id_raises():
    raw = fudo_expense(5)
    raw['id'] = 'abc'
    with pytest.raises(ParseError, match='id'):
        parse_expense(raw, {})


def test_client_collects_included_across_pages(monkeypatch):
    client = FudoClient(api_key='key', api_secret='secret')
    page1 = {'data': [{'id': str(i)} for i in range(500)], 'included': [fudo_provider(7, 'Molino Sur')]}
    page2 = {'data': [{'id': '500'}], 'included': [fudo_provider(7, 'Molino Sur'), fudo_expense_category(3, 'Insumos')]}
    calls = []

    def fake_request(endpoint, params=None):
        calls.append(params)
        return [page1, page2][params['page[number]'] - 1]

    monkeypatch.setattr(client, '_make_request', fake_request)

    result = client.get_all_expenses_with_included(start_date='2026-10-01', end_date='2026-10-15')

    assert len(result['data']) == 501
    assert [(i['type'], i['id']) for i in result['included']] == [('Provider', '7'), ('ExpenseCategory', '3')]
    assert calls[0]['filter[date]'] == 'and(gte.2026-10-01,lte.2026-10-15)'
    assert len(client.get_all_expenses()) == 501  # el método viejo sigue devolviendo solo la lista
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `cd backend && venv/Scripts/python.exe -m pytest tests/test_expense_fudo_parsing.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'app.services.expense_fudo_parsing'`.

- [ ] **Step 3: Cliente**

En `backend/app/utils/fudo_client.py`, reemplazar el método `get_all_expenses` completo por:

```python
    def get_all_expenses_with_included(self,
                                       start_date: Optional[str] = None,
                                       end_date: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        Get all expenses with their JSON:API `included` resources (provider, category, payment method...).

        Args:
            start_date: Start date in format YYYY-MM-DD
            end_date: End date in format YYYY-MM-DD

        Returns:
            {'data': [...expenses], 'included': [...related resources, deduplicated by (type, id)]}
        """
        filters = {}
        if start_date and end_date:
            filters['date'] = f'and(gte.{start_date},lte.{end_date})'
        elif start_date:
            filters['date'] = f'gte.{start_date}'
        elif end_date:
            filters['date'] = f'lte.{end_date}'

        all_expenses = []
        included = {}
        page_number = 1
        page_size = 500
        while True:
            response = self.get_expenses(page_size=page_size, page_number=page_number, filters=filters)
            expenses_data = response.get('data', [])
            for item in response.get('included', []) or []:
                included.setdefault((item.get('type'), str(item.get('id'))), item)
            if not expenses_data:
                break
            all_expenses.extend(expenses_data)
            if len(expenses_data) < page_size:
                break
            page_number += 1

        return {'data': all_expenses, 'included': list(included.values())}

    def get_all_expenses(self,
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> List[Dict]:
        """Get all expenses (without included resources)."""
        return self.get_all_expenses_with_included(start_date=start_date, end_date=end_date)['data']
```

- [ ] **Step 4: Parseo**

`backend/app/services/expense_fudo_parsing.py`:

```python
"""Traduce un gasto de Fudo (JSON:API) a los campos de `Expense`. Puro: no toca la base."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

# Nombres de Fudo (confirmados en la Tarea 1 del plan con scripts/inspect_fudo_expenses.py).
ATTR = {
    'date': 'date',
    'due_date': 'dueDate',
    'amount': 'amount',
    'description': 'description',
    'status': 'status',
    'receipt_number': 'receiptNumber',
    'from_cash': 'useInCashCount',
}
REL = {
    'provider': 'provider',
    'category': 'expenseCategory',
    'payment_method': 'paymentMethod',
    'receipt_type': 'receiptType',
    'cash_register': 'cashRegister',
}
PROVIDER_ATTR = {'name': 'name', 'cuit': 'fiscalNumber'}
STATUS_MAP = {'PENDING': 'Pendiente', 'PAID': 'Pagado', 'CANCELLED': 'Cancelado', 'CANCELED': 'Cancelado'}
CANCELLED_STATUSES = {'CANCELLED', 'CANCELED'}

FUDO_FIELDS = (
    'fecha', 'fecha_vencimiento', 'importe', 'comentario', 'estado_pago', 'cancelado', 'de_caja', 'caja',
    'medio_pago', 'tipo_comprobante', 'numero_comprobante', 'numero_fiscal', 'proveedor',
)

CENT = Decimal('0.01')


class ParseError(ValueError):
    pass


@dataclass(frozen=True)
class ProviderRef:
    fudo_id: str
    name: str | None
    cuit: str | None


@dataclass(frozen=True)
class CategoryRef:
    fudo_id: str
    name: str | None


@dataclass
class ParsedExpense:
    external_id: int
    fields: dict
    provider: ProviderRef | None
    category: CategoryRef | None


def index_included(included):
    return {(item.get('type'), str(item.get('id'))): item.get('attributes') or {} for item in included or []}


def _related(raw, rel_key, index):
    """(id, atributos) del recurso relacionado, o (None, {}) si no hay relación."""
    data = ((raw.get('relationships') or {}).get(REL[rel_key]) or {}).get('data')
    if not data or data.get('id') is None:
        return None, {}
    rel_id = str(data['id'])
    return rel_id, index.get((data.get('type'), rel_id), {})


def _text(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _date(value, field, required):
    if value in (None, ''):
        if required:
            raise ParseError(f'{field} vacía')
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        raise ParseError(f'{field} inválida: {value!r}')


def _amount(value):
    if value is None or str(value).strip() == '':
        raise ParseError('importe vacío')
    try:
        return Decimal(str(value)).quantize(CENT)
    except InvalidOperation:
        raise ParseError(f'importe inválido: {value!r}')


def parse_expense(raw, index):
    try:
        external_id = int(raw.get('id'))
    except (TypeError, ValueError):
        raise ParseError(f'id inválido: {raw.get("id")!r}')

    attrs = raw.get('attributes') or {}
    status = (attrs.get(ATTR['status']) or '').upper()

    provider_id, provider_attrs = _related(raw, 'provider', index)
    provider = None
    if provider_id:
        provider = ProviderRef(provider_id, _text(provider_attrs.get(PROVIDER_ATTR['name'])),
                               _text(provider_attrs.get(PROVIDER_ATTR['cuit'])))

    category_id, category_attrs = _related(raw, 'category', index)
    category = CategoryRef(category_id, _text(category_attrs.get('name'))) if category_id else None

    _, method_attrs = _related(raw, 'payment_method', index)
    _, receipt_attrs = _related(raw, 'receipt_type', index)
    _, cash_attrs = _related(raw, 'cash_register', index)

    fields = {
        'fecha': _date(attrs.get(ATTR['date']), 'fecha', required=True),
        'fecha_vencimiento': _date(attrs.get(ATTR['due_date']), 'fecha de vencimiento', required=False),
        'importe': _amount(attrs.get(ATTR['amount'])),
        'comentario': _text(attrs.get(ATTR['description'])),
        'estado_pago': STATUS_MAP.get(status, 'Pendiente'),
        'cancelado': status in CANCELLED_STATUSES,
        'de_caja': bool(attrs.get(ATTR['from_cash'])),
        'caja': _text(cash_attrs.get('name')),
        'medio_pago': _text(method_attrs.get('name')),
        'tipo_comprobante': _text(receipt_attrs.get('name')),
        'numero_comprobante': _text(attrs.get(ATTR['receipt_number'])),
        'numero_fiscal': provider.cuit if provider else None,
        'proveedor': provider.name if provider else None,
    }
    return ParsedExpense(external_id, fields, provider, category)
```

- [ ] **Step 5: Correr los tests**

Run: `cd backend && venv/Scripts/python.exe -m pytest tests/test_expense_fudo_parsing.py tests/test_fudo_client_products.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/utils/fudo_client.py backend/app/services/expense_fudo_parsing.py backend/tests/test_expense_fudo_parsing.py
git commit -m "feat(fudo): parseo de gastos con recursos included"
```

---

### Task 4: Vinculación de proveedores y categorías

**Files:**
- Create: `backend/app/services/expense_fudo_linking.py`
- Test: `backend/tests/test_expense_fudo_linking.py`

**Interfaces:**
- Consumes: `ProviderRef`, `CategoryRef` (Tarea 3); `Supplier.fudo_provider_id`, `ExpenseCategory.fudo_category_id`, `infer_expense_type` (Tarea 2).
- Produces:
  - `normalize_name(value: str | None) -> str`, `normalize_cuit(value: str | None) -> str | None`
  - `new_link_stats() -> dict` con `suppliers_created, suppliers_linked, categories_created, categories_linked` en 0 y `warnings: []`
  - `add_capped(items: list, item, limit=50) -> None`
  - `class Linker(stats: dict)` con `supplier_for(ref: ProviderRef | None) -> Supplier | None`, `category_for(ref: CategoryRef | None) -> ExpenseCategory`, `reset() -> None` (vacía la caché). Hace `flush`, nunca `commit`.
  - `DEFAULT_CATEGORY_NAME = 'Sin categoría'`

- [ ] **Step 1: Escribir los tests que fallan**

`backend/tests/test_expense_fudo_linking.py`:

```python
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
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `cd backend && venv/Scripts/python.exe -m pytest tests/test_expense_fudo_linking.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'app.services.expense_fudo_linking'`.

- [ ] **Step 3: Implementar**

`backend/app/services/expense_fudo_linking.py`:

```python
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
```

- [ ] **Step 4: Correr los tests**

Run: `cd backend && venv/Scripts/python.exe -m pytest tests/test_expense_fudo_linking.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/expense_fudo_linking.py backend/tests/test_expense_fudo_linking.py
git commit -m "feat(expenses): vincular proveedores y categorías de Fudo con Galia"
```

---

### Task 5: Servicio de sincronización (upsert)

**Files:**
- Create: `backend/app/services/expense_sync_service.py`
- Test: `backend/tests/test_expense_sync.py`

**Interfaces:**
- Consumes: `FakeExpensesClient` y builders (Tarea 1); `index_included`, `parse_expense`, `FUDO_FIELDS` (Tarea 3); `Linker`, `new_link_stats`, `add_capped` (Tarea 4).
- Produces: `expense_sync_service.sync_expenses(client, start_date: str, end_date: str) -> dict` con las claves de stats de Global Constraints. Commitea. `BATCH_SIZE = 200`.

- [ ] **Step 1: Escribir los tests que fallan**

`backend/tests/test_expense_sync.py`:

```python
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
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `cd backend && venv/Scripts/python.exe -m pytest tests/test_expense_sync.py -v`
Expected: FAIL con `ImportError: cannot import name 'expense_sync_service'`.

- [ ] **Step 3: Implementar**

`backend/app/services/expense_sync_service.py`:

```python
"""Importa/actualiza gastos desde Fudo con proveedor y categoría vinculados (ver spec 2026-10-15)."""
import logging

from app.extensions import db
from app.models.expense import Expense
from app.services.expense_fudo_linking import Linker, add_capped, new_link_stats
from app.services.expense_fudo_parsing import index_included, parse_expense

logger = logging.getLogger(__name__)

BATCH_SIZE = 200
LINK_COUNTERS = ('suppliers_created', 'suppliers_linked', 'categories_created', 'categories_linked')


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
        db.session.add(Expense(external_id=parsed.external_id, source='fudo', creado_por='Fudo Sync',
                               supplier_id=supplier_id, category_id=category.id, **parsed.fields))
        db.session.flush()
        stats['created'] += 1
        return

    changed = False
    for field, value in parsed.fields.items():
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
```

- [ ] **Step 4: Correr los tests**

Run: `cd backend && venv/Scripts/python.exe -m pytest tests/test_expense_sync.py tests/test_expense_fudo_linking.py tests/test_expense_fudo_parsing.py -v`
Expected: PASS.

Si `test_second_run_is_idempotent` falla con `updated == 1`, comparar el campo que difiere (p. ej. `importe` como `Decimal` vs `float` en SQLite) imprimiendo `getattr(expense, field), value` dentro del loop, y normalizar ese campo en la comparación; no relajar el test.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/expense_sync_service.py backend/tests/test_expense_sync.py
git commit -m "feat(expenses): servicio de sincronización de gastos con Fudo"
```

---

### Task 6: Corridas y endpoints de sync

**Files:**
- Create: `backend/app/services/fudo_sync_runs.py`
- Modify: `backend/app/routes/fudo_sync.py` (borrar `parse_fudo_expense`, `_sync_expenses_background` y el `sync_expenses` viejo; agregar los nuevos)
- Test: `backend/tests/test_fudo_sync_runs.py`

**Interfaces:**
- Consumes: `FudoSyncRun` (Tarea 2), `expense_sync_service.sync_expenses` (Tarea 5), `FakeExpensesClient` (Tarea 1), fixtures `menu_client`, `admin_headers`, `employee_headers` de `tests/conftest.py`.
- Produces:
  - `fudo_sync_runs.STALE_AFTER = timedelta(minutes=30)`
  - `class SyncInProgress(Exception)` con atributo `run`
  - `start_run(kind: str, params: dict, user_id: int | None = None, now: datetime | None = None) -> FudoSyncRun`
  - `finish_run(run_id: int, stats: dict | None = None, error: str | None = None) -> None`
  - `run_expenses_sync(app, run_id: int, start_date: str, end_date: str, client_factory) -> None`
  - HTTP: `POST /api/v1/fudo/sync/expenses?start_date&end_date` → 202 `{message, status: 'processing', run_id}` / 400 `{error}` / 409 `{error, run_id}`; `GET /api/v1/fudo/sync/runs/<id>` → `FudoSyncRun.to_dict()`; `GET /api/v1/fudo/sync/runs?kind=expenses&limit=5` → `{runs: [...]}` más reciente primero.
  - `routes.fudo_sync._launch(target, *args)` (los tests lo reemplazan por una llamada sincrónica).

- [ ] **Step 1: Escribir los tests que fallan**

`backend/tests/test_fudo_sync_runs.py`:

```python
from datetime import datetime, timedelta

import pytest

from app.extensions import db
from app.models.expense import Expense
from app.models.fudo_sync_run import FudoSyncRun
from app.routes import fudo_sync
from app.services import fudo_sync_runs
from app.services.fudo_sync_runs import SyncInProgress
from fudo_expense_fakes import FakeExpensesClient, fudo_expense

URL = '/api/v1/fudo/sync/expenses'


@pytest.fixture
def run_inline(monkeypatch):
    """Corre la sync en el mismo hilo y con un cliente fake configurable."""
    holder = {'client': FakeExpensesClient(data=[fudo_expense(101)])}
    monkeypatch.setattr(fudo_sync, '_launch', lambda target, *args: target(*args))
    monkeypatch.setattr(fudo_sync, 'FudoClient', lambda: holder['client'])
    return holder


def test_start_run_blocks_recent_running(menu_app):
    now = datetime(2026, 10, 15, 12, 0)
    first = fudo_sync_runs.start_run('expenses', {}, now=now)

    with pytest.raises(SyncInProgress) as exc:
        fudo_sync_runs.start_run('expenses', {}, now=now + timedelta(minutes=10))
    assert exc.value.run.id == first.id


def test_start_run_abandons_stale_running(menu_app):
    now = datetime(2026, 10, 15, 12, 0)
    stale = fudo_sync_runs.start_run('expenses', {}, now=now)

    fresh = fudo_sync_runs.start_run('expenses', {}, now=now + timedelta(minutes=31))

    db.session.refresh(stale)
    assert stale.status == 'error'
    assert 'abandonada' in stale.error
    assert fresh.status == 'running'


def test_run_expenses_sync_records_error(menu_app):
    run = fudo_sync_runs.start_run('expenses', {})

    fudo_sync_runs.run_expenses_sync(menu_app, run.id, '2026-10-01', '2026-10-31',
                                     lambda: FakeExpensesClient(error=RuntimeError('401 Unauthorized')))

    run = db.session.get(FudoSyncRun, run.id)
    assert run.status == 'error'
    assert run.error == '401 Unauthorized'
    assert run.finished_at is not None


def test_post_runs_sync_and_records_stats(menu_client, admin_headers, run_inline):
    response = menu_client.post(f'{URL}?start_date=2026-10-01&end_date=2026-10-31', headers=admin_headers)

    assert response.status_code == 202
    run_id = response.get_json()['run_id']
    run = menu_client.get(f'/api/v1/fudo/sync/runs/{run_id}', headers=admin_headers).get_json()
    assert run['status'] == 'ok'
    assert run['stats']['created'] == 1
    assert run['params'] == {'start_date': '2026-10-01', 'end_date': '2026-10-31'}
    assert run_inline['client'].calls == [('2026-10-01', '2026-10-31')]
    assert Expense.query.count() == 1


@pytest.mark.parametrize('query', [
    '', 'start_date=2026-10-01', 'start_date=01/10/2026&end_date=2026-10-31',
    'start_date=2026-10-31&end_date=2026-10-01', 'start_date=2025-01-01&end_date=2026-10-31',
])
def test_post_rejects_bad_ranges(menu_client, admin_headers, run_inline, query):
    response = menu_client.post(f'{URL}?{query}', headers=admin_headers)

    assert response.status_code == 400
    assert response.get_json()['error']
    assert FudoSyncRun.query.count() == 0


def test_post_conflicts_with_running_sync(menu_client, admin_headers, run_inline):
    running = fudo_sync_runs.start_run('expenses', {})

    response = menu_client.post(f'{URL}?start_date=2026-10-01&end_date=2026-10-31', headers=admin_headers)

    assert response.status_code == 409
    assert response.get_json()['run_id'] == running.id


def test_post_requires_admin(menu_client, employee_headers, run_inline):
    response = menu_client.post(f'{URL}?start_date=2026-10-01&end_date=2026-10-31', headers=employee_headers)
    assert response.status_code == 403


def test_list_runs_newest_first(menu_client, admin_headers):
    base = datetime(2026, 10, 15, 12, 0)
    for minutes in (0, 40, 80):
        run = fudo_sync_runs.start_run('expenses', {}, now=base + timedelta(minutes=minutes))
        fudo_sync_runs.finish_run(run.id, stats={'created': minutes})

    runs = menu_client.get('/api/v1/fudo/sync/runs?kind=expenses&limit=2', headers=admin_headers).get_json()['runs']

    assert [r['stats']['created'] for r in runs] == [80, 40]


def test_get_unknown_run_is_404(menu_client, admin_headers):
    assert menu_client.get('/api/v1/fudo/sync/runs/999', headers=admin_headers).status_code == 404
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `cd backend && venv/Scripts/python.exe -m pytest tests/test_fudo_sync_runs.py -v`
Expected: FAIL con `ImportError: cannot import name 'fudo_sync_runs'`.

- [ ] **Step 3: Servicio de corridas**

`backend/app/services/fudo_sync_runs.py`:

```python
"""Registro de corridas de sincronización con Fudo y ejecución en segundo plano."""
import logging
from datetime import datetime, timedelta

from app.extensions import db
from app.models.fudo_sync_run import FudoSyncRun
from app.services import expense_sync_service

logger = logging.getLogger(__name__)

STALE_AFTER = timedelta(minutes=30)


class SyncInProgress(Exception):
    def __init__(self, run):
        super().__init__(f'Corrida {run.id} en curso')
        self.run = run


def start_run(kind, params, user_id=None, now=None):
    now = now or datetime.utcnow()
    for running in FudoSyncRun.query.filter_by(kind=kind, status='running').all():
        if now - running.started_at < STALE_AFTER:
            raise SyncInProgress(running)
        running.status = 'error'
        running.finished_at = now
        running.error = 'Corrida abandonada (no terminó en 30 minutos)'
    run = FudoSyncRun(kind=kind, status='running', started_at=now, params=params, triggered_by=user_id)
    db.session.add(run)
    db.session.commit()
    return run


def finish_run(run_id, stats=None, error=None):
    run = db.session.get(FudoSyncRun, run_id)
    run.status = 'error' if error else 'ok'
    run.finished_at = datetime.utcnow()
    run.stats = stats
    run.error = error
    db.session.commit()


def run_expenses_sync(app, run_id, start_date, end_date, client_factory):
    with app.app_context():
        try:
            stats = expense_sync_service.sync_expenses(client_factory(), start_date, end_date)
        except Exception as exc:
            logger.exception('Sync de gastos %s falló', run_id)
            db.session.rollback()
            finish_run(run_id, error=str(exc) or exc.__class__.__name__)
            return
        finish_run(run_id, stats=stats)
```

- [ ] **Step 4: Rutas**

En `backend/app/routes/fudo_sync.py`:

1. Imports: cambiar `from flask import Blueprint, request, jsonify` por `from flask import Blueprint, current_app, request, jsonify`; cambiar `from datetime import datetime` por `from datetime import date, datetime`; agregar

```python
from app.models.fudo_sync_run import FudoSyncRun
from app.services import fudo_sync_runs
from app.services.fudo_sync_runs import SyncInProgress
```

2. Borrar completas las funciones `parse_fudo_expense`, `_sync_expenses_background` y la ruta `sync_expenses` (con su decorador `@bp.route('/sync/expenses', ...)`). Si `Expense` queda sin uso en el archivo, sacarlo del import (`ExpenseCategory` se sigue usando en `/categories`).

3. Agregar, en el lugar donde estaba la ruta borrada:

```python
MAX_RANGE_DAYS = 366


def _parse_range(args):
    """(start, end) en ISO o un mensaje de error."""
    start_raw, end_raw = args.get('start_date'), args.get('end_date')
    if not start_raw or not end_raw:
        return None, 'start_date y end_date son obligatorias (YYYY-MM-DD)'
    try:
        start, end = date.fromisoformat(start_raw), date.fromisoformat(end_raw)
    except ValueError:
        return None, 'Formato de fecha inválido, usá YYYY-MM-DD'
    if start > end:
        return None, 'start_date no puede ser posterior a end_date'
    if (end - start).days > MAX_RANGE_DAYS:
        return None, f'El rango no puede superar {MAX_RANGE_DAYS} días'
    return (start.isoformat(), end.isoformat()), None


def _launch(target, *args):
    threading.Thread(target=target, args=args, daemon=True).start()


@bp.route('/sync/expenses', methods=['POST'])
@token_required
@admin_required
def sync_expenses(current_user):
    """Sincroniza gastos de Fudo en segundo plano. Query: start_date, end_date (YYYY-MM-DD)."""
    dates, error = _parse_range(request.args)
    if error:
        return jsonify({'error': error}), 400
    start, end = dates
    try:
        run = fudo_sync_runs.start_run('expenses', {'start_date': start, 'end_date': end}, current_user.id)
    except SyncInProgress as exc:
        return jsonify({'error': 'Ya hay una sincronización de gastos en curso', 'run_id': exc.run.id}), 409

    _launch(fudo_sync_runs.run_expenses_sync, current_app._get_current_object(), run.id, start, end, FudoClient)
    return jsonify({'message': 'Sincronización de gastos iniciada', 'status': 'processing', 'run_id': run.id}), 202


@bp.route('/sync/runs/<int:run_id>', methods=['GET'])
@token_required
@admin_required
def get_sync_run(current_user, run_id):
    run = db.session.get(FudoSyncRun, run_id)
    if run is None:
        return jsonify({'error': 'Corrida no encontrada'}), 404
    return jsonify(run.to_dict()), 200


@bp.route('/sync/runs', methods=['GET'])
@token_required
@admin_required
def list_sync_runs(current_user):
    kind = request.args.get('kind', 'expenses')
    try:
        limit = max(1, min(int(request.args.get('limit', 5)), 50))
    except ValueError:
        limit = 5
    runs = (FudoSyncRun.query.filter_by(kind=kind)
            .order_by(FudoSyncRun.started_at.desc(), FudoSyncRun.id.desc()).limit(limit).all())
    return jsonify({'runs': [run.to_dict() for run in runs]}), 200
```

- [ ] **Step 5: Correr los tests**

Run: `cd backend && venv/Scripts/python.exe -m pytest tests/test_fudo_sync_runs.py tests/test_expense_sync.py tests/test_route_access_coverage.py -v`
Expected: PASS. Si `test_route_access_coverage.py` exige registrar las rutas nuevas en alguna lista, agregarlas ahí siguiendo el formato de las demás rutas `/api/v1/fudo/...`.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/fudo_sync_runs.py backend/app/routes/fudo_sync.py backend/tests/test_fudo_sync_runs.py
git commit -m "feat(fudo): corridas de sync de gastos con seguimiento (202 + run_id, 409 si hay otra)"
```

---

### Task 7: Banderas de corrección y re-vinculación de categorías

**Files:**
- Modify: `backend/app/routes/expenses.py` (`update_expense` ~248-302, `classify_expenses` ~508-545)
- Modify: `backend/app/routes/reports.py` (`update_expense_category` ~981-998)
- Test: `backend/tests/test_expense_overrides.py`

**Interfaces:**
- Consumes: columnas de la Tarea 2.
- Produces: `PUT /api/v1/expenses/<id>` y `POST /api/v1/expenses/classify` marcan `category_overridden` / `supplier_overridden` solo si `source == 'fudo'` y el valor cambió; `PUT /api/v1/reports/expense-categories/<id>` acepta `fudo_category_id` (string, número o `null`) y lo saca de la categoría que lo tenía.

- [ ] **Step 1: Escribir los tests que fallan**

`backend/tests/test_expense_overrides.py`:

```python
from datetime import date
from decimal import Decimal

from app.extensions import db
from app.models.expense import Expense, ExpenseCategory
from app.models.supplier import Supplier


def _expense(source, category, supplier=None):
    expense = Expense(fecha=date(2026, 10, 1), importe=Decimal('100'), category_id=category.id,
                      supplier_id=supplier.id if supplier else None, source=source,
                      external_id=1 if source == 'fudo' else None)
    db.session.add(expense)
    db.session.commit()
    return expense


def _setup():
    first, second = ExpenseCategory(name='A'), ExpenseCategory(name='B')
    supplier_a, supplier_b = Supplier(name='S1'), Supplier(name='S2')
    db.session.add_all([first, second, supplier_a, supplier_b])
    db.session.commit()
    return first, second, supplier_a, supplier_b


def test_put_marks_overrides_on_fudo_expense(menu_client, admin_headers):
    first, second, supplier_a, supplier_b = _setup()
    expense = _expense('fudo', first, supplier_a)

    response = menu_client.put(f'/api/v1/expenses/{expense.id}', headers=admin_headers,
                               json={'category_id': second.id, 'supplier_id': supplier_b.id})

    assert response.status_code == 200
    data = response.get_json()
    assert data['category_overridden'] is True
    assert data['supplier_overridden'] is True


def test_put_with_same_values_does_not_mark(menu_client, admin_headers):
    first, _, supplier_a, _ = _setup()
    expense = _expense('fudo', first, supplier_a)

    data = menu_client.put(f'/api/v1/expenses/{expense.id}', headers=admin_headers,
                           json={'category_id': first.id, 'supplier_id': supplier_a.id, 'comentario': 'x'}).get_json()

    assert data['category_overridden'] is False
    assert data['supplier_overridden'] is False


def test_put_on_manual_expense_does_not_mark(menu_client, admin_headers):
    first, second, _, _ = _setup()
    expense = _expense('galia', first)

    data = menu_client.put(f'/api/v1/expenses/{expense.id}', headers=admin_headers,
                           json={'category_id': second.id}).get_json()

    assert data['category_overridden'] is False


def test_classify_marks_category_override(menu_client, admin_headers):
    first, second, _, _ = _setup()
    fudo_expense = _expense('fudo', first)

    response = menu_client.post('/api/v1/expenses/classify', headers=admin_headers,
                                json={'classifications': [{'expense_id': fudo_expense.id, 'category_id': second.id}]})

    assert response.status_code == 200
    db.session.refresh(fudo_expense)
    assert fudo_expense.category_overridden is True


def test_relink_fudo_category_moves_link(menu_client, admin_headers):
    old = ExpenseCategory(name='Vieja', fudo_category_id='3')
    new = ExpenseCategory(name='Nueva')
    db.session.add_all([old, new])
    db.session.commit()

    response = menu_client.put(f'/api/v1/reports/expense-categories/{new.id}', headers=admin_headers,
                               json={'fudo_category_id': 3})

    assert response.status_code == 200
    assert response.get_json()['fudo_category_id'] == '3'
    db.session.refresh(old)
    assert old.fudo_category_id is None


def test_unlink_fudo_category(menu_client, admin_headers):
    category = ExpenseCategory(name='Vieja', fudo_category_id='3')
    db.session.add(category)
    db.session.commit()

    data = menu_client.put(f'/api/v1/reports/expense-categories/{category.id}', headers=admin_headers,
                           json={'fudo_category_id': None}).get_json()

    assert data['fudo_category_id'] is None
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `cd backend && venv/Scripts/python.exe -m pytest tests/test_expense_overrides.py -v`
Expected: FAIL (las banderas quedan en `False`; `fudo_category_id` no cambia).

- [ ] **Step 3: Implementar en `routes/expenses.py`**

En `update_expense`, dentro de `if 'category_id' in data:` reemplazar la línea `expense.category_id = category_id` por:

```python
            if category_id != expense.category_id and expense.source == 'fudo':
                expense.category_overridden = True
            expense.category_id = category_id
```

En el bloque `if 'supplier_id' in data:`, dentro de `if new_supplier_id != expense.supplier_id:`, justo antes de `expense.supplier_id = new_supplier_id`:

```python
            if expense.source == 'fudo':
                expense.supplier_overridden = True
```

En `classify_expenses`, reemplazar `expense.category_id = category_id` por:

```python
                    if category_id != expense.category_id and expense.source == 'fudo':
                        expense.category_overridden = True
                    expense.category_id = category_id
```

- [ ] **Step 4: Implementar en `routes/reports.py`**

En `update_expense_category`, antes de `db.session.commit()`:

```python
    if 'fudo_category_id' in data:
        raw = data['fudo_category_id']
        fudo_category_id = str(raw).strip() if raw not in (None, '') else None
        if fudo_category_id:
            previous = ExpenseCategory.query.filter(ExpenseCategory.fudo_category_id == fudo_category_id,
                                                    ExpenseCategory.id != category.id).first()
            if previous:
                previous.fudo_category_id = None
                db.session.flush()
        category.fudo_category_id = fudo_category_id
```

- [ ] **Step 5: Correr los tests**

Run: `cd backend && venv/Scripts/python.exe -m pytest tests/test_expense_overrides.py tests/test_expense_sync.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/routes/expenses.py backend/app/routes/reports.py backend/tests/test_expense_overrides.py
git commit -m "feat(expenses): respetar correcciones manuales y re-vincular categorías de Fudo"
```

---

### Task 8: Frontend — servicio, helpers y modal

**Files:**
- Modify: `frontend/src/services/fudoService.js`
- Create: `frontend/src/components/fudo/syncRunSummary.js`
- Test: `frontend/src/components/fudo/syncRunSummary.test.js`
- Rewrite: `frontend/src/components/fudo/FudoSyncExpensesModal.jsx`

**Interfaces:**
- Consumes: endpoints de la Tarea 6.
- Produces:
  - `fudoService.syncExpenses(startDate, endDate) -> Promise<{run_id, ...}>`, `fudoService.getSyncRun(id) -> Promise<run>`, `fudoService.getSyncRuns(kind = 'expenses', limit = 1) -> Promise<run[]>`
  - `syncRunSummary.js`: `RUN_STATS`, `isRunFinished(run) -> boolean`, `summarizeRun(run) -> {key, label, value}[]`, `validateRange(start, end) -> string | null`, `formatRunDate(iso) -> string`
  - `<FudoSyncExpensesModal isOpen onClose onSuccess />` (mismas props que hoy).

- [ ] **Step 1: Escribir los tests que fallan**

`frontend/src/components/fudo/syncRunSummary.test.js`:

```js
import { describe, expect, it } from 'vitest';
import { isRunFinished, summarizeRun, validateRange } from './syncRunSummary';

describe('validateRange', () => {
  it('requires both dates', () => {
    expect(validateRange('', '2026-10-31')).toMatch(/dos fechas/);
    expect(validateRange('2026-10-01', '')).toMatch(/dos fechas/);
  });
  it('rejects inverted ranges', () => {
    expect(validateRange('2026-10-31', '2026-10-01')).toMatch(/posterior/);
  });
  it('rejects ranges over 366 days', () => {
    expect(validateRange('2025-01-01', '2026-10-31')).toMatch(/366/);
  });
  it('accepts a valid range', () => {
    expect(validateRange('2026-10-01', '2026-10-31')).toBeNull();
  });
});

describe('isRunFinished', () => {
  it('is false while running or without a run', () => {
    expect(isRunFinished(null)).toBe(false);
    expect(isRunFinished({ status: 'running' })).toBe(false);
  });
  it('is true for ok and error', () => {
    expect(isRunFinished({ status: 'ok' })).toBe(true);
    expect(isRunFinished({ status: 'error' })).toBe(true);
  });
});

describe('summarizeRun', () => {
  it('lists every stat with 0 for missing ones', () => {
    const rows = summarizeRun({ stats: { created: 3, suppliers_created: 1 } });
    expect(rows.find((r) => r.key === 'created').value).toBe(3);
    expect(rows.find((r) => r.key === 'suppliers_created').value).toBe(1);
    expect(rows.find((r) => r.key === 'updated').value).toBe(0);
    expect(rows).toHaveLength(8);
  });
  it('handles a run without stats', () => {
    expect(summarizeRun({ stats: null }).every((r) => r.value === 0)).toBe(true);
  });
});
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `cd frontend && npx vitest run src/components/fudo/syncRunSummary.test.js`
Expected: FAIL (`Failed to resolve import "./syncRunSummary"`).

- [ ] **Step 3: Helpers**

`frontend/src/components/fudo/syncRunSummary.js`:

```js
export const RUN_STATS = [
  ['fetched', 'Obtenidos de Fudo'],
  ['created', 'Nuevos'],
  ['updated', 'Actualizados'],
  ['unchanged', 'Sin cambios'],
  ['suppliers_created', 'Proveedores nuevos'],
  ['suppliers_linked', 'Proveedores vinculados'],
  ['categories_created', 'Categorías nuevas'],
  ['categories_linked', 'Categorías vinculadas'],
];

const MAX_RANGE_DAYS = 366;
const DAY_MS = 24 * 60 * 60 * 1000;

export const isRunFinished = (run) => Boolean(run) && run.status !== 'running';

export const summarizeRun = (run) =>
  RUN_STATS.map(([key, label]) => ({ key, label, value: run?.stats?.[key] ?? 0 }));

export const validateRange = (start, end) => {
  if (!start || !end) return 'Elegí las dos fechas';
  if (start > end) return 'La fecha "Desde" no puede ser posterior a "Hasta"';
  if ((Date.parse(end) - Date.parse(start)) / DAY_MS > MAX_RANGE_DAYS) {
    return `El rango no puede superar ${MAX_RANGE_DAYS} días`;
  }
  return null;
};

export const formatRunDate = (iso) => (iso ? new Date(`${iso}Z`).toLocaleString('es-AR') : '-');
```

(`started_at` llega en UTC sin zona; el `Z` lo marca como UTC antes de pasarlo a hora local.)

- [ ] **Step 4: Correr los tests**

Run: `cd frontend && npx vitest run src/components/fudo/syncRunSummary.test.js`
Expected: PASS.

- [ ] **Step 5: Servicio**

En `frontend/src/services/fudoService.js`, reemplazar `syncExpenses` por:

```js
  syncExpenses: async (startDate, endDate) => {
    const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
    const response = await api.post(`/fudo/sync/expenses?${params.toString()}`);
    return response.data;
  },

  getSyncRun: async (runId) => {
    const response = await api.get(`/fudo/sync/runs/${runId}`);
    return response.data;
  },

  getSyncRuns: async (kind = 'expenses', limit = 1) => {
    const response = await api.get('/fudo/sync/runs', { params: { kind, limit } });
    return response.data.runs;
  }
```

- [ ] **Step 6: Reescribir el modal**

`frontend/src/components/fudo/FudoSyncExpensesModal.jsx` (reemplazo completo):

```jsx
import { useState, useEffect } from 'react';
import { X, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react';
import fudoService from '../../services/fudoService';
import { formatRunDate, isRunFinished, summarizeRun, validateRange } from './syncRunSummary';

const POLL_MS = 2000;

const FudoSyncExpensesModal = ({ isOpen, onClose, onSuccess }) => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [run, setRun] = useState(null);
  const [lastRun, setLastRun] = useState(null);
  const [error, setError] = useState(null);
  const [starting, setStarting] = useState(false);

  const running = run && !isRunFinished(run);

  useEffect(() => {
    if (!isOpen) return;
    setRun(null);
    setError(null);
    fudoService.getSyncRuns('expenses', 1)
      .then((runs) => {
        const latest = runs[0] || null;
        setLastRun(latest);
        if (latest && !isRunFinished(latest)) setRun(latest);
      })
      .catch(() => setLastRun(null));
  }, [isOpen]);

  useEffect(() => {
    if (!running) return undefined;
    const timer = setInterval(async () => {
      try {
        const updated = await fudoService.getSyncRun(run.id);
        setRun(updated);
        if (isRunFinished(updated)) {
          setLastRun(updated);
          if (updated.status === 'ok') onSuccess?.();
        }
      } catch (err) {
        setError(err.response?.data?.error || 'No se pudo consultar el estado de la sincronización');
      }
    }, POLL_MS);
    return () => clearInterval(timer);
  }, [running, run?.id, onSuccess]);

  const handleSync = async () => {
    const rangeError = validateRange(startDate, endDate);
    if (rangeError) {
      setError(rangeError);
      return;
    }
    setStarting(true);
    setError(null);
    try {
      const { run_id: runId } = await fudoService.syncExpenses(startDate, endDate);
      setRun({ id: runId, status: 'running' });
    } catch (err) {
      if (err.response?.status === 409 && err.response.data?.run_id) {
        setError('Ya hay una sincronización en curso; te muestro su avance.');
        setRun({ id: err.response.data.run_id, status: 'running' });
      } else {
        setError(err.response?.data?.error || 'Error al iniciar la sincronización');
      }
    } finally {
      setStarting(false);
    }
  };

  if (!isOpen) return null;

  const shown = run && isRunFinished(run) ? run : null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-4 border-b flex items-center justify-between sticky top-0 bg-white z-10">
          <h2 className="text-lg font-semibold">Sincronizar gastos desde Fudo</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700" aria-label="Cerrar">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <p className="text-sm text-gray-600">
            Trae los gastos del rango elegido. Los proveedores y categorías se vinculan solos con los de Galia
            (o se crean si no existen). Si corregiste a mano la categoría o el proveedor de un gasto, se respeta.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <label className="block">
              <span className="block text-sm font-medium text-gray-700 mb-1">Desde</span>
              <input type="date" value={startDate} disabled={running}
                     onChange={(e) => setStartDate(e.target.value)}
                     className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500" />
            </label>
            <label className="block">
              <span className="block text-sm font-medium text-gray-700 mb-1">Hasta</span>
              <input type="date" value={endDate} disabled={running}
                     onChange={(e) => setEndDate(e.target.value)}
                     className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500" />
            </label>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {running && (
            <div className="flex items-center gap-2 text-sm text-blue-800 bg-blue-50 rounded-lg p-3">
              <RefreshCw className="w-4 h-4 animate-spin" />
              Sincronizando… podés cerrar esta ventana, sigue en segundo plano.
            </div>
          )}

          {shown && shown.status === 'error' && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800">
              La sincronización falló: {shown.error}
            </div>
          )}

          {shown && shown.status === 'ok' && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 space-y-3">
              <div className="flex items-center gap-2 text-green-900 font-medium">
                <CheckCircle className="w-5 h-5" /> Sincronización terminada
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {summarizeRun(shown).map(({ key, label, value }) => (
                  <div key={key} className="bg-white rounded p-2 text-center">
                    <div className="text-xl font-bold text-gray-900">{value}</div>
                    <div className="text-xs text-gray-600">{label}</div>
                  </div>
                ))}
              </div>
              {shown.stats?.warnings?.length > 0 && (
                <details className="text-sm text-amber-800">
                  <summary>{shown.stats.warnings.length} avisos</summary>
                  <ul className="list-disc ml-5 mt-1">
                    {shown.stats.warnings.map((warning) => <li key={warning}>{warning}</li>)}
                  </ul>
                </details>
              )}
              {shown.stats?.errors?.length > 0 && (
                <details className="text-sm text-red-700">
                  <summary>{shown.stats.errors.length} gastos no se pudieron importar</summary>
                  <ul className="list-disc ml-5 mt-1">
                    {shown.stats.errors.map((item) => (
                      <li key={item.expense_id}>Gasto {item.expense_id}: {item.error}</li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          )}

          {!run && lastRun && (
            <p className="text-xs text-gray-500">
              Última sincronización: {formatRunDate(lastRun.started_at)} ·{' '}
              {lastRun.status === 'ok' ? 'OK' : lastRun.status === 'error' ? 'con error' : 'en curso'}
              {lastRun.params && ` · ${lastRun.params.start_date} a ${lastRun.params.end_date}`}
            </p>
          )}
        </div>

        <div className="p-4 border-t bg-gray-50 flex gap-3 justify-end">
          <button onClick={onClose} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">
            Cerrar
          </button>
          <button
            onClick={handleSync}
            disabled={starting || running}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 ${starting || running ? 'animate-spin' : ''}`} />
            {running ? 'Sincronizando…' : 'Sincronizar gastos'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default FudoSyncExpensesModal;
```

- [ ] **Step 7: Verificar build y tests**

Run: `cd frontend && npx vitest run && npm run build`
Expected: tests PASS y build sin errores.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/services/fudoService.js frontend/src/components/fudo
git commit -m "feat(frontend): modal de sync de gastos con seguimiento de la corrida"
```

---

### Task 9: Frontend — montar el modal, badge "Fudo" y vínculo en categorías

**Files:**
- Modify: `frontend/src/pages/Expenses.jsx`
- Modify: `frontend/src/pages/ExpenseCategories.jsx`

**Interfaces:**
- Consumes: `<FudoSyncExpensesModal />` (Tarea 8), `fudoService.getCategories()` (existente: `{fudo_categories: [{id, name, active}], galia_categories: [...]}`), `expense.source` y `category.fudo_category_id` (Tarea 2), PUT con `fudo_category_id` (Tarea 7).

- [ ] **Step 1: `Expenses.jsx` — botón y modal**

1. Agregar `Cloud` a la lista de íconos importados de `lucide-react` e importar el modal debajo de `ExpenseClassifierModal`:

```jsx
import FudoSyncExpensesModal from '../components/fudo/FudoSyncExpensesModal';
```

2. Junto a los demás `useState` de modales: `const [showFudoSyncModal, setShowFudoSyncModal] = useState(false);`
3. En el header, antes del botón "Importar CSV":

```jsx
          <button
            onClick={() => setShowFudoSyncModal(true)}
            className="inline-flex items-center px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm font-medium"
            title="Sincronizar desde Fudo"
          >
            <Cloud className="w-4 h-4 mr-1" />
            Sync Fudo
          </button>
```

4. Al final del JSX, junto a los otros modales:

```jsx
      <FudoSyncExpensesModal
        isOpen={showFudoSyncModal}
        onClose={() => setShowFudoSyncModal(false)}
        onSuccess={fetchExpenses}
      />
```

(`fetchExpenses` es el `useCallback` existente en la línea ~66. `onSuccess` va en las deps del efecto de polling del modal: como es un `useCallback` no reinicia el intervalo en cada render.)

- [ ] **Step 2: `Expenses.jsx` — badge**

En la celda del proveedor de la tabla, reemplazar `{expense.proveedor || '-'}` por:

```jsx
                      <div className="flex items-center gap-1">
                        <span>{expense.proveedor || '-'}</span>
                        {expense.source === 'fudo' && (
                          <span className="text-xs px-1.5 py-0.5 rounded bg-purple-100 text-purple-700" title="Importado desde Fudo">
                            Fudo
                          </span>
                        )}
                      </div>
```

- [ ] **Step 3: `ExpenseCategories.jsx` — selector de vínculo**

1. Importar el servicio: `import fudoService from '../services/fudoService';`
2. Estado: `const [fudoCategories, setFudoCategories] = useState(null);` (`null` = no disponible, p. ej. usuario no admin o Fudo caído).
3. En los tres lugares donde se arma `formData` (estado inicial, `handleOpenModal` en sus dos ramas y `handleCloseModal`), agregar la clave `fudo_category_id`: en la rama de edición `fudo_category_id: category.fudo_category_id || ''`, en las demás `fudo_category_id: ''`.
4. Al final de `handleOpenModal`, antes de `setShowModal(true)`:

```jsx
    if (fudoCategories === null) {
      fudoService.getCategories()
        .then((data) => setFudoCategories(data.fudo_categories || []))
        .catch(() => setFudoCategories(null));
    }
```

5. En `handleSubmit`, enviar `null` en vez de `''`: reemplazar `formData` en las llamadas `api.put(...)` y `api.post(...)` por `payload`, definido al principio del `try`:

```jsx
      const payload = { ...formData, fudo_category_id: formData.fudo_category_id || null };
```

6. En el formulario, después del bloque del select "Tipo de Gasto" (el `div` que termina con el `<p>` "Los gastos directos están relacionados…"):

```jsx
                {fudoCategories && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Categoría de Fudo vinculada
                    </label>
                    <select
                      value={formData.fudo_category_id}
                      onChange={(e) => setFormData({ ...formData, fudo_category_id: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    >
                      <option value="">Sin vincular</option>
                      {fudoCategories.map((fudoCategory) => {
                        const owner = categories.find(
                          (c) => c.fudo_category_id === fudoCategory.id && c.id !== editingCategory?.id
                        );
                        return (
                          <option key={fudoCategory.id} value={fudoCategory.id}>
                            {fudoCategory.name}{owner ? ` (hoy en "${owner.name}")` : ''}
                          </option>
                        );
                      })}
                    </select>
                    <p className="text-xs text-gray-500 mt-1">
                      Los gastos de esa categoría de Fudo caen acá en la próxima sincronización
                      (salvo los que corregiste a mano).
                    </p>
                  </div>
                )}
```

- [ ] **Step 4: Build**

Run: `cd frontend && npm run build`
Expected: build sin errores.

- [ ] **Step 5: Verificación en el navegador**

Levantar backend y frontend con `preview_start` (configuraciones de `.claude/launch.json`; si no hay una para esta rama, crearla con el backend en el puerto 5001 sobre una SQLite de scratchpad y `vite` en 5173). Con un admin:
- `/expenses`: aparece "Sync Fudo"; abre el modal; con rango inválido muestra el error; sin credenciales de Fudo, sincronizar termina en "La sincronización falló: …" (el mensaje de `FudoClient`), sin romper la página.
- Un gasto con `source='fudo'` (crear uno vía SQL o con `Expense(source='fudo', ...)`) muestra el badge "Fudo".
- `/expense-categories` → editar: el selector de Fudo no aparece si `/fudo/categories` falla (sin credenciales) y el guardado sigue funcionando.
- Mirar `read_console_messages` (sin errores) y sacar una captura del modal con el resultado.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/Expenses.jsx frontend/src/pages/ExpenseCategories.jsx
git commit -m "feat(frontend): sync de gastos desde la página de Gastos, badge Fudo y vínculo de categorías"
```

---

### Task 10: Verificación final

**Files:** ninguno nuevo.

- [ ] **Step 1: Tests nuevos y vecinos**

Run: `cd backend && venv/Scripts/python.exe -m pytest tests/test_expense_fudo_models.py tests/test_expense_fudo_parsing.py tests/test_expense_fudo_linking.py tests/test_expense_sync.py tests/test_fudo_sync_runs.py tests/test_expense_overrides.py tests/test_migration_chain.py tests/test_suppliers.py tests/test_fudo_client_products.py tests/test_product_sync.py tests/test_route_access_coverage.py -v`
Expected: PASS.

- [ ] **Step 2: Suite completa contra la línea de base**

Run: `cd backend && venv/Scripts/python.exe -m pytest -q 2>&1 | tail -15`
Expected: las únicas fallas son las preexistentes listadas en Global Constraints (comparar nombres de archivo, no solo el total).

- [ ] **Step 3: Migración en Postgres (si hay Docker o un Postgres local)**

Run: `cd backend && flask db upgrade && flask db downgrade b4a0_add_fiscal_invoicing && flask db upgrade` contra un Postgres de prueba.
Expected: los tres comandos sin error. Si no hay Postgres disponible, dejarlo anotado como pendiente en el PR (igual que la migración `b2b0`).

- [ ] **Step 4: Frontend**

Run: `cd frontend && npx vitest run && npm run build`
Expected: PASS y build OK.
