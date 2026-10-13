# Caja y arqueo (sub-proyecto 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sesiones de caja con fondo, movimientos de efectivo (gasto, retiro, ingreso), cierre con arqueo visible por medio de pago e historial, sobre el POS nativo de Galia.

**Architecture:** Tablas propias (`cash_registers`, `cash_sessions`, `cash_movements`, `cash_session_counts`, `cash_events`) con la lógica en `services/pos/cash_service.py` y un blueprint `pos_cash`. Cada pago guarda la sesión abierta al registrarse y la sesión abierta al anularse. Lo esperado se calcula con consultas exactas por sesión. El frontend suma una pantalla "Caja" en `/pos`, el indicador en la barra, un aviso en el cobro y el historial en Galia.

**Tech Stack:** Flask, Flask-SQLAlchemy 3 / SQLAlchemy 2.0, Alembic, pytest (SQLite en memoria; PostgreSQL opcional para concurrencia). React 18, React Router 6, TanStack React Query 5, Tailwind (paleta Galia), lucide-react, axios, Vitest 1.6.

**Spec:** `docs/superpowers/specs/2026-10-13-pos-caja-arqueo-design.md`

## Global Constraints

- **Worktree:** `C:\Users\onofr\Desktop\galia-app\.claude\worktrees\pos-base`, rama `feature/pos-caja-arqueo` (sale de `main`). Las rutas del plan son relativas a esa raíz.
- **Python** (`PY`): `C:\Users\onofr\Desktop\galia-app\backend\venv\Scripts\python.exe`. Los tests corren con cwd = `backend/`: `PY -m pytest -q -p no:cacheprovider <archivos>`. Si Bash rechaza el comando, usar PowerShell (`Set-Location …\backend; & <PY> -m pytest …`).
- **Node:** con cwd = `frontend/` (`npm test`, `npm run build`, `npx vitest run <archivo>`). Nunca correr vitest desde la raíz del repo.
- **Encoding:** UTF-8 con acentos. Editar solo con Edit/Write.
- **Línea base del backend:** `PY scripts/compare_baseline.py <salida> ../docs/superpowers/plans/2026-10-08-pos-base-test-baseline.txt`. Criterio: `Sin fallas nuevas.`
- **Lint:** no hay configuración de ESLint. El frontend se verifica con `npm test` y `npm run build`.
- **Vitest:** entorno `node` y sin Testing Library. Solo se testea lógica pura; los tests importan con rutas relativas.
- **Dinero:**
  - en el backend: `Decimal` cuantizado a 0,01 con `pricing.money`; los montos entrantes se validan con `parse_decimal`, que levanta `ValueError` y la ruta lo convierte en 400;
  - en la API: los montos salen como `float`.
  - en el frontend: no calcula montos guardados; solo la diferencia en vivo del arqueo.
- **Errores:**
  - `PosError` (409 por defecto), `bad_request` (400), `forbidden` (403) y `not_found` (404), de `app.services.pos.errors`;
  - mensajes en castellano rioplatense.
- **Fechas:**
  - se guardan en UTC naive (`common.now()`);
  - el día de los filtros y del gasto es el de Argentina (`ARGENTINA_TZ`, `get_current_date_argentina`).
- **Permisos:**
  - abrir, cerrar, movimientos, historial, pagos sin caja y categorías: módulo `POS`;
  - `GET /registers`: `POS` o `Camarero`, porque el indicador lo ven todos;
  - anular movimiento y reabrir sesión: admin.
- **La caja (1b) y el celular (1c)** no cambian de comportamiento, salvo el aviso de "sin caja" en el cobro.
- **Commits:** terminan con la línea de atribución que pida el harness.

## Review Focus

1. **Arqueo con varios medios de efectivo** (dos medios con `kind = 'cash'`): los movimientos se aplican solo al primero por `position`, y el arqueo no duplica el fondo. Lo cubre la Task 3 (`test_movements_apply_to_first_cash_method_only`).
2. **Pago anulado en una sesión posterior al cierre:** descuenta en la sesión nueva y el resumen de la sesión cerrada no cambia. Lo cubre la Task 3.
3. **Cierre con un medio sin contar y sin movimiento:** se toma contado = esperado y no se crean filas en 0 para medios inactivos sin pagos. Lo cubre la Task 4.
4. **Filtro de historial por día de Argentina:** una sesión abierta a las 23:30 de Argentina (02:30 UTC del día siguiente) cae en el día de Argentina. Lo cubre la Task 4 (`test_list_sessions_uses_argentina_day`).
5. **Indicador de caja en el celular para un usuario `Camarero` sin `POS`:** `GET /registers` le responde 200, y el resto de la API de caja, 403. Lo cubre la Task 5.

## Mapa de archivos

**Backend**
- Create: `backend/app/models/pos/cash.py`: modelos de caja.
- Modify: `backend/app/models/pos/payments.py` (dos columnas), `backend/app/models/pos/__init__.py` (exports).
- Create: `backend/migrations/versions/b2a0_add_cash_registers.py`.
- Create: `backend/app/services/pos/cash_service.py`, `backend/app/services/pos/cash_serializers.py`.
- Modify: `backend/app/services/pos/payment_service.py` (asignación de sesión).
- Create: `backend/app/routes/pos_cash.py`. Modify: `backend/app/__init__.py` (registro), `backend/app/routes/pos_floor.py` (`cash_version` en `/changes`).
- Tests:
  - `backend/tests/cash_helpers.py`;
  - `test_pos_cash_models.py`, `test_pos_cash_service.py`, `test_pos_cash_payments.py`, `test_pos_cash_close.py`, `test_pos_cash_api.py`, `test_pos_cash_concurrency_pg.py`;
  - `test_migration_chain.py` (modificado).

**Frontend**
- Modify: `frontend/src/pos/api/posApi.js` (`posCashApi`), `frontend/src/pos/hooks/keys.js`, `frontend/src/pos/hooks/usePosChanges.js`, `frontend/src/pos/utils/changes.js` (+ test).
- Create: `frontend/src/pos/hooks/useCash.js`, `frontend/src/pos/utils/cashMath.js` (+ test).
- Create: `frontend/src/pos/cash/`: `CashPage.jsx`, `CashSummaryCards.jsx`, `MovementList.jsx`, `OpenSessionModal.jsx`, `MovementModal.jsx`, `CloseSessionModal.jsx`, `CashStatusBadge.jsx`.
- Modify: `frontend/src/pos/layout/PosTopBar.jsx`, `frontend/src/pos/modals/PaymentModal.jsx`, `frontend/src/App.jsx`, `frontend/src/components/layout/Sidebar.jsx`.
- Create: `frontend/src/pages/CashSessions.jsx`, `frontend/src/pages/CashSessionDetail.jsx`.

---

### Task 1: Modelos y migración

**Files:**
- Create: `backend/app/models/pos/cash.py`
- Modify: `backend/app/models/pos/payments.py`, `backend/app/models/pos/__init__.py`
- Create: `backend/migrations/versions/b2a0_add_cash_registers.py`
- Create: `backend/tests/cash_helpers.py`
- Test: `backend/tests/test_pos_cash_models.py`, `backend/tests/test_migration_chain.py`

**Interfaces:**
- Produces:
  - modelos `CashRegister`, `CashSession`, `CashMovement`, `CashSessionCount`, `CashEvent` y constantes `CASH_MOVEMENT_KINDS`, `CASH_SESSION_STATUSES`, exportados en `app.models.pos`;
  - columnas `PosPayment.cash_session_id` y `PosPayment.cancel_cash_session_id`;
  - relaciones: `CashSession.register`, `.opener`, `.closer`, `.movements` (orden por id) y `.counts` (orden por id, `cascade='all, delete-orphan'`); `CashMovement.session`, `.creator`; `CashEvent.user`;
  - helpers de test `make_register(name='Caja principal')` y `make_methods()`, que devuelve `SimpleNamespace(efectivo, debito)`.

- [ ] **Step 1: Tests que fallan.** Crear `backend/tests/cash_helpers.py`:

```python
"""Fábricas compartidas por los tests de caja."""
from types import SimpleNamespace

from app.extensions import db
from app.models.pos import CashRegister, PaymentMethod


def make_register(name='Caja principal'):
    register = CashRegister(name=name)
    db.session.add(register)
    db.session.commit()
    return register


def make_methods():
    efectivo = PaymentMethod(name='Efectivo', kind='cash', position=0)
    debito = PaymentMethod(name='Débito', kind='card', position=1)
    db.session.add_all([efectivo, debito])
    db.session.commit()
    return SimpleNamespace(efectivo=efectivo, debito=debito)
```

Crear `backend/tests/test_pos_cash_models.py`:

```python
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.pos import CashSession
from cash_helpers import make_register
from pos_helpers import make_user, pos_app  # noqa: F401


def _session(register, user, status='open'):
    return CashSession(register_id=register.id, status=status, opened_at=datetime.utcnow(), opened_by=user.id,
                       opening_float=Decimal('0'))


def test_only_one_open_session_per_register(pos_app):
    user = make_user('caja@test.com', modules=('POS',))
    register = make_register()
    db.session.add(_session(register, user))
    db.session.commit()
    db.session.add(_session(register, user))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_closed_sessions_do_not_block_a_new_open_one(pos_app):
    user = make_user('caja@test.com', modules=('POS',))
    register = make_register()
    other = make_register('Barra')
    db.session.add_all([_session(register, user, 'closed'), _session(register, user, 'closed'),
                        _session(register, user), _session(other, user)])
    db.session.commit()
    assert CashSession.query.filter_by(status='open').count() == 2
```

En `backend/tests/test_migration_chain.py` agregar al final:

```python
def test_cash_registers_follows_cash_ui_support():
    assert _revisions()['b2a0_add_cash_registers'] == ['b1b1_add_pos_cash_ui_support']
```

- [ ] **Step 2: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_pos_cash_models.py tests/test_migration_chain.py`
Expected: ImportError (`CashSession`) y `KeyError: 'b2a0_add_cash_registers'`.

- [ ] **Step 3: Modelos.** Crear `backend/app/models/pos/cash.py`:

```python
from app.extensions import db

CASH_SESSION_STATUSES = ('open', 'closed')
CASH_MOVEMENT_KINDS = ('opening_float', 'expense', 'withdrawal', 'deposit')


class CashRegister(db.Model):
    __tablename__ = 'cash_registers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False, unique=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)


class CashSession(db.Model):
    __tablename__ = 'cash_sessions'
    # Una sola sesión abierta por caja; el servicio además lo valida con bloqueo de fila.
    __table_args__ = (
        db.Index('uq_cash_sessions_open_register', 'register_id', unique=True,
                 postgresql_where=db.text("status = 'open'"), sqlite_where=db.text("status = 'open'")),
    )

    id = db.Column(db.Integer, primary_key=True)
    register_id = db.Column(db.Integer, db.ForeignKey('cash_registers.id'), nullable=False, index=True)
    status = db.Column(db.String(10), nullable=False, default='open')
    opened_at = db.Column(db.DateTime, nullable=False)
    opened_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    opening_float = db.Column(db.Numeric(12, 2), nullable=False)
    closed_at = db.Column(db.DateTime, nullable=True)
    closed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    closing_note = db.Column(db.String(500), nullable=True)

    register = db.relationship('CashRegister')
    opener = db.relationship('User', foreign_keys=[opened_by])
    closer = db.relationship('User', foreign_keys=[closed_by])
    movements = db.relationship('CashMovement', back_populates='session', order_by='CashMovement.id')
    counts = db.relationship('CashSessionCount', back_populates='session', order_by='CashSessionCount.id',
                             cascade='all, delete-orphan')


class CashMovement(db.Model):
    __tablename__ = 'cash_movements'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('cash_sessions.id'), nullable=False, index=True)
    kind = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    cancelled_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancel_reason = db.Column(db.String(255), nullable=True)

    session = db.relationship('CashSession', back_populates='movements')
    creator = db.relationship('User', foreign_keys=[created_by])

    @property
    def is_active(self):
        return self.cancelled_at is None


class CashSessionCount(db.Model):
    __tablename__ = 'cash_session_counts'
    __table_args__ = (db.UniqueConstraint('session_id', 'payment_method_id', name='uq_cash_session_counts_method'),)

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('cash_sessions.id'), nullable=False)
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_methods.id'), nullable=False)
    method_name = db.Column(db.String(50), nullable=False)
    expected = db.Column(db.Numeric(12, 2), nullable=False)
    counted = db.Column(db.Numeric(12, 2), nullable=False)
    difference = db.Column(db.Numeric(12, 2), nullable=False)

    session = db.relationship('CashSession', back_populates='counts')


class CashEvent(db.Model):
    __tablename__ = 'cash_events'

    id = db.Column(db.Integer, primary_key=True)
    register_id = db.Column(db.Integer, db.ForeignKey('cash_registers.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('cash_sessions.id'), nullable=True, index=True)
    kind = db.Column(db.String(30), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    payload = db.Column(db.JSON, nullable=False, default=dict)

    user = db.relationship('User')
```

En `backend/app/models/pos/payments.py`, dentro de `PosPayment`, después de `cancel_reason_id`:

```python
    # Sesión de caja abierta al registrar el pago y al anularlo (nulas: sin caja).
    cash_session_id = db.Column(db.Integer, db.ForeignKey('cash_sessions.id'), nullable=True, index=True)
    cancel_cash_session_id = db.Column(db.Integer, db.ForeignKey('cash_sessions.id'), nullable=True, index=True)
```

En `backend/app/models/pos/__init__.py`, agregar después de la línea de `CancelReason`:

```python
from app.models.pos.cash import (CASH_MOVEMENT_KINDS, CASH_SESSION_STATUSES, CashEvent, CashMovement, CashRegister,
                                 CashSession, CashSessionCount)
```

Y sumar a `__all__`: `'CashRegister', 'CashSession', 'CashMovement', 'CashSessionCount', 'CashEvent', 'CASH_MOVEMENT_KINDS', 'CASH_SESSION_STATUSES'`.

- [ ] **Step 4: Migración.** Crear `backend/migrations/versions/b2a0_add_cash_registers.py`:

```python
"""add cash registers, sessions, movements, counts and events; cash session on POS payments

Revision ID: b2a0_add_cash_registers
Revises: b1b1_add_pos_cash_ui_support
Create Date: 2026-10-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b2a0_add_cash_registers'
down_revision = 'b1b1_add_pos_cash_ui_support'
branch_labels = None
depends_on = None

OPEN_ONLY = "status = 'open'"


def upgrade():
    registers = op.create_table(
        'cash_registers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=60), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_table(
        'cash_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('register_id', sa.Integer(), sa.ForeignKey('cash_registers.id'), nullable=False),
        sa.Column('status', sa.String(length=10), nullable=False),
        sa.Column('opened_at', sa.DateTime(), nullable=False),
        sa.Column('opened_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('opening_float', sa.Numeric(12, 2), nullable=False),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('closed_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('closing_note', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cash_sessions_register_id', 'cash_sessions', ['register_id'])
    op.create_index('uq_cash_sessions_open_register', 'cash_sessions', ['register_id'], unique=True,
                    postgresql_where=sa.text(OPEN_ONLY), sqlite_where=sa.text(OPEN_ONLY))
    op.create_table(
        'cash_movements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('cash_sessions.id'), nullable=False),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('expense_id', sa.Integer(), sa.ForeignKey('expenses.id'), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('cancelled_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancel_reason', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cash_movements_session_id', 'cash_movements', ['session_id'])
    op.create_table(
        'cash_session_counts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('cash_sessions.id'), nullable=False),
        sa.Column('payment_method_id', sa.Integer(), sa.ForeignKey('payment_methods.id'), nullable=False),
        sa.Column('method_name', sa.String(length=50), nullable=False),
        sa.Column('expected', sa.Numeric(12, 2), nullable=False),
        sa.Column('counted', sa.Numeric(12, 2), nullable=False),
        sa.Column('difference', sa.Numeric(12, 2), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'payment_method_id', name='uq_cash_session_counts_method'),
    )
    op.create_table(
        'cash_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('register_id', sa.Integer(), sa.ForeignKey('cash_registers.id'), nullable=False),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('cash_sessions.id'), nullable=True),
        sa.Column('kind', sa.String(length=30), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cash_events_session_id', 'cash_events', ['session_id'])
    with op.batch_alter_table('pos_payments') as batch:
        batch.add_column(sa.Column('cash_session_id', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('cancel_cash_session_id', sa.Integer(), nullable=True))
        batch.create_foreign_key('fk_pos_payments_cash_session_id', 'cash_sessions', ['cash_session_id'], ['id'])
        batch.create_foreign_key('fk_pos_payments_cancel_cash_session_id', 'cash_sessions',
                                 ['cancel_cash_session_id'], ['id'])
        batch.create_index('ix_pos_payments_cash_session_id', ['cash_session_id'])
        batch.create_index('ix_pos_payments_cancel_cash_session_id', ['cancel_cash_session_id'])
    op.bulk_insert(registers, [{'name': 'Caja principal', 'position': 0, 'is_active': True}])


def downgrade():
    with op.batch_alter_table('pos_payments') as batch:
        batch.drop_index('ix_pos_payments_cancel_cash_session_id')
        batch.drop_index('ix_pos_payments_cash_session_id')
        batch.drop_constraint('fk_pos_payments_cancel_cash_session_id', type_='foreignkey')
        batch.drop_constraint('fk_pos_payments_cash_session_id', type_='foreignkey')
        batch.drop_column('cancel_cash_session_id')
        batch.drop_column('cash_session_id')
    op.drop_index('ix_cash_events_session_id', table_name='cash_events')
    op.drop_table('cash_events')
    op.drop_table('cash_session_counts')
    op.drop_index('ix_cash_movements_session_id', table_name='cash_movements')
    op.drop_table('cash_movements')
    op.drop_index('uq_cash_sessions_open_register', table_name='cash_sessions')
    op.drop_index('ix_cash_sessions_register_id', table_name='cash_sessions')
    op.drop_table('cash_sessions')
    op.drop_table('cash_registers')
```

- [ ] **Step 5: Correr**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_pos_cash_models.py tests/test_migration_chain.py tests/test_pos_models.py tests/test_pos_payments.py`
Expected: todos pasan.

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/pos backend/migrations/versions/b2a0_add_cash_registers.py backend/tests/cash_helpers.py backend/tests/test_pos_cash_models.py backend/tests/test_migration_chain.py
git commit -m "feat(pos): add cash register models and migration"
```

---

### Task 2: Servicio de caja: abrir, movimientos, anular y resumen

**Files:**
- Create: `backend/app/services/pos/cash_service.py`
- Test: `backend/tests/test_pos_cash_service.py`

**Interfaces:**
- Consumes: modelos de la Task 1; `common.now`, `common.parse_id`, `common.require_reason`, `common.MAX_MONEY`, `pricing.money`, `audit._jsonable`.
- Produces (`app.services.pos.cash_service`):
  - `current_session_id() -> int | None`;
  - `open_session(user, register_id, opening_float) -> CashSession`;
  - `add_movement(user, session_id, kind, amount, reason, category_id=None, supplier_id=None) -> CashSession`;
  - `cancel_movement(user, movement_id, reason) -> CashSession`;
  - `load_session(session_id, lock=False) -> CashSession`;
  - `expected_lines(session) -> list[Line]`, donde `Line(method, collected, cancelled, expected)` usa `Decimal`;
  - `open_sales_count() -> int`;
  - `session_summary(session) -> dict`, listo para JSON, con esta forma:
    ```
    {"methods": [{"payment_method_id", "method_name", "kind", "collected", "cancelled", "expected"}],
     "cash": {"payment_method_id", "opening_float", "sales", "cancelled", "expenses", "withdrawals", "deposits", "expected"},
     "collected_net": float, "open_sales": int}
    ```

- [ ] **Step 1: Tests que fallan.** Crear `backend/tests/test_pos_cash_service.py`:

```python
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import Expense, ExpenseCategory, Supplier
from app.models.pos import CashEvent, CashMovement
from app.services.pos import cash_service
from app.services.pos.errors import PosError
from cash_helpers import make_methods, make_register
from pos_helpers import make_user, pos_app  # noqa: F401


@pytest.fixture
def cashier(pos_app):
    return make_user('caja@test.com', modules=('POS',))


def _category(name='Insumos'):
    category = ExpenseCategory(name=name)
    db.session.add(category)
    db.session.commit()
    return category


def test_open_session_records_float_movement_and_event(cashier):
    register = make_register()
    session = cash_service.open_session(cashier, register.id, '1500')
    assert session.status == 'open' and session.opening_float == Decimal('1500.00')
    assert [(m.kind, m.amount) for m in session.movements] == [('opening_float', Decimal('1500.00'))]
    assert [e.kind for e in CashEvent.query.all()] == ['opened']
    assert cash_service.current_session_id() == session.id


def test_open_twice_is_conflict(cashier):
    register = make_register()
    cash_service.open_session(cashier, register.id, 0)
    with pytest.raises(PosError) as error:
        cash_service.open_session(cashier, register.id, 0)
    assert error.value.status == 409


@pytest.mark.parametrize('value', ['-1', 'abc', None])
def test_open_rejects_invalid_float(cashier, value):
    register = make_register()
    with pytest.raises(ValueError):
        cash_service.open_session(cashier, register.id, value)


def test_open_inactive_register_is_bad_request(cashier):
    register = make_register()
    register.is_active = False
    db.session.commit()
    with pytest.raises(PosError) as error:
        cash_service.open_session(cashier, register.id, 0)
    assert error.value.status == 400


def test_current_session_needs_exactly_one_open(cashier):
    assert cash_service.current_session_id() is None
    first = cash_service.open_session(cashier, make_register().id, 0)
    assert cash_service.current_session_id() == first.id
    cash_service.open_session(cashier, make_register('Barra').id, 0)
    assert cash_service.current_session_id() is None


def test_movements_feed_the_cash_breakdown(cashier):
    methods = make_methods()
    category = _category()
    session = cash_service.open_session(cashier, make_register().id, '1000')
    cash_service.add_movement(cashier, session.id, 'deposit', '500', 'Cambio')
    cash_service.add_movement(cashier, session.id, 'withdrawal', '300', 'Depósito al banco')
    cash_service.add_movement(cashier, session.id, 'expense', '200', 'Hielo', category_id=category.id)
    summary = cash_service.session_summary(session)
    assert summary['cash'] == {'payment_method_id': methods.efectivo.id, 'opening_float': 1000.0, 'sales': 0.0,
                               'cancelled': 0.0, 'expenses': 200.0, 'withdrawals': 300.0, 'deposits': 500.0,
                               'expected': 1000.0}
    cash_line = next(m for m in summary['methods'] if m['kind'] == 'cash')
    assert cash_line['expected'] == 1000.0
    assert summary['collected_net'] == 0.0 and summary['open_sales'] == 0


def test_expense_movement_creates_a_cash_expense(cashier):
    category = _category()
    supplier = Supplier(name='Lácteos SA')
    db.session.add(supplier)
    db.session.commit()
    session = cash_service.open_session(cashier, make_register().id, 0)
    cash_service.add_movement(cashier, session.id, 'expense', '250.5', 'Leche', category_id=category.id,
                              supplier_id=supplier.id)
    expense = Expense.query.one()
    assert (expense.importe, expense.de_caja, expense.caja, expense.medio_pago, expense.estado_pago,
            expense.category_id, expense.supplier_id, expense.proveedor, expense.comentario, expense.creado_por,
            expense.cancelado) == (Decimal('250.50'), True, 'Caja principal', 'Efectivo', 'Pagado', category.id,
                                   supplier.id, 'Lácteos SA', 'Leche', 'caja@test.com', False)
    assert CashMovement.query.filter_by(kind='expense').one().expense_id == expense.id


@pytest.mark.parametrize('kwargs, status', [
    ({'kind': 'gift', 'amount': '10', 'reason': 'x'}, 400),
    ({'kind': 'deposit', 'amount': '10', 'reason': '  '}, 400),
    ({'kind': 'expense', 'amount': '10', 'reason': 'x', 'category_id': 999}, 400),
])
def test_movement_validation(cashier, kwargs, status):
    session = cash_service.open_session(cashier, make_register().id, 0)
    with pytest.raises(PosError) as error:
        cash_service.add_movement(cashier, session.id, **kwargs)
    assert error.value.status == status


def test_movement_amount_must_be_positive(cashier):
    session = cash_service.open_session(cashier, make_register().id, 0)
    with pytest.raises(ValueError):
        cash_service.add_movement(cashier, session.id, 'deposit', '0', 'Cambio')


def test_movement_on_closed_session_is_conflict(cashier):
    session = cash_service.open_session(cashier, make_register().id, 0)
    session.status = 'closed'
    db.session.commit()
    with pytest.raises(PosError) as error:
        cash_service.add_movement(cashier, session.id, 'deposit', '10', 'Cambio')
    assert error.value.status == 409


def test_cancel_movement_is_admin_only_and_cancels_the_expense(cashier):
    admin = make_user('admin@test.com', role='admin')
    make_methods()
    category = _category()
    session = cash_service.open_session(cashier, make_register().id, '100')
    session = cash_service.add_movement(cashier, session.id, 'expense', '40', 'Hielo', category_id=category.id)
    movement = session.movements[-1]
    with pytest.raises(PosError) as error:
        cash_service.cancel_movement(cashier, movement.id, 'Error')
    assert error.value.status == 403
    session = cash_service.cancel_movement(admin, movement.id, 'Error de carga')
    assert movement.cancelled_at is not None and movement.cancel_reason == 'Error de carga'
    assert Expense.query.one().cancelado is True
    assert cash_service.session_summary(session)['cash']['expected'] == 100.0
    assert [e.kind for e in CashEvent.query.order_by(CashEvent.id)] == ['opened', 'movement_added',
                                                                        'movement_cancelled']


def test_cancel_movement_rules(cashier):
    admin = make_user('admin@test.com', role='admin')
    session = cash_service.open_session(cashier, make_register().id, '100')
    opening = session.movements[0]
    with pytest.raises(PosError) as error:
        cash_service.cancel_movement(admin, opening.id, 'x')
    assert error.value.status == 409
    session = cash_service.add_movement(cashier, session.id, 'deposit', '10', 'Cambio')
    deposit = session.movements[-1]
    session.status = 'closed'
    db.session.commit()
    with pytest.raises(PosError) as error:
        cash_service.cancel_movement(admin, deposit.id, 'x')
    assert error.value.status == 409
```

- [ ] **Step 2: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_pos_cash_service.py`
Expected: `ImportError: cannot import name 'cash_service'`.

- [ ] **Step 3: Implementar.** Crear `backend/app/services/pos/cash_service.py`:

```python
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


def _event(register_id, session_id, user, kind, **payload):
    db.session.add(CashEvent(register_id=register_id, session_id=session_id, user_id=user.id, kind=kind,
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
```

- [ ] **Step 4: Correr**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_pos_cash_service.py`
Expected: todos pasan.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/pos/cash_service.py backend/tests/test_pos_cash_service.py
git commit -m "feat(pos): cash sessions, movements and summary service"
```

---

### Task 3: Pagos asociados a la sesión de caja

**Files:**
- Modify: `backend/app/services/pos/payment_service.py` (`add_payment`, `cancel_payment`)
- Test: `backend/tests/test_pos_cash_payments.py`

**Interfaces:**
- Consumes: `cash_service.current_session_id()`, `cash_service.session_summary`, `cash_service.open_session` (Task 2).
- Produces: `PosPayment.cash_session_id` y `PosPayment.cancel_cash_session_id` completados por el cobro y la anulación.

- [ ] **Step 1: Tests que fallan.** Crear `backend/tests/test_pos_cash_payments.py`:

```python
import pytest

from app.extensions import db
from app.models.pos import PaymentMethod, PosPayment
from app.services.pos import cash_service, payment_service, sale_service
from cash_helpers import make_register
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401


@pytest.fixture
def ctx(pos_app):
    user = make_user('caja@test.com', modules=('POS', 'Anular'))
    cat = make_catalog()
    _salon, t1, t2 = make_floor()
    return user, cat, (t1, t2)


def _billed_sale(user, cat, table):
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=1)
    sale_service.add_item(user, sale.id, cat.unidad.id)  # $900
    sale_service.confirm_batch(user, sale.id)
    sale_service.request_bill(user, sale.id)
    return sale


def _close(session):
    session.status = 'closed'
    db.session.commit()


def test_payment_takes_the_open_session(ctx):
    user, cat, (t1, _t2) = ctx
    session = cash_service.open_session(user, make_register().id, 0)
    sale = _billed_sale(user, cat, t1)
    payment_service.add_payment(user, sale.id, cat.efectivo.id, 900, tendered=1000)
    assert PosPayment.query.one().cash_session_id == session.id


def test_payment_without_open_session_has_no_session(ctx):
    user, cat, (t1, _t2) = ctx
    sale = _billed_sale(user, cat, t1)
    payment_service.add_payment(user, sale.id, cat.efectivo.id, 900)
    assert PosPayment.query.one().cash_session_id is None


def test_payment_with_two_open_registers_has_no_session(ctx):
    user, cat, (t1, _t2) = ctx
    cash_service.open_session(user, make_register().id, 0)
    cash_service.open_session(user, make_register('Barra').id, 0)
    sale = _billed_sale(user, cat, t1)
    payment_service.add_payment(user, sale.id, cat.efectivo.id, 900)
    assert PosPayment.query.one().cash_session_id is None


def test_summary_counts_applied_amount_not_tendered(ctx):
    user, cat, (t1, t2) = ctx
    session = cash_service.open_session(user, make_register().id, '1000')
    payment_service.add_payment(user, _billed_sale(user, cat, t1).id, cat.efectivo.id, 900, tendered=2000)
    payment_service.add_payment(user, _billed_sale(user, cat, t2).id, cat.debito.id, 900)
    summary = cash_service.session_summary(session)
    by_name = {m['method_name']: m for m in summary['methods']}
    assert by_name['Efectivo']['collected'] == 900.0 and by_name['Efectivo']['expected'] == 1900.0
    assert by_name['Débito']['expected'] == 900.0
    assert summary['cash']['sales'] == 900.0 and summary['cash']['expected'] == 1900.0
    assert summary['collected_net'] == 1800.0


def test_cancel_in_same_session_nets_zero(ctx):
    user, cat, (t1, _t2) = ctx
    session = cash_service.open_session(user, make_register().id, 0)
    sale = payment_service.add_payment(user, _billed_sale(user, cat, t1).id, cat.debito.id, 900)
    payment_service.cancel_payment(user, sale.payments[0].id, 'Error')
    payment = PosPayment.query.one()
    assert payment.cancel_cash_session_id == session.id
    debit = next(m for m in cash_service.session_summary(session)['methods'] if m['method_name'] == 'Débito')
    assert (debit['collected'], debit['cancelled'], debit['expected']) == (900.0, 900.0, 0.0)


def test_cancel_after_close_hits_the_new_session_only(ctx):
    user, cat, (t1, _t2) = ctx
    register = make_register()
    first = cash_service.open_session(user, register.id, 0)
    sale = payment_service.add_payment(user, _billed_sale(user, cat, t1).id, cat.efectivo.id, 900)
    before = cash_service.session_summary(first)
    _close(first)
    second = cash_service.open_session(user, register.id, '500')
    payment_service.cancel_payment(user, sale.payments[0].id, 'Devolución')
    assert cash_service.session_summary(first)['methods'] == before['methods']
    cash = cash_service.session_summary(second)['cash']
    assert (cash['sales'], cash['cancelled'], cash['expected']) == (0.0, 900.0, -400.0)


def test_movements_apply_to_first_cash_method_only(ctx):
    user, cat, (t1, _t2) = ctx
    vales = PaymentMethod(name='Vales', kind='cash', position=9)
    db.session.add(vales)
    db.session.commit()
    session = cash_service.open_session(user, make_register().id, '300')
    payment_service.add_payment(user, _billed_sale(user, cat, t1).id, vales.id, 900)
    by_name = {m['method_name']: m for m in cash_service.session_summary(session)['methods']}
    assert by_name['Efectivo']['expected'] == 300.0
    assert by_name['Vales']['expected'] == 900.0
```

- [ ] **Step 2: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_pos_cash_payments.py`
Expected: fallan los tests que miran `cash_session_id` y `cancel_cash_session_id` (quedan en `None`), y los de resumen dan 0 en lo cobrado.

- [ ] **Step 3: Implementar.** En `backend/app/services/pos/payment_service.py`:

Agregar el import (junto a los de `app.services.pos`):

```python
from app.services.pos.cash_service import current_session_id
```

En `add_payment`, reemplazar la creación del pago por:

```python
    payment = PosPayment(payment_method_id=method.id, method_name=method.name, amount=amount, tendered=tendered,
                         change=change, client_request_id=request_id, created_by=user.id, created_at=now(),
                         cash_session_id=current_session_id())
```

En `cancel_payment`, después de `payment.cancel_reason_id = reason_id`:

```python
    payment.cancel_cash_session_id = current_session_id()
```

Comprobar que no hay import circular: `cash_service` no importa `payment_service`.

- [ ] **Step 4: Correr**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_pos_cash_payments.py tests/test_pos_payments.py tests/test_pos_hardening.py tests/test_pos_final_review.py`
Expected: todos pasan.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/pos/payment_service.py backend/tests/test_pos_cash_payments.py
git commit -m "feat(pos): attach payments and cancellations to the open cash session"
```

---

### Task 4: Cerrar, reabrir, historial y pagos sin caja

**Files:**
- Modify: `backend/app/services/pos/cash_service.py`
- Test: `backend/tests/test_pos_cash_close.py`

**Interfaces:**
- Consumes: `load_session`, `expected_lines`, `open_sales_count`, `_load_register`, `_event`, `_money`, `_require_admin`, `ZERO` (Task 2).
- Produces:
  - `close_session(user, session_id, counts, note) -> CashSession`;
  - `reopen_session(user, session_id, reason) -> CashSession`;
  - `argentina_day_bounds(from_date, to_date) -> (datetime, datetime)` en UTC naive, con el fin excluido;
  - `list_sessions(from_date, to_date, register_id=None, page=1, per_page=50) -> dict` con `{'sessions': [row], 'total', 'page', 'pages'}`, donde cada fila es `{'id', 'register': {'id', 'name'}, 'status', 'opened_at', 'opened_by': {'id', 'name'}, 'closed_at', 'closed_by', 'collected_net', 'cash_difference'}`;
  - `unassigned_payments(from_date, to_date) -> list[dict]`, cada uno `{'id', 'sale_id', 'sale_number', 'table', 'method_name', 'amount', 'created_by': {'id', 'name'}, 'created_at', 'cancelled'}`.

- [ ] **Step 1: Tests que fallan.** Crear `backend/tests/test_pos_cash_close.py`:

```python
from datetime import date, datetime, timedelta

import pytest

from app.extensions import db
from app.models.pos import CashEvent, CashSessionCount
from app.services.pos import cash_service, payment_service, sale_service
from app.services.pos.errors import PosError
from cash_helpers import make_register
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401


@pytest.fixture
def ctx(pos_app):
    user = make_user('caja@test.com', modules=('POS',))
    admin = make_user('admin@test.com', role='admin')
    cat = make_catalog()
    _salon, t1, t2 = make_floor()
    return user, admin, cat, (t1, t2)


def _paid(user, cat, table, method, tendered=None):
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=1)
    sale_service.add_item(user, sale.id, cat.unidad.id)  # $900
    sale_service.confirm_batch(user, sale.id)
    sale_service.request_bill(user, sale.id)
    return payment_service.add_payment(user, sale.id, method.id, 900, tendered=tendered)


def test_close_is_blocked_while_sales_are_open(ctx):
    user, _admin, cat, (t1, _t2) = ctx
    session = cash_service.open_session(user, make_register().id, 0)
    sale_service.open_sale(user, 'salon', table_id=t1.id, people=1)
    with pytest.raises(PosError) as error:
        cash_service.close_session(user, session.id, [{'payment_method_id': cat.efectivo.id, 'counted': 0}], None)
    assert error.value.status == 409 and error.value.extra == {'open_sales': 1}
    assert 'Hay 1 ventas abiertas' in error.value.message


def test_close_stores_counts_with_server_expected(ctx):
    user, _admin, cat, (t1, t2) = ctx
    session = cash_service.open_session(user, make_register().id, '1000')
    _paid(user, cat, t1, cat.efectivo, tendered=1000)
    _paid(user, cat, t2, cat.debito)
    session = cash_service.close_session(user, session.id, [
        {'payment_method_id': cat.efectivo.id, 'counted': '1850'},
        {'payment_method_id': cat.debito.id, 'counted': 900},
    ], 'Faltan 50 en el cambio')
    assert session.status == 'closed' and session.closed_by == user.id
    assert session.closing_note == 'Faltan 50 en el cambio'
    rows = {c.method_name: (float(c.expected), float(c.counted), float(c.difference)) for c in session.counts}
    assert rows == {'Efectivo': (1900.0, 1850.0, -50.0), 'Débito': (900.0, 900.0, 0.0)}
    event = CashEvent.query.filter_by(kind='closed').one()
    assert event.payload['differences'] == {'Efectivo': '-50.00', 'Débito': '0.00'}


def test_note_is_required_with_a_difference(ctx):
    user, _admin, cat, _tables = ctx
    session = cash_service.open_session(user, make_register().id, '100')
    with pytest.raises(PosError) as error:
        cash_service.close_session(user, session.id, [{'payment_method_id': cat.efectivo.id, 'counted': 90}], '  ')
    assert error.value.status == 400


def test_omitted_methods_count_as_expected_and_cash_is_required(ctx):
    user, _admin, cat, (t1, _t2) = ctx
    session = cash_service.open_session(user, make_register().id, '100')
    _paid(user, cat, t1, cat.debito)
    with pytest.raises(PosError) as error:
        cash_service.close_session(user, session.id, [{'payment_method_id': cat.debito.id, 'counted': 900}], None)
    assert error.value.status == 400
    session = cash_service.close_session(user, session.id, [{'payment_method_id': cat.efectivo.id, 'counted': 100}],
                                         None)
    rows = {c.method_name: float(c.counted) for c in session.counts}
    assert rows == {'Efectivo': 100.0, 'Débito': 900.0}


def test_inactive_unused_methods_get_no_count_row(ctx):
    user, _admin, cat, _tables = ctx
    cat.debito.is_active = False
    db.session.commit()
    session = cash_service.open_session(user, make_register().id, '0')
    session = cash_service.close_session(user, session.id, [{'payment_method_id': cat.efectivo.id, 'counted': 0}],
                                         None)
    assert [c.method_name for c in session.counts] == ['Efectivo']


def test_unknown_method_and_double_close(ctx):
    user, _admin, cat, _tables = ctx
    session = cash_service.open_session(user, make_register().id, '0')
    with pytest.raises(PosError) as error:
        cash_service.close_session(user, session.id, [{'payment_method_id': 999, 'counted': 0}], None)
    assert error.value.status == 400
    cash_service.close_session(user, session.id, [{'payment_method_id': cat.efectivo.id, 'counted': 0}], None)
    with pytest.raises(PosError) as error:
        cash_service.close_session(user, session.id, [{'payment_method_id': cat.efectivo.id, 'counted': 0}], None)
    assert error.value.status == 409


def test_reopen_is_admin_only_and_clears_counts(ctx):
    user, admin, cat, _tables = ctx
    register = make_register()
    session = cash_service.open_session(user, register.id, '0')
    cash_service.close_session(user, session.id, [{'payment_method_id': cat.efectivo.id, 'counted': 0}], None)
    with pytest.raises(PosError) as error:
        cash_service.reopen_session(user, session.id, 'Error')
    assert error.value.status == 403
    session = cash_service.reopen_session(admin, session.id, 'Faltó un gasto')
    assert session.status == 'open' and session.closed_at is None and session.closing_note is None
    assert CashSessionCount.query.count() == 0
    assert CashEvent.query.order_by(CashEvent.id.desc()).first().kind == 'reopened'


def test_reopen_conflicts_with_another_open_session(ctx):
    user, admin, cat, _tables = ctx
    register = make_register()
    first = cash_service.open_session(user, register.id, '0')
    cash_service.close_session(user, first.id, [{'payment_method_id': cat.efectivo.id, 'counted': 0}], None)
    cash_service.open_session(user, register.id, '0')
    with pytest.raises(PosError) as error:
        cash_service.reopen_session(admin, first.id, 'x')
    assert error.value.status == 409


def test_list_sessions_filters_and_totals(ctx):
    user, _admin, cat, (t1, _t2) = ctx
    register = make_register()
    old = cash_service.open_session(user, register.id, '0')
    cash_service.close_session(user, old.id, [{'payment_method_id': cat.efectivo.id, 'counted': 10}], 'sobra')
    old.opened_at = datetime.utcnow() - timedelta(days=10)
    db.session.commit()
    today = cash_service.open_session(user, register.id, '0')
    _paid(user, cat, t1, cat.efectivo)
    day = date.today()
    result = cash_service.list_sessions(day - timedelta(days=1), day + timedelta(days=1))
    assert [row['id'] for row in result['sessions']] == [today.id]
    assert result['sessions'][0]['collected_net'] == 900.0 and result['sessions'][0]['cash_difference'] is None
    result = cash_service.list_sessions(day - timedelta(days=30), day + timedelta(days=1))
    assert [row['id'] for row in result['sessions']] == [today.id, old.id]
    assert result['sessions'][1]['cash_difference'] == 10.0 and result['total'] == 2 and result['pages'] == 1


def test_list_sessions_uses_argentina_day(ctx):
    user, _admin, _cat, _tables = ctx
    session = cash_service.open_session(user, make_register().id, '0')
    session.opened_at = datetime(2026, 10, 14, 2, 30)  # 23:30 del 13 en Argentina
    db.session.commit()
    assert [r['id'] for r in cash_service.list_sessions(date(2026, 10, 13), date(2026, 10, 13))['sessions']] == [
        session.id]
    assert cash_service.list_sessions(date(2026, 10, 14), date(2026, 10, 14))['sessions'] == []


def test_unassigned_payments_by_date(ctx):
    user, _admin, cat, (t1, t2) = ctx
    _paid(user, cat, t1, cat.efectivo)
    cash_service.open_session(user, make_register().id, '0')
    _paid(user, cat, t2, cat.debito)
    day = date.today()
    rows = cash_service.unassigned_payments(day - timedelta(days=1), day + timedelta(days=1))
    assert [(r['method_name'], r['amount'], r['table']) for r in rows] == [('Efectivo', 900.0, 'Mesa 1')]
```

`'Mesa 1'` es el `label` de la mesa número 1 sin nombre (`PosTable.label`).

- [ ] **Step 2: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_pos_cash_close.py`
Expected: `AttributeError: module 'app.services.pos.cash_service' has no attribute 'close_session'` (y equivalentes).

- [ ] **Step 3: Implementar.** En `backend/app/services/pos/cash_service.py`:

Cambiar los imports de arriba a:

```python
from collections import namedtuple
from datetime import datetime, time, timedelta
from decimal import Decimal
from math import ceil

import pytz
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Expense, ExpenseCategory, Supplier, User
from app.models.pos import (ACTIVE_SALE_STATUSES, CashEvent, CashMovement, CashRegister, CashSession,
                            CashSessionCount, PaymentMethod, PosPayment, PosSale)
from app.services.pos import pricing
from app.services.pos.audit import _jsonable
from app.services.pos.common import MAX_MONEY, display_name, now, parse_id, require_reason
from app.services.pos.errors import PosError, bad_request, forbidden, not_found
from app.utils.timezone_utils import ARGENTINA_TZ, get_current_date_argentina
from app.utils.validation import clean_str, parse_decimal
```

Agregar al final del archivo:

```python
def close_session(user, session_id, counts, note):
    session = load_session(session_id, lock=True)
    if session.status != 'open':
        raise PosError('La caja ya está cerrada')
    open_sales = open_sales_count()
    if open_sales:
        raise PosError(f'Hay {open_sales} ventas abiertas. Cobralas o anulalas antes de cerrar', open_sales=open_sales)
    if not isinstance(counts, list):
        raise bad_request('Los conteos son inválidos')
    lines = {line.method.id: line for line in expected_lines(session)}
    counted = {}
    for entry in counts:
        if not isinstance(entry, dict):
            raise bad_request('Los conteos son inválidos')
        method_id = parse_id(entry.get('payment_method_id'), 'El medio de pago')
        if method_id not in lines:
            method = db.session.get(PaymentMethod, method_id)
            if method is None:
                raise bad_request('El medio de pago no existe')
            lines[method_id] = Line(method, ZERO, ZERO, ZERO)
        counted[method_id] = _money(entry.get('counted'), f'Lo contado en {lines[method_id].method.name}',
                                    Decimal('0'))
    cash = next((line for line in lines.values() if line.method.kind == 'cash'), None)
    if cash is not None and cash.method.id not in counted:
        raise bad_request('Cargá lo contado en efectivo')
    note = clean_str(note, 500)
    rows = []
    for method_id, line in lines.items():
        value = counted.get(method_id, line.expected)
        if line.expected == 0 and value == 0 and method_id not in counted and line.method.kind != 'cash':
            continue
        rows.append(CashSessionCount(payment_method_id=method_id, method_name=line.method.name,
                                     expected=line.expected, counted=value, difference=value - line.expected))
    if any(row.difference != 0 for row in rows) and not note:
        raise bad_request('Explicá la diferencia en la nota')
    session.counts = rows
    session.status = 'closed'
    session.closed_at = now()
    session.closed_by = user.id
    session.closing_note = note
    _event(session.register_id, session.id, user, 'closed',
           differences={row.method_name: row.difference for row in rows}, note=note)
    db.session.commit()
    db.session.refresh(session)
    return session


def reopen_session(user, session_id, reason):
    _require_admin(user, 'Solo un administrador reabre una caja')
    reason = require_reason(reason)
    session = load_session(session_id, lock=True)
    if session.status != 'closed':
        raise PosError('La caja no está cerrada')
    other = (CashSession.query.filter(CashSession.register_id == session.register_id, CashSession.status == 'open',
                                      CashSession.id != session.id).first())
    if other is not None:
        raise PosError('La caja ya tiene otra sesión abierta')
    session.counts.clear()
    session.status = 'open'
    session.closed_at = None
    session.closed_by = None
    session.closing_note = None
    _event(session.register_id, session.id, user, 'reopened', reason=reason)
    db.session.commit()
    db.session.refresh(session)
    return session


def argentina_day_bounds(from_date, to_date):
    """Desde el inicio de `from_date` hasta el inicio del día siguiente a `to_date`, en hora argentina, en UTC."""
    def to_utc(day):
        local = ARGENTINA_TZ.localize(datetime.combine(day, time.min))
        return local.astimezone(pytz.utc).replace(tzinfo=None)
    return to_utc(from_date), to_utc(to_date + timedelta(days=1))


def _person(user):
    return {'id': user.id, 'name': display_name(user)} if user is not None else None


def _net_by_session(session_ids):
    if not session_ids:
        return {}
    got = dict(db.session.query(PosPayment.cash_session_id, func.sum(PosPayment.amount))
               .filter(PosPayment.cash_session_id.in_(session_ids)).group_by(PosPayment.cash_session_id).all())
    back = dict(db.session.query(PosPayment.cancel_cash_session_id, func.sum(PosPayment.amount))
                .filter(PosPayment.cancel_cash_session_id.in_(session_ids))
                .group_by(PosPayment.cancel_cash_session_id).all())
    return {sid: pricing.money(Decimal(str(got.get(sid) or 0)) - Decimal(str(back.get(sid) or 0)))
            for sid in session_ids}


def list_sessions(from_date, to_date, register_id=None, page=1, per_page=50):
    start, end = argentina_day_bounds(from_date, to_date)
    query = CashSession.query.filter(CashSession.opened_at >= start, CashSession.opened_at < end)
    if register_id is not None:
        query = query.filter(CashSession.register_id == register_id)
    total = query.count()
    sessions = (query.options(selectinload(CashSession.counts), selectinload(CashSession.register))
                .order_by(CashSession.opened_at.desc(), CashSession.id.desc())
                .offset((page - 1) * per_page).limit(per_page).all())
    net = _net_by_session([s.id for s in sessions])
    rows = []
    for session in sessions:
        cash_count = next((c for c in session.counts
                           if db.session.get(PaymentMethod, c.payment_method_id).kind == 'cash'), None)
        rows.append({
            'id': session.id, 'register': {'id': session.register.id, 'name': session.register.name},
            'status': session.status, 'opened_at': session.opened_at.isoformat(), 'opened_by': _person(session.opener),
            'closed_at': session.closed_at.isoformat() if session.closed_at else None,
            'closed_by': _person(session.closer), 'collected_net': float(net.get(session.id, ZERO)),
            'cash_difference': float(cash_count.difference) if cash_count is not None else None,
        })
    return {'sessions': rows, 'total': total, 'page': page, 'pages': max(1, ceil(total / per_page))}


def unassigned_payments(from_date, to_date):
    start, end = argentina_day_bounds(from_date, to_date)
    payments = (PosPayment.query.options(selectinload(PosPayment.sale))
                .filter(PosPayment.cash_session_id.is_(None), PosPayment.created_at >= start,
                        PosPayment.created_at < end)
                .order_by(PosPayment.created_at, PosPayment.id).all())
    rows = []
    for payment in payments:
        sale = payment.sale
        creator = db.session.get(User, payment.created_by)
        rows.append({
            'id': payment.id, 'sale_id': sale.id, 'sale_number': sale.number,
            'table': sale.table.label if sale.table else None, 'method_name': payment.method_name,
            'amount': float(payment.amount), 'created_by': _person(creator), 'created_at': payment.created_at.isoformat(),
            'cancelled': payment.cancelled_at is not None,
        })
    return rows
```

- [ ] **Step 4: Correr**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_pos_cash_close.py tests/test_pos_cash_service.py tests/test_pos_cash_payments.py`
Expected: todos pasan.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/pos/cash_service.py backend/tests/test_pos_cash_close.py
git commit -m "feat(pos): close and reopen cash sessions, history and unassigned payments"
```

---

### Task 5: API de caja, `cash_version` y concurrencia

**Files:**
- Create: `backend/app/services/pos/cash_serializers.py`
- Create: `backend/app/routes/pos_cash.py`
- Modify: `backend/app/__init__.py` (import y registro del blueprint)
- Modify: `backend/app/routes/pos_floor.py` (función `changes`)
- Test: `backend/tests/test_pos_cash_api.py`, `backend/tests/test_pos_cash_concurrency_pg.py`

**Interfaces:**
- Consumes: todo `cash_service` (Tasks 2 a 4); `serializers._iso`, `serializers._money`; `common.display_name`.
- Produces, en `/api/v1/pos/cash`:
  - `GET /registers` → `{"registers": [{"id", "name", "position", "open_session": null | {"id", "opened_at", "opened_by": {"id", "name"}}}]}` (`POS` o `Camarero`);
  - `POST /sessions` → `session_payload`;
  - `GET /sessions/current?register_id=` → `session_payload` o 404;
  - `GET /sessions/<id>` → `session_payload` con detalle;
  - `POST /sessions/<id>/movements` → `session_payload`;
  - `POST /movements/<id>/cancel` (admin) → `session_payload`;
  - `POST /sessions/<id>/close` → `session_payload`;
  - `POST /sessions/<id>/reopen` (admin) → `session_payload`;
  - `GET /sessions?from=&to=&register_id=&page=` → resultado de `list_sessions`;
  - `GET /unassigned-payments?from=&to=` → `{"payments": [...]}`;
  - `GET /expense-categories` → `{"categories": [{"id", "name"}]}`.
- `session_payload` = `{"id", "register": {"id", "name"}, "status", "opened_at", "opened_by", "opening_float", "closed_at", "closed_by", "closing_note", "summary", "movements": [movement], "counts": [count], "events": [event] (solo en el detalle)}`.
  - `movement` = `{"id", "kind", "amount", "reason", "expense_id", "created_by", "created_at", "cancelled_at", "cancel_reason", "is_active"}`.
  - `count` = `{"payment_method_id", "method_name", "expected", "counted", "difference"}`.
  - `event` = `{"id", "kind", "user", "created_at", "payload"}`.
- `GET /api/v1/pos/changes` suma `cash_version` (int) en todas sus respuestas.

- [ ] **Step 1: Tests que fallan.** Crear `backend/tests/test_pos_cash_api.py`:

```python
from datetime import date, timedelta

from app.extensions import db
from app.models import ExpenseCategory
from cash_helpers import make_register
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401

BASE = '/api/v1/pos/cash'


def _setup(pos_app):
    client = pos_app.test_client()
    cashier = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    register = make_register()
    return client, auth_headers(client, cashier), cat, register


def test_registers_visible_to_waiters_but_cash_ops_are_not(pos_app):
    client, _headers, _cat, register = _setup(pos_app)
    waiter = auth_headers(client, make_user('mozo@test.com', modules=('Camarero',)))
    data = client.get(f'{BASE}/registers', headers=waiter).get_json()
    assert data['registers'] == [{'id': register.id, 'name': 'Caja principal', 'position': 0, 'open_session': None}]
    assert client.post(f'{BASE}/sessions', json={'register_id': register.id, 'opening_float': 0},
                       headers=waiter).status_code == 403
    assert client.get(f'{BASE}/sessions', headers=waiter).status_code == 403


def test_open_movement_and_detail(pos_app):
    client, headers, cat, register = _setup(pos_app)
    category = ExpenseCategory(name='Insumos')
    db.session.add(category)
    db.session.commit()
    opened = client.post(f'{BASE}/sessions', json={'register_id': register.id, 'opening_float': '1000'},
                         headers=headers)
    assert opened.status_code == 200
    session = opened.get_json()
    assert session['status'] == 'open' and session['opening_float'] == 1000.0
    assert session['summary']['cash']['expected'] == 1000.0
    again = client.post(f'{BASE}/sessions', json={'register_id': register.id, 'opening_float': 0}, headers=headers)
    assert again.status_code == 409
    moved = client.post(f"{BASE}/sessions/{session['id']}/movements",
                        json={'kind': 'expense', 'amount': 200, 'reason': 'Hielo', 'category_id': category.id},
                        headers=headers).get_json()
    assert moved['summary']['cash']['expected'] == 800.0 and moved['movements'][-1]['kind'] == 'expense'
    detail = client.get(f"{BASE}/sessions/{session['id']}", headers=headers).get_json()
    assert [e['kind'] for e in detail['events']] == ['opened', 'movement_added']
    registers = client.get(f'{BASE}/registers', headers=headers).get_json()['registers']
    assert registers[0]['open_session']['id'] == session['id']
    current = client.get(f'{BASE}/sessions/current?register_id={register.id}', headers=headers)
    assert current.status_code == 200 and current.get_json()['id'] == session['id']
    bad = client.post(f"{BASE}/sessions/{session['id']}/movements",
                      json={'kind': 'deposit', 'amount': 'x', 'reason': 'a'}, headers=headers)
    assert bad.status_code == 400


def test_admin_only_endpoints(pos_app):
    client, headers, cat, register = _setup(pos_app)
    session = client.post(f'{BASE}/sessions', json={'register_id': register.id, 'opening_float': 0},
                          headers=headers).get_json()
    deposit = client.post(f"{BASE}/sessions/{session['id']}/movements",
                          json={'kind': 'deposit', 'amount': 50, 'reason': 'Cambio'}, headers=headers).get_json()
    movement_id = deposit['movements'][-1]['id']
    assert client.post(f'{BASE}/movements/{movement_id}/cancel', json={'reason': 'x'},
                       headers=headers).status_code == 403
    admin = auth_headers(client, make_user('admin@test.com', role='admin'))
    cancelled = client.post(f'{BASE}/movements/{movement_id}/cancel', json={'reason': 'Error'}, headers=admin)
    assert cancelled.status_code == 200 and cancelled.get_json()['summary']['cash']['expected'] == 0.0
    closed = client.post(f"{BASE}/sessions/{session['id']}/close",
                         json={'counts': [{'payment_method_id': cat.efectivo.id, 'counted': 0}]}, headers=headers)
    assert closed.status_code == 200 and closed.get_json()['status'] == 'closed'
    assert client.post(f"{BASE}/sessions/{session['id']}/reopen", json={'reason': 'x'},
                       headers=headers).status_code == 403
    assert client.post(f"{BASE}/sessions/{session['id']}/reopen", json={'reason': 'x'},
                       headers=admin).get_json()['status'] == 'open'


def test_close_conflict_reports_open_sales(pos_app):
    client, headers, cat, register = _setup(pos_app)
    _salon, t1, _t2 = make_floor()
    session = client.post(f'{BASE}/sessions', json={'register_id': register.id, 'opening_float': 0},
                          headers=headers).get_json()
    client.post('/api/v1/pos/sales', json={'sale_type': 'salon', 'table_id': t1.id, 'people': 1}, headers=headers)
    response = client.post(f"{BASE}/sessions/{session['id']}/close",
                           json={'counts': [{'payment_method_id': cat.efectivo.id, 'counted': 0}]}, headers=headers)
    assert response.status_code == 409 and response.get_json()['open_sales'] == 1


def test_history_unassigned_and_categories(pos_app):
    client, headers, _cat, register = _setup(pos_app)
    db.session.add_all([ExpenseCategory(name='Insumos'), ExpenseCategory(name='Vieja', is_active=False)])
    db.session.commit()
    client.post(f'{BASE}/sessions', json={'register_id': register.id, 'opening_float': 0}, headers=headers)
    day = date.today()
    params = f'from={(day - timedelta(days=1)).isoformat()}&to={(day + timedelta(days=1)).isoformat()}'
    history = client.get(f'{BASE}/sessions?{params}', headers=headers).get_json()
    assert history['total'] == 1 and history['sessions'][0]['status'] == 'open'
    assert client.get(f'{BASE}/sessions?from=ayer', headers=headers).status_code == 400
    assert client.get(f'{BASE}/unassigned-payments?{params}', headers=headers).get_json() == {'payments': []}
    categories = client.get(f'{BASE}/expense-categories', headers=headers).get_json()['categories']
    assert [c['name'] for c in categories] == ['Insumos']


def test_changes_reports_cash_version(pos_app):
    client, headers, _cat, register = _setup(pos_app)
    first = client.get('/api/v1/pos/changes', headers=headers).get_json()
    assert first['cash_version'] == 0
    client.post(f'{BASE}/sessions', json={'register_id': register.id, 'opening_float': 0}, headers=headers)
    second = client.get(f"/api/v1/pos/changes?since={first['last_event_id']}", headers=headers).get_json()
    assert second['cash_version'] > 0
```

Crear `backend/tests/test_pos_cash_concurrency_pg.py`:

```python
import os
import threading

import pytest

from app import create_app
from app.config import Config, config
from app.extensions import db
from app.models import User
from app.services.pos import cash_service
from app.services.pos.errors import PosError
from cash_helpers import make_methods, make_register
from pos_helpers import make_user

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


def _parallel(app, fn, workers=2):
    barrier = threading.Barrier(workers)
    results = [None] * workers

    def run(index):
        with app.app_context():
            barrier.wait()
            try:
                results[index] = ('ok', fn())
            except Exception as exc:  # noqa: BLE001 - el test inspecciona el error
                db.session.rollback()
                results[index] = ('error', exc)
            finally:
                db.session.remove()

    threads = [threading.Thread(target=run, args=(i,)) for i in range(workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return results


def _single_winner(results):
    errors = [r[1] for r in results if r[0] == 'error']
    assert [r[0] for r in results].count('ok') == 1
    assert len(errors) == 1 and isinstance(errors[0], PosError) and errors[0].status == 409


def test_two_cashiers_opening_the_same_register(pg_app):
    with pg_app.app_context():
        user_id = make_user('caja@test.com', modules=('POS',)).id
        register_id = make_register().id

    def open_register():
        return cash_service.open_session(db.session.get(User, user_id), register_id, 0).id

    _single_winner(_parallel(pg_app, open_register))


def test_two_cashiers_closing_the_same_session(pg_app):
    with pg_app.app_context():
        user = make_user('caja@test.com', modules=('POS',))
        user_id = user.id
        cash_id = make_methods().efectivo.id
        session_id = cash_service.open_session(user, make_register().id, 0).id

    def close():
        user = db.session.get(User, user_id)
        return cash_service.close_session(user, session_id, [{'payment_method_id': cash_id, 'counted': 0}], None).id

    _single_winner(_parallel(pg_app, close))
```

- [ ] **Step 2: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_pos_cash_api.py`
Expected: 404 en las rutas `/api/v1/pos/cash/...` y `KeyError: 'cash_version'`.

- [ ] **Step 3: Serializadores.** Crear `backend/app/services/pos/cash_serializers.py`:

```python
"""JSON de la caja: sesión, movimiento, conteo y evento."""
from app.services.pos.common import display_name
from app.services.pos.serializers import _iso, _money


def person(user):
    return {'id': user.id, 'name': display_name(user)} if user is not None else None


def movement_to_dict(movement):
    return {'id': movement.id, 'kind': movement.kind, 'amount': _money(movement.amount), 'reason': movement.reason,
            'expense_id': movement.expense_id, 'created_by': person(movement.creator),
            'created_at': _iso(movement.created_at), 'cancelled_at': _iso(movement.cancelled_at),
            'cancel_reason': movement.cancel_reason, 'is_active': movement.is_active}


def count_to_dict(count):
    return {'payment_method_id': count.payment_method_id, 'method_name': count.method_name,
            'expected': _money(count.expected), 'counted': _money(count.counted),
            'difference': _money(count.difference)}


def event_to_dict(event):
    return {'id': event.id, 'kind': event.kind, 'user': person(event.user), 'created_at': _iso(event.created_at),
            'payload': event.payload}


def session_to_dict(session, summary, events=None):
    data = {
        'id': session.id, 'register': {'id': session.register.id, 'name': session.register.name},
        'status': session.status, 'opened_at': _iso(session.opened_at), 'opened_by': person(session.opener),
        'opening_float': _money(session.opening_float), 'closed_at': _iso(session.closed_at),
        'closed_by': person(session.closer), 'closing_note': session.closing_note, 'summary': summary,
        'movements': [movement_to_dict(m) for m in session.movements],
        'counts': [count_to_dict(c) for c in session.counts],
    }
    if events is not None:
        data['events'] = [event_to_dict(e) for e in events]
    return data


def register_to_dict(register, open_session):
    return {'id': register.id, 'name': register.name, 'position': register.position,
            'open_session': ({'id': open_session.id, 'opened_at': _iso(open_session.opened_at),
                              'opened_by': person(open_session.opener)} if open_session else None)}
```

- [ ] **Step 4: Rutas.** Crear `backend/app/routes/pos_cash.py`:

```python
"""API de caja del POS. Las rutas validan permisos y traducen errores; la lógica está en cash_service."""
import logging
from datetime import date, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import DataError, IntegrityError

from app.extensions import db
from app.models import ExpenseCategory
from app.models.pos import CashEvent, CashRegister, CashSession
from app.services.pos import cash_service
from app.services.pos.cash_serializers import register_to_dict, session_to_dict
from app.services.pos.errors import PosError, bad_request, not_found
from app.utils.decorators import admin_required, module_required
from app.utils.jwt_utils import token_required
from app.utils.timezone_utils import get_current_date_argentina

logger = logging.getLogger(__name__)
bp = Blueprint('pos_cash', __name__, url_prefix='/api/v1/pos/cash')


def _body():
    data = request.get_json(silent=True)
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
        return jsonify({'error': 'Otra operación modificó la caja al mismo tiempo, probá de nuevo'}), 409
    except DataError:
        db.session.rollback()
        return jsonify({'error': 'Algún valor es demasiado grande'}), 400
    except Exception:
        db.session.rollback()
        logger.exception('Error inesperado en la caja')
        return jsonify({'error': 'Error interno, probá de nuevo'}), 500
    return jsonify(payload), 200


def _payload(session, detail=False):
    events = (CashEvent.query.filter_by(session_id=session.id).order_by(CashEvent.id).all() if detail else None)
    return session_to_dict(session, cash_service.session_summary(session), events)


def _date_arg(name, default):
    value = request.args.get(name)
    if not value:
        return default
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise bad_request('La fecha tiene que tener el formato AAAA-MM-DD')


def _range():
    today = get_current_date_argentina()
    start = _date_arg('from', today - timedelta(days=6))
    end = _date_arg('to', today)
    if end < start:
        raise bad_request('La fecha final es anterior a la inicial')
    return start, end


@bp.route('/registers', methods=['GET'])
@token_required
@module_required('POS', 'Camarero')
def registers(current_user):
    def action():
        rows = CashRegister.query.filter_by(is_active=True).order_by(CashRegister.position, CashRegister.id).all()
        open_by_register = {s.register_id: s for s in CashSession.query.filter_by(status='open').all()}
        return {'registers': [register_to_dict(r, open_by_register.get(r.id)) for r in rows]}
    return _run(action)


@bp.route('/sessions', methods=['POST'])
@token_required
@module_required('POS')
def open_session(current_user):
    def action():
        data = _body()
        return _payload(cash_service.open_session(current_user, data.get('register_id'), data.get('opening_float')))
    return _run(action)


@bp.route('/sessions/current', methods=['GET'])
@token_required
@module_required('POS')
def current_session(current_user):
    def action():
        register_id = request.args.get('register_id', type=int)
        session = CashSession.query.filter_by(register_id=register_id, status='open').first()
        if session is None:
            raise not_found('La caja no está abierta')
        return _payload(session)
    return _run(action)


@bp.route('/sessions/<int:session_id>', methods=['GET'])
@token_required
@module_required('POS')
def session_detail(current_user, session_id):
    return _run(lambda: _payload(cash_service.load_session(session_id), detail=True))


@bp.route('/sessions/<int:session_id>/movements', methods=['POST'])
@token_required
@module_required('POS')
def add_movement(current_user, session_id):
    def action():
        data = _body()
        return _payload(cash_service.add_movement(
            current_user, session_id, data.get('kind'), data.get('amount'), data.get('reason'),
            category_id=data.get('category_id'), supplier_id=data.get('supplier_id')))
    return _run(action)


@bp.route('/movements/<int:movement_id>/cancel', methods=['POST'])
@token_required
@admin_required
def cancel_movement(current_user, movement_id):
    return _run(lambda: _payload(cash_service.cancel_movement(current_user, movement_id, _body().get('reason'))))


@bp.route('/sessions/<int:session_id>/close', methods=['POST'])
@token_required
@module_required('POS')
def close_session(current_user, session_id):
    def action():
        data = _body()
        return _payload(cash_service.close_session(current_user, session_id, data.get('counts'), data.get('note')))
    return _run(action)


@bp.route('/sessions/<int:session_id>/reopen', methods=['POST'])
@token_required
@admin_required
def reopen_session(current_user, session_id):
    return _run(lambda: _payload(cash_service.reopen_session(current_user, session_id, _body().get('reason'))))


@bp.route('/sessions', methods=['GET'])
@token_required
@module_required('POS')
def list_sessions(current_user):
    def action():
        start, end = _range()
        page = max(1, request.args.get('page', 1, type=int))
        return cash_service.list_sessions(start, end, request.args.get('register_id', type=int), page)
    return _run(action)


@bp.route('/unassigned-payments', methods=['GET'])
@token_required
@module_required('POS')
def unassigned_payments(current_user):
    def action():
        start, end = _range()
        return {'payments': cash_service.unassigned_payments(start, end)}
    return _run(action)


@bp.route('/expense-categories', methods=['GET'])
@token_required
@module_required('POS')
def expense_categories(current_user):
    rows = ExpenseCategory.query.filter_by(is_active=True).order_by(ExpenseCategory.name).all()
    return jsonify({'categories': [{'id': c.id, 'name': c.name} for c in rows]}), 200
```

En `backend/app/__init__.py`, agregar `pos_cash` a la lista del `from app.routes import …` (después de `pos_sales`) y, después de `app.register_blueprint(pos_sales.bp)`:

```python
    app.register_blueprint(pos_cash.bp)
```

- [ ] **Step 5: `cash_version` en `/changes`.** En `backend/app/routes/pos_floor.py`:
  - agregar `CashEvent` al import de `app.models.pos`;
  - reemplazar el cuerpo de `changes` (desde `last = …` hasta el último `return`) por:

```python
    last = db.session.query(func.max(PosSaleEvent.id)).scalar() or 0
    cash_version = db.session.query(func.max(CashEvent.id)).scalar() or 0

    def respond(payload):
        return jsonify({**payload, 'cash_version': cash_version}), 200

    since = request.args.get('since', type=int)
    if since is None:
        return respond({'last_event_id': last, 'sales': []})
    if since > last:
        return respond({'last_event_id': last, 'reset': True, 'sales': []})
    # En la ventana hay a lo sumo CHANGES_OVERLAP ids <= since; si se llena el límite, hay más de
    # CHANGES_LIMIT eventos posteriores a since.
    rows = (db.session.query(PosSaleEvent.id, PosSaleEvent.sale_id)
            .filter(PosSaleEvent.id > max(0, since - CHANGES_OVERLAP)).order_by(PosSaleEvent.id)
            .limit(CHANGES_LIMIT + CHANGES_OVERLAP + 1).all())
    if sum(1 for row in rows if row.id > since) > CHANGES_LIMIT:
        return respond({'last_event_id': last, 'reset': True, 'sales': []})
    if not rows:
        return respond({'last_event_id': since, 'event_ids': [], 'sales': []})
    events_by_sale = defaultdict(list)
    for row in rows:
        events_by_sale[row.sale_id].append(row.id)
    sales = (PosSale.query.options(selectinload(PosSale.table))
             .filter(PosSale.id.in_(sorted(events_by_sale))).order_by(PosSale.id).all())
    return respond({'last_event_id': max(since, rows[-1].id), 'event_ids': [row.id for row in rows],
                    'sales': [_changed_sale(s, events_by_sale[s.id]) for s in sales]})
```

(El docstring de `changes` queda igual; agregar al final del docstring la línea `` `cash_version` es el último id de `cash_events`: la UI refresca la caja cuando cambia. ``)

- [ ] **Step 6: Correr**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_pos_cash_api.py tests/test_pos_cash_concurrency_pg.py tests/test_pos_cash_ui_api.py tests/test_route_access_coverage.py`
Expected: pasan. Los de PostgreSQL quedan `skipped` sin `POS_PG_TEST_URL`.

- [ ] **Step 7: Suite completa contra la línea base.** Con cwd = `backend/`; `<scratch>` es el scratchpad de la sesión.

```
PY -m pytest -q -p no:cacheprovider -rfE > <scratch>/pos_cash_pytest.txt
PY scripts/compare_baseline.py <scratch>/pos_cash_pytest.txt ../docs/superpowers/plans/2026-10-08-pos-base-test-baseline.txt
```

Expected: `Sin fallas nuevas.`

- [ ] **Step 8: Commit**

```bash
git add backend/app/services/pos/cash_serializers.py backend/app/routes/pos_cash.py backend/app/__init__.py backend/app/routes/pos_floor.py backend/tests/test_pos_cash_api.py backend/tests/test_pos_cash_concurrency_pg.py
git commit -m "feat(pos): cash register API and cash_version in changes"
```

---

### Task 6: Capa de datos del frontend y cálculo del arqueo

**Files:**
- Modify: `frontend/src/pos/api/posApi.js`, `frontend/src/pos/hooks/keys.js`, `frontend/src/pos/hooks/usePosChanges.js`, `frontend/src/pos/utils/changes.js`, `frontend/src/pos/utils/changes.test.js`
- Create: `frontend/src/pos/hooks/useCash.js`, `frontend/src/pos/utils/cashMath.js`, `frontend/src/pos/utils/cashMath.test.js`

**Interfaces:**
- Consumes: la API de la Task 5.
- Produces:
  - **`posCashApi`:** `registers()`, `session(id)`, `open({register_id, opening_float})`, `addMovement(id, body)`, `cancelMovement(movementId, reason)`, `close(id, {counts, note})`, `reopen(id, reason)`, `listSessions(params)`, `unassignedPayments(params)`, `expenseCategories()`.
  - **`posKeys`:** `cash`, `cashRegisters`, `cashSession(id)`, `cashSessions(params)`, `cashUnassigned(params)`, `expenseCategories`.
  - **Hooks:** `useRegisters(enabled = true)`, `useMainRegister()` → `{ register, openSessionId, isLoading, isError }`, `useCashSession(id)`, `useExpenseCategories(enabled)`, `useCashMutation()` → `{ run(fn): Promise<session|null>, busy }`.
  - **`cashMath`:** `countDifference(expected, text) → number|null`, `differenceTone(diff) → 'missing'|'over'|'even'|null`, `closeValidation(methods, texts, note) → { ok, error, counts }`, `cashStatusLabel(register, formatTime) → string`.
  - **`changes.js`:** `cashChanged(previous, next) → boolean`.

- [ ] **Step 1: Tests que fallan.** Crear `frontend/src/pos/utils/cashMath.test.js`:

```js
import { describe, expect, it } from 'vitest'
import { cashStatusLabel, closeValidation, countDifference, differenceTone } from './cashMath'

const methods = [
  { payment_method_id: 1, method_name: 'Efectivo', kind: 'cash', expected: 1900 },
  { payment_method_id: 2, method_name: 'Débito', kind: 'card', expected: 900 },
]

describe('countDifference', () => {
  it('resta lo esperado a lo contado y respeta el formato argentino', () => {
    expect(countDifference(1900, '1.850')).toBe(-50)
    expect(countDifference(900, '900,5')).toBe(0.5)
    expect(countDifference(900, '')).toBe(null)
    expect(countDifference(900, 'abc')).toBe(null)
  })
})

describe('differenceTone', () => {
  it('clasifica la diferencia', () => {
    expect(differenceTone(-1)).toBe('missing')
    expect(differenceTone(2)).toBe('over')
    expect(differenceTone(0)).toBe('even')
    expect(differenceTone(null)).toBe(null)
  })
})

describe('closeValidation', () => {
  it('exige el efectivo', () => {
    const result = closeValidation(methods, { 2: '900' }, '')
    expect(result.ok).toBe(false)
    expect(result.error).toBe('Cargá lo contado en efectivo')
  })

  it('toma lo esperado en los medios vacíos', () => {
    const result = closeValidation(methods, { 1: '1900' }, '')
    expect(result).toEqual({ ok: true, error: null, counts: [
      { payment_method_id: 1, counted: 1900 }, { payment_method_id: 2, counted: 900 },
    ] })
  })

  it('exige nota si hay diferencia', () => {
    expect(closeValidation(methods, { 1: '1850' }, '  ').error).toBe('Explicá la diferencia en la nota')
    expect(closeValidation(methods, { 1: '1850' }, 'Faltante').ok).toBe(true)
  })

  it('rechaza valores inválidos o negativos', () => {
    expect(closeValidation(methods, { 1: '1900', 2: 'x' }, '').error).toBe('Revisá lo contado en Débito')
    expect(closeValidation(methods, { 1: '-5' }, 'n').error).toBe('Revisá lo contado en Efectivo')
  })
})

describe('cashStatusLabel', () => {
  it('describe el estado de la caja', () => {
    const fmt = () => '09:02'
    expect(cashStatusLabel({ open_session: { opened_at: '2026-10-13T12:02:00' } }, fmt)).toBe('Caja abierta · desde 09:02')
    expect(cashStatusLabel({ open_session: null }, fmt)).toBe('Caja cerrada')
    expect(cashStatusLabel(null, fmt)).toBe('Sin caja configurada')
  })
})
```

En `frontend/src/pos/utils/changes.test.js`, agregar `cashChanged` al import existente de `./changes` y este bloque al final:

```js
describe('cashChanged', () => {
  it('detecta cambios de versión de caja, salvo en la primera lectura', () => {
    expect(cashChanged(null, 3)).toBe(false)
    expect(cashChanged(3, 3)).toBe(false)
    expect(cashChanged(3, 4)).toBe(true)
    expect(cashChanged(3, undefined)).toBe(false)
  })
})
```

- [ ] **Step 2: Correr y ver que fallen**

Run (cwd `frontend/`): `npx vitest run src/pos/utils/cashMath.test.js src/pos/utils/changes.test.js`
Expected: FAIL (no existe `./cashMath`; `cashChanged` no está exportado).

- [ ] **Step 3: Implementar la lógica pura.** Crear `frontend/src/pos/utils/cashMath.js`:

```js
import { parseAmount, round2 } from './money'
import { timeLabel } from './time'

// Diferencia en vivo del arqueo (contado − esperado). Lo guardado lo calcula el backend.
export function countDifference(expected, text) {
  const counted = parseAmount(text)
  if (!Number.isFinite(counted)) return null
  return round2(counted - Number(expected))
}

export function differenceTone(diff) {
  if (diff == null) return null
  if (diff < 0) return 'missing'
  if (diff > 0) return 'over'
  return 'even'
}

// Valida el cierre: el efectivo es obligatorio, lo vacío vale lo esperado y una diferencia exige nota.
export function closeValidation(methods, texts, note) {
  const counts = []
  let hasDifference = false
  for (const method of methods) {
    const text = String(texts[method.payment_method_id] ?? '').trim()
    if (!text) {
      if (method.kind === 'cash') return { ok: false, error: 'Cargá lo contado en efectivo', counts: [] }
      counts.push({ payment_method_id: method.payment_method_id, counted: Number(method.expected) })
      continue
    }
    const counted = parseAmount(text)
    if (!Number.isFinite(counted) || counted < 0) {
      return { ok: false, error: `Revisá lo contado en ${method.method_name}`, counts: [] }
    }
    if (round2(counted - Number(method.expected)) !== 0) hasDifference = true
    counts.push({ payment_method_id: method.payment_method_id, counted })
  }
  if (hasDifference && !String(note ?? '').trim()) {
    return { ok: false, error: 'Explicá la diferencia en la nota', counts: [] }
  }
  return { ok: true, error: null, counts }
}

export function cashStatusLabel(register, formatTime = timeLabel) {
  if (!register) return 'Sin caja configurada'
  if (!register.open_session) return 'Caja cerrada'
  return `Caja abierta · desde ${formatTime(register.open_session.opened_at)}`
}
```

En `frontend/src/pos/utils/changes.js`, agregar al final:

```js
// La caja se refresca cuando cambia `cash_version` (último id de cash_events). La primera lectura no cuenta.
export function cashChanged(previous, next) {
  return previous != null && next != null && previous !== next
}
```

- [ ] **Step 4: Correr**

Run: `npx vitest run src/pos/utils/cashMath.test.js src/pos/utils/changes.test.js`
Expected: PASS.

- [ ] **Step 5: API, claves, hooks y polling.** En `frontend/src/pos/api/posApi.js`, agregar al final:

```js
export const posCashApi = {
  registers: () => data(api.get('/pos/cash/registers')).then((d) => d.registers),
  session: (id) => data(api.get(`/pos/cash/sessions/${id}`)),
  open: (body) => data(api.post('/pos/cash/sessions', body)),
  addMovement: (id, body) => data(api.post(`/pos/cash/sessions/${id}/movements`, body)),
  cancelMovement: (movementId, reason) => data(api.post(`/pos/cash/movements/${movementId}/cancel`, { reason })),
  close: (id, body) => data(api.post(`/pos/cash/sessions/${id}/close`, body)),
  reopen: (id, reason) => data(api.post(`/pos/cash/sessions/${id}/reopen`, { reason })),
  listSessions: (params) => data(api.get('/pos/cash/sessions', { params })),
  unassignedPayments: (params) => data(api.get('/pos/cash/unassigned-payments', { params })).then((d) => d.payments),
  expenseCategories: () => data(api.get('/pos/cash/expense-categories')).then((d) => d.categories),
}
```

En `frontend/src/pos/hooks/keys.js`, agregar dentro de `posKeys`:

```js
  cash: ['pos', 'cash'],
  cashRegisters: ['pos', 'cash', 'registers'],
  cashSession: (id) => ['pos', 'cash', 'session', id],
  cashSessions: (params) => ['pos', 'cash', 'sessions', params],
  cashUnassigned: (params) => ['pos', 'cash', 'unassigned', params],
  expenseCategories: ['pos', 'cash', 'expense-categories'],
```

Crear `frontend/src/pos/hooks/useCash.js`:

```js
import { useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { posCashApi } from '../api/posApi'
import { useToast } from '../ui/Toasts'
import { errorMessage } from '../utils/errors'
import { posKeys } from './keys'

export const useRegisters = (enabled = true) => useQuery({
  queryKey: posKeys.cashRegisters,
  queryFn: posCashApi.registers,
  enabled,
  refetchInterval: 60_000,
  staleTime: 10_000,
})

// Hoy hay una sola caja: la primera activa.
export function useMainRegister(enabled = true) {
  const query = useRegisters(enabled)
  const register = query.data?.[0] ?? null
  return { register, openSessionId: register?.open_session?.id ?? null, isLoading: query.isLoading, isError: query.isError }
}

export const useCashSession = (id) => useQuery({
  queryKey: posKeys.cashSession(id),
  queryFn: () => posCashApi.session(id),
  enabled: Boolean(id),
  staleTime: 5_000,
})

export const useExpenseCategories = (enabled = true) => useQuery({
  queryKey: posKeys.expenseCategories,
  queryFn: posCashApi.expenseCategories,
  enabled,
  staleTime: 5 * 60_000,
})

// Acción de caja: la sesión devuelta reemplaza la caché; se refrescan cajas e historial.
export function useCashMutation() {
  const queryClient = useQueryClient()
  const toast = useToast()
  const { mutateAsync, isPending } = useMutation({
    mutationFn: (fn) => fn(),
    onSuccess: (session) => {
      if (session?.id) queryClient.setQueryData(posKeys.cashSession(session.id), session)
      queryClient.invalidateQueries({ queryKey: posKeys.cashRegisters })
      queryClient.invalidateQueries({ queryKey: ['pos', 'cash', 'sessions'] })
    },
  })
  const run = useCallback(async (fn) => {
    try {
      return await mutateAsync(fn)
    } catch (error) {
      toast.error(errorMessage(error))
      return null
    }
  }, [mutateAsync, toast])
  return { run, busy: isPending }
}
```

En `frontend/src/pos/hooks/usePosChanges.js`:
- cambiar el import de utils a `import { cashChanged, keysToInvalidate, rememberEventIds, unseenChanges } from '../utils/changes'`;
- después de `const seen = useRef(new Set())`, agregar `const cashVersion = useRef(null)`;
- dentro del `try`, justo antes de `seen.current = rememberEventIds(...)`, agregar:

```js
        if (cashChanged(cashVersion.current, response.cash_version)) {
          queryClient.invalidateQueries({ queryKey: posKeys.cash })
        }
        if (response.cash_version != null) cashVersion.current = response.cash_version
```

- [ ] **Step 6: Verificar**

Run (cwd `frontend/`): `npm test` y `npm run build`.
Expected: todo pasa.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pos
git commit -m "feat(pos): cash API client, hooks and count math"
```

---

### Task 7: Pantalla "Caja" en `/pos`: abrir, movimientos e indicador

**Files:**
- Create: `frontend/src/pos/cash/CashPage.jsx`, `CashSummaryCards.jsx`, `MovementList.jsx`, `OpenSessionModal.jsx`, `MovementModal.jsx`, `CashStatusBadge.jsx`
- Modify: `frontend/src/pos/layout/PosTopBar.jsx`, `frontend/src/App.jsx`

**Interfaces:**
- Consumes: `useMainRegister`, `useCashSession`, `useCashMutation`, `useExpenseCategories`, `posCashApi` y `cashStatusLabel` (Task 6); del 1b: `Modal`, `NumericKeypad`, `applyKey` (`../utils/keypad`), `btn`, `Chip`, `formatMoney`, `amountToText`, `parseAmount`, `timeLabel`, `usePosPermissions`, `CenteredMessage`; del resto de Galia: `useAuth` (`isAdmin`, `hasModuleAccess`) y `api` (`@/services/api`).
- Produces:
  - la ruta `/pos/caja`, solo con `POS`;
  - `CashStatusBadge` en la barra superior;
  - el botón "Cerrar caja" de `CashPage` abre `CloseSessionModal`, que crea la Task 8. En esta tarea el botón existe y, hasta la Task 8, abre un `Modal` simple con el texto "El cierre llega en la próxima tarea". Ese texto lo reemplaza la Task 8.

- [ ] **Step 1: Indicador.** Crear `frontend/src/pos/cash/CashStatusBadge.jsx`:

```jsx
import { useMainRegister } from '../hooks/useCash'
import { cashStatusLabel } from '../utils/cashMath'

export default function CashStatusBadge() {
  const { register, isLoading } = useMainRegister()
  if (isLoading) return null
  const open = Boolean(register?.open_session)
  return (
    <span className={`hidden whitespace-nowrap rounded-full px-3 py-1 text-xs font-medium lg:inline-block ${
      open ? 'bg-green-100 text-green-800' : 'bg-white/15 text-galia-cream'}`}>
      {cashStatusLabel(register)}
    </span>
  )
}
```

En `frontend/src/pos/layout/PosTopBar.jsx`:
- agregar `import CashStatusBadge from '../cash/CashStatusBadge'`;
- dentro del `<nav aria-label="Salones">`, después del `NavLink` de Mostrador, agregar:

```jsx
        {perms.pos && <NavLink to="/pos/caja" className={tabClass}>Caja</NavLink>}
```

- antes del `<span className="hidden px-2 text-sm …">{user?.email}</span>`, agregar `<CashStatusBadge />`.

- [ ] **Step 2: Modales de apertura y movimiento.** Crear `frontend/src/pos/cash/OpenSessionModal.jsx`:

```jsx
import { useState } from 'react'
import { posCashApi } from '../api/posApi'
import { useCashMutation } from '../hooks/useCash'
import NumericKeypad from '../modals/NumericKeypad'
import Modal from '../ui/Modal'
import { btn } from '../ui/buttons'
import { applyKey } from '../utils/keypad'
import { parseAmount } from '../utils/money'

export default function OpenSessionModal({ register, onClose }) {
  const [text, setText] = useState('')
  const [fresh, setFresh] = useState(true)
  const [error, setError] = useState('')
  const { run, busy } = useCashMutation()

  const submit = async () => {
    const amount = parseAmount(text || '0')
    if (!Number.isFinite(amount) || amount < 0) return setError('Indicá el fondo inicial')
    const session = await run(() => posCashApi.open({ register_id: register.id, opening_float: amount }))
    if (session) onClose()
  }

  const footer = (
    <div className="flex justify-end gap-2">
      <button type="button" className={btn('secondary')} onClick={onClose}>Cancelar</button>
      <button type="button" className={btn('primary')} disabled={busy} onClick={submit}>Abrir caja</button>
    </div>
  )

  return (
    <Modal title={`Abrir ${register.name}`} onClose={onClose} size="sm" footer={footer}>
      <label className="block text-sm font-medium text-gray-700">
        Fondo inicial (efectivo contado)
        <input inputMode="decimal" value={text} autoFocus placeholder="0"
          onChange={(e) => { setText(e.target.value); setFresh(false); setError('') }}
          className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-2xl" />
      </label>
      <div className="mt-3">
        <NumericKeypad onKey={(key) => { setText((t) => applyKey(t, key, fresh)); setFresh(false); setError('') }} />
      </div>
      {error && <p className="mt-2 text-sm text-red-700">{error}</p>}
    </Modal>
  )
}
```

Crear `frontend/src/pos/cash/MovementModal.jsx`:

```jsx
import { useEffect, useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import api from '@/services/api'
import { posCashApi } from '../api/posApi'
import { useCashMutation, useExpenseCategories } from '../hooks/useCash'
import Modal from '../ui/Modal'
import { btn } from '../ui/buttons'
import { parseAmount } from '../utils/money'

const TITLES = { expense: 'Gasto de caja', withdrawal: 'Retiro de efectivo', deposit: 'Ingreso de efectivo' }
const field = 'mt-1 w-full rounded-lg border border-gray-300 px-3 py-2'

// kind: 'expense' | 'withdrawal' | 'deposit'.
export default function MovementModal({ session, kind, onClose }) {
  const { hasModuleAccess } = useAuth()
  const isExpense = kind === 'expense'
  const canPickSupplier = isExpense && hasModuleAccess('Suppliers')
  const { data: categories = [] } = useExpenseCategories(isExpense)
  const [suppliers, setSuppliers] = useState([])
  const [amount, setAmount] = useState('')
  const [reason, setReason] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [supplierId, setSupplierId] = useState('')
  const [error, setError] = useState('')
  const { run, busy } = useCashMutation()

  useEffect(() => {
    if (!canPickSupplier) return
    api.get('/suppliers').then((r) => setSuppliers((r.data.suppliers ?? []).filter((s) => s.is_active)))
      .catch(() => setSuppliers([]))
  }, [canPickSupplier])

  const submit = async () => {
    const value = parseAmount(amount)
    if (!(value > 0)) return setError('Indicá el monto')
    if (!reason.trim()) return setError('Indicá el motivo')
    if (isExpense && !categoryId) return setError('Elegí la categoría del gasto')
    const body = { kind, amount: value, reason: reason.trim() }
    if (isExpense) {
      body.category_id = Number(categoryId)
      if (supplierId) body.supplier_id = Number(supplierId)
    }
    if (await run(() => posCashApi.addMovement(session.id, body))) onClose()
  }

  const footer = (
    <div className="flex justify-end gap-2">
      <button type="button" className={btn('secondary')} onClick={onClose}>Cancelar</button>
      <button type="button" className={btn('primary')} disabled={busy} onClick={submit}>Registrar</button>
    </div>
  )

  return (
    <Modal title={TITLES[kind]} onClose={onClose} size="sm" footer={footer}>
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700">Monto
          <input inputMode="decimal" autoFocus value={amount} onChange={(e) => { setAmount(e.target.value); setError('') }}
            className={`${field} text-xl`} />
        </label>
        <label className="block text-sm font-medium text-gray-700">Motivo
          <input value={reason} maxLength={255} onChange={(e) => { setReason(e.target.value); setError('') }} className={field} />
        </label>
        {isExpense && (
          <label className="block text-sm font-medium text-gray-700">Categoría
            <select value={categoryId} onChange={(e) => { setCategoryId(e.target.value); setError('') }} className={field}>
              <option value="">Elegí una categoría</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </label>
        )}
        {canPickSupplier && (
          <label className="block text-sm font-medium text-gray-700">Proveedor (opcional)
            <select value={supplierId} onChange={(e) => setSupplierId(e.target.value)} className={field}>
              <option value="">Sin proveedor</option>
              {suppliers.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </label>
        )}
        {error && <p className="text-sm text-red-700">{error}</p>}
      </div>
    </Modal>
  )
}
```

- [ ] **Step 3: Resumen y movimientos.** Crear `frontend/src/pos/cash/CashSummaryCards.jsx`:

```jsx
import { formatMoney } from '../utils/money'

function Row({ label, value, sign = '' }) {
  return (
    <div className="flex justify-between text-sm">
      <dt className="text-gray-600">{label}</dt>
      <dd>{sign}{formatMoney(value)}</dd>
    </div>
  )
}

export default function CashSummaryCards({ summary }) {
  const { cash, methods } = summary
  const others = methods.filter((m) => m.payment_method_id !== cash.payment_method_id)
  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      <section className="rounded-xl border-2 border-galia-plum/30 bg-white p-4">
        <h3 className="font-semibold text-galia-plum">Efectivo</h3>
        <dl className="mt-2 space-y-1">
          <Row label="Fondo inicial" value={cash.opening_float} />
          <Row label="Ventas" value={cash.sales} sign="+ " />
          {cash.cancelled > 0 && <Row label="Anulaciones" value={cash.cancelled} sign="− " />}
          {cash.expenses > 0 && <Row label="Gastos" value={cash.expenses} sign="− " />}
          {cash.withdrawals > 0 && <Row label="Retiros" value={cash.withdrawals} sign="− " />}
          {cash.deposits > 0 && <Row label="Ingresos" value={cash.deposits} sign="+ " />}
          <div className="flex justify-between border-t pt-2 text-lg font-bold text-galia-plum">
            <dt>Esperado</dt><dd>{formatMoney(cash.expected)}</dd>
          </div>
        </dl>
      </section>
      {others.map((m) => (
        <section key={m.payment_method_id} className="rounded-xl border border-gray-200 bg-white p-4">
          <h3 className="font-semibold">{m.method_name}</h3>
          <p className="mt-2 text-2xl font-bold">{formatMoney(m.expected)}</p>
          {m.cancelled > 0 && <p className="text-xs text-gray-500">Cobrado {formatMoney(m.collected)} · anulado {formatMoney(m.cancelled)}</p>}
        </section>
      ))}
    </div>
  )
}
```

Crear `frontend/src/pos/cash/MovementList.jsx`:

```jsx
import { useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { posCashApi } from '../api/posApi'
import { useCashMutation } from '../hooks/useCash'
import Modal from '../ui/Modal'
import { btn } from '../ui/buttons'
import { formatMoney } from '../utils/money'
import { timeLabel } from '../utils/time'

const LABELS = { opening_float: 'Fondo inicial', expense: 'Gasto', withdrawal: 'Retiro', deposit: 'Ingreso' }
const SIGNS = { opening_float: '+', deposit: '+', expense: '−', withdrawal: '−' }

export default function MovementList({ session }) {
  const { isAdmin } = useAuth()
  const [cancelling, setCancelling] = useState(null)
  const [reason, setReason] = useState('')
  const { run, busy } = useCashMutation()
  const canCancel = isAdmin() && session.status === 'open'

  const confirm = async () => {
    if (!reason.trim()) return
    if (await run(() => posCashApi.cancelMovement(cancelling.id, reason.trim()))) {
      setCancelling(null)
      setReason('')
    }
  }

  return (
    <>
      <ul className="divide-y rounded-xl border border-gray-200 bg-white">
        {session.movements.map((m) => (
          <li key={m.id} className={`flex items-center gap-3 px-4 py-2 text-sm ${m.is_active ? '' : 'text-gray-400 line-through'}`}>
            <span className="w-12 text-gray-500">{timeLabel(m.created_at)}</span>
            <span className="w-24 font-medium">{LABELS[m.kind]}</span>
            <span className="min-w-0 flex-1 truncate">{m.reason ?? ''}{m.created_by ? ` · ${m.created_by.name}` : ''}</span>
            <span className="whitespace-nowrap font-medium">{SIGNS[m.kind]} {formatMoney(m.amount)}</span>
            {canCancel && m.is_active && m.kind !== 'opening_float' && (
              <button type="button" className="text-red-700 underline" onClick={() => setCancelling(m)}>Anular</button>
            )}
          </li>
        ))}
      </ul>
      {cancelling && (
        <Modal title={`Anular ${LABELS[cancelling.kind].toLowerCase()} de ${formatMoney(cancelling.amount)}`}
          onClose={() => setCancelling(null)} size="sm"
          footer={(
            <div className="flex justify-end gap-2">
              <button type="button" className={btn('secondary')} onClick={() => setCancelling(null)}>Volver</button>
              <button type="button" className={btn('danger')} disabled={busy || !reason.trim()} onClick={confirm}>Anular</button>
            </div>
          )}>
          <label className="block text-sm font-medium text-gray-700">Motivo
            <input autoFocus value={reason} maxLength={255} onChange={(e) => setReason(e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
          </label>
        </Modal>
      )}
    </>
  )
}
```

- [ ] **Step 4: Página.** Crear `frontend/src/pos/cash/CashPage.jsx`:

```jsx
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { posCashApi } from '../api/posApi'
import { posKeys } from '../hooks/keys'
import { useCashSession, useMainRegister } from '../hooks/useCash'
import CenteredMessage from '../ui/CenteredMessage'
import Modal from '../ui/Modal'
import { btn } from '../ui/buttons'
import { formatMoney } from '../utils/money'
import { timeLabel } from '../utils/time'
import CashSummaryCards from './CashSummaryCards'
import MovementList from './MovementList'
import MovementModal from './MovementModal'
import OpenSessionModal from './OpenSessionModal'

function LastClosed({ registerId }) {
  const params = { register_id: registerId, page: 1 }
  const { data } = useQuery({ queryKey: posKeys.cashSessions(params), queryFn: () => posCashApi.listSessions(params) })
  const last = data?.sessions?.find((s) => s.status === 'closed')
  if (!last) return null
  return (
    <p className="text-sm text-gray-600">
      Último cierre: {timeLabel(last.closed_at)} por {last.closed_by?.name} · cobrado {formatMoney(last.collected_net)}
      {last.cash_difference ? ` · diferencia en efectivo ${formatMoney(last.cash_difference)}` : ''}
    </p>
  )
}

export default function CashPage() {
  const { register, openSessionId, isLoading, isError } = useMainRegister()
  const { data: session } = useCashSession(openSessionId)
  const [modal, setModal] = useState(null)
  const close = () => setModal(null)

  if (isLoading) return <CenteredMessage>Cargando caja…</CenteredMessage>
  if (isError) return <CenteredMessage>No se pudo cargar la caja.</CenteredMessage>
  if (!register) return <CenteredMessage>No hay ninguna caja configurada.</CenteredMessage>

  if (!openSessionId) {
    return (
      <div className="mx-auto max-w-xl space-y-4 p-6 text-center">
        <h2 className="text-2xl font-semibold text-galia-plum">{register.name} cerrada</h2>
        <button type="button" className={btn('primary', 'text-lg')} onClick={() => setModal('open')}>Abrir caja</button>
        <LastClosed registerId={register.id} />
        {modal === 'open' && <OpenSessionModal register={register} onClose={close} />}
      </div>
    )
  }
  if (!session) return <CenteredMessage>Cargando caja…</CenteredMessage>

  return (
    <div className="h-full space-y-4 overflow-y-auto p-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-galia-plum">{session.register.name}</h2>
          <p className="text-sm text-gray-600">
            Abierta {timeLabel(session.opened_at)} por {session.opened_by?.name} · fondo {formatMoney(session.opening_float)}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" className={btn('secondary')} onClick={() => setModal('expense')}>Gasto</button>
          <button type="button" className={btn('secondary')} onClick={() => setModal('withdrawal')}>Retiro</button>
          <button type="button" className={btn('secondary')} onClick={() => setModal('deposit')}>Ingreso</button>
          <button type="button" className={btn('primary')} onClick={() => setModal('close')}>Cerrar caja</button>
        </div>
      </header>
      <CashSummaryCards summary={session.summary} />
      <h3 className="font-semibold">Movimientos</h3>
      <MovementList session={session} />
      {['expense', 'withdrawal', 'deposit'].includes(modal) && <MovementModal session={session} kind={modal} onClose={close} />}
      {modal === 'close' && (
        <Modal title="Cerrar caja" onClose={close} size="sm">
          <p>El cierre llega en la próxima tarea.</p>
        </Modal>
      )}
    </div>
  )
}
```

- [ ] **Step 5: Ruta.** En `frontend/src/App.jsx`:
  - agregar `import CashPage from './pos/cash/CashPage'` junto a los imports del POS;
  - dentro de `<Route path="/pos" …>`, después de la ruta `config`, agregar:

```jsx
            <Route path="caja" element={<PosRoute require="pos"><CashPage /></PosRoute>} />
```

- [ ] **Step 6: Verificar**

Run (cwd `frontend/`): `npm test` y `npm run build`.
Expected: todo pasa.

Verificación en el navegador (la hace quien coordina): con `caja@galia.test` en `/pos/caja`:
- abrir con fondo;
- el indicador de la barra pasa a "Caja abierta";
- gasto, retiro e ingreso actualizan el desglose;
- admin anula un movimiento.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pos frontend/src/App.jsx
git commit -m "feat(pos): cash page with open, movements and status badge"
```

---

### Task 8: Cerrar caja con arqueo

**Files:**
- Create: `frontend/src/pos/cash/CloseSessionModal.jsx`
- Modify: `frontend/src/pos/cash/CashPage.jsx`

**Interfaces:**
- Consumes: `closeValidation`, `countDifference`, `differenceTone` (Task 6); `posCashApi.close`, `useCashMutation`; `NumericKeypad`, `applyKey`, `Modal`, `btn`, `formatMoney`.
- Produces: `CloseSessionModal({ session, onClose })`.

- [ ] **Step 1: Modal.** Crear `frontend/src/pos/cash/CloseSessionModal.jsx`:

```jsx
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { posCashApi } from '../api/posApi'
import { useCashMutation } from '../hooks/useCash'
import NumericKeypad from '../modals/NumericKeypad'
import Modal from '../ui/Modal'
import { btn } from '../ui/buttons'
import { closeValidation, countDifference, differenceTone } from '../utils/cashMath'
import { applyKey } from '../utils/keypad'
import { formatMoney } from '../utils/money'

const TONES = { missing: 'text-red-700', over: 'text-amber-700', even: 'text-gray-500' }

export default function CloseSessionModal({ session, onClose }) {
  const methods = session.summary.methods
  const [texts, setTexts] = useState({})
  const [focused, setFocused] = useState(methods.find((m) => m.kind === 'cash')?.payment_method_id ?? null)
  const [fresh, setFresh] = useState(true)
  const [note, setNote] = useState('')
  const [closed, setClosed] = useState(null)
  const { run, busy } = useCashMutation()
  const validation = closeValidation(methods, texts, note)

  if (session.summary.open_sales > 0) {
    return (
      <Modal title="Cerrar caja" onClose={onClose} size="sm"
        footer={<Link to="/pos" className={btn('primary', 'w-full')}>Ir al plano</Link>}>
        <p>Hay {session.summary.open_sales} ventas abiertas. Cobralas o anulalas antes de cerrar.</p>
      </Modal>
    )
  }

  if (closed) {
    return (
      <Modal title="Caja cerrada" onClose={onClose} size="sm"
        footer={<button type="button" className={btn('primary', 'w-full')} onClick={onClose}>Listo</button>}>
        <ul className="space-y-1 text-sm">
          {closed.counts.map((c) => (
            <li key={c.payment_method_id} className="flex justify-between">
              <span>{c.method_name}</span>
              <span className={TONES[differenceTone(c.difference)]}>
                {formatMoney(c.counted)}{c.difference !== 0 ? ` (${c.difference > 0 ? '+' : ''}${formatMoney(c.difference)})` : ''}
              </span>
            </li>
          ))}
        </ul>
      </Modal>
    )
  }

  const setText = (id, value) => setTexts((current) => ({ ...current, [id]: value }))
  const onKey = (key) => {
    if (focused == null) return
    setText(focused, applyKey(texts[focused] ?? '', key, fresh))
    setFresh(false)
  }
  const submit = async () => {
    if (!validation.ok) return
    const result = await run(() => posCashApi.close(session.id, { counts: validation.counts, note: note.trim() || null }))
    if (result) setClosed(result)
  }

  return (
    <Modal title="Cerrar caja" onClose={onClose} size="lg">
      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500"><th>Medio</th><th>Esperado</th><th>Contado</th><th>Diferencia</th></tr>
            </thead>
            <tbody>
              {methods.map((m) => {
                const diff = countDifference(m.expected, texts[m.payment_method_id] ?? '')
                return (
                  <tr key={m.payment_method_id} className="border-t">
                    <td className="py-2 font-medium">{m.method_name}</td>
                    <td>{formatMoney(m.expected)}</td>
                    <td>
                      <input inputMode="decimal" value={texts[m.payment_method_id] ?? ''}
                        placeholder={m.kind === 'cash' ? 'Obligatorio' : formatMoney(m.expected)}
                        onFocus={() => { setFocused(m.payment_method_id); setFresh(true) }}
                        onChange={(e) => { setText(m.payment_method_id, e.target.value); setFresh(false) }}
                        className={`w-28 rounded-lg border px-2 py-1 ${focused === m.payment_method_id ? 'border-galia-plum' : 'border-gray-300'}`} />
                    </td>
                    <td className={TONES[differenceTone(diff)] ?? 'text-gray-400'}>{diff == null ? '—' : formatMoney(diff)}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          <label className="mt-4 block text-sm font-medium text-gray-700">Nota
            <textarea rows={2} maxLength={500} value={note} onChange={(e) => setNote(e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
          </label>
          {!validation.ok && <p className="mt-2 text-sm text-amber-700">{validation.error}</p>}
        </div>
        <div>
          <NumericKeypad onKey={onKey} />
          <button type="button" className={btn('primary', 'mt-3 w-full text-lg')} disabled={busy || !validation.ok}
            onClick={submit}>
            Confirmar cierre
          </button>
        </div>
      </div>
    </Modal>
  )
}
```

- [ ] **Step 2: Usarlo en la página.** En `frontend/src/pos/cash/CashPage.jsx`:
  - agregar `import CloseSessionModal from './CloseSessionModal'`;
  - quitar `import Modal from '../ui/Modal'` si queda sin uso;
  - reemplazar el bloque:

```jsx
      {modal === 'close' && (
        <Modal title="Cerrar caja" onClose={close} size="sm">
          <p>El cierre llega en la próxima tarea.</p>
        </Modal>
      )}
```

por:

```jsx
      {modal === 'close' && <CloseSessionModal session={session} onClose={close} />}
```

- [ ] **Step 3: Verificar**

Run (cwd `frontend/`): `npm test` y `npm run build`.
Expected: todo pasa.

Verificación en el navegador (la hace quien coordina):
- con una mesa abierta, "Cerrar caja" muestra el bloqueo con "Ir al plano";
- sin mesas abiertas, cargar el efectivo con una diferencia exige la nota;
- "Confirmar cierre" muestra el resumen y la página vuelve a "caja cerrada" con "Último cierre".

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pos/cash
git commit -m "feat(pos): close cash session with visible count"
```

---

### Task 9: Aviso en el cobro e historial en Galia

**Files:**
- Modify: `frontend/src/pos/modals/PaymentModal.jsx`
- Create: `frontend/src/pages/CashSessions.jsx`, `frontend/src/pages/CashSessionDetail.jsx`
- Modify: `frontend/src/App.jsx`, `frontend/src/components/layout/Sidebar.jsx`

**Interfaces:**
- Consumes: `useMainRegister`, `posCashApi`, `posKeys`, `useCashMutation` (Task 6); `CashSummaryCards`, `MovementList` (Task 7); `ToastProvider`, `formatMoney`, `timeLabel`, `btn`; `RoleProtectedRoute`; `useAuth`.
- Produces: las rutas `/cash-sessions` y `/cash-sessions/:id`, y la entrada "Cajas" en Finanzas.

- [ ] **Step 1: Aviso de "sin caja".** En `frontend/src/pos/modals/PaymentModal.jsx`:
  - agregar `import { useMainRegister } from '../hooks/useCash'`;
  - dentro del componente, después de `const { run, busy } = useSaleMutation()`, agregar:

```js
  const { register, isLoading: registerLoading } = useMainRegister()
  const withoutCash = !registerLoading && !register?.open_session
```

  - en el `return` principal, justo después de `<Modal title={`Cobrar ${saleTitle(sale)}`} onClose={onClose} size="lg">`, agregar:

```jsx
      {withoutCash && (
        <p className="mb-4 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
          No hay caja abierta: este pago queda sin caja.
        </p>
      )}
```

- [ ] **Step 2: Historial.** Crear `frontend/src/pages/CashSessions.jsx`:

```jsx
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { posCashApi } from '@/pos/api/posApi'
import { posKeys } from '@/pos/hooks/keys'
import { formatMoney } from '@/pos/utils/money'

const isoDay = (date) => date.toISOString().slice(0, 10)
const today = () => new Date()
const daysAgo = (n) => new Date(Date.now() - n * 86_400_000)
const when = (iso) => (iso ? new Date(/[zZ]$/.test(iso) ? iso : `${iso}Z`).toLocaleString('es-AR', { dateStyle: 'short', timeStyle: 'short' }) : '—')

function Sessions({ params, setPage }) {
  const { data, isLoading, isError } = useQuery({ queryKey: posKeys.cashSessions(params), queryFn: () => posCashApi.listSessions(params) })
  if (isLoading) return <p className="text-gray-500">Cargando…</p>
  if (isError) return <p className="text-red-700">No se pudieron cargar las cajas.</p>
  return (
    <>
      <table className="w-full rounded-xl bg-white text-sm shadow-sm">
        <thead>
          <tr className="border-b text-left text-gray-500">
            <th className="p-3">Caja</th><th>Apertura</th><th>Cierre</th><th>Cobrado</th><th>Dif. efectivo</th><th>Estado</th>
          </tr>
        </thead>
        <tbody>
          {data.sessions.map((s) => (
            <tr key={s.id} className="border-b last:border-0 hover:bg-gray-50">
              <td className="p-3"><Link to={`/cash-sessions/${s.id}`} className="font-medium text-galia-plum underline">{s.register.name}</Link></td>
              <td>{when(s.opened_at)} · {s.opened_by?.name}</td>
              <td>{s.closed_at ? `${when(s.closed_at)} · ${s.closed_by?.name}` : '—'}</td>
              <td>{formatMoney(s.collected_net)}</td>
              <td className={s.cash_difference < 0 ? 'text-red-700' : s.cash_difference > 0 ? 'text-amber-700' : ''}>
                {s.cash_difference == null ? '—' : formatMoney(s.cash_difference)}
              </td>
              <td>{s.status === 'open' ? 'Abierta' : 'Cerrada'}</td>
            </tr>
          ))}
          {data.sessions.length === 0 && <tr><td colSpan={6} className="p-6 text-center text-gray-500">Sin sesiones en el rango.</td></tr>}
        </tbody>
      </table>
      {data.pages > 1 && (
        <div className="mt-3 flex items-center gap-3">
          <button type="button" disabled={params.page <= 1} onClick={() => setPage(params.page - 1)} className="underline disabled:opacity-40">Anterior</button>
          <span>Página {data.page} de {data.pages}</span>
          <button type="button" disabled={params.page >= data.pages} onClick={() => setPage(params.page + 1)} className="underline disabled:opacity-40">Siguiente</button>
        </div>
      )}
    </>
  )
}

function Unassigned({ params }) {
  const { data = [], isLoading } = useQuery({ queryKey: posKeys.cashUnassigned(params), queryFn: () => posCashApi.unassignedPayments(params) })
  if (isLoading) return <p className="text-gray-500">Cargando…</p>
  return (
    <table className="w-full rounded-xl bg-white text-sm shadow-sm">
      <thead><tr className="border-b text-left text-gray-500"><th className="p-3">Fecha</th><th>Venta</th><th>Medio</th><th>Monto</th><th>Cobró</th></tr></thead>
      <tbody>
        {data.map((p) => (
          <tr key={p.id} className={`border-b last:border-0 ${p.cancelled ? 'text-gray-400 line-through' : ''}`}>
            <td className="p-3">{when(p.created_at)}</td>
            <td>#{p.sale_number}{p.table ? ` · ${p.table}` : ''}</td>
            <td>{p.method_name}</td>
            <td>{formatMoney(p.amount)}</td>
            <td>{p.created_by?.name}</td>
          </tr>
        ))}
        {data.length === 0 && <tr><td colSpan={5} className="p-6 text-center text-gray-500">No hay pagos sin caja.</td></tr>}
      </tbody>
    </table>
  )
}

export default function CashSessions() {
  const [from, setFrom] = useState(isoDay(daysAgo(6)))
  const [to, setTo] = useState(isoDay(today()))
  const [page, setPage] = useState(1)
  const [tab, setTab] = useState('sessions')
  const range = { from, to }
  return (
    <div className="space-y-4">
      <h1 className="text-3xl">Cajas</h1>
      <div className="flex flex-wrap items-end gap-3">
        <label className="text-sm">Desde<input type="date" value={from} onChange={(e) => { setFrom(e.target.value); setPage(1) }} className="ml-2 rounded border px-2 py-1" /></label>
        <label className="text-sm">Hasta<input type="date" value={to} onChange={(e) => { setTo(e.target.value); setPage(1) }} className="ml-2 rounded border px-2 py-1" /></label>
      </div>
      <div className="flex gap-1 border-b">
        {[['sessions', 'Sesiones'], ['unassigned', 'Pagos sin caja']].map(([key, label]) => (
          <button key={key} type="button" onClick={() => setTab(key)}
            className={`px-4 py-2 font-medium ${tab === key ? 'border-b-2 border-galia-plum text-galia-plum' : 'text-gray-600'}`}>{label}</button>
        ))}
      </div>
      {tab === 'sessions' ? <Sessions params={{ ...range, page }} setPage={setPage} /> : <Unassigned params={range} />}
    </div>
  )
}
```

La fecha "hoy" sale de la hora local del navegador (Argentina en el uso real). El backend toma el rango como días de Argentina.

Crear `frontend/src/pages/CashSessionDetail.jsx`:

```jsx
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { posCashApi } from '@/pos/api/posApi'
import CashSummaryCards from '@/pos/cash/CashSummaryCards'
import MovementList from '@/pos/cash/MovementList'
import { useCashMutation, useCashSession } from '@/pos/hooks/useCash'
import { ToastProvider } from '@/pos/ui/Toasts'
import { btn } from '@/pos/ui/buttons'
import { formatMoney } from '@/pos/utils/money'

const when = (iso) => (iso ? new Date(/[zZ]$/.test(iso) ? iso : `${iso}Z`).toLocaleString('es-AR', { dateStyle: 'short', timeStyle: 'short' }) : '—')
const EVENTS = { opened: 'Apertura', movement_added: 'Movimiento', movement_cancelled: 'Movimiento anulado', closed: 'Cierre', reopened: 'Reapertura' }

function Detail() {
  const id = Number(useParams().id)
  const { isAdmin } = useAuth()
  const { data: session, isLoading, isError } = useCashSession(id)
  const { run, busy } = useCashMutation()
  const [reason, setReason] = useState('')

  if (isLoading) return <p className="text-gray-500">Cargando…</p>
  if (isError || !session) return <p className="text-red-700">No se encontró la sesión.</p>

  return (
    <div className="space-y-4">
      <Link to="/cash-sessions" className="text-galia-plum underline">← Cajas</Link>
      <h1 className="text-3xl">{session.register.name} · {session.status === 'open' ? 'abierta' : 'cerrada'}</h1>
      <p className="text-sm text-gray-600">
        Apertura {when(session.opened_at)} por {session.opened_by?.name} · fondo {formatMoney(session.opening_float)}
        {session.closed_at && ` · cierre ${when(session.closed_at)} por ${session.closed_by?.name}`}
      </p>
      {session.closing_note && <p className="rounded bg-gray-50 p-3 text-sm">Nota: {session.closing_note}</p>}
      <CashSummaryCards summary={session.summary} />
      {session.counts.length > 0 && (
        <table className="w-full rounded-xl bg-white text-sm shadow-sm">
          <thead><tr className="border-b text-left text-gray-500"><th className="p-3">Medio</th><th>Esperado</th><th>Contado</th><th>Diferencia</th></tr></thead>
          <tbody>
            {session.counts.map((c) => (
              <tr key={c.payment_method_id} className="border-b last:border-0">
                <td className="p-3">{c.method_name}</td><td>{formatMoney(c.expected)}</td><td>{formatMoney(c.counted)}</td>
                <td className={c.difference < 0 ? 'text-red-700' : c.difference > 0 ? 'text-amber-700' : ''}>{formatMoney(c.difference)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <h2 className="text-xl">Movimientos</h2>
      <MovementList session={session} />
      <h2 className="text-xl">Historial</h2>
      <ol className="space-y-1 text-sm">
        {(session.events ?? []).map((e) => (
          <li key={e.id}>{when(e.created_at)} · {EVENTS[e.kind] ?? e.kind} · {e.user?.name}{e.payload?.reason ? ` · ${e.payload.reason}` : ''}</li>
        ))}
      </ol>
      {isAdmin() && session.status === 'closed' && (
        <div className="flex flex-wrap items-end gap-2 rounded-xl border border-gray-200 p-4">
          <label className="text-sm">Motivo de la reapertura
            <input value={reason} onChange={(e) => setReason(e.target.value)} maxLength={255}
              className="ml-2 rounded border px-2 py-1" />
          </label>
          <button type="button" className={btn('danger')} disabled={busy || !reason.trim()}
            onClick={async () => { if (await run(() => posCashApi.reopen(session.id, reason.trim()))) setReason('') }}>
            Reabrir
          </button>
        </div>
      )}
    </div>
  )
}

// Fuera del POS no hay ToastProvider: se provee acá para los avisos de las acciones de caja.
export default function CashSessionDetail() {
  return <ToastProvider><Detail /></ToastProvider>
}
```

`MovementList` también lo usa la página de Galia; ahí el detalle trae `events` (Task 5) y la lista de movimientos ya muestra "Anular" solo a admin con la sesión abierta.

- [ ] **Step 3: Rutas y Sidebar.** En `frontend/src/App.jsx`:
  - agregar `import CashSessions from './pages/CashSessions'` e `import CashSessionDetail from './pages/CashSessionDetail'`;
  - dentro del `Layout`, después de la ruta `/expenses`, agregar:

```jsx
            <Route path="/cash-sessions" element={<RoleProtectedRoute moduleName="POS"><CashSessions /></RoleProtectedRoute>} />
            <Route path="/cash-sessions/:id" element={<RoleProtectedRoute moduleName="POS"><CashSessionDetail /></RoleProtectedRoute>} />
```

En `frontend/src/components/layout/Sidebar.jsx`:
- agregar `Banknote,` al import multilínea de `lucide-react`;
- en la sección Finanzas, después de `{ to: '/sales', … }`, agregar:

```js
      { to: '/cash-sessions', icon: Banknote, label: 'Cajas', module: 'POS' },
```

- [ ] **Step 4: Verificar**

Run (cwd `frontend/`): `npm test` y `npm run build`.
Expected: todo pasa.

Verificación en el navegador (la hace quien coordina):
- con la caja cerrada, el cobro muestra el aviso;
- Finanzas → Cajas lista las sesiones, con detalle y reapertura como admin;
- "Pagos sin caja" lista el pago cobrado sin caja.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pos/modals/PaymentModal.jsx frontend/src/pages/CashSessions.jsx frontend/src/pages/CashSessionDetail.jsx frontend/src/App.jsx frontend/src/components/layout/Sidebar.jsx
git commit -m "feat(pos): no-cash notice on payment and cash sessions history in Galia"
```

---

### Task 10: Verificación final

**Files:** ninguno nuevo (preview fuera del repo).

- [ ] **Step 1: Suites**

Backend (cwd `backend/`):

```
PY -m pytest -q -p no:cacheprovider -rfE > <scratch>/pos_cash_final_pytest.txt
PY scripts/compare_baseline.py <scratch>/pos_cash_final_pytest.txt ../docs/superpowers/plans/2026-10-08-pos-base-test-baseline.txt
```

Expected: `Sin fallas nuevas.`

Frontend (cwd `frontend/`): `npm test` y `npm run build`.
Expected: todo pasa.

- [ ] **Step 2: Preview.** Base SQLite descartable nueva, con el mismo script `prep_sqlite_preview.py` del 1c (en el scratchpad). Agregar, después de los motivos de anulación:
  - una `CashRegister(name='Caja principal')`;
  - una `ExpenseCategory(name='Insumos')`.

  Levantar el backend y el frontend como en el 1c.

- [ ] **Step 3: Verificación manual** (spec, sección "Verificación manual"):
  1. Abrir caja con fondo; el indicador cambia.
  2. Cobrar en efectivo con vuelto y con débito; las tarjetas se actualizan.
  3. Gasto (aparece en Gastos con `de_caja`), retiro e ingreso; admin anula uno.
  4. Intentar cerrar con una mesa abierta: bloqueado.
  5. Cobrar la mesa; cerrar con una diferencia en efectivo (nota obligatoria).
  6. Ver la sesión en Finanzas → Cajas y reabrirla como admin.
  7. Cobrar sin caja: aviso en el cobro y fila en "Pagos sin caja".
  8. Con una sesión nueva abierta, anular un pago de la sesión anterior: descuenta en la nueva y la anterior no cambia.
  9. Otra pestaña con `/pos` ve el cambio de estado de la caja en unos 3 s (con el panel visible).
