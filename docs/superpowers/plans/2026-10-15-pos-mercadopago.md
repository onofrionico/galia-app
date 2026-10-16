# MercadoPago integrado (sub-proyecto 5) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cobrar con el Point Smart desde la caja y Camarero, con registro automático e idempotente del pago y devolución opcional al anular, y conciliar los movimientos de la cuenta de MercadoPago con los pagos de Galia.

**Architecture:**
- **Backend:** un paquete `app/services/mercadopago/` con:
  - un cliente REST propio (`requests`) y un `FakeMercadoPago` intercambiable (`get_client`);
  - configuración cifrada;
  - servicios de cobro con Point, devolución y conciliación.
- **Resultado del Point:** llega por webhook firmado o por consulta de respaldo. Las dos vías usan `point_service.apply`, que bloquea la orden y crea el pago con `client_request_id` único.
- **Frontend:** la espera del cobro en el modal de pago, Ajustes → MercadoPago y Finanzas → Conciliación.

**Tech Stack:** Flask, SQLAlchemy 2.0, Alembic, pytest, `requests` (ya instalada), `cryptography`. React 18, React Query 5, Tailwind, Vitest.

**Spec:** `docs/superpowers/specs/2026-10-15-pos-mercadopago-design.md`

## Global Constraints

- **Worktree:** `C:\Users\onofr\Desktop\galia-app\.claude\worktrees\pos-base`, rama `feature/pos-mercadopago` (sale de `main` en `d44ca14`). Las rutas del plan son relativas a esa raíz.
- **Python** (`PY`): `C:\Users\onofr\Desktop\galia-app\backend\venv\Scripts\python.exe` (3.10). Los tests corren con cwd = `backend/`: `PY -m pytest -q -p no:cacheprovider <archivos>`.
- **Node:** con cwd = `frontend/` (`npm test`, `npm run build`, `npx vitest run <archivo>`); o desde otro directorio con `npm --prefix <worktree>/frontend …`. Nunca correr vitest desde la raíz.
- **Edición y git:** solo con Edit/Write. El sandbox rechaza heredocs complejos y `cd` + git, así que git va con `git -C <worktree>`.
- **Línea base del backend:** `PY scripts/compare_baseline.py <salida> ../docs/superpowers/plans/2026-10-08-pos-base-test-baseline.txt`. Criterio: `Sin fallas nuevas.`
- **Vitest:** entorno `node`, solo lógica pura, con imports relativos.
- **Migración:** `b5a0_add_mercadopago` con `down_revision = 'b4a0_add_fiscal_invoicing'`.
- **Errores:**
  - `PosError` (409 por defecto), `bad_request`, `forbidden` y `not_found`, de `app.services.pos.errors`;
  - mensajes en castellano rioplatense;
  - el detalle técnico de MercadoPago va al log, nunca a la caja.
- **Fechas:** se guardan en UTC naive (`common.now()`). El día de conciliación es el día de Argentina (`ARGENTINA_TZ`).
- **`FakeMercadoPago`:** solo se activa con `MP_FAKE=1` **y** base SQLite.

**Datos de la API de MercadoPago** (verificados en la documentación oficial el 2026-10-15, salvo donde dice "a confirmar"):
- **Crear orden:** `POST https://api.mercadopago.com/v1/orders`, con el header `X-Idempotency-Key`.
  - Cuerpo: `{"type": "point", "external_reference", "expiration_time": "PT10M", "transactions": {"payments": [{"amount": "1234.00"}]}, "config": {"point": {"terminal_id", "print_on_terminal": "no_ticket"}}}`.
  - El monto va como **string** con 2 decimales.
- **Consultar:** `GET /v1/orders/{id}`. Trae `status` y `status_detail`, y en `transactions.payments[]` los campos `id`, `amount`, `status`, `status_detail` y `reference_id` (este último a confirmar).
- **Estados de la orden:** `created`, `at_terminal`, `processed`, `canceled`, `expired`, `refunded`. También `failed` y `action_required`, a confirmar.
- **Cancelar:** `POST /v1/orders/{id}/cancel`.
  - En `created` responde 200 y la orden pasa a `canceled`.
  - En `at_terminal` necesita el header `x-allow-cancelable-status: at_terminal`, responde 202 y la confirmación llega por webhook.
  - Sin ese header, en `at_terminal` responde 409 `cannot_cancel_order`.
- **Devolver:** `POST /v1/orders/{id}/refund` sin cuerpo (total), con `X-Idempotency-Key`. La orden pasa a `refunded`.
- **Terminales:** `GET /terminals/v1/list` (respuesta `data.terminals[]` con `id` y `operating_mode`). Para pasar a modo PDV: `PATCH /terminals/v1/setup` con `{"terminals": [{"id", "operating_mode": "PDV"}]}` (a confirmar).
- **Cuenta y pagos:**
  - `GET /users/me`;
  - `GET /v1/payments/search?range=date_created&begin_date&end_date&sort=date_created&criteria=asc&limit=50&offset`, que devuelve `results[]` y `paging.total`.
- **Webhook:** el tema es `orders` y el cuerpo trae `{"type", "action", "data": {"id"}}`.
  - Header `x-signature: ts=<ts>,v1=<hex>` y header `x-request-id`.
  - El *manifest* es `id:<data.id>;request-id:<x-request-id>;ts:<ts>;`. Si una parte falta, se omite; `data.id` va en minúsculas si es alfanumérico.
  - La firma es un HMAC-SHA256 en hex con la clave secreta.
  - Tanto el *manifest* como el lugar del `data.id` (query o cuerpo) están **a confirmar en el entorno de prueba**.
- **Ajustes al spec, por la documentación** (quedan como decisiones en el ledger y en la guía):
  - **Devolución:** se hace sobre la **orden**, así que "Devolver también en MercadoPago" solo aparece en pagos que vinieron de un cobro con el Point. Los pagos con `mp_payment_id` cargados desde la conciliación solo se anulan en Galia.
  - **Cancelar:** se permite en `created` y en `at_terminal` (con el header). En `at_terminal` queda "cancelando" hasta el aviso.
  - **Vencimiento:** el vencimiento local de 10 min se reemplaza por `expiration_time: "PT10M"` en la orden; MercadoPago la vence y avisa.
  - **Cruce automático en la conciliación:** además del `mp_payment_id`, un movimiento con `external_reference` igual al de una orden de Point aprobada se cruza con el pago de esa orden.

## Review Focus

1. **El webhook y la consulta de respaldo aplican la misma orden aprobada casi al mismo tiempo:** hay un solo pago en la venta. Lo cubren la Task 3 (`test_apply_twice_creates_one_payment`) y la Task 6 (PostgreSQL).
2. **El cobro se aprueba por un monto distinto del pedido, o la venta ya no tiene saldo (se cobró de otra forma mientras tanto):** se registra hasta el saldo y la orden queda con "Cobrado de más: $X". Lo cubre la Task 3 (`test_approved_over_balance_is_flagged`).
3. **El aviso de MercadoPago llega con una firma inválida o con un tema desconocido:** responde 401 o 200 sin efectos. Lo cubre la Task 6 (`test_webhook_signature`).
4. **Anular con "Devolver también" cuando MercadoPago rechaza o no responde:** el pago **no** se anula en Galia. Lo cubre la Task 4 (`test_refund_rejected_keeps_payment`).
5. **Volver a traer un día ya conciliado:** no duplica movimientos y conserva las resoluciones. Lo cubre la Task 5 (`test_fetch_twice_is_idempotent`).

## Mapa de archivos

**Backend**
- Create:
  - `backend/app/models/mercadopago.py`;
  - `backend/migrations/versions/b5a0_add_mercadopago.py`;
  - `backend/app/services/mercadopago/__init__.py` (`get_client`, errores);
  - `client.py`, `fake.py`, `settings.py`, `point_service.py`, `webhook.py`, `refund_service.py`, `reconciliation_service.py`, `summary.py` (estos dentro de `backend/app/services/mercadopago/`);
  - `backend/app/routes/mercadopago.py`;
  - `docs/pos/mercadopago.md`.
- Modify:
  - `backend/app/models/__init__.py`, `backend/app/models/pos/payments.py` (`is_mercadopago`, `mp_payment_id`);
  - `backend/app/routes/pos_config.py` (medio de pago);
  - `backend/app/routes/pos_sales.py` (`refund_mp`);
  - `backend/app/services/pos/serializers.py` (`point_order`, `mp_payment_id`);
  - `backend/app/__init__.py`.
- Tests:
  - `backend/tests/mp_helpers.py`;
  - `test_mp_models.py`, `test_mp_client.py`, `test_mp_point.py`, `test_mp_refund.py`, `test_mp_reconciliation.py`, `test_mp_api.py`, `test_mp_concurrency_pg.py`, `test_mp_sandbox.py`;
  - `test_migration_chain.py`, `test_route_access_coverage.py`.

**Frontend**
- Create:
  - `frontend/src/pos/mercadopago/pointCharge.js` (+ test), `reconciliation.js` (+ test);
  - `PointWait.jsx`, `PointPendingNotice.jsx` (en `frontend/src/pos/mercadopago/`);
  - `frontend/src/pages/admin/MercadoPagoSettings.jsx`, `frontend/src/pages/MpReconciliation.jsx`.
- Modify:
  - `frontend/src/pos/api/posApi.js`, `frontend/src/pos/hooks/keys.js`;
  - `frontend/src/pos/modals/PaymentModal.jsx`, `CancelReasonModal.jsx`;
  - `frontend/src/pos/sale/SalePanel.jsx`;
  - `frontend/src/pages/admin/PosSettings.jsx`;
  - `frontend/src/App.jsx`, `frontend/src/components/layout/Sidebar.jsx`.

---

### Task 1: Modelos, migración, flags de medios de pago y módulo "Conciliar"

**Files:**
- Create: `backend/app/models/mercadopago.py`, `backend/migrations/versions/b5a0_add_mercadopago.py`, `backend/tests/test_mp_models.py`
- Modify: `backend/app/models/__init__.py`, `backend/app/models/pos/payments.py`, `backend/app/routes/pos_config.py`, `backend/app/services/pos/serializers.py`, `backend/tests/test_migration_chain.py`

**Interfaces:**
- Produces:
  - **Modelos:**
    - `MpSettings` (`SETTINGS_ID = 1`), con `token(environment)` / `set_token(environment, value)` sobre `test_access_token` y `prod_access_token`;
    - `MpPointOrder`, con `ACTIVE_STATUSES = ('creating', 'created', 'processing', 'canceling')` y `FINAL_STATUSES = ('approved', 'failed', 'canceled', 'expired')`;
    - `MpMovement`;
    - `MpReconciliation`, con `RESOLUTION_KINDS = ('matched_manual', 'payment_created', 'not_a_sale', 'reviewed')`.
  - **Medios de pago:**
    - `PaymentMethod.is_mercadopago` (en `to_dict`), editable en `/pos/config/payment-methods`;
    - `PosPayment.mp_payment_id`, que `payment_to_dict` devuelve.
  - **Permiso:** el módulo `Conciliar` sembrado por la migración.

- [ ] **Step 1: Tests que fallan.** Crear `backend/tests/test_mp_models.py`:

```python
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import MpPointOrder
from app.services.pos import sale_service
from app.services.pos.common import now
from app.services.pos.serializers import payment_to_dict
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401


def _order(sale, user, terminal='T1', status='created'):
    order = MpPointOrder(sale_id=sale.id, amount=Decimal('100'), terminal_id=terminal,
                         external_reference=f'galia-venta-{sale.id}-x{status}', idempotency_key=f'k-{status}-{terminal}',
                         status=status, created_by=user.id, created_at=now(), updated_at=now())
    db.session.add(order)
    db.session.commit()
    return order


def test_one_active_order_per_terminal(pos_app):
    user = make_user('caja@test.com', modules=('POS',))
    make_catalog()
    _salon, t1, _t2 = make_floor()
    sale = sale_service.open_sale(user, 'salon', table_id=t1.id, people=1)
    _order(sale, user, status='created')
    with pytest.raises(IntegrityError):
        _order(sale, user, status='processing')
    db.session.rollback()
    _order(sale, user, status='approved')  # los finales no cuentan
    _order(sale, user, terminal='T2', status='created')


def test_payment_method_is_mercadopago_flag(pos_app):
    client = pos_app.test_client()
    admin = auth_headers(client, make_user('admin@test.com', role='admin'))
    created = client.post('/api/v1/pos/config/payment-methods', json={'name': 'Point', 'kind': 'card',
                                                                       'is_mercadopago': True}, headers=admin)
    assert created.status_code == 201 and created.get_json()['is_mercadopago'] is True
    other = client.post('/api/v1/pos/config/payment-methods', json={'name': 'Visa', 'kind': 'card'}, headers=admin)
    assert other.get_json()['is_mercadopago'] is False


def test_payment_dict_includes_mp_payment_id(pos_app):
    user = make_user('caja@test.com', modules=('POS',))
    cat = make_catalog()
    sale = sale_service.open_sale(user, 'counter')
    sale_service.add_item(user, sale.id, cat.unidad.id)
    from app.services.pos import payment_service
    payment_service.add_payment(user, sale.id, cat.debito.id, 900)
    payment = sale.payments[0]
    payment.mp_payment_id = '123'
    db.session.commit()
    assert payment_to_dict(payment)['mp_payment_id'] == '123'
```

En `backend/tests/test_migration_chain.py` agregar:

```python


def test_mercadopago_follows_fiscal_invoicing():
    assert _revisions()['b5a0_add_mercadopago'] == ['b4a0_add_fiscal_invoicing']
```

- [ ] **Step 2: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_mp_models.py tests/test_migration_chain.py`
Expected: ImportError (`MpPointOrder`) y `KeyError: 'b5a0_add_mercadopago'`.

- [ ] **Step 3: Modelos.** Crear `backend/app/models/mercadopago.py`:

```python
"""MercadoPago: configuración, cobros con Point, movimientos de la cuenta y resoluciones de conciliación."""
from app.extensions import db

SETTINGS_ID = 1
ENVIRONMENTS = ('test', 'production')
ACTIVE_STATUSES = ('creating', 'created', 'processing', 'canceling')
FINAL_STATUSES = ('approved', 'failed', 'canceled', 'expired')
RESOLUTION_KINDS = ('matched_manual', 'payment_created', 'not_a_sale', 'reviewed')


class MpSettings(db.Model):
    """Una sola fila. Los tokens y el secreto del webhook van cifrados."""
    __tablename__ = 'mp_settings'

    id = db.Column(db.Integer, primary_key=True)
    environment = db.Column(db.String(12), nullable=False, default='test')
    test_access_token = db.Column(db.Text, nullable=True)
    prod_access_token = db.Column(db.Text, nullable=True)
    terminal_id = db.Column(db.String(80), nullable=True)
    webhook_secret = db.Column(db.Text, nullable=True)
    point_payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_methods.id'), nullable=True)
    user_id = db.Column(db.String(30), nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)

    def token(self, environment):
        return self.prod_access_token if environment == 'production' else self.test_access_token

    def set_token(self, environment, value):
        if environment == 'production':
            self.prod_access_token = value
        else:
            self.test_access_token = value


class MpPointOrder(db.Model):
    __tablename__ = 'mp_point_orders'
    __table_args__ = (
        db.Index('ix_mp_point_orders_sale_id', 'sale_id'),
        # Un cobro activo por terminal.
        db.Index('uq_mp_point_orders_active_terminal', 'terminal_id', unique=True,
                 postgresql_where=db.text("status IN ('creating', 'created', 'processing', 'canceling')"),
                 sqlite_where=db.text("status IN ('creating', 'created', 'processing', 'canceling')")),
    )

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('pos_sales.id'), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    terminal_id = db.Column(db.String(80), nullable=False)
    mp_order_id = db.Column(db.String(80), nullable=True, unique=True)
    external_reference = db.Column(db.String(64), nullable=False, unique=True)
    idempotency_key = db.Column(db.String(64), nullable=False, unique=True)
    status = db.Column(db.String(12), nullable=False)
    status_detail = db.Column(db.String(80), nullable=True)
    error = db.Column(db.String(255), nullable=True)
    mp_payment_id = db.Column(db.String(80), nullable=True)
    approved_amount = db.Column(db.Numeric(12, 2), nullable=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('pos_payments.id'), nullable=True)
    refunded_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    last_checked_at = db.Column(db.DateTime, nullable=True)

    sale = db.relationship('PosSale')
    payment = db.relationship('PosPayment')


class MpMovement(db.Model):
    __tablename__ = 'mp_movements'

    id = db.Column(db.Integer, primary_key=True)
    mp_payment_id = db.Column(db.String(80), nullable=False, unique=True)
    date_created = db.Column(db.DateTime, nullable=False)
    business_date = db.Column(db.Date, nullable=False, index=True)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    refunded_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    net_amount = db.Column(db.Numeric(14, 2), nullable=True)
    currency = db.Column(db.String(5), nullable=True)
    status = db.Column(db.String(30), nullable=False)
    status_detail = db.Column(db.String(80), nullable=True)
    channel = db.Column(db.String(12), nullable=False)
    payment_type = db.Column(db.String(30), nullable=True)
    payment_method = db.Column(db.String(30), nullable=True)
    description = db.Column(db.String(255), nullable=True)
    external_reference = db.Column(db.String(64), nullable=True, index=True)
    payer_label = db.Column(db.String(120), nullable=True)
    raw = db.Column(db.JSON, nullable=True)
    fetched_at = db.Column(db.DateTime, nullable=False)


class MpReconciliation(db.Model):
    __tablename__ = 'mp_reconciliations'
    __table_args__ = (
        db.Index('uq_mp_reconciliations_movement', 'mp_movement_id', unique=True,
                 postgresql_where=db.text('mp_movement_id IS NOT NULL'),
                 sqlite_where=db.text('mp_movement_id IS NOT NULL')),
        db.Index('uq_mp_reconciliations_payment', 'payment_id', unique=True,
                 postgresql_where=db.text('payment_id IS NOT NULL'), sqlite_where=db.text('payment_id IS NOT NULL')),
    )

    id = db.Column(db.Integer, primary_key=True)
    mp_movement_id = db.Column(db.Integer, db.ForeignKey('mp_movements.id'), nullable=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('pos_payments.id'), nullable=True)
    kind = db.Column(db.String(20), nullable=False)
    note = db.Column(db.String(255), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
```

En `backend/app/models/__init__.py`, después del import de `fiscal`:

```python
from app.models.mercadopago import MpMovement, MpPointOrder, MpReconciliation, MpSettings
```

y sumar esos cuatro nombres al principio de `__all__`.

En `backend/app/models/pos/payments.py`:
- en `PaymentMethod`, después de `invoiced_externally`:

```python
    # Los pagos de este medio entran a la cuenta de MercadoPago (se concilian).
    is_mercadopago = db.Column(db.Boolean, nullable=False, default=False)
```

  y sumar `'is_mercadopago': self.is_mercadopago` a su `to_dict`;
- en `PosPayment`, después de `cancel_cash_session_id`:

```python
    # Id del pago en MercadoPago (cobros del Point o asociados en la conciliación).
    mp_payment_id = db.Column(db.String(80), nullable=True, index=True)
```

En `backend/app/routes/pos_config.py`, en `_apply_payment_method`, al final:

```python
    if 'is_mercadopago' in data:
        method.is_mercadopago = bool(data['is_mercadopago'])
```

En `backend/app/services/pos/serializers.py`, en `payment_to_dict`, sumar `'mp_payment_id': payment.mp_payment_id,`.

- [ ] **Step 4: Migración.** Crear `backend/migrations/versions/b5a0_add_mercadopago.py`:

```python
"""add MercadoPago settings, Point orders, movements, reconciliations; payment flags; Conciliar module

Revision ID: b5a0_add_mercadopago
Revises: b4a0_add_fiscal_invoicing
Create Date: 2026-10-15 12:00:00.000000

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = 'b5a0_add_mercadopago'
down_revision = 'b4a0_add_fiscal_invoicing'
branch_labels = None
depends_on = None

ACTIVE = "status IN ('creating', 'created', 'processing', 'canceling')"


def upgrade():
    op.create_table(
        'mp_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('environment', sa.String(length=12), nullable=False, server_default='test'),
        sa.Column('test_access_token', sa.Text(), nullable=True),
        sa.Column('prod_access_token', sa.Text(), nullable=True),
        sa.Column('terminal_id', sa.String(length=80), nullable=True),
        sa.Column('webhook_secret', sa.Text(), nullable=True),
        sa.Column('point_payment_method_id', sa.Integer(), sa.ForeignKey('payment_methods.id'), nullable=True),
        sa.Column('user_id', sa.String(length=30), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('payment_methods') as batch:
        batch.add_column(sa.Column('is_mercadopago', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.execute("UPDATE payment_methods SET is_mercadopago = true WHERE lower(name) LIKE '%mercado%'")
    with op.batch_alter_table('pos_payments') as batch:
        batch.add_column(sa.Column('mp_payment_id', sa.String(length=80), nullable=True))
    op.create_index('ix_pos_payments_mp_payment_id', 'pos_payments', ['mp_payment_id'])
    op.create_table(
        'mp_point_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sale_id', sa.Integer(), sa.ForeignKey('pos_sales.id'), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('terminal_id', sa.String(length=80), nullable=False),
        sa.Column('mp_order_id', sa.String(length=80), nullable=True),
        sa.Column('external_reference', sa.String(length=64), nullable=False),
        sa.Column('idempotency_key', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=12), nullable=False),
        sa.Column('status_detail', sa.String(length=80), nullable=True),
        sa.Column('error', sa.String(length=255), nullable=True),
        sa.Column('mp_payment_id', sa.String(length=80), nullable=True),
        sa.Column('approved_amount', sa.Numeric(12, 2), nullable=True),
        sa.Column('payment_id', sa.Integer(), sa.ForeignKey('pos_payments.id'), nullable=True),
        sa.Column('refunded_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_checked_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('mp_order_id'),
        sa.UniqueConstraint('external_reference'),
        sa.UniqueConstraint('idempotency_key'),
    )
    op.create_index('ix_mp_point_orders_sale_id', 'mp_point_orders', ['sale_id'])
    op.create_index('uq_mp_point_orders_active_terminal', 'mp_point_orders', ['terminal_id'], unique=True,
                    postgresql_where=sa.text(ACTIVE), sqlite_where=sa.text(ACTIVE))
    op.create_table(
        'mp_movements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('mp_payment_id', sa.String(length=80), nullable=False),
        sa.Column('date_created', sa.DateTime(), nullable=False),
        sa.Column('business_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(14, 2), nullable=False),
        sa.Column('refunded_amount', sa.Numeric(14, 2), nullable=False, server_default='0'),
        sa.Column('net_amount', sa.Numeric(14, 2), nullable=True),
        sa.Column('currency', sa.String(length=5), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('status_detail', sa.String(length=80), nullable=True),
        sa.Column('channel', sa.String(length=12), nullable=False),
        sa.Column('payment_type', sa.String(length=30), nullable=True),
        sa.Column('payment_method', sa.String(length=30), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('external_reference', sa.String(length=64), nullable=True),
        sa.Column('payer_label', sa.String(length=120), nullable=True),
        sa.Column('raw', sa.JSON(), nullable=True),
        sa.Column('fetched_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('mp_payment_id'),
    )
    op.create_index('ix_mp_movements_business_date', 'mp_movements', ['business_date'])
    op.create_index('ix_mp_movements_external_reference', 'mp_movements', ['external_reference'])
    op.create_table(
        'mp_reconciliations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('mp_movement_id', sa.Integer(), sa.ForeignKey('mp_movements.id'), nullable=True),
        sa.Column('payment_id', sa.Integer(), sa.ForeignKey('pos_payments.id'), nullable=True),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('uq_mp_reconciliations_movement', 'mp_reconciliations', ['mp_movement_id'], unique=True,
                    postgresql_where=sa.text('mp_movement_id IS NOT NULL'),
                    sqlite_where=sa.text('mp_movement_id IS NOT NULL'))
    op.create_index('uq_mp_reconciliations_payment', 'mp_reconciliations', ['payment_id'], unique=True,
                    postgresql_where=sa.text('payment_id IS NOT NULL'), sqlite_where=sa.text('payment_id IS NOT NULL'))
    now = datetime.utcnow()
    bind = op.get_bind()
    exists = bind.execute(sa.text("SELECT id FROM modules WHERE name = 'Conciliar'")).first()
    if exists is None:
        modules = sa.table('modules', sa.column('name', sa.String), sa.column('display_name', sa.String),
                           sa.column('description', sa.Text), sa.column('icon', sa.String),
                           sa.column('category', sa.String), sa.column('route', sa.String),
                           sa.column('is_active', sa.Boolean), sa.column('created_at', sa.DateTime),
                           sa.column('updated_at', sa.DateTime))
        op.bulk_insert(modules, [{'name': 'Conciliar', 'display_name': 'Conciliar MercadoPago',
                                  'description': 'Traer movimientos de MercadoPago y resolver diferencias',
                                  'icon': None, 'category': 'Operations', 'route': '/mp/reconciliation',
                                  'is_active': True, 'created_at': now, 'updated_at': now}])
        module_id = bind.execute(sa.text("SELECT id FROM modules WHERE name = 'Conciliar'")).scalar()
        role_permissions = sa.table('role_permissions', sa.column('role', sa.String),
                                    sa.column('module_id', sa.Integer), sa.column('is_granted', sa.Boolean),
                                    sa.column('created_at', sa.DateTime), sa.column('updated_at', sa.DateTime))
        op.bulk_insert(role_permissions, [
            {'role': 'admin', 'module_id': module_id, 'is_granted': True, 'created_at': now, 'updated_at': now},
            {'role': 'employee', 'module_id': module_id, 'is_granted': False, 'created_at': now, 'updated_at': now},
        ])


def downgrade():
    bind = op.get_bind()
    module_id = bind.execute(sa.text("SELECT id FROM modules WHERE name = 'Conciliar'")).scalar()
    if module_id is not None:
        bind.execute(sa.text('DELETE FROM user_permissions WHERE module_id = :id'), {'id': module_id})
        bind.execute(sa.text('DELETE FROM role_permissions WHERE module_id = :id'), {'id': module_id})
        bind.execute(sa.text('DELETE FROM modules WHERE id = :id'), {'id': module_id})
    op.drop_index('uq_mp_reconciliations_payment', table_name='mp_reconciliations')
    op.drop_index('uq_mp_reconciliations_movement', table_name='mp_reconciliations')
    op.drop_table('mp_reconciliations')
    op.drop_index('ix_mp_movements_external_reference', table_name='mp_movements')
    op.drop_index('ix_mp_movements_business_date', table_name='mp_movements')
    op.drop_table('mp_movements')
    op.drop_index('uq_mp_point_orders_active_terminal', table_name='mp_point_orders')
    op.drop_index('ix_mp_point_orders_sale_id', table_name='mp_point_orders')
    op.drop_table('mp_point_orders')
    op.drop_index('ix_pos_payments_mp_payment_id', table_name='pos_payments')
    with op.batch_alter_table('pos_payments') as batch:
        batch.drop_column('mp_payment_id')
    with op.batch_alter_table('payment_methods') as batch:
        batch.drop_column('is_mercadopago')
    op.drop_table('mp_settings')
```

Antes de escribir el bloque de módulos, revisar en `b1a4_add_pos_sales_engine.py` los nombres reales de las columnas de `modules`, `role_permissions` y `user_permissions`, y ajustar el `sa.table` a esos nombres si difieren.

- [ ] **Step 5: Correr**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_mp_models.py tests/test_migration_chain.py tests/test_pos_config_api.py tests/test_fiscal_models.py`
Expected: todos pasan.

- [ ] **Step 6: Commit**

```bash
git -C <worktree> add backend/app/models backend/migrations/versions/b5a0_add_mercadopago.py backend/app/routes/pos_config.py backend/app/services/pos/serializers.py backend/tests/test_mp_models.py backend/tests/test_migration_chain.py
git -C <worktree> commit -m "feat(mp): MercadoPago models, migration and payment method flag"
```

---

### Task 2: Cliente de MercadoPago, fake, configuración y firma del webhook

**Files:**
- Create:
  - `backend/app/services/mercadopago/__init__.py`, `client.py`, `fake.py`, `settings.py`, `webhook.py`;
  - `backend/tests/mp_helpers.py`, `backend/tests/test_mp_client.py`.

**Interfaces:**
- Consumes: modelos de la Task 1.
- Produces:
  - **`app.services.mercadopago`:**
    - `MpUnavailable(Exception)` y `MpRejected(Exception)` con `.status`, `.code` y `.message`;
    - `fake_enabled()`;
    - `get_client(settings) -> MpClient | FakeMercadoPago`.
  - **`client`:**
    - `ORDER_STATUS_MAP` y `order_state(order_json) -> {'status', 'status_detail', 'mp_payment_id', 'approved_amount'}`;
    - `money_str(Decimal) -> '1234.00'`;
    - `movement_fields(payment_json) -> dict` y `channel_of(payment_json) -> str`;
    - `MpClient(access_token)` con:
      - `me()`, `list_terminals()`, `set_pdv_mode(terminal_id)`;
      - `create_order(terminal_id, amount, external_reference, idempotency_key)`;
      - `get_order(order_id)`, `cancel_order(order_id, at_terminal=False)`, `refund_order(order_id, idempotency_key)`;
      - `search_payments(begin_utc, end_utc, offset=0)`.
  - **`fake.FakeMercadoPago`:** la misma API, más:
    - `simulate(order_id, outcome)`, con `outcome` en `approved`, `rejected`, `expired` o `processing`;
    - `add_payment_movement(...)`, `fail_next(kind)`, `reset()`;
    - estado de clase en `orders`, `payments` y `refunds`.
  - **`settings`:**
    - `get_settings(lock=False)`, `get_or_create_settings()`;
    - `encrypt(text)` / `decrypt(token)`, con HKDF `info=b'galia-mp-token'`;
    - `access_token(settings)`;
    - `missing(settings) -> list[str]`, `require_ready(settings)`;
    - `settings_to_dict(settings)`.
  - **`webhook`:** `verify_signature(secret, x_signature, x_request_id, data_id) -> bool`.
  - **`tests/mp_helpers.py`:**
    - `configure_mp(point_method=None) -> MpSettings` (entorno `test`, token `TEST-TOKEN`, terminal `PAX_A910__SMARTPOS1`, secreto `whsec`, medio Point creado si no se pasa);
    - `billing_sale(user, cat, table)`: mesa con 2 medialunas ($1800) y la cuenta pedida.

- [ ] **Step 1: Tests que fallan.** Crear `backend/tests/mp_helpers.py`:

```python
"""Fábricas compartidas por los tests de MercadoPago."""
from app.extensions import db
from app.models.pos import PaymentMethod
from app.services.mercadopago import settings as mp_settings
from app.services.pos import sale_service

TERMINAL = 'PAX_A910__SMARTPOS1'


def configure_mp(point_method=None):
    if point_method is None:
        point_method = PaymentMethod(name='MercadoPago Point', kind='card', position=9, is_mercadopago=True)
        db.session.add(point_method)
        db.session.flush()
    settings = mp_settings.get_or_create_settings()
    settings.environment = 'test'
    settings.set_token('test', mp_settings.encrypt('TEST-TOKEN'))
    settings.terminal_id = TERMINAL
    settings.webhook_secret = mp_settings.encrypt('whsec')
    settings.point_payment_method_id = point_method.id
    db.session.commit()
    return settings


def billing_sale(user, cat, table):
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=1)
    sale_service.add_item(user, sale.id, cat.unidad.id, quantity=2)
    sale_service.confirm_batch(user, sale.id)
    return sale_service.request_bill(user, sale.id)
```

Crear `backend/tests/test_mp_client.py`:

```python
import hashlib
import hmac
from decimal import Decimal

import pytest

from app.services import mercadopago
from app.services.mercadopago import client as mpc
from app.services.mercadopago import settings as mps
from app.services.mercadopago.fake import FakeMercadoPago
from app.services.mercadopago.webhook import verify_signature
from mp_helpers import configure_mp
from pos_helpers import pos_app  # noqa: F401


def _order(status, payment_status=None, detail=None, amount='1800.00'):
    payments = [] if payment_status is None else [
        {'id': 'PAY01', 'amount': amount, 'paid_amount': amount, 'status': payment_status,
         'status_detail': detail, 'reference_id': '987654'}]
    return {'id': 'ORD01', 'status': status, 'status_detail': detail, 'transactions': {'payments': payments}}


def test_order_state_mapping():
    assert mpc.order_state(_order('created'))['status'] == 'created'
    assert mpc.order_state(_order('at_terminal'))['status'] == 'processing'
    approved = mpc.order_state(_order('processed', 'processed', 'accredited'))
    assert approved == {'status': 'approved', 'status_detail': 'accredited', 'mp_payment_id': '987654',
                        'approved_amount': Decimal('1800.00')}
    assert mpc.order_state(_order('canceled'))['status'] == 'canceled'
    assert mpc.order_state(_order('expired'))['status'] == 'expired'
    rejected = mpc.order_state(_order('failed', 'rejected', 'cc_rejected_insufficient_amount'))
    assert rejected['status'] == 'failed' and rejected['status_detail'] == 'cc_rejected_insufficient_amount'
    assert mpc.order_state(_order('refunded', 'refunded'))['status'] == 'approved'
    assert mpc.order_state(_order('something_new'))['status'] == 'processing'


def test_money_and_channels():
    assert mpc.money_str(Decimal('1234.5')) == '1234.50'
    assert mpc.channel_of({'point_of_interaction': {'type': 'POINT'}}) == 'point'
    assert mpc.channel_of({'point_of_interaction': {'type': 'INSTORE'}, 'payment_type_id': 'account_money'}) == 'qr'
    assert mpc.channel_of({'payment_type_id': 'bank_transfer'}) == 'transfer'
    assert mpc.channel_of({'operation_type': 'regular_payment', 'payment_type_id': 'credit_card'}) == 'link'
    assert mpc.channel_of({'payment_type_id': 'ticket'}) == 'other'


def test_movement_fields():
    fields = mpc.movement_fields({
        'id': 123, 'date_created': '2026-10-15T01:30:00.000-03:00', 'transaction_amount': 1800,
        'transaction_amount_refunded': 0, 'transaction_details': {'net_received_amount': 1750.5},
        'currency_id': 'ARS', 'status': 'approved', 'status_detail': 'accredited', 'payment_type_id': 'debit_card',
        'payment_method_id': 'debvisa', 'description': 'Venta', 'external_reference': 'galia-venta-1-1',
        'point_of_interaction': {'type': 'POINT'}, 'payer': {'email': 'cliente@example.com',
                                                               'identification': {'number': '30123456'}}})
    assert fields['mp_payment_id'] == '123' and fields['amount'] == Decimal('1800.00')
    assert fields['business_date'].isoformat() == '2026-10-15' and fields['channel'] == 'point'
    assert fields['net_amount'] == Decimal('1750.50') and 'cliente' not in str(fields['raw'])
    assert fields['payer_label'] == 'debvisa'


def test_webhook_signature():
    secret, request_id, data_id, ts = 'whsec', 'req-1', 'ORD01ABC', '1704908010'
    manifest = f'id:{data_id.lower()};request-id:{request_id};ts:{ts};'
    digest = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    assert verify_signature(secret, f'ts={ts},v1={digest}', request_id, data_id) is True
    assert verify_signature(secret, f'ts={ts},v1={"0" * 64}', request_id, data_id) is False
    assert verify_signature(secret, None, request_id, data_id) is False
    assert verify_signature(None, f'ts={ts},v1={digest}', request_id, data_id) is False


def test_settings_encryption_and_missing(pos_app):
    settings = mps.get_or_create_settings()
    assert 'token de prueba' in mps.missing(settings)
    configure_mp()
    settings = mps.get_settings()
    assert mps.missing(settings) == [] and mps.access_token(settings) == 'TEST-TOKEN'
    assert 'TEST-TOKEN' not in str(mps.settings_to_dict(settings))
    pos_app.config['SECRET_KEY'] = 'otra'
    assert any('no se puede leer' in item for item in mps.missing(settings))


def test_fake_client_only_with_flag_and_sqlite(pos_app, monkeypatch):
    configure_mp()
    monkeypatch.setenv('MP_FAKE', '1')
    assert isinstance(mercadopago.get_client(mps.get_settings()), FakeMercadoPago)
    monkeypatch.delenv('MP_FAKE')
    assert isinstance(mercadopago.get_client(mps.get_settings()), mpc.MpClient)


def test_fake_order_lifecycle(pos_app):
    FakeMercadoPago.reset()
    fake = FakeMercadoPago()
    order = fake.create_order('T1', Decimal('100'), 'ref-1', 'key-1')
    assert fake.create_order('T1', Decimal('100'), 'ref-1', 'key-1')['id'] == order['id']  # idempotente
    assert mpc.order_state(fake.get_order(order['id']))['status'] == 'created'
    fake.simulate(order['id'], 'approved')
    state = mpc.order_state(fake.get_order(order['id']))
    assert state['status'] == 'approved' and state['approved_amount'] == Decimal('100.00')
    assert fake.search_payments(None, None)['results'][0]['external_reference'] == 'ref-1'
    fake.refund_order(order['id'], 'r-1')
    assert fake.get_order(order['id'])['status'] == 'refunded'
    other = fake.create_order('T1', Decimal('5'), 'ref-2', 'key-2')
    fake.cancel_order(other['id'])
    assert fake.get_order(other['id'])['status'] == 'canceled'
    fake.fail_next('create')
    with pytest.raises(mercadopago.MpUnavailable):
        fake.create_order('T1', Decimal('5'), 'ref-3', 'key-3')
```

- [ ] **Step 2: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_mp_client.py`
Expected: `ModuleNotFoundError: app.services.mercadopago`.

- [ ] **Step 3: Paquete.** Crear `backend/app/services/mercadopago/__init__.py`:

```python
"""MercadoPago: cliente REST propio o FakeMercadoPago (desarrollo y tests)."""
import os

from app.extensions import db


class MpUnavailable(Exception):
    """MercadoPago no respondió (red, timeout, 5xx)."""


class MpRejected(Exception):
    """MercadoPago respondió con un error (4xx)."""

    def __init__(self, status, code, message):
        super().__init__(f'{status} {code}: {message}')
        self.status = status
        self.code = code
        self.message = message


def fake_enabled():
    return os.getenv('MP_FAKE') == '1' and db.engine.dialect.name == 'sqlite'


def get_client(settings):
    if fake_enabled():
        from app.services.mercadopago.fake import FakeMercadoPago
        return FakeMercadoPago()
    from app.services.mercadopago import settings as mp_settings
    from app.services.mercadopago.client import MpClient
    return MpClient(mp_settings.access_token(settings))
```

- [ ] **Step 4: Cliente.** Crear `backend/app/services/mercadopago/client.py`:

```python
"""Cliente REST de MercadoPago (Órdenes de Point, terminales, pagos). El armado y la lectura son puros."""
from datetime import datetime, timezone
from decimal import Decimal

import pytz
import requests

from app.services.mercadopago import MpRejected, MpUnavailable
from app.utils.timezone_utils import ARGENTINA_TZ

BASE_URL = 'https://api.mercadopago.com'
TIMEOUT = (5, 20)
ORDER_EXPIRATION = 'PT10M'
# Estado de la orden de MercadoPago -> estado de Galia.
ORDER_STATUS_MAP = {'created': 'created', 'at_terminal': 'processing', 'processed': 'approved',
                    'canceled': 'canceled', 'expired': 'expired', 'failed': 'failed', 'refunded': 'approved',
                    'action_required': 'processing'}
APPROVED_PAYMENT = ('approved', 'processed', 'accredited', 'refunded')
REJECTED_PAYMENT = ('rejected', 'failed')
RAW_FIELDS = ('id', 'date_created', 'date_approved', 'status', 'status_detail', 'transaction_amount',
              'transaction_amount_refunded', 'currency_id', 'payment_type_id', 'payment_method_id',
              'operation_type', 'external_reference', 'description')


def money_str(value):
    return f'{Decimal(value).quantize(Decimal("0.01")):.2f}'


def _money(value):
    return Decimal(str(value)).quantize(Decimal('0.01')) if value not in (None, '') else None


def order_state(order):
    """Estado de Galia de una orden de Point: status, status_detail, mp_payment_id, approved_amount."""
    payments = ((order.get('transactions') or {}).get('payments') or [])
    payment = payments[0] if payments else {}
    status = ORDER_STATUS_MAP.get(order.get('status'), 'processing')
    payment_status = payment.get('status')
    if payment_status in REJECTED_PAYMENT:
        status = 'failed'
    elif payment_status in APPROVED_PAYMENT and status in ('processing', 'approved'):
        status = 'approved'
    detail = payment.get('status_detail') or order.get('status_detail')
    approved = status == 'approved'
    payment_id = payment.get('reference_id') or payment.get('id')
    return {'status': status, 'status_detail': detail,
            'mp_payment_id': str(payment_id) if approved and payment_id else None,
            'approved_amount': _money(payment.get('paid_amount') or payment.get('amount')) if approved else None}


def channel_of(payment):
    poi = ((payment.get('point_of_interaction') or {}).get('type') or '').upper()
    payment_type = payment.get('payment_type_id')
    if poi == 'POINT':
        return 'point'
    if poi in ('INSTORE', 'QR', 'OPENPLATFORM'):
        return 'qr'
    if payment_type == 'bank_transfer':
        return 'transfer'
    if payment_type in ('credit_card', 'debit_card', 'account_money', 'prepaid_card'):
        return 'link'
    return 'other'


def movement_fields(payment):
    """Campos de mp_movements a partir de un pago de la búsqueda. Sin datos personales del pagador."""
    created = datetime.fromisoformat(payment['date_created'])
    created_utc = created.astimezone(timezone.utc).replace(tzinfo=None)
    business_date = created.astimezone(ARGENTINA_TZ).date()
    details = payment.get('transaction_details') or {}
    return {
        'mp_payment_id': str(payment['id']), 'date_created': created_utc, 'business_date': business_date,
        'amount': _money(payment.get('transaction_amount')) or Decimal('0.00'),
        'refunded_amount': _money(payment.get('transaction_amount_refunded')) or Decimal('0.00'),
        'net_amount': _money(details.get('net_received_amount')), 'currency': payment.get('currency_id'),
        'status': payment.get('status') or 'unknown', 'status_detail': payment.get('status_detail'),
        'channel': channel_of(payment), 'payment_type': payment.get('payment_type_id'),
        'payment_method': payment.get('payment_method_id'), 'description': (payment.get('description') or '')[:255],
        'external_reference': (payment.get('external_reference') or None) and payment['external_reference'][:64],
        'payer_label': payment.get('payment_method_id'),
        'raw': {k: payment.get(k) for k in RAW_FIELDS},
    }


def _iso(moment_utc):
    return pytz.utc.localize(moment_utc).astimezone(ARGENTINA_TZ).isoformat(timespec='milliseconds')


class MpClient:
    def __init__(self, access_token):
        self.access_token = access_token

    def _request(self, method, path, idempotency_key=None, extra_headers=None, **kwargs):
        headers = {'Authorization': f'Bearer {self.access_token}', 'Content-Type': 'application/json'}
        if idempotency_key:
            headers['X-Idempotency-Key'] = idempotency_key
        headers.update(extra_headers or {})
        try:
            response = requests.request(method, f'{BASE_URL}{path}', headers=headers, timeout=TIMEOUT, **kwargs)
        except requests.RequestException as exc:
            raise MpUnavailable(str(exc))
        if response.status_code >= 500:
            raise MpUnavailable(f'{response.status_code} {response.text[:200]}')
        data = response.json() if response.content else {}
        if response.status_code >= 400:
            errors = data.get('errors') or [{}]
            raise MpRejected(response.status_code, errors[0].get('code') or data.get('error') or '',
                             errors[0].get('message') or data.get('message') or response.text[:200])
        return data

    def me(self):
        return self._request('GET', '/users/me')

    def list_terminals(self):
        data = self._request('GET', '/terminals/v1/list', params={'limit': 50})
        return (data.get('data') or {}).get('terminals') or []

    def set_pdv_mode(self, terminal_id):
        return self._request('PATCH', '/terminals/v1/setup',
                             json={'terminals': [{'id': terminal_id, 'operating_mode': 'PDV'}]})

    def create_order(self, terminal_id, amount, external_reference, idempotency_key):
        body = {'type': 'point', 'external_reference': external_reference, 'expiration_time': ORDER_EXPIRATION,
                'transactions': {'payments': [{'amount': money_str(amount)}]},
                'config': {'point': {'terminal_id': terminal_id, 'print_on_terminal': 'no_ticket'}}}
        return self._request('POST', '/v1/orders', idempotency_key=idempotency_key, json=body)

    def get_order(self, order_id):
        return self._request('GET', f'/v1/orders/{order_id}')

    def cancel_order(self, order_id, at_terminal=False):
        extra = {'x-allow-cancelable-status': 'at_terminal'} if at_terminal else None
        return self._request('POST', f'/v1/orders/{order_id}/cancel', idempotency_key=f'cancel-{order_id}',
                             extra_headers=extra)

    def refund_order(self, order_id, idempotency_key):
        return self._request('POST', f'/v1/orders/{order_id}/refund', idempotency_key=idempotency_key)

    def search_payments(self, begin_utc, end_utc, offset=0):
        return self._request('GET', '/v1/payments/search', params={
            'range': 'date_created', 'begin_date': _iso(begin_utc), 'end_date': _iso(end_utc),
            'sort': 'date_created', 'criteria': 'asc', 'limit': 50, 'offset': offset})
```

- [ ] **Step 5: Fake.** Crear `backend/app/services/mercadopago/fake.py`:

```python
"""MercadoPago de mentira para tests y el preview local (MP_FAKE=1 con SQLite). Nunca en producción."""
import itertools
import threading
from datetime import datetime, timezone
from decimal import Decimal

from app.services.mercadopago import MpRejected, MpUnavailable


class FakeMercadoPago:
    orders = {}
    payments = []
    by_key = {}
    failures = set()
    _ids = itertools.count(1)
    _lock = threading.Lock()

    @classmethod
    def reset(cls):
        with cls._lock:
            cls.orders, cls.payments, cls.by_key, cls.failures = {}, [], {}, set()

    @classmethod
    def fail_next(cls, kind):
        cls.failures.add(kind)

    def _maybe_fail(self, kind):
        if kind in self.failures:
            self.failures.discard(kind)
            raise MpUnavailable(f'{kind} (simulado)')

    def me(self):
        return {'id': 1, 'nickname': 'GALIA-PRUEBA'}

    def list_terminals(self):
        return [{'id': 'PAX_A910__SMARTPOS1', 'operating_mode': 'PDV'}]

    def set_pdv_mode(self, terminal_id):
        return {'terminals': [{'id': terminal_id, 'operating_mode': 'PDV'}]}

    def create_order(self, terminal_id, amount, external_reference, idempotency_key):
        self._maybe_fail('create')
        with self._lock:
            if idempotency_key in self.by_key:
                return dict(self.orders[self.by_key[idempotency_key]])
            order_id = f'ORD{next(self._ids):05d}'
            self.orders[order_id] = {'id': order_id, 'status': 'created', 'external_reference': external_reference,
                                     'terminal_id': terminal_id, 'transactions': {'payments': [
                                         {'id': f'PAY{order_id}', 'amount': f'{Decimal(amount):.2f}',
                                          'status': 'created'}]}}
            self.by_key[idempotency_key] = order_id
            return dict(self.orders[order_id])

    def get_order(self, order_id):
        self._maybe_fail('get')
        if order_id not in self.orders:
            raise MpRejected(404, 'order_not_found', 'Order not found')
        return dict(self.orders[order_id])

    def simulate(self, order_id, outcome, paid_amount=None):
        """Lo que haría el Point: approved | rejected | expired | processing."""
        with self._lock:
            order = self.orders[order_id]
            payment = order['transactions']['payments'][0]
            if outcome == 'processing':
                order['status'] = 'at_terminal'
            elif outcome == 'approved':
                order['status'] = 'processed'
                payment.update({'status': 'processed', 'status_detail': 'accredited',
                                'paid_amount': paid_amount or payment['amount'],
                                'reference_id': str(70000 + len(self.payments))})
                self.payments.append({
                    'id': int(payment['reference_id']),
                    'date_created': datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
                    'transaction_amount': float(Decimal(payment['paid_amount'])), 'status': 'approved',
                    'status_detail': 'accredited', 'payment_type_id': 'debit_card', 'payment_method_id': 'debvisa',
                    'external_reference': order['external_reference'], 'currency_id': 'ARS',
                    'point_of_interaction': {'type': 'POINT'}})
            elif outcome == 'rejected':
                order['status'] = 'failed'
                payment.update({'status': 'rejected', 'status_detail': 'cc_rejected_insufficient_amount'})
            elif outcome == 'expired':
                order['status'] = 'expired'

    def add_payment_movement(self, payment):
        with self._lock:
            self.payments.append(payment)

    def cancel_order(self, order_id, at_terminal=False):
        self._maybe_fail('cancel')
        order = self.orders[order_id]
        if order['status'] == 'at_terminal' and not at_terminal:
            raise MpRejected(409, 'cannot_cancel_order', 'Order cannot be canceled')
        if order['status'] not in ('created', 'at_terminal'):
            raise MpRejected(409, 'cannot_cancel_order', 'Order cannot be canceled')
        order['status'] = 'canceled'
        return dict(order)

    def refund_order(self, order_id, idempotency_key):
        self._maybe_fail('refund')
        order = self.orders[order_id]
        if order['status'] not in ('processed', 'refunded'):
            raise MpRejected(400, 'invalid_status', 'Order cannot be refunded')
        order['status'] = 'refunded'
        return dict(order)

    def search_payments(self, begin_utc, end_utc, offset=0):
        self._maybe_fail('search')
        results = self.payments[offset:offset + 50]
        return {'results': [dict(p) for p in results], 'paging': {'total': len(self.payments), 'offset': offset}}
```

- [ ] **Step 6: Configuración y firma.** Crear `backend/app/services/mercadopago/settings.py`:

```python
"""Configuración de MercadoPago: tokens y secreto cifrados con una clave derivada de SECRET_KEY."""
import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from flask import current_app

from app.extensions import db
from app.models import MpSettings, PaymentMethod
from app.models.mercadopago import SETTINGS_ID
from app.services.pos.errors import PosError

UNREADABLE = 'El token de MercadoPago no se puede leer: cargalo de nuevo'


def get_settings(lock=False):
    query = MpSettings.query.filter_by(id=SETTINGS_ID)
    if lock:
        query = query.with_for_update().populate_existing()
    return query.first()


def get_or_create_settings():
    settings = get_settings()
    if settings is None:
        settings = MpSettings(id=SETTINGS_ID, environment='test')
        db.session.add(settings)
        db.session.flush()
    return settings


def _fernet():
    key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b'galia-mp-token').derive(
        current_app.config['SECRET_KEY'].encode())
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt(text):
    return _fernet().encrypt(text.encode()).decode()


def decrypt(token):
    try:
        return _fernet().decrypt(token.encode()).decode()
    except (InvalidToken, ValueError, AttributeError):
        raise PosError(UNREADABLE)


def access_token(settings):
    token = settings.token(settings.environment) if settings else None
    if not token:
        raise PosError('Falta configurar MercadoPago: token')
    return decrypt(token)


def webhook_secret(settings):
    if settings is None or not settings.webhook_secret:
        return None
    try:
        return decrypt(settings.webhook_secret)
    except PosError:
        return None


def missing(settings):
    if settings is None:
        return ['token de prueba', 'terminal', 'medio de pago del Point']
    items = []
    token = settings.token(settings.environment)
    if not token:
        items.append('token de prueba' if settings.environment == 'test' else 'token de producción')
    else:
        try:
            decrypt(token)
        except PosError:
            items.append('el token no se puede leer: cargalo de nuevo')
    if not settings.terminal_id:
        items.append('terminal')
    method = db.session.get(PaymentMethod, settings.point_payment_method_id) if settings.point_payment_method_id \
        else None
    if method is None or not method.is_active:
        items.append('medio de pago del Point')
    return items


def require_ready(settings):
    items = missing(settings)
    if items:
        raise PosError(f'Falta configurar MercadoPago: {", ".join(items)}')


def settings_to_dict(settings):
    return {'environment': settings.environment, 'has_test_token': bool(settings.test_access_token),
            'has_prod_token': bool(settings.prod_access_token), 'terminal_id': settings.terminal_id,
            'has_webhook_secret': bool(settings.webhook_secret),
            'point_payment_method_id': settings.point_payment_method_id, 'user_id': settings.user_id,
            'missing': missing(settings)}
```

Crear `backend/app/services/mercadopago/webhook.py`:

```python
"""Verificación de la firma de los avisos de MercadoPago (header x-signature: ts=...,v1=...)."""
import hashlib
import hmac


def _parts(x_signature):
    parts = {}
    for chunk in (x_signature or '').split(','):
        key, _, value = chunk.strip().partition('=')
        if key and value:
            parts[key] = value
    return parts


def manifest(data_id, request_id, ts):
    """id:<data.id>;request-id:<x-request-id>;ts:<ts>; (las partes que faltan se omiten; id en minúsculas)."""
    text = ''
    if data_id:
        text += f'id:{str(data_id).lower()};'
    if request_id:
        text += f'request-id:{request_id};'
    if ts:
        text += f'ts:{ts};'
    return text


def verify_signature(secret, x_signature, x_request_id, data_id):
    parts = _parts(x_signature)
    if not secret or 'ts' not in parts or 'v1' not in parts:
        return False
    expected = hmac.new(secret.encode(), manifest(data_id, x_request_id, parts['ts']).encode(),
                        hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, parts['v1'])
```

- [ ] **Step 7: Correr**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_mp_client.py`
Expected: todos pasan.

- [ ] **Step 8: Commit**

```bash
git -C <worktree> add backend/app/services/mercadopago backend/tests/mp_helpers.py backend/tests/test_mp_client.py
git -C <worktree> commit -m "feat(mp): MercadoPago REST client, fake, encrypted settings and webhook signature"
```

---

### Task 3: Cobro con Point (crear, aplicar, refrescar, cancelar) y aviso en la venta

**Files:**
- Create: `backend/app/services/mercadopago/point_service.py`, `backend/app/services/mercadopago/summary.py`, `backend/tests/test_mp_point.py`
- Modify: `backend/app/services/pos/serializers.py` (`point_order`)

**Interfaces:**
- Consumes:
  - `get_client`, `settings.*`, `client.order_state`, `MpUnavailable`, `MpRejected` (Task 2);
  - `payment_service.add_payment`, `common.load_sale`, `common.require_module`.
- Produces:
  - **`point_service`:**
    - `start(user, sale_id, amount) -> MpPointOrder`;
    - `apply(order_id) -> MpPointOrder`, idempotente, hace commit;
    - `refresh(order_id) -> MpPointOrder`, que solo llama a `apply` si la orden no es final y el último chequeo tiene más de 5 s;
    - `cancel(user, order_id) -> MpPointOrder`;
    - `order_to_dict(order)`, `sale_orders(sale_id)`;
    - `apply_by_mp_order_id(mp_order_id)`, para el webhook;
    - `REFRESH_AFTER = timedelta(seconds=5)`.
  - **`summary.active_point_order(sale_id) -> dict | None`:** `{'id', 'status', 'amount'}`, el cobro activo, para `sale_to_dict`. Solo importa modelos.

- [ ] **Step 1: Tests que fallan.** Crear `backend/tests/test_mp_point.py`:

```python
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import MpPointOrder
from app.services import mercadopago
from app.services.mercadopago import point_service
from app.services.mercadopago.fake import FakeMercadoPago
from app.services.pos import payment_service, sale_service
from app.services.pos.errors import PosError
from app.services.pos.serializers import sale_to_dict
from mp_helpers import billing_sale, configure_mp
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401


@pytest.fixture
def ctx(pos_app, monkeypatch):
    FakeMercadoPago.reset()
    monkeypatch.setattr(mercadopago, 'get_client', lambda settings: FakeMercadoPago())
    user = make_user('caja@test.com', modules=('POS', 'Anular'))
    cat = make_catalog()
    _salon, t1, t2 = make_floor()
    settings = configure_mp()
    return user, cat, t1, t2, settings


def _approve(order, amount=None):
    FakeMercadoPago().simulate(order.mp_order_id, 'approved', paid_amount=amount)
    return point_service.apply(order.id)


def test_start_creates_order_at_terminal(ctx):
    user, cat, t1, _t2, _s = ctx
    sale = billing_sale(user, cat, t1)
    order = point_service.start(user, sale.id, Decimal('1800'))
    assert order.status == 'created' and order.mp_order_id and order.external_reference.startswith(
        f'galia-venta-{sale.id}-')
    assert sale_to_dict(sale)['point_order'] == {'id': order.id, 'status': 'created', 'amount': '1800.00'}


def test_approved_registers_payment_and_closes_sale(ctx):
    user, cat, t1, _t2, settings = ctx
    sale = billing_sale(user, cat, t1)
    order = point_service.start(user, sale.id, Decimal('1800'))
    order = _approve(order)
    db.session.refresh(sale)
    assert order.status == 'approved' and sale.status == 'closed'
    payment = order.payment
    assert payment.payment_method_id == settings.point_payment_method_id and payment.amount == Decimal('1800')
    assert payment.mp_payment_id == order.mp_payment_id and payment.client_request_id == f'mp-order-{order.id}'
    assert sale_to_dict(sale)['point_order'] is None


def test_apply_twice_creates_one_payment(ctx):
    user, cat, t1, _t2, _s = ctx
    sale = billing_sale(user, cat, t1)
    order = point_service.start(user, sale.id, Decimal('1000'))
    _approve(order)
    point_service.apply(order.id)
    order.status = 'processing'  # como si otra vía lo viera antes de terminar
    db.session.commit()
    point_service.apply(order.id)
    db.session.refresh(sale)
    assert len([p for p in sale.payments if p.cancelled_at is None]) == 1 and sale.balance == Decimal('800')


def test_one_order_per_terminal_and_amount_rules(ctx):
    user, cat, t1, t2, _s = ctx
    sale = billing_sale(user, cat, t1)
    other = billing_sale(user, cat, t2)
    point_service.start(user, sale.id, Decimal('500'))
    with pytest.raises(PosError) as error:
        point_service.start(user, other.id, Decimal('500'))
    assert 'El Point está cobrando Mesa 1' in error.value.message
    db.session.rollback()
    for bad in (Decimal('0'), Decimal('5000')):
        with pytest.raises(PosError):
            point_service.start(user, other.id, bad)
        db.session.rollback()
    open_sale = sale_service.open_sale(user, 'salon', table_id=t2.id, people=1)
    with pytest.raises(PosError) as error:
        point_service.start(user, open_sale.id, Decimal('1'))
    assert 'Pedí la cuenta' in error.value.message


def test_rejected_and_retry(ctx):
    user, cat, t1, _t2, _s = ctx
    sale = billing_sale(user, cat, t1)
    order = point_service.start(user, sale.id, Decimal('1800'))
    FakeMercadoPago().simulate(order.mp_order_id, 'rejected')
    order = point_service.apply(order.id)
    assert order.status == 'failed' and 'rechazado' in order.error
    again = point_service.start(user, sale.id, Decimal('1800'))
    assert again.status == 'created'


def test_unavailable_on_create_retries_once_with_same_key(ctx):
    user, cat, t1, _t2, _s = ctx
    sale = billing_sale(user, cat, t1)
    FakeMercadoPago.fail_next('create')
    order = point_service.start(user, sale.id, Decimal('1800'))
    assert order.status == 'created'
    assert len(FakeMercadoPago.by_key) == 1


def test_approved_over_balance_is_flagged(ctx):
    user, cat, t1, _t2, _s = ctx
    sale = billing_sale(user, cat, t1)
    order = point_service.start(user, sale.id, Decimal('1800'))
    payment_service.add_payment(user, sale.id, cat.efectivo.id, 1000)  # se cobró parte en efectivo mientras tanto
    order = _approve(order)
    db.session.refresh(sale)
    assert order.status == 'approved' and order.payment.amount == Decimal('800')
    assert order.error == 'Cobrado de más: $1000.00, revisalo en Conciliación' and sale.status == 'closed'


def test_cancel_created_and_at_terminal(ctx):
    user, cat, t1, _t2, _s = ctx
    sale = billing_sale(user, cat, t1)
    order = point_service.start(user, sale.id, Decimal('1800'))
    order = point_service.cancel(user, order.id)
    assert order.status == 'canceled'
    second = point_service.start(user, sale.id, Decimal('1800'))
    FakeMercadoPago().simulate(second.mp_order_id, 'processing')
    point_service.apply(second.id)
    second = point_service.cancel(user, second.id)
    assert second.status in ('canceling', 'canceled')


def test_refresh_only_checks_when_stale(ctx):
    user, cat, t1, _t2, _s = ctx
    sale = billing_sale(user, cat, t1)
    order = point_service.start(user, sale.id, Decimal('1800'))
    FakeMercadoPago().simulate(order.mp_order_id, 'approved')
    order.last_checked_at = datetime.utcnow()
    db.session.commit()
    assert point_service.refresh(order.id).status == 'created'
    order.last_checked_at = datetime.utcnow() - timedelta(seconds=6)
    db.session.commit()
    assert point_service.refresh(order.id).status == 'approved'


def test_requires_charge_permission_and_configuration(ctx):
    _user, cat, t1, _t2, settings = ctx
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    cashier = make_user('caja2@test.com', modules=('POS',))
    sale = billing_sale(cashier, cat, t1)
    with pytest.raises(PosError) as error:
        point_service.start(waiter, sale.id, Decimal('100'))
    assert error.value.status == 403
    settings.terminal_id = None
    db.session.commit()
    with pytest.raises(PosError) as error:
        point_service.start(cashier, sale.id, Decimal('100'))
    assert error.value.message.startswith('Falta configurar MercadoPago')
```

- [ ] **Step 2: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_mp_point.py`
Expected: ImportError (`point_service`).

- [ ] **Step 3: Resumen para la venta.** Crear `backend/app/services/mercadopago/summary.py`:

```python
"""Cobro de Point activo de una venta (para el aviso "Cobro en Point pendiente"). Solo modelos: sin ciclos."""
from app.models import MpPointOrder
from app.models.mercadopago import ACTIVE_STATUSES


def active_point_order(sale_id):
    order = MpPointOrder.query.filter(MpPointOrder.sale_id == sale_id,
                                      MpPointOrder.status.in_(ACTIVE_STATUSES)).order_by(MpPointOrder.id.desc()).first()
    if order is None:
        return None
    return {'id': order.id, 'status': order.status, 'amount': f'{order.amount:.2f}'}
```

En `backend/app/services/pos/serializers.py`:
- importar `from app.services.mercadopago import summary as mp_summary`;
- en `sale_to_dict`, dentro de `if include_items:`, sumar `data['point_order'] = mp_summary.active_point_order(sale.id)`.

- [ ] **Step 4: Servicio.** Crear `backend/app/services/mercadopago/point_service.py`:

```python
"""Cobros con el Point Smart: crear la orden, aplicar el resultado (idempotente), refrescar y cancelar.

El resultado llega por webhook o por la consulta de respaldo del frontend; las dos vías llaman a apply(), que
bloquea la orden, consulta a MercadoPago y crea el pago una sola vez (client_request_id 'mp-order-<id>').
"""
import logging
import uuid
from datetime import timedelta
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import MpPointOrder, PosPayment, User
from app.models.mercadopago import ACTIVE_STATUSES, FINAL_STATUSES
from app.services import mercadopago
from app.services.mercadopago import MpRejected, MpUnavailable
from app.services.mercadopago import settings as mp_settings
from app.services.mercadopago.client import order_state
from app.services.pos import audit, payment_service
from app.services.pos.common import load_sale, now, parse_id
from app.services.pos.errors import PosError, bad_request, forbidden, not_found
from app.utils.permissions import check_module_access
from app.utils.validation import parse_decimal

logger = logging.getLogger(__name__)
REFRESH_AFTER = timedelta(seconds=5)
UNAVAILABLE = 'MercadoPago no responde, probá de nuevo'
NOT_READY = 'El Point no está listo para recibir cobros: revisá que esté prendido y en modo PDV'
REJECTION_TEXT = {
    'cc_rejected_insufficient_amount': 'fondos insuficientes',
    'cc_rejected_bad_filled_security_code': 'código de seguridad incorrecto',
    'cc_rejected_call_for_authorize': 'la tarjeta pide autorización al banco',
    'cc_rejected_card_disabled': 'tarjeta inhabilitada',
    'cc_rejected_high_risk': 'rechazado por seguridad',
}


def _require_charge(user):
    if not (check_module_access(user, 'POS') or check_module_access(user, 'Cobrar')):
        raise forbidden('No tenés permiso para cobrar')


def _place(sale):
    return sale.table.label if sale.table is not None else f'Mostrador #{sale.number}'


def order_to_dict(order):
    return {'id': order.id, 'sale_id': order.sale_id, 'amount': f'{order.amount:.2f}', 'status': order.status,
            'status_detail': order.status_detail, 'error': order.error, 'mp_order_id': order.mp_order_id,
            'mp_payment_id': order.mp_payment_id, 'payment_id': order.payment_id,
            'approved_amount': f'{order.approved_amount:.2f}' if order.approved_amount is not None else None,
            'created_at': order.created_at.isoformat(), 'fake': mercadopago.fake_enabled()}


def _load(order_id, lock=False):
    query = MpPointOrder.query.filter_by(id=parse_id(order_id, 'El cobro'))
    if lock:
        query = query.with_for_update().populate_existing()
    order = query.first()
    if order is None:
        raise not_found('El cobro no existe')
    return order


def start(user, sale_id, amount):
    _require_charge(user)
    settings = mp_settings.get_settings()
    mp_settings.require_ready(settings)
    client = mercadopago.get_client(settings)
    sale = load_sale(parse_id(sale_id, 'La venta'))
    if not (sale.status == 'billing' or (sale.status == 'open' and sale.sale_type == 'counter')):
        raise PosError('Pedí la cuenta antes de cobrar')
    amount = parse_decimal(amount, 'El monto', minimum=Decimal('0.01'))
    if amount > sale.balance:
        raise bad_request(f'El monto tiene que ser mayor a 0 y no superar el saldo (${sale.balance:.2f})')
    busy = MpPointOrder.query.filter(MpPointOrder.terminal_id == settings.terminal_id,
                                     MpPointOrder.status.in_(ACTIVE_STATUSES)).first()
    if busy is not None:
        raise PosError(f'El Point está cobrando {_place(busy.sale)} (${busy.amount:.2f}): esperá o cancelalo')
    key = str(uuid.uuid4())
    order = MpPointOrder(sale_id=sale.id, amount=amount, terminal_id=settings.terminal_id, status='creating',
                         external_reference=f'galia-venta-{sale.id}-{key[:8]}', idempotency_key=key,
                         created_by=user.id, created_at=now(), updated_at=now())
    db.session.add(order)
    try:
        db.session.commit()  # el índice único rechaza un segundo cobro activo en la terminal
    except IntegrityError:
        db.session.rollback()
        raise PosError('El Point está ocupado con otro cobro: esperá o cancelalo')
    response = None
    for attempt in (1, 2):  # un reintento con la misma clave de idempotencia
        try:
            response = client.create_order(order.terminal_id, order.amount, order.external_reference, key)
            break
        except MpUnavailable as exc:
            logger.warning('MercadoPago sin respuesta creando la orden %s (intento %s): %s', order.id, attempt, exc)
        except MpRejected as exc:
            logger.warning('MercadoPago rechazó la orden %s: %s', order.id, exc)
            order.status, order.error = 'failed', NOT_READY if exc.status in (400, 404, 409) else exc.message
            order.updated_at = now()
            db.session.commit()
            return order
    if response is None:
        order.status, order.error, order.updated_at = 'failed', UNAVAILABLE, now()
        db.session.commit()
        return order
    order.mp_order_id = str(response['id'])
    order.status = 'created'
    order.updated_at = order.last_checked_at = now()
    audit.record(sale, user, 'point_order_created', order_id=order.id, amount=order.amount)
    db.session.commit()
    return order


def _register_payment(order, approved_amount):
    """Crea el pago de Galia por lo aprobado, hasta el saldo. Lo que sobra queda marcado para conciliar."""
    settings = mp_settings.get_settings()
    user = db.session.get(User, order.created_by)
    sale = order.sale
    balance = sale.balance if sale.status in ('billing', 'open') else Decimal('0')
    to_register = min(approved_amount, balance)
    if approved_amount > to_register:
        order.error = f'Cobrado de más: ${approved_amount - to_register:.2f}, revisalo en Conciliación'
        logger.error('Cobro de Point %s excede el saldo de la venta %s', order.id, sale.id)
    if to_register <= 0:
        db.session.commit()
        return None
    request_id = f'mp-order-{order.id}'
    db.session.commit()  # persiste el estado approved antes de crear el pago (add_payment hace su propio commit)
    payment_service.add_payment(user, sale.id, settings.point_payment_method_id, to_register,
                                client_request_id=request_id)
    payment = PosPayment.query.filter_by(client_request_id=request_id).first()
    payment.mp_payment_id = order.mp_payment_id
    order.payment_id = payment.id
    db.session.commit()
    return payment


def apply(order_id):
    order = _load(order_id, lock=True)
    if order.status in FINAL_STATUSES or not order.mp_order_id:
        db.session.commit()
        return order
    client = mercadopago.get_client(mp_settings.get_settings())
    try:
        state = order_state(client.get_order(order.mp_order_id))
    except (MpUnavailable, MpRejected) as exc:
        logger.warning('No se pudo consultar la orden %s: %s', order.id, exc)
        order.last_checked_at = now()
        db.session.commit()
        return order
    order.last_checked_at = order.updated_at = now()
    order.status_detail = state['status_detail']
    if state['status'] == 'approved':
        order.status = 'approved'
        order.mp_payment_id = state['mp_payment_id']
        order.approved_amount = state['approved_amount'] or order.amount
        try:
            _register_payment(order, order.approved_amount)
        except PosError as exc:
            db.session.rollback()
            order = _load(order_id, lock=True)
            order.error = f'Cobrado pero no registrado: {exc.message}. Revisalo en Conciliación'
            logger.error('Cobro de Point %s aprobado sin registrar: %s', order.id, exc.message)
            db.session.commit()
        return order
    if state['status'] == 'failed':
        reason = REJECTION_TEXT.get(state['status_detail'] or '', state['status_detail'] or 'sin detalle')
        order.status, order.error = 'failed', f'El pago fue rechazado en el Point: {reason}'
    elif state['status'] in ('canceled', 'expired'):
        order.status = state['status']
        order.error = 'Se canceló el cobro' if state['status'] == 'canceled' else 'El cobro venció sin pagarse'
    elif order.status != 'canceling':
        order.status = state['status']
    db.session.commit()
    return order


def apply_by_mp_order_id(mp_order_id):
    order = MpPointOrder.query.filter_by(mp_order_id=str(mp_order_id)).first()
    return apply(order.id) if order is not None else None


def refresh(order_id):
    order = _load(order_id)
    if order.status in FINAL_STATUSES:
        return order
    if order.last_checked_at is None or order.last_checked_at < now() - REFRESH_AFTER:
        return apply(order.id)
    return order


def cancel(user, order_id):
    _require_charge(user)
    order = _load(order_id, lock=True)
    if order.status not in ('created', 'processing'):
        raise PosError('Ese cobro ya terminó')
    client = mercadopago.get_client(mp_settings.get_settings())
    try:
        client.cancel_order(order.mp_order_id, at_terminal=order.status == 'processing')
    except MpUnavailable:
        db.session.rollback()
        raise PosError(UNAVAILABLE)
    except MpRejected:
        db.session.rollback()
        apply(order_id)
        raise PosError('El cobro ya se está procesando en el Point: esperá el resultado')
    order.status = 'canceled' if order.status == 'created' else 'canceling'
    order.error = 'Se canceló el cobro' if order.status == 'canceled' else None
    order.updated_at = now()
    audit.record(order.sale, user, 'point_order_canceled', order_id=order.id)
    db.session.commit()
    return order


def sale_orders(sale_id):
    rows = MpPointOrder.query.filter_by(sale_id=parse_id(sale_id, 'La venta')).order_by(MpPointOrder.id).all()
    return [order_to_dict(o) for o in rows]
```

Revisar en `backend/app/services/pos/audit.py` la firma de `audit.record(sale, user, kind, **data)` y que acepte tipos `Decimal` (lo hace en `payment_added`).

Si `audit.record` necesita que el `kind` esté en una lista cerrada (`EVENT_KINDS` o similar), sumar `point_order_created` y `point_order_canceled`.

- [ ] **Step 5: Correr**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_mp_point.py tests/test_mp_client.py tests/test_pos_payments.py tests/test_pos_sales_api.py`
Expected: todos pasan (si `test_pos_sales_api.py` no existe, correr `tests/test_pos_*.py`).

- [ ] **Step 6: Commit**

```bash
git -C <worktree> add backend/app/services backend/tests/test_mp_point.py
git -C <worktree> commit -m "feat(mp): Point charges with idempotent payment registration"
```

---

### Task 4: Devolución al anular un pago del Point

**Files:**
- Create: `backend/app/services/mercadopago/refund_service.py`, `backend/tests/test_mp_refund.py`
- Modify: `backend/app/routes/pos_sales.py` (`cancel_payment`), `backend/app/services/pos/serializers.py` (`refundable_mp`)

**Interfaces:**
- Consumes: `MpPointOrder`, `get_client`, `payment_service.cancel_payment`.
- Produces:
  - `refund_service.cancel_with_refund(user, payment_id, reason, reason_id) -> PosSale`;
  - `payment_to_dict(...)['refundable_mp']`: bool, verdadero si el pago vino de una orden de Point no devuelta.

- [ ] **Step 1: Tests que fallan.** Crear `backend/tests/test_mp_refund.py`:

```python
from decimal import Decimal

import pytest

from app.extensions import db
from app.services import mercadopago
from app.services.mercadopago import point_service, refund_service
from app.services.mercadopago.fake import FakeMercadoPago
from app.services.pos.errors import PosError
from app.services.pos.serializers import payment_to_dict
from mp_helpers import billing_sale, configure_mp
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401


@pytest.fixture
def paid(pos_app, monkeypatch):
    FakeMercadoPago.reset()
    monkeypatch.setattr(mercadopago, 'get_client', lambda settings: FakeMercadoPago())
    user = make_user('caja@test.com', modules=('POS', 'Anular'))
    cat = make_catalog()
    _salon, t1, _t2 = make_floor()
    configure_mp()
    sale = billing_sale(user, cat, t1)
    order = point_service.start(user, sale.id, Decimal('1800'))
    FakeMercadoPago().simulate(order.mp_order_id, 'approved')
    order = point_service.apply(order.id)
    return pos_app, user, sale, order


def test_payment_dict_marks_refundable(paid):
    _app, _user, _sale, order = paid
    assert payment_to_dict(order.payment)['refundable_mp'] is True


def test_refund_then_cancel(paid):
    _app, user, sale, order = paid
    refund_service.cancel_with_refund(user, order.payment_id, 'Cliente se arrepintió')
    db.session.refresh(order)
    assert order.refunded_at is not None and order.payment.cancelled_at is not None
    assert FakeMercadoPago.orders[order.mp_order_id]['status'] == 'refunded'
    assert payment_to_dict(order.payment)['refundable_mp'] is False


def test_refund_rejected_keeps_payment(paid):
    _app, user, _sale, order = paid
    FakeMercadoPago.orders[order.mp_order_id]['status'] = 'expired'  # MercadoPago no la acepta
    with pytest.raises(PosError) as error:
        refund_service.cancel_with_refund(user, order.payment_id, 'x')
    assert error.value.message.startswith('MercadoPago rechazó la devolución')
    db.session.rollback()
    FakeMercadoPago.orders[order.mp_order_id]['status'] = 'processed'
    FakeMercadoPago.fail_next('refund')
    with pytest.raises(PosError) as error:
        refund_service.cancel_with_refund(user, order.payment_id, 'x')
    assert error.value.message == 'MercadoPago no responde: no se anuló el pago'
    db.session.rollback()
    db.session.refresh(order.payment)
    assert order.payment.cancelled_at is None


def test_route_refund_flag(paid):
    app, _user, sale, order = paid
    client = app.test_client()
    headers = auth_headers(client, make_user('anula@test.com', modules=('POS', 'Anular')))
    only_galia = client.post(f'/api/v1/pos/payments/{order.payment_id}/cancel',
                             json={'reason': 'Error', 'refund_mp': False}, headers=headers)
    assert only_galia.status_code == 200
    assert FakeMercadoPago.orders[order.mp_order_id]['status'] == 'processed'
```

- [ ] **Step 2: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_mp_refund.py`
Expected: ImportError (`refund_service`).

- [ ] **Step 3: Implementar.** Crear `backend/app/services/mercadopago/refund_service.py`:

```python
"""Anular un pago del Point devolviendo el dinero en MercadoPago (reembolso total de la orden)."""
import logging

from app.extensions import db
from app.models import MpPointOrder
from app.services import mercadopago
from app.services.mercadopago import MpRejected, MpUnavailable
from app.services.mercadopago import settings as mp_settings
from app.services.pos import payment_service
from app.services.pos.common import now, parse_id, require_module
from app.services.pos.errors import PosError

logger = logging.getLogger(__name__)


def order_for_payment(payment_id):
    return MpPointOrder.query.filter_by(payment_id=payment_id).first()


def cancel_with_refund(user, payment_id, reason, reason_id=None):
    """Primero la devolución en MercadoPago; si la acepta, se anula en Galia. Si no, no se anula nada."""
    require_module(user, 'Anular', 'No tenés permiso para anular pagos')
    order = order_for_payment(parse_id(payment_id, 'El pago'))
    if order is None:
        raise PosError('Ese pago no vino de un cobro con el Point: anulalo solo en Galia')
    if order.refunded_at is None:
        client = mercadopago.get_client(mp_settings.get_settings())
        try:
            client.refund_order(order.mp_order_id, f'refund-{order.payment_id}')
        except MpUnavailable as exc:
            logger.warning('MercadoPago sin respuesta devolviendo la orden %s: %s', order.id, exc)
            raise PosError('MercadoPago no responde: no se anuló el pago')
        except MpRejected as exc:
            logger.warning('MercadoPago rechazó la devolución de la orden %s: %s', order.id, exc)
            raise PosError(f'MercadoPago rechazó la devolución: {exc.message}')
        order.refunded_at = now()
        db.session.commit()  # la devolución ya ocurrió: queda registrada aunque la anulación falle después
    return payment_service.cancel_payment(user, payment_id, reason, reason_id=reason_id)
```

En `backend/app/routes/pos_sales.py`, en `cancel_payment`, reemplazar el cuerpo de `action` por:

```python
    def action():
        data = _body()
        if data.get('refund_mp'):
            from app.services.mercadopago import refund_service
            return refund_service.cancel_with_refund(current_user, payment_id, data.get('reason'),
                                                     reason_id=data.get('reason_id'))
        return payment_service.cancel_payment(current_user, payment_id, data.get('reason'),
                                              reason_id=data.get('reason_id'))
```

En `backend/app/services/pos/serializers.py`, en `payment_to_dict`, sumar:

```python
        'refundable_mp': mp_summary.refundable(payment),
```

y en `backend/app/services/mercadopago/summary.py` agregar:

```python
def refundable(payment):
    """El pago vino de un cobro con el Point que todavía no se devolvió."""
    if payment.id is None or payment.cancelled_at is not None:
        return False
    order = MpPointOrder.query.filter_by(payment_id=payment.id).first()
    return order is not None and order.refunded_at is None
```

- [ ] **Step 4: Correr**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_mp_refund.py tests/test_mp_point.py tests/test_pos_payments.py tests/test_fiscal_cancel.py`
Expected: todos pasan.

- [ ] **Step 5: Commit**

```bash
git -C <worktree> add backend/app/services backend/app/routes/pos_sales.py backend/tests/test_mp_refund.py
git -C <worktree> commit -m "feat(mp): refund Point payments in MercadoPago when cancelling"
```

---

### Task 5: Conciliación

**Files:**
- Create: `backend/app/services/mercadopago/reconciliation_service.py`, `backend/tests/test_mp_reconciliation.py`

**Interfaces:**
- Consumes: `get_client`, `client.movement_fields`, `MpMovement`, `MpReconciliation`, `MpPointOrder`, `payment_service.add_payment`.
- Produces (`reconciliation_service`):
  - `day_bounds(day) -> (begin_utc, end_utc)`;
  - `fetch(user, day) -> {'fetched': n, 'truncated': bool}`;
  - `day(day) -> dict`, con:
    - `matched`, `only_mp` y `only_galia` (cada fila de `only_mp` con `suggestions`);
    - `rejected` y `totals`;
    - `status` (`conciliado` | `con_diferencias` | `sin_traer`) y `pending`;
  - `summary(date_from, date_to) -> [{'day', 'status', 'pending'}]`;
  - `resolve(user, kind, movement_id=None, payment_id=None, sale_id=None, payment_method_id=None, note=None) -> dict`;
  - `undo(user, resolution_id)`;
  - `MAX_PER_DAY = 1000`, `SUGGEST_WINDOW = timedelta(minutes=15)`.

- [ ] **Step 1: Tests que fallan.** Crear `backend/tests/test_mp_reconciliation.py`:

```python
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import MpMovement, MpReconciliation
from app.services import mercadopago
from app.services.mercadopago import point_service
from app.services.mercadopago import reconciliation_service as rs
from app.services.mercadopago.fake import FakeMercadoPago
from app.services.pos import payment_service
from app.services.pos.errors import PosError
from mp_helpers import billing_sale, configure_mp
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401

TODAY = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-3))).date()


def _mp_payment(pid, amount, minutes_ago=1, status='approved', ptype='account_money', poi='INSTORE', ref=None):
    moment = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    return {'id': pid, 'date_created': moment.isoformat(timespec='milliseconds'), 'transaction_amount': amount,
            'status': status, 'status_detail': 'accredited', 'payment_type_id': ptype, 'payment_method_id': 'qr',
            'currency_id': 'ARS', 'external_reference': ref, 'point_of_interaction': {'type': poi}}


@pytest.fixture
def ctx(pos_app, monkeypatch):
    FakeMercadoPago.reset()
    monkeypatch.setattr(mercadopago, 'get_client', lambda settings: FakeMercadoPago())
    user = make_user('admin@test.com', role='admin')
    cat = make_catalog()
    _salon, t1, t2 = make_floor()
    configure_mp()
    cat.debito.is_mercadopago = True
    db.session.commit()
    return user, cat, t1, t2


def test_point_payment_matches_automatically(ctx):
    user, cat, t1, _t2 = ctx
    sale = billing_sale(user, cat, t1)
    order = point_service.start(user, sale.id, Decimal('1800'))
    FakeMercadoPago().simulate(order.mp_order_id, 'approved')
    point_service.apply(order.id)
    rs.fetch(user, TODAY)
    data = rs.day(TODAY)
    assert len(data['matched']) == 1 and data['only_mp'] == [] and data['only_galia'] == []
    assert data['status'] == 'conciliado'


def test_only_lists_and_suggestions(ctx):
    user, cat, t1, t2, = ctx
    sale = billing_sale(user, cat, t1)
    payment_service.add_payment(user, sale.id, cat.debito.id, 1800)  # cargado a mano, sin id de MP
    FakeMercadoPago().add_payment_movement(_mp_payment(555, 1800))
    FakeMercadoPago().add_payment_movement(_mp_payment(556, 5000, ptype='bank_transfer', poi=''))
    FakeMercadoPago().add_payment_movement(_mp_payment(557, 300, status='rejected'))
    rs.fetch(user, TODAY)
    data = rs.day(TODAY)
    only_mp = {row['mp_payment_id']: row for row in data['only_mp']}
    assert set(only_mp) == {'555', '556'} and [r['mp_payment_id'] for r in data['rejected']] == ['557']
    assert [s['payment_id'] for s in only_mp['555']['suggestions']] == [sale.payments[0].id]
    assert only_mp['556']['suggestions'] == [] and only_mp['556']['channel'] == 'transfer'
    assert len(data['only_galia']) == 1 and data['status'] == 'con_diferencias' and data['pending'] == 3
    assert data['totals']['only_mp'] == '6800.00'


def test_resolutions_and_undo(ctx):
    user, cat, t1, t2 = ctx
    sale = billing_sale(user, cat, t1)
    payment_service.add_payment(user, sale.id, cat.debito.id, 1800)
    other = billing_sale(user, cat, t2)
    FakeMercadoPago().add_payment_movement(_mp_payment(555, 1800))
    FakeMercadoPago().add_payment_movement(_mp_payment(556, 5000, ptype='bank_transfer', poi=''))
    FakeMercadoPago().add_payment_movement(_mp_payment(558, 900))
    rs.fetch(user, TODAY)
    movements = {m.mp_payment_id: m for m in MpMovement.query}
    matched = rs.resolve(user, 'matched_manual', movement_id=movements['555'].id, payment_id=sale.payments[0].id)
    assert sale.payments[0].mp_payment_id == '555' and matched['kind'] == 'matched_manual'
    with pytest.raises(PosError):
        rs.resolve(user, 'not_a_sale', movement_id=movements['556'].id)  # nota obligatoria
    db.session.rollback()
    rs.resolve(user, 'not_a_sale', movement_id=movements['556'].id, note='Transferencia de un proveedor')
    created = rs.resolve(user, 'payment_created', movement_id=movements['558'].id, sale_id=other.id,
                         payment_method_id=cat.debito.id)
    db.session.refresh(other)
    assert created['kind'] == 'payment_created' and other.paid_total == Decimal('900')
    assert rs.day(TODAY)['status'] == 'conciliado'
    rs.undo(user, created['id'])
    db.session.refresh(other)
    assert other.payments[0].mp_payment_id is None and other.payments[0].cancelled_at is None
    assert rs.day(TODAY)['pending'] == 2  # el movimiento vuelve a "solo en MP" y el pago queda "solo en Galia"
    with pytest.raises(PosError):
        rs.resolve(user, 'reviewed', payment_id=sale.payments[0].id, note='ok')  # ya cruzado
    db.session.rollback()


def test_fetch_twice_is_idempotent(ctx):
    user, *_ = ctx
    FakeMercadoPago().add_payment_movement(_mp_payment(555, 1800))
    rs.fetch(user, TODAY)
    movement = MpMovement.query.one()
    rs.resolve(user, 'not_a_sale', movement_id=movement.id, note='prueba')
    FakeMercadoPago.payments[0]['status'] = 'refunded'
    FakeMercadoPago.payments[0]['transaction_amount_refunded'] = 1800
    rs.fetch(user, TODAY)
    assert MpMovement.query.count() == 1 and MpReconciliation.query.count() == 1
    assert MpMovement.query.one().refunded_amount == Decimal('1800.00')


def test_summary_and_permissions(ctx):
    user, *_ = ctx
    assert rs.summary(TODAY, TODAY) == [{'day': TODAY.isoformat(), 'status': 'sin_traer', 'pending': 0}]
    FakeMercadoPago().add_payment_movement(_mp_payment(555, 1800))
    rs.fetch(user, TODAY)
    assert rs.summary(TODAY, TODAY)[0]['status'] == 'con_diferencias'
    cashier = make_user('caja@test.com', modules=('POS',))
    with pytest.raises(PosError) as error:
        rs.fetch(cashier, TODAY)
    assert error.value.status == 403


def test_day_bounds_are_argentina():
    begin, end = rs.day_bounds(date(2026, 10, 15))
    assert begin == datetime(2026, 10, 15, 3, 0) and end == datetime(2026, 10, 16, 2, 59, 59)
```

- [ ] **Step 2: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_mp_reconciliation.py`
Expected: ImportError.

- [ ] **Step 3: Implementar.** Crear `backend/app/services/mercadopago/reconciliation_service.py`:

```python
"""Conciliación diaria: movimientos de la cuenta de MercadoPago contra pagos de Galia con medios de MercadoPago."""
import logging
from datetime import datetime, time, timedelta
from decimal import Decimal

import pytz

from app.extensions import db
from app.models import MpMovement, MpPointOrder, MpReconciliation, PaymentMethod, PosPayment
from app.models.mercadopago import RESOLUTION_KINDS
from app.services import mercadopago
from app.services.mercadopago import MpRejected, MpUnavailable
from app.services.mercadopago import settings as mp_settings
from app.services.mercadopago.client import movement_fields
from app.services.pos import payment_service
from app.services.pos.common import now, parse_id, require_module
from app.services.pos.errors import PosError, bad_request, not_found
from app.utils.timezone_utils import ARGENTINA_TZ
from app.utils.validation import clean_str

logger = logging.getLogger(__name__)
MAX_PER_DAY = 1000
SUGGEST_WINDOW = timedelta(minutes=15)
MONEY_STATUSES = ('approved', 'refunded', 'charged_back', 'partially_refunded', 'in_mediation')


def _require(user):
    require_module(user, 'Conciliar', 'No tenés permiso para conciliar')


def day_bounds(day):
    """(inicio, fin) del día de Argentina en UTC naive."""
    begin = ARGENTINA_TZ.localize(datetime.combine(day, time.min)).astimezone(pytz.utc).replace(tzinfo=None)
    return begin, begin + timedelta(days=1) - timedelta(seconds=1)


def fetch(user, day):
    _require(user)
    settings = mp_settings.get_settings()
    client = mercadopago.get_client(settings)
    begin, end = day_bounds(day)
    fetched, offset, truncated = 0, 0, False
    try:
        while True:
            page = client.search_payments(begin, end, offset)
            results = page.get('results') or []
            for payment in results:
                fields = movement_fields(payment)
                movement = MpMovement.query.filter_by(mp_payment_id=fields['mp_payment_id']).first()
                if movement is None:
                    movement = MpMovement(mp_payment_id=fields['mp_payment_id'])
                    db.session.add(movement)
                for key, value in fields.items():
                    setattr(movement, key, value)
                movement.fetched_at = now()
                fetched += 1
            offset += len(results)
            total = (page.get('paging') or {}).get('total', 0)
            if not results or offset >= total:
                break
            if offset >= MAX_PER_DAY:
                truncated = True
                break
    except MpUnavailable:
        db.session.rollback()
        raise PosError('MercadoPago no responde, probá de nuevo')
    except MpRejected as exc:
        db.session.rollback()
        raise PosError(f'MercadoPago respondió: {exc.message}')
    db.session.commit()
    return {'fetched': fetched, 'truncated': truncated}


def _galia_payments(day):
    begin, end = day_bounds(day)
    method_ids = [m.id for m in PaymentMethod.query.filter_by(is_mercadopago=True)]
    if not method_ids:
        return []
    return PosPayment.query.filter(PosPayment.payment_method_id.in_(method_ids), PosPayment.created_at >= begin,
                                   PosPayment.created_at <= end).order_by(PosPayment.id).all()


def _payment_row(payment):
    sale = payment.sale
    return {'payment_id': payment.id, 'sale_id': payment.sale_id, 'sale_number': sale.number if sale else None,
            'method_name': payment.method_name, 'amount': f'{payment.amount:.2f}',
            'created_at': payment.created_at.isoformat(), 'is_active': payment.cancelled_at is None,
            'mp_payment_id': payment.mp_payment_id}


def _movement_row(movement):
    return {'movement_id': movement.id, 'mp_payment_id': movement.mp_payment_id,
            'date_created': movement.date_created.isoformat(), 'amount': f'{movement.amount:.2f}',
            'refunded_amount': f'{movement.refunded_amount:.2f}', 'status': movement.status,
            'channel': movement.channel, 'payment_method': movement.payment_method,
            'description': movement.description, 'external_reference': movement.external_reference}


def _resolution_row(resolution):
    return {'id': resolution.id, 'kind': resolution.kind, 'note': resolution.note,
            'created_at': resolution.created_at.isoformat()}


def day(day):
    begin, end = day_bounds(day)
    movements = MpMovement.query.filter_by(business_date=day).order_by(MpMovement.date_created).all()
    if not movements and not MpMovement.query.filter(MpMovement.business_date == day).first():
        fetched = False
    else:
        fetched = True
    money = [m for m in movements if m.status in MONEY_STATUSES]
    rejected = [m for m in movements if m.status not in MONEY_STATUSES]
    payments = _galia_payments(day)
    by_mp_id = {p.mp_payment_id: p for p in payments if p.mp_payment_id}
    by_reference = {o.external_reference: o.payment for o in MpPointOrder.query.filter(
        MpPointOrder.payment_id.isnot(None), MpPointOrder.created_at >= begin - timedelta(hours=1))}
    resolutions = {r.mp_movement_id: r for r in MpReconciliation.query.filter(
        MpReconciliation.mp_movement_id.in_([m.id for m in movements] or [0]))}
    payment_resolutions = {r.payment_id: r for r in MpReconciliation.query.filter(
        MpReconciliation.payment_id.in_([p.id for p in payments] or [0]))}
    matched, only_mp, used = [], [], set()
    for movement in money:
        resolution = resolutions.get(movement.id)
        payment = by_mp_id.get(movement.mp_payment_id) or by_reference.get(movement.external_reference or '')
        if resolution is not None and resolution.payment_id is not None:
            payment = db.session.get(PosPayment, resolution.payment_id)
        if payment is not None:
            used.add(payment.id)
            matched.append({'movement': _movement_row(movement), 'payment': _payment_row(payment),
                            'resolution': _resolution_row(resolution) if resolution else None,
                            'difference': f'{movement.amount - movement.refunded_amount - (payment.amount if payment.cancelled_at is None else 0):.2f}'})
        elif resolution is not None:  # not_a_sale
            matched.append({'movement': _movement_row(movement), 'payment': None,
                            'resolution': _resolution_row(resolution), 'difference': '0.00'})
        else:
            only_mp.append(movement)
    free = [p for p in payments if p.id not in used and p.cancelled_at is None]
    only_mp_rows = []
    for movement in only_mp:
        suggestions = [_payment_row(p) for p in free if p.amount == movement.amount and p.id not in payment_resolutions
                       and abs(p.created_at - movement.date_created) <= SUGGEST_WINDOW]
        only_mp_rows.append({**_movement_row(movement), 'suggestions': suggestions})
    only_galia = []
    for payment in free:
        resolution = payment_resolutions.get(payment.id)
        if resolution is not None and resolution.kind == 'reviewed':
            matched.append({'movement': None, 'payment': _payment_row(payment),
                            'resolution': _resolution_row(resolution), 'difference': '0.00'})
        else:
            only_galia.append(_payment_row(payment))
    pending = len(only_mp_rows) + len(only_galia)
    status = 'sin_traer' if not fetched else ('conciliado' if pending == 0 else 'con_diferencias')
    totals = {
        'matched': f'{sum((Decimal(r["movement"]["amount"]) for r in matched if r["movement"]), Decimal(0)):.2f}',
        'only_mp': f'{sum((m.amount for m in only_mp), Decimal(0)):.2f}',
        'only_galia': f'{sum((Decimal(r["amount"]) for r in only_galia), Decimal(0)):.2f}',
        'by_channel': {},
    }
    for movement in money:
        totals['by_channel'][movement.channel] = f'{Decimal(totals["by_channel"].get(movement.channel, "0")) + movement.amount:.2f}'
    return {'day': day.isoformat(), 'status': status, 'pending': pending, 'matched': matched,
            'only_mp': only_mp_rows, 'only_galia': only_galia, 'rejected': [_movement_row(m) for m in rejected],
            'totals': totals}


def summary(date_from, date_to):
    days, current = [], date_from
    while current <= date_to:
        data = day(current)
        days.append({'day': current.isoformat(), 'status': data['status'], 'pending': data['pending']})
        current += timedelta(days=1)
    return days


def _resolution_exists(movement_id=None, payment_id=None):
    if movement_id and MpReconciliation.query.filter_by(mp_movement_id=movement_id).first():
        return True
    if payment_id and MpReconciliation.query.filter_by(payment_id=payment_id).first():
        return True
    return False


def resolve(user, kind, movement_id=None, payment_id=None, sale_id=None, payment_method_id=None, note=None):
    _require(user)
    if kind not in RESOLUTION_KINDS:
        raise bad_request('La resolución es inválida')
    note = clean_str(note, 255)
    movement = db.session.get(MpMovement, parse_id(movement_id, 'El movimiento')) if movement_id else None
    payment = db.session.get(PosPayment, parse_id(payment_id, 'El pago')) if payment_id else None
    if movement_id and movement is None:
        raise not_found('El movimiento no existe')
    if payment_id and payment is None:
        raise not_found('El pago no existe')
    if kind in ('matched_manual', 'not_a_sale', 'payment_created') and movement is None:
        raise bad_request('Elegí el movimiento de MercadoPago')
    if _resolution_exists(movement.id if movement else None, payment.id if payment else None) or \
            (payment is not None and payment.mp_payment_id and kind != 'matched_manual'):
        raise PosError('Ya está conciliado')
    if kind == 'matched_manual':
        if payment is None:
            raise bad_request('Elegí el pago de Galia')
        if payment.mp_payment_id:
            raise PosError('Ese pago ya está cruzado con otro movimiento')
        payment.mp_payment_id = movement.mp_payment_id
    elif kind == 'payment_created':
        if not sale_id or not payment_method_id:
            raise bad_request('Elegí la venta y el medio de pago')
        method = db.session.get(PaymentMethod, parse_id(payment_method_id, 'El medio de pago'))
        if method is None or not method.is_mercadopago:
            raise bad_request('Elegí un medio de pago de MercadoPago')
        request_id = f'mp-mov-{movement.id}'
        payment_service.add_payment(user, parse_id(sale_id, 'La venta'), method.id, movement.amount,
                                    client_request_id=request_id)
        payment = PosPayment.query.filter_by(client_request_id=request_id).first()
        payment.mp_payment_id = movement.mp_payment_id
    elif kind == 'not_a_sale':
        if not note:
            raise bad_request('Contá en la nota qué es ese movimiento')
        payment = None
    elif kind == 'reviewed':
        if payment is None:
            raise bad_request('Elegí el pago de Galia')
        if not note:
            raise bad_request('Contá en la nota qué revisaste')
        movement = None
    resolution = MpReconciliation(mp_movement_id=movement.id if movement else None,
                                  payment_id=payment.id if payment else None, kind=kind, note=note,
                                  created_by=user.id, created_at=now())
    db.session.add(resolution)
    db.session.commit()
    return _resolution_row(resolution)


def undo(user, resolution_id):
    _require(user)
    resolution = db.session.get(MpReconciliation, parse_id(resolution_id, 'La resolución'))
    if resolution is None:
        raise not_found('La resolución no existe')
    if resolution.kind in ('matched_manual', 'payment_created') and resolution.payment_id:
        payment = db.session.get(PosPayment, resolution.payment_id)
        payment.mp_payment_id = None
    db.session.delete(resolution)
    db.session.commit()
```

Nota: deshacer `payment_created` borra el `mp_payment_id` del pago (si no, el cruce por id lo volvería a emparejar), pero **no** anula el pago: se anula aparte, con el flujo normal, como dice el spec. Por eso `test_resolutions_and_undo` espera `pending == 2`.

- [ ] **Step 4: Correr**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_mp_reconciliation.py`
Expected: todos pasan.

- [ ] **Step 5: Commit**

```bash
git -C <worktree> add backend/app/services/mercadopago/reconciliation_service.py backend/tests/test_mp_reconciliation.py
git -C <worktree> commit -m "feat(mp): daily reconciliation of MercadoPago movements"
```

---

### Task 6: API de MercadoPago (cobros, webhook, conciliación, configuración, fake)

**Files:**
- Create: `backend/app/routes/mercadopago.py`, `backend/tests/test_mp_api.py`, `backend/tests/test_mp_concurrency_pg.py`, `backend/tests/test_mp_sandbox.py`
- Modify: `backend/app/__init__.py`, `backend/tests/test_route_access_coverage.py`

**Interfaces:**
- Consumes: `point_service`, `reconciliation_service`, `settings`, `webhook.verify_signature`, `get_client`, `FakeMercadoPago`.
- Produces (prefijo `/api/v1`):
  - las rutas de la tabla del spec;
  - `GET /mp/point-config` (POS o Cobrar) → `{'enabled': bool, 'payment_method_id', 'fake': bool}`;
  - solo con el fake: `POST /mp/fake/point-orders/<id>/<outcome>` (POS o Cobrar), que devuelve 404 si no está el fake.

- [ ] **Step 1: Tests que fallan.** Crear `backend/tests/test_mp_api.py`:

```python
import hashlib
import hmac

import pytest

from app.models import MpPointOrder
from app.services import mercadopago
from app.services.mercadopago.fake import FakeMercadoPago
from mp_helpers import billing_sale, configure_mp
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401


@pytest.fixture
def ctx(pos_app, monkeypatch):
    FakeMercadoPago.reset()
    monkeypatch.setattr(mercadopago, 'get_client', lambda settings: FakeMercadoPago())
    client = pos_app.test_client()
    user = make_user('caja@test.com', modules=('POS', 'Anular'))
    headers = auth_headers(client, user)
    cat = make_catalog()
    _salon, t1, t2 = make_floor()
    configure_mp()
    return client, headers, user, cat, t1, t2


def _signed(data_id, secret='whsec', request_id='req-1', ts='1704908010'):
    manifest = f'id:{data_id.lower()};request-id:{request_id};ts:{ts};'
    digest = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return {'x-signature': f'ts={ts},v1={digest}', 'x-request-id': request_id}


def test_point_flow_through_the_api(ctx):
    client, headers, user, cat, t1, _t2 = ctx
    sale = billing_sale(user, cat, t1)
    config = client.get('/api/v1/mp/point-config', headers=headers).get_json()
    assert config['enabled'] is True
    created = client.post(f'/api/v1/mp/sales/{sale.id}/point', json={'amount': '1800'}, headers=headers)
    assert created.status_code == 201 and created.get_json()['status'] == 'created'
    order_id = created.get_json()['id']
    sale_data = client.get(f'/api/v1/pos/sales/{sale.id}', headers=headers).get_json()
    assert sale_data['point_order']['id'] == order_id
    mp_order_id = MpPointOrder.query.get(order_id).mp_order_id
    FakeMercadoPago().simulate(mp_order_id, 'approved')
    hook = client.post(f'/api/v1/mercadopago/webhook?data.id={mp_order_id}&type=order',
                       json={'type': 'order', 'action': 'order.processed', 'data': {'id': mp_order_id}},
                       headers=_signed(mp_order_id))
    assert hook.status_code == 200
    status = client.get(f'/api/v1/mp/point-orders/{order_id}', headers=headers).get_json()
    assert status['status'] == 'approved' and status['payment_id']
    assert client.get(f'/api/v1/mp/sales/{sale.id}/point-orders', headers=headers).get_json()['orders'][0]['id'] == \
        order_id


def test_webhook_signature(ctx):
    client, *_ = ctx
    bad = client.post('/api/v1/mercadopago/webhook?data.id=X', json={'type': 'order', 'data': {'id': 'X'}},
                      headers={'x-signature': 'ts=1,v1=00', 'x-request-id': 'r'})
    assert bad.status_code == 401
    other = client.post('/api/v1/mercadopago/webhook?data.id=123', json={'type': 'payment', 'data': {'id': '123'}},
                        headers=_signed('123'))
    assert other.status_code == 200
    unknown_order = client.post('/api/v1/mercadopago/webhook?data.id=NOPE', json={'type': 'order', 'data': {'id': 'NOPE'}},
                                headers=_signed('NOPE'))
    assert unknown_order.status_code == 200


def test_cancel_and_permissions(ctx):
    client, headers, user, cat, t1, t2 = ctx
    sale = billing_sale(user, cat, t1)
    order_id = client.post(f'/api/v1/mp/sales/{sale.id}/point', json={'amount': '100'}, headers=headers).get_json()['id']
    busy = client.post(f'/api/v1/mp/sales/{billing_sale(user, cat, t2).id}/point', json={'amount': '100'},
                       headers=headers)
    assert busy.status_code == 409 and 'El Point está cobrando' in busy.get_json()['error']
    assert client.post(f'/api/v1/mp/point-orders/{order_id}/cancel', headers=headers).get_json()['status'] == 'canceled'
    waiter = auth_headers(client, make_user('mozo@test.com', modules=('Camarero',)))
    assert client.post(f'/api/v1/mp/sales/{sale.id}/point', json={'amount': '1'}, headers=waiter).status_code == 403
    charger = auth_headers(client, make_user('mozo2@test.com', modules=('Camarero', 'Cobrar')))
    assert client.post(f'/api/v1/mp/sales/{sale.id}/point', json={'amount': '1'}, headers=charger).status_code == 201
    assert client.get('/api/v1/mp/settings', headers=headers).status_code == 403
    assert client.get('/api/v1/mp/reconciliation/2026-10-15', headers=headers).status_code == 403


def test_reconciliation_api(ctx):
    client, *_ = ctx
    concilia = auth_headers(client, make_user('conc@test.com', modules=('Conciliar',)))
    FakeMercadoPago().add_payment_movement({'id': 1, 'date_created': '2026-10-15T12:00:00.000-03:00',
                                            'transaction_amount': 500, 'status': 'approved',
                                            'payment_type_id': 'bank_transfer'})
    assert client.post('/api/v1/mp/reconciliation/2026-10-15/fetch', headers=concilia).get_json()['fetched'] == 1
    day = client.get('/api/v1/mp/reconciliation/2026-10-15', headers=concilia).get_json()
    movement_id = day['only_mp'][0]['movement_id']
    resolved = client.post('/api/v1/mp/reconciliation/resolutions', json={
        'kind': 'not_a_sale', 'movement_id': movement_id, 'note': 'Aporte del dueño'}, headers=concilia)
    assert resolved.status_code == 201
    summary = client.get('/api/v1/mp/reconciliation?from=2026-10-15&to=2026-10-15', headers=concilia).get_json()
    assert summary['days'][0]['status'] == 'conciliado'
    assert client.delete(f"/api/v1/mp/reconciliation/resolutions/{resolved.get_json()['id']}",
                         headers=concilia).status_code == 200
    assert client.get('/api/v1/mp/reconciliation/xx', headers=concilia).status_code == 400


def test_settings_admin(ctx):
    client, *_ = ctx
    admin = auth_headers(client, make_user('admin@test.com', role='admin'))
    data = client.get('/api/v1/mp/settings', headers=admin).get_json()
    assert data['terminal_id'] and 'TEST-TOKEN' not in str(data)
    saved = client.put('/api/v1/mp/settings/token', json={'environment': 'test', 'access_token': 'TEST-2'},
                       headers=admin)
    assert saved.status_code == 200 and saved.get_json()['user_id'] == '1'
    assert client.get('/api/v1/mp/settings/terminals', headers=admin).get_json()['terminals'][0]['operating_mode'] == 'PDV'
    assert client.post('/api/v1/mp/settings/terminals/PAX_A910__SMARTPOS1/pdv', headers=admin).status_code == 200
    put = client.put('/api/v1/mp/settings', json={'terminal_id': 'PAX_A910__SMARTPOS1', 'webhook_secret': 'nuevo',
                                                  'environment': 'test'}, headers=admin)
    assert put.status_code == 200 and put.get_json()['has_webhook_secret'] is True
    assert client.post('/api/v1/mp/settings/test', headers=admin).get_json()['ok'] is True
    assert client.put('/api/v1/mp/settings', json={'environment': 'x'}, headers=admin).status_code == 400


def test_fake_debug_endpoint_only_with_fake(ctx, monkeypatch):
    client, headers, user, cat, t1, _t2 = ctx
    sale = billing_sale(user, cat, t1)
    order_id = client.post(f'/api/v1/mp/sales/{sale.id}/point', json={'amount': '1800'}, headers=headers).get_json()['id']
    assert client.post(f'/api/v1/mp/fake/point-orders/{order_id}/approved', headers=headers).status_code == 404
    monkeypatch.setenv('MP_FAKE', '1')
    simulated = client.post(f'/api/v1/mp/fake/point-orders/{order_id}/approved', headers=headers)
    assert simulated.status_code == 200 and simulated.get_json()['status'] == 'approved'
```

Crear `backend/tests/test_mp_concurrency_pg.py`:

```python
import os
import threading
from decimal import Decimal

import pytest

from app import create_app
from app.config import Config, config
from app.extensions import db
from app.models import PosPayment
from app.services import mercadopago
from app.services.mercadopago import point_service
from app.services.mercadopago.fake import FakeMercadoPago
from mp_helpers import billing_sale, configure_mp
from pos_helpers import make_catalog, make_floor, make_user

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


def test_webhook_and_refresh_apply_once(pg_app, monkeypatch):
    FakeMercadoPago.reset()
    monkeypatch.setattr(mercadopago, 'get_client', lambda settings: FakeMercadoPago())
    with pg_app.app_context():
        user = make_user('caja@test.com', modules=('POS',))
        cat = make_catalog()
        _salon, t1, _t2 = make_floor()
        configure_mp()
        sale = billing_sale(user, cat, t1)
        order = point_service.start(user, sale.id, Decimal('1800'))
        FakeMercadoPago().simulate(order.mp_order_id, 'approved')
        order_id = order.id
    barrier = threading.Barrier(2)

    def run():
        with pg_app.app_context():
            barrier.wait()
            point_service.apply(order_id)
            db.session.remove()

    threads = [threading.Thread(target=run) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    with pg_app.app_context():
        assert PosPayment.query.filter_by(client_request_id=f'mp-order-{order_id}').count() == 1
```

Crear `backend/tests/test_mp_sandbox.py`:

```python
"""Crea y cancela una orden real en el entorno de prueba de MercadoPago. Solo con MP_TEST_TOKEN y MP_TEST_TERMINAL."""
import os
import uuid
from decimal import Decimal

import pytest

from app.services.mercadopago.client import MpClient, order_state

pytestmark = pytest.mark.skipif(not (os.getenv('MP_TEST_TOKEN') and os.getenv('MP_TEST_TERMINAL')),
                                reason='Sin credenciales de prueba de MercadoPago')


def test_real_order_create_and_cancel():
    client = MpClient(os.environ['MP_TEST_TOKEN'])
    assert client.me()['id']
    terminals = [t['id'] for t in client.list_terminals()]
    assert os.environ['MP_TEST_TERMINAL'] in terminals
    key = str(uuid.uuid4())
    order = client.create_order(os.environ['MP_TEST_TERMINAL'], Decimal('15'), f'galia-test-{key[:8]}', key)
    assert order_state(client.get_order(order['id']))['status'] in ('created', 'processing')
    client.cancel_order(order['id'])
    assert order_state(client.get_order(order['id']))['status'] == 'canceled'
```

- [ ] **Step 2: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_mp_api.py`
Expected: 404 en las rutas.

- [ ] **Step 3: Rutas.** Crear `backend/app/routes/mercadopago.py`:

```python
"""API de MercadoPago: cobros con Point, webhook, conciliación y configuración."""
import logging
from datetime import date

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import DataError, IntegrityError

from app.extensions import db
from app.services import mercadopago
from app.services.mercadopago import MpRejected, MpUnavailable, point_service
from app.services.mercadopago import reconciliation_service as reconciliation
from app.services.mercadopago import settings as mp_settings
from app.services.mercadopago.webhook import verify_signature
from app.services.pos.errors import PosError, bad_request, not_found
from app.utils.decorators import admin_required, module_required, public_endpoint
from app.utils.jwt_utils import token_required
from app.utils.validation import clean_str, json_object

logger = logging.getLogger(__name__)
bp = Blueprint('mercadopago', __name__, url_prefix='/api/v1')


def _body():
    return json_object() or {}


def _run(action, status=200):
    try:
        payload = action()
        if isinstance(payload, tuple):
            payload, status = payload
    except PosError as exc:
        db.session.rollback()
        return jsonify({'error': exc.message, **exc.extra}), exc.status
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Otra operación modificó los datos al mismo tiempo, probá de nuevo'}), 409
    except DataError:
        db.session.rollback()
        return jsonify({'error': 'Algún valor es demasiado grande'}), 400
    except Exception:
        db.session.rollback()
        logger.exception('Error inesperado en MercadoPago')
        return jsonify({'error': 'Error interno, probá de nuevo'}), 500
    return jsonify(payload), status


def _day(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise bad_request('La fecha es inválida')


# Cobros con Point

@bp.route('/mp/point-config', methods=['GET'])
@token_required
@module_required('POS', 'Cobrar')
def point_config(current_user):
    settings = mp_settings.get_settings()
    return jsonify({'enabled': not mp_settings.missing(settings),
                    'payment_method_id': settings.point_payment_method_id if settings else None,
                    'fake': mercadopago.fake_enabled()}), 200


@bp.route('/mp/sales/<int:sale_id>/point', methods=['POST'])
@token_required
@module_required('POS', 'Cobrar')
def start_point(current_user, sale_id):
    return _run(lambda: (point_service.order_to_dict(
        point_service.start(current_user, sale_id, _body().get('amount'))), 201))


@bp.route('/mp/point-orders/<int:order_id>', methods=['GET'])
@token_required
@module_required('POS', 'Cobrar')
def get_point_order(current_user, order_id):
    return _run(lambda: point_service.order_to_dict(point_service.refresh(order_id)))


@bp.route('/mp/point-orders/<int:order_id>/cancel', methods=['POST'])
@token_required
@module_required('POS', 'Cobrar')
def cancel_point_order(current_user, order_id):
    return _run(lambda: point_service.order_to_dict(point_service.cancel(current_user, order_id)))


@bp.route('/mp/sales/<int:sale_id>/point-orders', methods=['GET'])
@token_required
@module_required('POS', 'Cobrar')
def sale_point_orders(current_user, sale_id):
    return _run(lambda: {'orders': point_service.sale_orders(sale_id)})


@bp.route('/mp/fake/point-orders/<int:order_id>/<outcome>', methods=['POST'])
@token_required
@module_required('POS', 'Cobrar')
def fake_point(current_user, order_id, outcome):
    """Solo con FakeMercadoPago: simula lo que haría el Point (para el preview)."""
    def action():
        if not mercadopago.fake_enabled() or outcome not in ('approved', 'rejected', 'expired', 'processing'):
            raise not_found('No disponible')
        from app.services.mercadopago.fake import FakeMercadoPago
        from app.models import MpPointOrder
        order = db.session.get(MpPointOrder, order_id)
        if order is None or not order.mp_order_id:
            raise not_found('El cobro no existe')
        FakeMercadoPago().simulate(order.mp_order_id, outcome)
        return point_service.order_to_dict(point_service.apply(order.id))
    return _run(action)


@bp.route('/mercadopago/webhook', methods=['POST'])
@public_endpoint
def webhook():
    payload = request.get_json(silent=True) or {}
    data_id = request.args.get('data.id') or (payload.get('data') or {}).get('id')
    secret = mp_settings.webhook_secret(mp_settings.get_settings())
    if not verify_signature(secret, request.headers.get('x-signature'), request.headers.get('x-request-id'),
                            data_id):
        logger.warning('Webhook de MercadoPago con firma inválida (data.id=%s)', data_id)
        return jsonify({'error': 'firma inválida'}), 401
    topic = payload.get('type') or request.args.get('type') or ''
    if topic.startswith('order') and data_id:
        try:
            point_service.apply_by_mp_order_id(data_id)
        except Exception:
            db.session.rollback()
            logger.exception('Error procesando el webhook de la orden %s', data_id)
    return jsonify({'ok': True}), 200


# Conciliación

@bp.route('/mp/reconciliation', methods=['GET'])
@token_required
@module_required('Conciliar')
def reconciliation_summary(current_user):
    return _run(lambda: {'days': reconciliation.summary(_day(request.args.get('from')),
                                                        _day(request.args.get('to')))})


@bp.route('/mp/reconciliation/<day>', methods=['GET'])
@token_required
@module_required('Conciliar')
def reconciliation_day(current_user, day):
    return _run(lambda: reconciliation.day(_day(day)))


@bp.route('/mp/reconciliation/<day>/fetch', methods=['POST'])
@token_required
@module_required('Conciliar')
def reconciliation_fetch(current_user, day):
    return _run(lambda: reconciliation.fetch(current_user, _day(day)))


@bp.route('/mp/reconciliation/resolutions', methods=['POST'])
@token_required
@module_required('Conciliar')
def reconciliation_resolve(current_user):
    def action():
        data = _body()
        return reconciliation.resolve(current_user, data.get('kind'), data.get('movement_id'), data.get('payment_id'),
                                      data.get('sale_id'), data.get('payment_method_id'), data.get('note')), 201
    return _run(action)


@bp.route('/mp/reconciliation/resolutions/<int:resolution_id>', methods=['DELETE'])
@token_required
@module_required('Conciliar')
def reconciliation_undo(current_user, resolution_id):
    def action():
        reconciliation.undo(current_user, resolution_id)
        return {'ok': True}
    return _run(action)


# Configuración (admin)

@bp.route('/mp/settings', methods=['GET'])
@token_required
@admin_required
def get_settings(current_user):
    def action():
        settings = mp_settings.get_or_create_settings()
        db.session.commit()
        return mp_settings.settings_to_dict(settings)
    return _run(action)


@bp.route('/mp/settings', methods=['PUT'])
@token_required
@admin_required
def put_settings(current_user):
    def action():
        data = _body()
        settings = mp_settings.get_or_create_settings()
        if 'environment' in data:
            if data['environment'] not in ('test', 'production'):
                raise bad_request('El entorno tiene que ser prueba o producción')
            settings.environment = data['environment']
        if 'terminal_id' in data:
            settings.terminal_id = clean_str(data['terminal_id'], 80)
        if 'webhook_secret' in data:
            secret = clean_str(data['webhook_secret'], 200)
            settings.webhook_secret = mp_settings.encrypt(secret) if secret else None
        if 'point_payment_method_id' in data:
            settings.point_payment_method_id = data['point_payment_method_id'] or None
        db.session.commit()
        return mp_settings.settings_to_dict(settings)
    return _run(action)


@bp.route('/mp/settings/token', methods=['PUT'])
@token_required
@admin_required
def put_token(current_user):
    def action():
        data = _body()
        environment = data.get('environment')
        token = clean_str(data.get('access_token'), 300)
        if environment not in ('test', 'production') or not token:
            raise bad_request('Indicá el entorno y el access token')
        settings = mp_settings.get_or_create_settings()
        settings.set_token(environment, mp_settings.encrypt(token))
        db.session.flush()
        previous = settings.environment
        settings.environment = environment
        try:
            account = mercadopago.get_client(settings).me()
        except MpUnavailable:
            raise PosError('MercadoPago no responde, probá de nuevo')
        except MpRejected:
            raise bad_request('MercadoPago no aceptó el token: revisá que sea el access token de la integración')
        finally:
            settings.environment = previous
        settings.user_id = str(account.get('id'))
        db.session.commit()
        return mp_settings.settings_to_dict(settings)
    return _run(action)


@bp.route('/mp/settings/terminals', methods=['GET'])
@token_required
@admin_required
def list_terminals(current_user):
    def action():
        try:
            return {'terminals': mercadopago.get_client(mp_settings.get_settings()).list_terminals()}
        except MpUnavailable:
            raise PosError('MercadoPago no responde, probá de nuevo')
        except MpRejected as exc:
            raise PosError(f'MercadoPago respondió: {exc.message}')
    return _run(action)


@bp.route('/mp/settings/terminals/<terminal_id>/pdv', methods=['POST'])
@token_required
@admin_required
def set_pdv(current_user, terminal_id):
    def action():
        try:
            mercadopago.get_client(mp_settings.get_settings()).set_pdv_mode(terminal_id)
        except MpUnavailable:
            raise PosError('MercadoPago no responde, probá de nuevo')
        except MpRejected as exc:
            raise PosError(f'MercadoPago respondió: {exc.message}')
        return {'ok': True, 'message': 'Listo: reiniciá el Point para que tome el modo PDV'}
    return _run(action)


@bp.route('/mp/settings/test', methods=['POST'])
@token_required
@admin_required
def test_connection(current_user):
    def action():
        settings = mp_settings.get_settings()
        mp_settings.require_ready(settings)
        client = mercadopago.get_client(settings)
        try:
            account = client.me()
            terminals = {t['id']: t for t in client.list_terminals()}
        except MpUnavailable:
            raise PosError('MercadoPago no responde, probá de nuevo')
        except MpRejected as exc:
            raise PosError(f'MercadoPago respondió: {exc.message}')
        terminal = terminals.get(settings.terminal_id)
        if terminal is None:
            raise PosError('La terminal configurada no está en la cuenta')
        if terminal.get('operating_mode') != 'PDV':
            raise PosError('La terminal no está en modo PDV')
        return {'ok': True, 'account': account.get('nickname') or account.get('id'), 'terminal': settings.terminal_id}
    return _run(action)
```

Antes de usarlo, revisar en `backend/app/utils/decorators.py` cómo se marca un endpoint público. Si no existe `public_endpoint`, no usar decorador: alcanza con sumar `'mercadopago.webhook'` a `PUBLIC_ENDPOINTS`. En ese caso, quitar el import y el decorador.

En `backend/tests/test_route_access_coverage.py`, sumar `'mercadopago.webhook',` a `PUBLIC_ENDPOINTS`.

En `backend/app/__init__.py`, sumar `mercadopago` al import de rutas (ojo con el nombre: importarlo como `mercadopago as mercadopago_routes` para no chocar con el paquete de servicios) y registrar `app.register_blueprint(mercadopago_routes.bp)` después de `fiscal.bp`.

- [ ] **Step 4: Correr**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_mp_api.py tests/test_mp_concurrency_pg.py tests/test_mp_sandbox.py tests/test_route_access_coverage.py`
Expected: pasan; los de PostgreSQL y del entorno de prueba quedan `skipped`.

- [ ] **Step 5: Suite completa contra la línea base** (cwd `backend/`):

```
PY -m pytest -q -p no:cacheprovider -rfE > <scratch>/mp_pytest.txt
PY scripts/compare_baseline.py <scratch>/mp_pytest.txt ../docs/superpowers/plans/2026-10-08-pos-base-test-baseline.txt
```

Expected: `Sin fallas nuevas.`

- [ ] **Step 6: Commit**

```bash
git -C <worktree> add backend/app/routes/mercadopago.py backend/app/__init__.py backend/tests/test_mp_api.py backend/tests/test_mp_concurrency_pg.py backend/tests/test_mp_sandbox.py backend/tests/test_route_access_coverage.py
git -C <worktree> commit -m "feat(mp): MercadoPago API, signed webhook, reconciliation and settings endpoints"
```

---

### Task 7: Frontend, datos y lógica pura

**Files:**
- Create: `frontend/src/pos/mercadopago/pointCharge.js` (+ `.test.js`), `frontend/src/pos/mercadopago/reconciliation.js` (+ `.test.js`)
- Modify: `frontend/src/pos/api/posApi.js`, `frontend/src/pos/hooks/keys.js`

**Interfaces:**
- Produces:
  - **`posMpApi`:**
    - de cobro: `pointConfig()`, `startPoint(saleId, amount)`, `pointOrder(id)`, `cancelPoint(id)`, `salePointOrders(saleId)`, `fakePoint(id, outcome)`;
    - de conciliación: `reconciliationSummary(from, to)`, `reconciliationDay(day)`, `fetchDay(day)`, `resolve(body)`, `undo(id)`;
    - de configuración: `settings()`, `saveSettings(body)`, `saveToken(environment, token)`, `terminals()`, `setPdv(id)`, `testConnection()`.
  - **`posKeys`:** `mp: ['pos', 'mp']`, `mpPointConfig`, `mpPointOrder(id)`, `mpSettings`, `mpReconciliation(day)`, `mpReconciliationSummary(from, to)`.
  - **`pointCharge`:**
    - `isFinal(status)`, `isWaiting(status)`;
    - `waitingLabel(order) -> string`, `resultMessage(order) -> {tone, text}`;
    - `POLL_MS = 3000`, `elapsedText(createdAt, now)`.
  - **`reconciliation`:** `statusLabel(status)`, `channelLabel(channel)`, `monthDays(year, month) -> ['YYYY-MM-DD']`.

- [ ] **Step 1: Tests que fallan.** Crear `frontend/src/pos/mercadopago/pointCharge.test.js`:

```js
import { describe, expect, it } from 'vitest'
import { elapsedText, isFinal, isWaiting, resultMessage, waitingLabel } from './pointCharge'

describe('pointCharge', () => {
  it('clasifica los estados', () => {
    expect(isWaiting('created')).toBe(true)
    expect(isWaiting('canceling')).toBe(true)
    expect(isFinal('approved')).toBe(true)
    expect(isFinal('processing')).toBe(false)
  })
  it('describe la espera', () => {
    expect(waitingLabel({ status: 'created' })).toBe('Esperando el cobro en el Point…')
    expect(waitingLabel({ status: 'processing' })).toBe('Cobrando en el Point…')
    expect(waitingLabel({ status: 'canceling' })).toBe('Cancelando en el Point…')
  })
  it('arma el mensaje del resultado', () => {
    expect(resultMessage({ status: 'approved', error: null })).toEqual({ tone: 'ok', text: 'Cobro aprobado' })
    expect(resultMessage({ status: 'approved', error: 'Cobrado de más: $10.00, revisalo en Conciliación' }).tone).toBe('warn')
    expect(resultMessage({ status: 'failed', error: 'El pago fue rechazado en el Point: fondos insuficientes' }))
      .toEqual({ tone: 'error', text: 'El pago fue rechazado en el Point: fondos insuficientes' })
    expect(resultMessage({ status: 'expired', error: null }).text).toBe('El cobro venció sin pagarse')
  })
  it('muestra el tiempo transcurrido', () => {
    expect(elapsedText('2026-10-15T12:00:00', new Date('2026-10-15T12:01:05Z'))).toBe('1:05')
  })
})
```

Crear `frontend/src/pos/mercadopago/reconciliation.test.js`:

```js
import { describe, expect, it } from 'vitest'
import { channelLabel, monthDays, statusLabel } from './reconciliation'

describe('reconciliation', () => {
  it('etiquetas', () => {
    expect(statusLabel('conciliado')).toBe('Conciliado')
    expect(statusLabel('con_diferencias')).toBe('Con diferencias')
    expect(statusLabel('sin_traer')).toBe('Sin traer')
    expect(channelLabel('point')).toBe('Point')
    expect(channelLabel('transfer')).toBe('Transferencia')
    expect(channelLabel('raro')).toBe('Otro')
  })
  it('días del mes', () => {
    const days = monthDays(2026, 2)
    expect(days[0]).toBe('2026-02-01')
    expect(days.at(-1)).toBe('2026-02-28')
  })
})
```

- [ ] **Step 2: Correr y ver que fallen**

Run: `npx vitest run src/pos/mercadopago`
Expected: FAIL (no existen los módulos).

- [ ] **Step 3: Implementar.** Crear `frontend/src/pos/mercadopago/pointCharge.js`:

```js
import { parseServerDate } from '../utils/time'

export const POLL_MS = 3000
const WAITING = ['creating', 'created', 'processing', 'canceling']
const FINAL = ['approved', 'failed', 'canceled', 'expired']

export const isWaiting = (status) => WAITING.includes(status)
export const isFinal = (status) => FINAL.includes(status)

export function waitingLabel(order) {
  if (order.status === 'processing') return 'Cobrando en el Point…'
  if (order.status === 'canceling') return 'Cancelando en el Point…'
  return 'Esperando el cobro en el Point…'
}

export function resultMessage(order) {
  if (order.status === 'approved') {
    return order.error ? { tone: 'warn', text: order.error } : { tone: 'ok', text: 'Cobro aprobado' }
  }
  const fallback = { failed: 'No se pudo cobrar', canceled: 'Se canceló el cobro', expired: 'El cobro venció sin pagarse' }
  return { tone: 'error', text: order.error || fallback[order.status] || 'No se pudo cobrar' }
}

export function elapsedText(createdAt, now = new Date()) {
  const seconds = Math.max(0, Math.floor((now - parseServerDate(createdAt)) / 1000))
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`
}
```

Crear `frontend/src/pos/mercadopago/reconciliation.js`:

```js
const STATUS = { conciliado: 'Conciliado', con_diferencias: 'Con diferencias', sin_traer: 'Sin traer' }
const CHANNELS = { point: 'Point', qr: 'QR', link: 'Link de pago', transfer: 'Transferencia', other: 'Otro' }

export const statusLabel = (status) => STATUS[status] ?? status
export const channelLabel = (channel) => CHANNELS[channel] ?? 'Otro'

export function monthDays(year, month) {
  const last = new Date(Date.UTC(year, month, 0)).getUTCDate()
  return Array.from({ length: last }, (_, i) => `${year}-${String(month).padStart(2, '0')}-${String(i + 1).padStart(2, '0')}`)
}
```

En `frontend/src/pos/api/posApi.js`, agregar al final:

```js
export const posMpApi = {
  pointConfig: () => data(api.get('/mp/point-config')),
  startPoint: (saleId, amount) => data(api.post(`/mp/sales/${saleId}/point`, { amount })),
  pointOrder: (id) => data(api.get(`/mp/point-orders/${id}`)),
  cancelPoint: (id) => data(api.post(`/mp/point-orders/${id}/cancel`)),
  salePointOrders: (saleId) => data(api.get(`/mp/sales/${saleId}/point-orders`)).then((d) => d.orders),
  fakePoint: (id, outcome) => data(api.post(`/mp/fake/point-orders/${id}/${outcome}`)),
  reconciliationSummary: (from, to) => data(api.get('/mp/reconciliation', { params: { from, to } })).then((d) => d.days),
  reconciliationDay: (day) => data(api.get(`/mp/reconciliation/${day}`)),
  fetchDay: (day) => data(api.post(`/mp/reconciliation/${day}/fetch`)),
  resolve: (body) => data(api.post('/mp/reconciliation/resolutions', body)),
  undo: (id) => data(api.delete(`/mp/reconciliation/resolutions/${id}`)),
  settings: () => data(api.get('/mp/settings')),
  saveSettings: (body) => data(api.put('/mp/settings', body)),
  saveToken: (environment, accessToken) => data(api.put('/mp/settings/token', { environment, access_token: accessToken })),
  terminals: () => data(api.get('/mp/settings/terminals')).then((d) => d.terminals),
  setPdv: (id) => data(api.post(`/mp/settings/terminals/${id}/pdv`)),
  testConnection: () => data(api.post('/mp/settings/test')),
}
```

En `frontend/src/pos/hooks/keys.js`, dentro de `posKeys`:

```js
  mp: ['pos', 'mp'],
  mpPointConfig: ['pos', 'mp', 'point-config'],
  mpPointOrder: (id) => ['pos', 'mp', 'point-order', id],
  mpSettings: ['pos', 'mp', 'settings'],
  mpReconciliation: (day) => ['pos', 'mp', 'reconciliation', day],
  mpReconciliationSummary: (from, to) => ['pos', 'mp', 'reconciliation-summary', from, to],
```

- [ ] **Step 4: Verificar**

Run: `npx vitest run src/pos/mercadopago`, después `npm test` y `npm run build`.
Expected: todo pasa.

- [ ] **Step 5: Commit**

```bash
git -C <worktree> add frontend/src/pos
git -C <worktree> commit -m "feat(mp): MercadoPago API client and point charge logic"
```

---

### Task 8: Cobro con el Point en el modal de pago, aviso pendiente y devolución al anular

**Files:**
- Create: `frontend/src/pos/mercadopago/PointWait.jsx`, `frontend/src/pos/mercadopago/PointPendingNotice.jsx`
- Modify: `frontend/src/pos/modals/PaymentModal.jsx`, `frontend/src/pos/modals/CancelReasonModal.jsx`, `frontend/src/pos/sale/SalePanel.jsx`

**Interfaces:**
- Consumes: `posMpApi`, `posKeys`, `pointCharge` (Task 7); `Modal`, `btn`, `formatMoney`, `errorMessage`, `useToast`.
- Produces:
  - `PointWait({ orderId, onApproved, onDone })`: hace la consulta de respaldo y muestra el resultado;
  - `PointPendingNotice({ sale })`;
  - `CancelReasonModal` con la prop opcional `refundable`: suma `refund_mp` al body.

- [ ] **Step 1: Espera del cobro.** Crear `frontend/src/pos/mercadopago/PointWait.jsx`:

```jsx
import { useEffect, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { posMpApi } from '../api/posApi'
import { posKeys } from '../hooks/keys'
import { btn } from '../ui/buttons'
import { errorMessage } from '../utils/errors'
import { formatMoney } from '../utils/money'
import { POLL_MS, elapsedText, isFinal, resultMessage, waitingLabel } from './pointCharge'

const TONES = { ok: 'bg-green-50 text-green-800', warn: 'bg-amber-50 text-amber-900', error: 'bg-red-50 text-red-800' }

// Espera de un cobro en el Point: consulta cada 3 s (respaldo del webhook) y muestra el resultado.
export default function PointWait({ orderId, saleId, onApproved, onDone }) {
  const queryClient = useQueryClient()
  const [now, setNow] = useState(new Date())
  const [error, setError] = useState('')
  const { data: order } = useQuery({
    queryKey: posKeys.mpPointOrder(orderId), queryFn: () => posMpApi.pointOrder(orderId),
    refetchInterval: (query) => (query.state.data && isFinal(query.state.data.status) ? false : POLL_MS),
  })
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])
  useEffect(() => {
    if (order && isFinal(order.status)) {
      queryClient.invalidateQueries({ queryKey: posKeys.sale(saleId) })
      if (order.status === 'approved') onApproved?.(order)
    }
  }, [order?.status]) // eslint-disable-line react-hooks/exhaustive-deps

  const act = async (fn) => {
    setError('')
    try {
      queryClient.setQueryData(posKeys.mpPointOrder(orderId), await fn())
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  if (!order) return <p className="py-6 text-center text-gray-500">Enviando al Point…</p>
  if (isFinal(order.status)) {
    const message = resultMessage(order)
    return (
      <div className="space-y-3">
        <p className={`rounded-lg p-3 ${TONES[message.tone]}`}>{message.text}</p>
        <button type="button" className={btn('primary', 'w-full')} onClick={() => onDone?.(order)}>
          {order.status === 'approved' ? 'Listo' : 'Volver al cobro'}
        </button>
      </div>
    )
  }
  return (
    <div className="space-y-3 text-center">
      <p className="text-3xl font-bold text-galia-plum">{formatMoney(order.amount)}</p>
      <p className="text-gray-700">{waitingLabel(order)}</p>
      <p className="font-mono text-sm text-gray-500">{elapsedText(order.created_at, now)}</p>
      {error && <p className="text-sm text-red-700">{error}</p>}
      {order.status !== 'canceling' && (
        <button type="button" className={btn('secondary', 'w-full')} onClick={() => act(() => posMpApi.cancelPoint(orderId))}>
          Cancelar cobro
        </button>
      )}
      {order.fake && (
        <div className="flex gap-2 rounded-lg border border-dashed p-2 text-xs">
          <span className="self-center text-gray-500">Simular Point:</span>
          {['approved', 'rejected', 'expired'].map((outcome) => (
            <button key={outcome} type="button" className="underline" onClick={() => act(() => posMpApi.fakePoint(orderId, outcome))}>
              {outcome}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Integrar en el modal de pago.** En `frontend/src/pos/modals/PaymentModal.jsx`:
  - **Imports:**

```js
import { useQuery } from '@tanstack/react-query'
import { posMpApi } from '../api/posApi'
import { posKeys } from '../hooks/keys'
import PointWait from '../mercadopago/PointWait'
```

  (sumar `posMpApi` al import existente de `../api/posApi` en lugar de duplicarlo).
  - **Estado y config**, después de los `useState`:

```js
  const { data: pointConfig } = useQuery({ queryKey: posKeys.mpPointConfig, queryFn: posMpApi.pointConfig, staleTime: 60_000 })
  const [pointOrderId, setPointOrderId] = useState(sale.point_order?.id ?? null)
```

  - **Después de calcular `method`:**

```js
  const isPoint = Boolean(pointConfig?.enabled && method && method.id === pointConfig.payment_method_id)
```

  - **En `submit`**, después de las validaciones de monto y antes de armar `body`:

```js
    if (isPoint) {
      try {
        const order = await posMpApi.startPoint(sale.id, amount)
        if (order.status === 'failed') return setError(order.error)
        setPointOrderId(order.id)
      } catch (err) {
        setError(errorMessage(err))
      }
      return undefined
    }
```

  - **Antes del `return` principal** (el de "Cobrar …"), agregar:

```jsx
  if (pointOrderId) {
    return (
      <Modal title={`Cobrar ${saleTitle(sale)} · Point`} onClose={onClose} size="sm">
        <PointWait orderId={pointOrderId} saleId={sale.id}
          onDone={(order) => {
            setPointOrderId(null)
            if (order.status === 'approved') {
              if (order.approved_amount && Number(order.approved_amount) >= Number(sale.balance)) setClosedChange(0)
              else resetForNext({ balance: Math.max(0, Number(sale.balance) - Number(order.approved_amount ?? 0)) })
            }
          }} />
      </Modal>
    )
  }
```

  - **Botón principal:** cambiar su texto por `{isPoint ? 'Enviar al Point' : amount >= sale.balance ? 'Registrar pago y cerrar' : 'Registrar pago'}`.
  - **Recibido y vuelto:** ocultar el bloque de "Recibido/vuelto" cuando `isPoint` (ya pasa, porque el medio Point es `card`).

- [ ] **Step 3: Aviso pendiente en la venta.** Crear `frontend/src/pos/mercadopago/PointPendingNotice.jsx`:

```jsx
import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { posMpApi } from '../api/posApi'
import { posKeys } from '../hooks/keys'
import { useToast } from '../ui/Toasts'
import { errorMessage } from '../utils/errors'
import { formatMoney } from '../utils/money'

// "Cobro en Point pendiente": aparece si se cerró el modal mientras el Point cobraba.
export default function PointPendingNotice({ sale, onOpen }) {
  const queryClient = useQueryClient()
  const toast = useToast()
  const [busy, setBusy] = useState(false)
  const order = sale.point_order
  if (!order) return null
  const cancel = async () => {
    setBusy(true)
    try {
      await posMpApi.cancelPoint(order.id)
      toast.success('Se canceló el cobro en el Point')
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
      queryClient.invalidateQueries({ queryKey: posKeys.sale(sale.id) })
    }
  }
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 border-t bg-amber-50 px-4 py-2 text-sm text-amber-900">
      <span>Cobro en Point pendiente · {formatMoney(order.amount)}</span>
      <span className="flex gap-3">
        <button type="button" className="underline" onClick={onOpen}>Ver</button>
        <button type="button" className="underline" disabled={busy} onClick={cancel}>Cancelar</button>
      </span>
    </div>
  )
}
```

En `frontend/src/pos/sale/SalePanel.jsx`:
- importar `PointPendingNotice from '../mercadopago/PointPendingNotice'`;
- justo antes del `<div className="bg-gray-50 pb-[env(safe-area-inset-bottom)]">` del pie, agregar:

```jsx
      <PointPendingNotice sale={sale} onOpen={() => setModal({ type: 'pay' })} />
```

(`PaymentModal` arranca con `pointOrderId = sale.point_order?.id`, así que "Ver" reabre la espera).

- [ ] **Step 4: Devolución al anular.** En `frontend/src/pos/modals/CancelReasonModal.jsx`:
  - agregar la prop `refundable = false` y el estado `const [refund, setRefund] = useState(true)`;
  - en `submit`, `onConfirm({ reason_id: reasonId, reason: text.trim() || null, ...(refundable ? { refund_mp: refund } : {}) })`;
  - antes del mensaje de error, agregar:

```jsx
      {refundable && (
        <fieldset className="mt-4 space-y-1 text-sm">
          <label className="flex items-center gap-2">
            <input type="radio" checked={refund} onChange={() => setRefund(true)} /> Devolver también en MercadoPago
          </label>
          <label className="flex items-center gap-2">
            <input type="radio" checked={!refund} onChange={() => setRefund(false)} /> Solo anular en Galia
          </label>
        </fieldset>
      )}
```

En `frontend/src/pos/modals/PaymentModal.jsx`, pasar `refundable={Boolean(cancelling.refundable_mp)}` al `CancelReasonModal` del pago.

- [ ] **Step 5: Verificar**

Run: `npm test` y `npm run build`.
Expected: todo pasa.

- [ ] **Step 6: Commit**

```bash
git -C <worktree> add frontend/src/pos
git -C <worktree> commit -m "feat(mp): charge with the Point from the payment modal, pending notice and refund option"
```

---

### Task 9: Ajustes → MercadoPago, Conciliación, medios de pago y guía

**Files:**
- Create: `frontend/src/pages/admin/MercadoPagoSettings.jsx`, `frontend/src/pages/MpReconciliation.jsx`, `docs/pos/mercadopago.md`
- Modify: `frontend/src/pages/admin/PosSettings.jsx`, `frontend/src/App.jsx`, `frontend/src/components/layout/Sidebar.jsx`

**Interfaces:**
- Consumes: `posMpApi`, `posKeys`, `reconciliation.js` (Task 7).
- Produces:
  - las rutas `/admin/mercadopago` (admin) y `/mp/reconciliation` (módulo `Conciliar`);
  - la columna "Es de MercadoPago" en Medios de pago.

- [ ] **Step 1: Medios de pago.** En `frontend/src/pages/admin/PosSettings.jsx`, en `TABS['payment-methods']`:
  - `emptyItem` suma `is_mercadopago: false`;
  - `fields` suma `{ key: 'is_mercadopago', label: 'Es de MercadoPago', type: 'checkbox' },` antes de `is_active`.

- [ ] **Step 2: Ajustes.** Crear `frontend/src/pages/admin/MercadoPagoSettings.jsx`:

```jsx
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { posConfigApi, posMpApi } from '@/pos/api/posApi'
import { posKeys } from '@/pos/hooks/keys'
import { errorMessage } from '@/pos/utils/errors'

const card = 'space-y-3 rounded-xl bg-white p-5 shadow-sm'
const input = 'mt-1 w-full rounded border px-3 py-2'

// Ajustes → MercadoPago (admin): entorno, token, terminal (modo PDV), webhook y medio de pago del Point.
export default function MercadoPagoSettings() {
  const queryClient = useQueryClient()
  const { data: settings, isLoading, isError } = useQuery({ queryKey: posKeys.mpSettings, queryFn: posMpApi.settings })
  const { data: methods = [] } = useQuery({ queryKey: ['pos-settings', 'payment-methods'], queryFn: () => posConfigApi.listResource('payment-methods') })
  const [token, setToken] = useState('')
  const [secret, setSecret] = useState('')
  const [terminals, setTerminals] = useState(null)
  const [message, setMessage] = useState(null)
  const act = async (fn, ok) => {
    setMessage(null)
    try {
      const result = await fn()
      queryClient.invalidateQueries({ queryKey: posKeys.mp })
      setMessage({ ok: true, text: typeof ok === 'function' ? ok(result) : ok })
      return result
    } catch (err) {
      setMessage({ ok: false, text: errorMessage(err) })
      return null
    }
  }
  if (isError) return <p className="p-6 text-red-700">No se pudo cargar la configuración.</p>
  if (isLoading) return <p className="p-6">Cargando…</p>
  const webhookUrl = `${(import.meta.env.VITE_API_URL || window.location.origin).replace(/\/$/, '')}/api/v1/mercadopago/webhook`

  return (
    <div className="max-w-3xl space-y-5">
      <h1 className="text-3xl">MercadoPago</h1>
      {settings.environment === 'test' && <p className="rounded-lg bg-amber-50 p-3 text-amber-900">Modo prueba: los cobros no son reales.</p>}
      {settings.missing.length > 0 && <p className="rounded-lg bg-red-50 p-3 text-red-800">Falta: {settings.missing.join(', ')}</p>}
      {message && <p className={`rounded-lg p-3 ${message.ok ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>{message.text}</p>}

      <section className={card}>
        <h2 className="text-lg font-semibold">1. Entorno y token</h2>
        <div className="flex gap-2">
          {[['test', 'Prueba'], ['production', 'Producción']].map(([env, label]) => (
            <button key={env} type="button" className={`rounded px-3 py-1.5 text-sm ${settings.environment === env ? 'bg-galia-plum text-galia-cream' : 'bg-gray-100'}`}
              onClick={() => {
                if (env === 'production' && !window.confirm('Los cobros van a ser reales. ¿Pasar a producción?')) return
                act(() => posMpApi.saveSettings({ environment: env }), 'Entorno cambiado')
              }}>{label}</button>
          ))}
        </div>
        <p className="text-sm text-gray-600">
          Token de prueba: {settings.has_test_token ? 'cargado' : 'falta'} · Token de producción: {settings.has_prod_token ? 'cargado' : 'falta'}
          {settings.user_id ? ` · Cuenta ${settings.user_id}` : ''}
        </p>
        <label className="block text-sm">Access token ({settings.environment === 'test' ? 'prueba' : 'producción'})
          <input type="password" className={input} value={token} onChange={(e) => setToken(e.target.value)} placeholder="APP_USR-…" />
        </label>
        <button type="button" className="rounded bg-galia-plum px-4 py-2 text-galia-cream"
          onClick={() => act(() => posMpApi.saveToken(settings.environment, token), 'Token guardado y verificado').then((r) => r && setToken(''))}>
          Guardar token
        </button>
      </section>

      <section className={card}>
        <h2 className="text-lg font-semibold">2. Terminal</h2>
        <p className="text-sm">Terminal en uso: <span className="font-mono">{settings.terminal_id ?? '—'}</span></p>
        <button type="button" className="rounded border px-3 py-1.5 text-sm" onClick={() => act(posMpApi.terminals, 'Terminales encontradas').then((t) => t && setTerminals(t))}>
          Buscar terminales
        </button>
        {terminals && (
          <ul className="divide-y text-sm">
            {terminals.map((t) => (
              <li key={t.id} className="flex items-center justify-between py-2">
                <span className="font-mono">{t.id} · {t.operating_mode}</span>
                <span className="flex gap-3">
                  {t.operating_mode !== 'PDV' && (
                    <button type="button" className="underline" onClick={() => act(() => posMpApi.setPdv(t.id), (r) => r.message)}>Pasar a modo PDV</button>
                  )}
                  <button type="button" className="underline" onClick={() => act(() => posMpApi.saveSettings({ terminal_id: t.id }), 'Terminal elegida')}>Usar esta</button>
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className={card}>
        <h2 className="text-lg font-semibold">3. Avisos (webhook)</h2>
        <p className="text-sm">URL para cargar en el panel de MercadoPago (evento "Order (Mercado Pago)"):</p>
        <p className="break-all rounded bg-gray-100 p-2 font-mono text-xs">{webhookUrl}</p>
        <label className="block text-sm">Clave secreta {settings.has_webhook_secret ? '(cargada)' : '(falta)'}
          <input type="password" className={input} value={secret} onChange={(e) => setSecret(e.target.value)} />
        </label>
        <button type="button" className="rounded bg-galia-plum px-4 py-2 text-galia-cream"
          onClick={() => act(() => posMpApi.saveSettings({ webhook_secret: secret }), 'Clave guardada').then((r) => r && setSecret(''))}>
          Guardar clave
        </button>
      </section>

      <section className={card}>
        <h2 className="text-lg font-semibold">4. Medio de pago del Point y prueba</h2>
        <select className={input} value={settings.point_payment_method_id ?? ''}
          onChange={(e) => act(() => posMpApi.saveSettings({ point_payment_method_id: e.target.value ? Number(e.target.value) : null }), 'Medio de pago guardado')}>
          <option value="">Elegí el medio "MercadoPago Point"</option>
          {methods.filter((m) => m.is_active).map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
        </select>
        <p className="text-xs text-gray-500">Si no existe, crealo en Ajustes del POS → Medios de pago (tipo Tarjeta, "Es de MercadoPago" y "Lo factura otro sistema").</p>
        <button type="button" className="rounded border px-3 py-1.5 text-sm"
          onClick={() => act(posMpApi.testConnection, (r) => `Conectado · cuenta ${r.account} · terminal ${r.terminal}`)}>Probar conexión</button>
      </section>
    </div>
  )
}
```

- [ ] **Step 3: Conciliación.** Crear `frontend/src/pages/MpReconciliation.jsx`:

```jsx
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { posConfigApi, posMpApi } from '@/pos/api/posApi'
import { posKeys } from '@/pos/hooks/keys'
import { channelLabel, monthDays, statusLabel } from '@/pos/mercadopago/reconciliation'
import { errorMessage } from '@/pos/utils/errors'
import { formatMoney } from '@/pos/utils/money'

const TONE = { conciliado: 'bg-green-100 text-green-800', con_diferencias: 'bg-red-100 text-red-800', sin_traer: 'bg-gray-100 text-gray-600' }
const today = () => new Date().toLocaleDateString('sv-SE', { timeZone: 'America/Argentina/Buenos_Aires' })
const time = (iso) => new Date(`${iso}Z`).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })

function OnlyMpRow({ row, act, methods }) {
  const [mode, setMode] = useState(null)
  const [note, setNote] = useState('')
  const [saleId, setSaleId] = useState('')
  const [methodId, setMethodId] = useState(methods[0]?.id ?? '')
  return (
    <li className="space-y-2 py-2">
      <p>{time(row.date_created)} · {formatMoney(row.amount)} · {channelLabel(row.channel)} · {row.payment_method ?? ''} {row.description ? `· ${row.description}` : ''}</p>
      {row.suggestions.map((s) => (
        <button key={s.payment_id} type="button" className="mr-2 rounded bg-galia-plum/10 px-2 py-1 text-xs"
          onClick={() => act({ kind: 'matched_manual', movement_id: row.movement_id, payment_id: s.payment_id })}>
          Asociar a venta #{s.sale_number} · {s.method_name} {formatMoney(s.amount)} ({time(s.created_at)})
        </button>
      ))}
      <div className="flex flex-wrap gap-3 text-xs">
        <button type="button" className="underline" onClick={() => setMode('create')}>Crear pago en una venta</button>
        <button type="button" className="underline" onClick={() => setMode('not_a_sale')}>No es una venta</button>
      </div>
      {mode === 'create' && (
        <div className="flex flex-wrap gap-2 text-xs">
          <input className="w-24 rounded border px-2 py-1" placeholder="Id de venta" value={saleId} onChange={(e) => setSaleId(e.target.value)} />
          <select className="rounded border px-2 py-1" value={methodId} onChange={(e) => setMethodId(e.target.value)}>
            {methods.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
          </select>
          <button type="button" className="underline" onClick={() => act({ kind: 'payment_created', movement_id: row.movement_id, sale_id: Number(saleId), payment_method_id: Number(methodId) })}>Crear</button>
        </div>
      )}
      {mode === 'not_a_sale' && (
        <div className="flex gap-2 text-xs">
          <input className="flex-1 rounded border px-2 py-1" placeholder="¿Qué es? (obligatorio)" value={note} onChange={(e) => setNote(e.target.value)} />
          <button type="button" className="underline" onClick={() => act({ kind: 'not_a_sale', movement_id: row.movement_id, note })}>Guardar</button>
        </div>
      )}
    </li>
  )
}

// Finanzas → Conciliación MercadoPago: calendario del mes y detalle del día.
export default function MpReconciliation() {
  const queryClient = useQueryClient()
  const [day, setDay] = useState(today())
  const [message, setMessage] = useState('')
  const [year, month] = day.split('-').map(Number)
  const days = monthDays(year, month)
  const { data: summary = [] } = useQuery({
    queryKey: posKeys.mpReconciliationSummary(days[0], days.at(-1)),
    queryFn: () => posMpApi.reconciliationSummary(days[0], days.at(-1)),
  })
  const { data, isLoading } = useQuery({ queryKey: posKeys.mpReconciliation(day), queryFn: () => posMpApi.reconciliationDay(day) })
  const { data: methods = [] } = useQuery({ queryKey: ['pos-settings', 'payment-methods'], queryFn: () => posConfigApi.listResource('payment-methods') })
  const mpMethods = methods.filter((m) => m.is_mercadopago && m.is_active)
  const refresh = () => queryClient.invalidateQueries({ queryKey: posKeys.mp })
  const run = async (fn, ok) => {
    setMessage('')
    try {
      const result = await fn()
      setMessage(typeof ok === 'function' ? ok(result) : ok)
      refresh()
    } catch (err) {
      setMessage(errorMessage(err))
    }
  }
  const act = (body) => run(() => posMpApi.resolve(body), 'Resuelto')

  return (
    <div className="space-y-4">
      <h1 className="text-3xl">Conciliación MercadoPago</h1>
      <div className="grid grid-cols-7 gap-1 text-xs">
        {summary.map((d) => (
          <button key={d.day} type="button" onClick={() => setDay(d.day)}
            className={`rounded p-1 ${TONE[d.status]} ${d.day === day ? 'ring-2 ring-galia-plum' : ''}`}>
            {Number(d.day.slice(-2))}{d.pending ? ` · ${d.pending}` : ''}
          </button>
        ))}
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <input type="date" value={day} onChange={(e) => setDay(e.target.value)} className="rounded border px-2 py-1" />
        <button type="button" className="rounded bg-galia-plum px-3 py-1.5 text-galia-cream"
          onClick={() => run(() => posMpApi.fetchDay(day), (r) => `Se trajeron ${r.fetched} movimientos${r.truncated ? ' (hay más de 1000: revisá el día en la app)' : ''}`)}>
          Traer de MercadoPago
        </button>
        {data && <span className={`rounded-full px-2 py-0.5 text-sm ${TONE[data.status]}`}>{statusLabel(data.status)}</span>}
      </div>
      {message && <p className="text-sm text-gray-700">{message}</p>}
      {isLoading && <p>Cargando…</p>}
      {data && (
        <div className="grid gap-4 lg:grid-cols-2">
          <section className="rounded-xl bg-white p-4 shadow-sm">
            <h2 className="font-semibold">Solo en MercadoPago · {formatMoney(data.totals.only_mp)}</h2>
            <ul className="divide-y text-sm">
              {data.only_mp.map((row) => <OnlyMpRow key={row.movement_id} row={row} act={act} methods={mpMethods} />)}
              {data.only_mp.length === 0 && <li className="py-2 text-gray-500">Nada pendiente.</li>}
            </ul>
          </section>
          <section className="rounded-xl bg-white p-4 shadow-sm">
            <h2 className="font-semibold">Solo en Galia · {formatMoney(data.totals.only_galia)}</h2>
            <ul className="divide-y text-sm">
              {data.only_galia.map((p) => (
                <li key={p.payment_id} className="flex items-center justify-between gap-2 py-2">
                  <span>{time(p.created_at)} · Venta #{p.sale_number} · {p.method_name} · {formatMoney(p.amount)}</span>
                  <button type="button" className="text-xs underline" onClick={() => {
                    const note = window.prompt('¿Qué revisaste? (obligatorio)')
                    if (note) act({ kind: 'reviewed', payment_id: p.payment_id, note })
                  }}>Marcar revisado</button>
                </li>
              ))}
              {data.only_galia.length === 0 && <li className="py-2 text-gray-500">Nada pendiente.</li>}
            </ul>
          </section>
          <section className="rounded-xl bg-white p-4 shadow-sm lg:col-span-2">
            <h2 className="font-semibold">Coinciden · {formatMoney(data.totals.matched)}</h2>
            <ul className="divide-y text-sm">
              {data.matched.map((row, i) => (
                <li key={i} className="flex items-center justify-between gap-2 py-2">
                  <span>
                    {row.movement ? `${time(row.movement.date_created)} · ${formatMoney(row.movement.amount)} · ${channelLabel(row.movement.channel)}` : 'Sin movimiento'}
                    {row.payment ? ` ↔ Venta #${row.payment.sale_number} (${row.payment.method_name})` : ''}
                    {row.resolution?.note ? ` · ${row.resolution.note}` : ''}
                    {Number(row.difference) !== 0 ? ` · diferencia ${formatMoney(row.difference)}` : ''}
                  </span>
                  {row.resolution && (
                    <button type="button" className="text-xs underline" onClick={() => run(() => posMpApi.undo(row.resolution.id), 'Deshecho')}>Deshacer</button>
                  )}
                </li>
              ))}
            </ul>
          </section>
          {data.rejected.length > 0 && (
            <details className="rounded-xl bg-white p-4 text-sm shadow-sm lg:col-span-2">
              <summary>Rechazados o cancelados ({data.rejected.length})</summary>
              <ul>{data.rejected.map((m) => <li key={m.movement_id}>{time(m.date_created)} · {formatMoney(m.amount)} · {m.status}</li>)}</ul>
            </details>
          )}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Rutas y menú.**
  - En `frontend/src/App.jsx`, importar `MercadoPagoSettings from './pages/admin/MercadoPagoSettings'` y `MpReconciliation from './pages/MpReconciliation'`, y agregar:

```jsx
            <Route path="/mp/reconciliation" element={<RoleProtectedRoute moduleName="Conciliar"><MpReconciliation /></RoleProtectedRoute>} />
            <Route path="/admin/mercadopago" element={<RoleProtectedRoute adminOnly><MercadoPagoSettings /></RoleProtectedRoute>} />
```

  - En `frontend/src/components/layout/Sidebar.jsx` (leer antes el archivo actual, porque cambió en `main`):
    - en Finanzas, después de "Comprobantes": `{ to: '/mp/reconciliation', icon: Scale, label: 'Conciliación MP', module: 'Conciliar' },`, sumando `Scale` al import de `lucide-react`;
    - después de "Facturación": `{ to: '/admin/mercadopago', icon: CreditCard, label: 'MercadoPago', adminOnly: true },`, sumando `CreditCard` al import si no está.

- [ ] **Step 5: Guía.** Crear `docs/pos/mercadopago.md`:

````markdown
# MercadoPago: cobro con el Point y conciliación

## 1. Integración en MercadoPago (una vez, admin)

1. Entrar a **Tus integraciones** en el panel de desarrolladores de MercadoPago con la cuenta del café, y crear una aplicación de tipo **"Pagos presenciales" → Point**.
2. Copiar el **Access token** de prueba y el de producción ("Credenciales").
3. En **Webhooks → Configurar notificaciones**:
   - pegar la URL que muestra Galia en Ajustes → MercadoPago;
   - marcar el evento de **órdenes** ("Order");
   - guardar y **revelar la clave secreta**.

## 2. Configurar en Galia (Ajustes → MercadoPago)

1. **Entorno:** empezar en **Prueba**. Pegar el token de prueba y "Guardar token". Galia verifica la cuenta.
2. **Terminal:** "Buscar terminales" y "Usar esta" en el Point Smart. Si no está en **modo PDV**, tocar "Pasar a modo PDV" y **reiniciar el Point**.
3. **Webhook:** pegar la clave secreta y "Guardar clave".
4. **Medio de pago:** en Ajustes del POS → Medios de pago, crear "MercadoPago Point" (tipo Tarjeta, con "Es de MercadoPago" y "Lo factura otro sistema"). Elegirlo en el paso 4 de Ajustes → MercadoPago.
5. **Probar conexión.**
6. Cuando ande en prueba: pasar a **Producción**, cargar el token de producción y repetir la prueba.

## 3. Cobrar con el Point

En la caja o en Camarero (con permiso "Cobrar"):
1. Abrir **Cobrar**, elegir **MercadoPago Point** y el monto. Por defecto es el saldo, y se puede cobrar una parte.
2. Tocar **Enviar al Point**: el Point muestra el cobro.
3. El mozo lleva el Point a la mesa y el cliente paga. Galia registra el pago sola y, si cubre el saldo, cierra la venta.

- **Cancelar:** se puede mientras no se cobró.
- **Si se cierra la pantalla:** la venta muestra "Cobro en Point pendiente" con **Ver** y **Cancelar**.
- **Rechazos:** si el Point rechaza la tarjeta, Galia lo muestra y se puede reintentar o cobrar con otro medio.

## 4. Anular un pago del Point

Al anular el pago (permiso "Anular") se elige **"Devolver también en MercadoPago"** (devolución total, desde Galia) o **"Solo anular en Galia"**. Si MercadoPago rechaza la devolución (por ejemplo, porque pasaron más de 90 días), el pago no se anula.

## 5. Conciliación (permiso "Conciliar")

En **Finanzas → Conciliación MP**:
1. Elegir el día y tocar **Traer de MercadoPago**.
2. Revisar las tres listas:
   - **Coinciden:** los cobros del Point se cruzan solos.
   - **Solo en MercadoPago:** asociar a un pago sugerido, crear el pago en una venta o marcar "No es una venta", con nota.
   - **Solo en Galia:** marcar "Revisado", con nota.

El calendario muestra en verde los días conciliados y en rojo los que tienen diferencias.
````

- [ ] **Step 6: Verificar**

Run: `npm test` y `npm run build`.
Expected: todo pasa.

- [ ] **Step 7: Commit**

```bash
git -C <worktree> add frontend/src docs/pos/mercadopago.md
git -C <worktree> commit -m "feat(mp): MercadoPago settings, reconciliation page and payment method flag"
```

---

### Task 10: Verificación final

**Files:** ninguno (preview fuera del repo).

- [ ] **Step 1: Suites.** Backend completo contra la línea base (como en la Task 6, Step 5) y frontend con `npm test` y `npm run build`.
Expected: `Sin fallas nuevas.` y todo verde.

- [ ] **Step 2: Preview.**
  - Base SQLite descartable: `prep_caja_preview.py` del scratchpad, con `DATABASE_URL` nuevo y `POS_DEMO_SEED=1`.
  - Backend con `MP_FAKE=1` en segundo plano, con `cd` explícito al backend de la worktree. `flask run` carga el `.env` de un directorio superior; da igual, porque el fake no usa tokens reales.
  - Frontend con `npm --prefix <worktree>/frontend run dev`.

- [ ] **Step 3: Verificación manual** (como admin):
  1. **Ajustes → MercadoPago:**
     - token cualquiera: el fake responde `me()`;
     - "Buscar terminales" y "Usar esta";
     - clave del webhook;
     - crear el medio "MercadoPago Point" y elegirlo;
     - "Probar conexión" dice "Conectado".
  2. **Cobro aprobado:** venta de salón → Cobrar → MercadoPago Point → "Enviar al Point" → espera → "Simular Point: approved". Se cierra la venta.
  3. **Cobro parcial y otros resultados:**
     - cobro parcial: "approved" deja saldo, y se cobra el resto en efectivo;
     - "rejected": se ve el mensaje y se reintenta;
     - cancelar un cobro en espera.
  4. **Cobro pendiente:** se cierra el modal durante la espera y aparece "Cobro en Point pendiente"; "Ver" reabre la espera y "Cancelar" lo cancela.
  5. **Devolución:** anular el pago del Point con "Devolver también en MercadoPago". El pago queda anulado y la orden del fake, `refunded`.
  6. **Conciliación** (usuario con "Conciliar" o admin):
     - "Traer de MercadoPago": el cobro del Point coincide solo;
     - agregar un movimiento con `FakeMercadoPago.add_payment_movement` desde un script del scratchpad (no hace falta en la UI) y resolverlo con "No es una venta";
     - el calendario se pone en verde.
  7. **Camarero:** con un usuario con "Cobrar", desde el celular (`/camarero`), cobrar con el Point.
