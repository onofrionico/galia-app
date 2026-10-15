# Facturación electrónica ARCA (sub-proyecto 4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que la caja emita desde Galia la Factura C (y a futuro A/B) que pide un cliente sobre una venta cerrada, con CAE de ARCA, impresa en la térmica de caja con el QR, más la nota de crédito, los bloqueos y la configuración desde Galia.

**Architecture:**
- **Paquete `app/services/fiscal/`** con piezas separadas:
  - lógica pura de montos y receptor;
  - configuración y credenciales;
  - un **gateway de ARCA** intercambiable: el real (WSAA + WSFEv1 con `zeep`) o `FakeArca`, para tests y preview;
  - el servicio de comprobantes.
- **Emisión en dos fases:** reserva el número bajo lock, confirma, y recién después pide el CAE. Si se corta, queda un `pending` que se resuelve consultando a ARCA.
- **Frontend:** modal de facturación en la caja, Ajustes → Facturación y Finanzas → Comprobantes. La impresión reutiliza la cola del sub-proyecto 3.

**Tech Stack:** Flask, SQLAlchemy 2.0, Alembic, pytest, `cryptography` (ya instalada), `zeep==4.2.1`. React 18, React Query 5, Tailwind, Vitest.

**Spec:** `docs/superpowers/specs/2026-10-14-pos-facturacion-arca-design.md`

## Global Constraints

- **Worktree:** `C:\Users\onofr\Desktop\galia-app\.claude\worktrees\pos-base`, rama `feature/pos-facturacion` (sale de `main` en `7f7c6de`). Las rutas del plan son relativas a esa raíz.
- **Python** (`PY`): `C:\Users\onofr\Desktop\galia-app\backend\venv\Scripts\python.exe` (Python 3.10). Los tests corren con cwd = `backend/`: `PY -m pytest -q -p no:cacheprovider <archivos>`.
- **Node:** con cwd = `frontend/` (`npm test`, `npm run build`, `npx vitest run <archivo>`). Nunca correr vitest desde la raíz.
- **Encoding:** UTF-8 con acentos. Editar solo con Edit/Write (el sandbox rechaza heredocs complejos y `cd` + git en un mismo comando: los git van con `git -C <worktree>`).
- **Línea base del backend:** `PY scripts/compare_baseline.py <salida> ../docs/superpowers/plans/2026-10-08-pos-base-test-baseline.txt`. Criterio: `Sin fallas nuevas.`
- **Vitest:** entorno `node` y sin Testing Library. Solo lógica pura, con imports relativos.
- **Migración:** `b4a0_add_fiscal_invoicing`, con `down_revision = 'b3a0_add_print_stations'`.
- **Errores:**
  - `PosError` (409 por defecto), `bad_request` (400), `forbidden` (403) y `not_found` (404), de `app.services.pos.errors`;
  - mensajes en castellano rioplatense;
  - el detalle técnico de ARCA va al log y a `arca_result`, nunca a la caja.
- **Fechas:**
  - se guardan en UTC naive (`common.now()`);
  - `voucher_date` y la fecha del QR son el día de Argentina (`get_current_date_argentina()`).
- **Numeración visible:** `"<Tipo> <Letra> <pv 5 dígitos>-<número 8 dígitos>"`, por ejemplo `"Factura C 00005-00000123"`. El spec usa en un ejemplo un punto de venta de 4 dígitos (0005); el plan usa 5 dígitos, que es el formato vigente de ARCA.
- **Códigos ARCA:**
  - tipos de comprobante: Factura A 1, NC A 3, Factura B 6, NC B 8, Factura C 11, NC C 13;
  - tipos de documento: CUIT 80, CUIL 86, DNI 96, sin identificar 99;
  - condición frente al IVA del receptor: RI 1, Exento 4, CF 5, Monotributo 6;
  - alícuotas de IVA (`Id`): 0% 3, 10,5% 4, 21% 5, 27% 6.
- **Concurrencia:** si al reservar hay un `pending` reciente (menos de 120 s) del mismo entorno, punto de venta y tipo, la emisión responde 409 "Hay una factura emitiéndose, probá en unos segundos" en lugar de esperar. Se ajusta así la frase del spec "una espera a la otra": nunca hay números duplicados, y la segunda caja reintenta.
- **`FakeArca`:** se activa solo con `FISCAL_FAKE_ARCA=1` **y** base SQLite.
- **Los sub-proyectos 1 a 3** no cambian de comportamiento, salvo los bloqueos de anulación y el campo `invoice` de la venta.
- **Commits:** terminan con la línea de atribución que pida el harness.

## Review Focus

1. **ARCA autoriza el comprobante, pero la respuesta no llega** (corte o timeout): queda `pending`. "Verificar" lo encuentra en ARCA y lo marca `authorized` con el CAE de ARCA, sin emitir otro. Lo cubre la Task 6 (`test_timeout_after_arca_issued_resolves_to_authorized`).
2. **El token del WSAA ya fue entregado y se perdió:** el token se guarda apenas llega y se reutiliza hasta 10 minutos antes de vencer, sin pedir otro. Lo cubre la Task 4 (`test_credentials_are_cached_until_near_expiry`).
3. **Descuentos de venta y de ítem con centavos** en una factura por ítems: la suma de las líneas da exactamente el total. Lo cubre la Task 2 (`test_items_absorb_rounding_in_last_line`).
4. **Anular un pago cubierto, o la venta, con una factura vigente o `pending`:** responde 409 con el número de factura. Un pago de un medio que factura otro sistema se anula igual. Lo cubre la Task 7.
5. **Se rota `SECRET_KEY`:** la clave ya no se puede descifrar, la configuración lo informa y facturar responde un error claro en lugar de 500. Lo cubre la Task 3 (`test_undecryptable_key_reports_clear_error`).

## Mapa de archivos

**Backend**
- Create:
  - `backend/app/models/fiscal.py`: `FiscalSettings`, `ArcaToken`, `FiscalCustomer`, `Invoice`, `InvoicePayment`;
  - `backend/migrations/versions/b4a0_add_fiscal_invoicing.py`;
  - `backend/app/services/fiscal/__init__.py` (vacío);
  - `amounts.py`, `receivers.py`, `settings.py`, `guard.py`, `invoice_documents.py`, `invoice_service.py`;
  - `backend/app/services/fiscal/arca/__init__.py` (`get_gateway`), `wsaa.py`, `wsfe.py`, `fake.py`;
  - `backend/app/routes/fiscal.py`;
  - `docs/pos/facturacion-arca.md`.
- Modify:
  - `backend/app/models/__init__.py`, `backend/app/models/pos/payments.py` (`invoiced_externally`), `backend/app/models/pos/printing.py` (`PRINT_JOB_KINDS`);
  - `backend/app/routes/pos_config.py` (medio de pago);
  - `backend/app/services/pos/print_documents.py` (`item_description`), `sale_service.py`, `payment_service.py` (bloqueos), `serializers.py` (`invoice`);
  - `backend/app/__init__.py` (blueprint);
  - `backend/requirements.txt` (`zeep`).
- Tests:
  - `backend/tests/fiscal_helpers.py`;
  - `test_fiscal_models.py`, `test_fiscal_amounts.py`, `test_fiscal_receivers.py`, `test_fiscal_settings.py`, `test_fiscal_arca.py`, `test_fiscal_issue.py`, `test_fiscal_cancel.py`, `test_fiscal_api.py`, `test_fiscal_concurrency_pg.py`, `test_fiscal_homologacion.py`;
  - `test_migration_chain.py`.

**Frontend**
- Create:
  - `frontend/src/pos/fiscal/invoiceForm.js` (+ test), `InvoiceModal.jsx`, `InvoiceTag.jsx`;
  - `frontend/src/pages/admin/FiscalSettings.jsx`, `frontend/src/pages/Invoices.jsx`.
- Modify:
  - `frontend/src/pos/api/posApi.js` (`posFiscalApi`), `frontend/src/pos/hooks/keys.js`;
  - `frontend/src/pos/print/escpos.js` (+ test, QR), `printStatus.js` (label);
  - `frontend/src/pos/utils/permissions.js` (+ test);
  - `frontend/src/pos/sale/SaleFooter.jsx`, `SalePanel.jsx`, `frontend/src/pos/modals/PaymentModal.jsx`;
  - `frontend/src/pages/admin/PosSettings.jsx`;
  - `frontend/src/App.jsx`, `frontend/src/components/layout/Sidebar.jsx`.

---

### Task 1: Modelos, migración y medio de pago "lo factura otro sistema"

**Files:**
- Create: `backend/app/models/fiscal.py`, `backend/migrations/versions/b4a0_add_fiscal_invoicing.py`, `backend/tests/test_fiscal_models.py`
- Modify:
  - `backend/app/models/__init__.py`, `backend/app/models/pos/payments.py`, `backend/app/models/pos/printing.py`;
  - `backend/app/routes/pos_config.py`;
  - `backend/requirements.txt`;
  - `backend/tests/test_migration_chain.py`.

**Interfaces:**
- Produces:
  - **Modelos** (desde `app.models.fiscal` y reexportados en `app.models`):
    - `FiscalSettings` (columnas del spec), con `SETTINGS_ID = 1`;
    - `ArcaToken`;
    - `FiscalCustomer` con `to_dict()`;
    - `Invoice` con la relación `sale`, las propiedades `letter`, `label` y `is_credit_note`, y `payments` (relación a `InvoicePayment`);
    - `InvoicePayment`.
  - **Constantes:**
    - `VOUCHER_TYPES = {1: ('invoice', 'A'), 3: ('credit_note', 'A'), 6: ('invoice', 'B'), 8: ('credit_note', 'B'), 11: ('invoice', 'C'), 13: ('credit_note', 'C')}`;
    - `INVOICE_STATUSES = ('pending', 'authorized', 'rejected')`;
    - `ENVIRONMENTS = ('homologacion', 'produccion')`;
    - `EMITTER_CONDITIONS = ('monotributo', 'responsable_inscripto')`;
    - `RECEIVER_CONDITIONS = ('consumidor_final', 'monotributo', 'responsable_inscripto', 'exento')`.
  - **Medio de pago:** `PaymentMethod.invoiced_externally` (por defecto `kind != 'cash'`), en `to_dict()` y editable en `/pos/config/payment-methods`.
  - **Impresión:** `PRINT_JOB_KINDS` incluye `'invoice'`.

- [ ] **Step 1: Tests que fallan.** Crear `backend/tests/test_fiscal_models.py`:

```python
from decimal import Decimal

from app.extensions import db
from app.models import Invoice, PaymentMethod
from app.models.pos import PRINT_JOB_KINDS
from app.services.pos.common import now
from pos_helpers import auth_headers, make_catalog, make_user, pos_app  # noqa: F401


def test_invoiced_externally_defaults_by_kind(pos_app):
    cat = make_catalog()
    assert cat.efectivo.invoiced_externally is False
    assert cat.debito.invoiced_externally is True
    assert 'invoice' in PRINT_JOB_KINDS


def test_payment_method_flag_via_config_api(pos_app):
    client = pos_app.test_client()
    admin = auth_headers(client, make_user('admin@test.com', role='admin'))
    created = client.post('/api/v1/pos/config/payment-methods', json={'name': 'QR', 'kind': 'other'}, headers=admin)
    assert created.status_code == 201 and created.get_json()['invoiced_externally'] is True
    cash = client.post('/api/v1/pos/config/payment-methods', json={'name': 'Caja chica', 'kind': 'cash'},
                       headers=admin).get_json()
    assert cash['invoiced_externally'] is False
    updated = client.put(f"/api/v1/pos/config/payment-methods/{created.get_json()['id']}",
                         json={'invoiced_externally': False}, headers=admin)
    assert updated.status_code == 200 and updated.get_json()['invoiced_externally'] is False
    assert db.session.get(PaymentMethod, cash['id']).invoiced_externally is False


def test_invoice_label_and_letter(pos_app):
    user = make_user('caja@test.com', modules=('POS',))
    invoice = Invoice(kind='invoice', voucher_type=11, environment='homologacion', point_of_sale=5, number=123,
                      receiver_doc_type=99, receiver_doc_number='0', receiver_name='Consumidor final',
                      receiver_iva_condition='consumidor_final', detail_mode='generic', lines=[],
                      total=Decimal('10'), net=Decimal('10'), iva=Decimal('0'), iva_rate=Decimal('0'),
                      voucher_date=now().date(), status='pending', request={}, created_by=user.id,
                      created_at=now())
    db.session.add(invoice)
    db.session.commit()
    assert invoice.letter == 'C' and invoice.label == 'Factura C 00005-00000123'
    invoice.voucher_type = 13
    invoice.kind = 'credit_note'
    assert invoice.label == 'Nota de crédito C 00005-00000123' and invoice.is_credit_note
```

En `backend/tests/test_migration_chain.py` agregar al final:

```python


def test_fiscal_invoicing_follows_print_stations():
    assert _revisions()['b4a0_add_fiscal_invoicing'] == ['b3a0_add_print_stations']
```

- [ ] **Step 2: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_fiscal_models.py tests/test_migration_chain.py`
Expected: ImportError (`Invoice`) y `KeyError: 'b4a0_add_fiscal_invoicing'`.

- [ ] **Step 3: Dependencia.** En `backend/requirements.txt`, agregar `zeep==4.2.1`.
Run: `PY -m pip install zeep==4.2.1`
Expected: se instala sin errores.

- [ ] **Step 4: Modelos.** Crear `backend/app/models/fiscal.py`:

```python
"""Facturación electrónica ARCA: configuración, token WSAA, clientes y comprobantes."""
from app.extensions import db

SETTINGS_ID = 1
VOUCHER_TYPES = {1: ('invoice', 'A'), 3: ('credit_note', 'A'), 6: ('invoice', 'B'), 8: ('credit_note', 'B'),
                 11: ('invoice', 'C'), 13: ('credit_note', 'C')}
INVOICE_STATUSES = ('pending', 'authorized', 'rejected')
ENVIRONMENTS = ('homologacion', 'produccion')
EMITTER_CONDITIONS = ('monotributo', 'responsable_inscripto')
RECEIVER_CONDITIONS = ('consumidor_final', 'monotributo', 'responsable_inscripto', 'exento')


class FiscalSettings(db.Model):
    """Configuración fiscal. Una sola fila (id = SETTINGS_ID). Las claves privadas van cifradas."""
    __tablename__ = 'fiscal_settings'

    id = db.Column(db.Integer, primary_key=True)
    cuit = db.Column(db.String(11), nullable=True)
    business_name = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    gross_income = db.Column(db.String(40), nullable=True)
    activity_start = db.Column(db.Date, nullable=True)
    iva_condition = db.Column(db.String(30), nullable=False, default='monotributo')
    point_of_sale = db.Column(db.Integer, nullable=True)
    environment = db.Column(db.String(15), nullable=False, default='homologacion')
    cf_id_threshold = db.Column(db.Numeric(14, 2), nullable=True)
    default_iva_rate = db.Column(db.Numeric(5, 2), nullable=False, default=21)
    homo_private_key = db.Column(db.Text, nullable=True)
    homo_csr = db.Column(db.Text, nullable=True)
    homo_certificate = db.Column(db.Text, nullable=True)
    homo_cert_expires_at = db.Column(db.DateTime, nullable=True)
    prod_private_key = db.Column(db.Text, nullable=True)
    prod_csr = db.Column(db.Text, nullable=True)
    prod_certificate = db.Column(db.Text, nullable=True)
    prod_cert_expires_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)

    @staticmethod
    def prefix(environment):
        return 'homo' if environment == 'homologacion' else 'prod'

    def credential(self, environment, name):
        return getattr(self, f'{self.prefix(environment)}_{name}')

    def set_credential(self, environment, name, value):
        setattr(self, f'{self.prefix(environment)}_{name}', value)


class ArcaToken(db.Model):
    __tablename__ = 'arca_tokens'
    __table_args__ = (db.UniqueConstraint('service', 'environment', name='uq_arca_tokens_service_env'),)

    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(20), nullable=False)
    environment = db.Column(db.String(15), nullable=False)
    token = db.Column(db.Text, nullable=False)
    sign = db.Column(db.Text, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)


class FiscalCustomer(db.Model):
    __tablename__ = 'fiscal_customers'
    __table_args__ = (db.UniqueConstraint('doc_type', 'doc_number', name='uq_fiscal_customers_doc'),)

    id = db.Column(db.Integer, primary_key=True)
    doc_type = db.Column(db.String(5), nullable=False)
    doc_number = db.Column(db.String(11), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    iva_condition = db.Column(db.String(30), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        return {'id': self.id, 'doc_type': self.doc_type, 'doc_number': self.doc_number, 'name': self.name,
                'iva_condition': self.iva_condition, 'address': self.address}


class Invoice(db.Model):
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(15), nullable=False)
    voucher_type = db.Column(db.Integer, nullable=False)
    environment = db.Column(db.String(15), nullable=False)
    point_of_sale = db.Column(db.Integer, nullable=False)
    number = db.Column(db.Integer, nullable=False)
    sale_id = db.Column(db.Integer, db.ForeignKey('pos_sales.id'), nullable=True, index=True)
    related_invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('fiscal_customers.id'), nullable=True)
    receiver_doc_type = db.Column(db.Integer, nullable=False)
    receiver_doc_number = db.Column(db.String(11), nullable=False)
    receiver_name = db.Column(db.String(120), nullable=False)
    receiver_iva_condition = db.Column(db.String(30), nullable=False)
    receiver_address = db.Column(db.String(200), nullable=True)
    detail_mode = db.Column(db.String(10), nullable=False)
    lines = db.Column(db.JSON, nullable=False)
    total = db.Column(db.Numeric(14, 2), nullable=False)
    net = db.Column(db.Numeric(14, 2), nullable=False)
    iva = db.Column(db.Numeric(14, 2), nullable=False)
    iva_rate = db.Column(db.Numeric(5, 2), nullable=False)
    voucher_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10), nullable=False)
    cae = db.Column(db.String(20), nullable=True)
    cae_due = db.Column(db.Date, nullable=True)
    arca_result = db.Column(db.JSON, nullable=True)
    request = db.Column(db.JSON, nullable=False)
    error = db.Column(db.String(500), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    authorized_at = db.Column(db.DateTime, nullable=True)

    sale = db.relationship('PosSale')
    related = db.relationship('Invoice', remote_side=[id])
    payments = db.relationship('InvoicePayment', backref='invoice', cascade='all, delete-orphan')

    @property
    def letter(self):
        return VOUCHER_TYPES[self.voucher_type][1]

    @property
    def is_credit_note(self):
        return VOUCHER_TYPES[self.voucher_type][0] == 'credit_note'

    @property
    def label(self):
        name = 'Nota de crédito' if self.is_credit_note else 'Factura'
        return f'{name} {self.letter} {self.point_of_sale:05d}-{self.number:08d}'


class InvoicePayment(db.Model):
    __tablename__ = 'invoice_payments'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False, index=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('pos_payments.id'), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
```

En `backend/app/models/__init__.py`, agregar junto a los otros imports de modelos:

```python
from app.models.fiscal import ArcaToken, FiscalCustomer, FiscalSettings, Invoice, InvoicePayment
```

y sumar esos cinco nombres a `__all__` (si el archivo define `__all__`).

En `backend/app/models/pos/payments.py`, agregar a `PaymentMethod`, después de `is_active`:

```python
    # Si este medio ya lo factura otro sistema (MercadoPago, terminal): Galia no lo incluye en sus facturas.
    invoiced_externally = db.Column(db.Boolean, nullable=False,
                                    default=lambda ctx: ctx.get_current_parameters().get('kind') != 'cash')
```

y en su `to_dict`, sumar `'invoiced_externally': self.invoiced_externally`.

En `backend/app/models/pos/printing.py`, cambiar `PRINT_JOB_KINDS` a `('order', 'void', 'bill', 'receipt', 'test', 'invoice')`.

En `backend/app/routes/pos_config.py`, en `_apply_payment_method`, agregar al final:

```python
    if 'invoiced_externally' in data:
        method.invoiced_externally = bool(data['invoiced_externally'])
    elif creating:
        method.invoiced_externally = method.kind != 'cash'
```

- [ ] **Step 5: Migración.** Crear `backend/migrations/versions/b4a0_add_fiscal_invoicing.py`:

```python
"""add fiscal settings, ARCA tokens, fiscal customers, invoices; payment_methods.invoiced_externally

Revision ID: b4a0_add_fiscal_invoicing
Revises: b3a0_add_print_stations
Create Date: 2026-10-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b4a0_add_fiscal_invoicing'
down_revision = 'b3a0_add_print_stations'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'fiscal_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cuit', sa.String(length=11), nullable=True),
        sa.Column('business_name', sa.String(length=120), nullable=True),
        sa.Column('address', sa.String(length=200), nullable=True),
        sa.Column('gross_income', sa.String(length=40), nullable=True),
        sa.Column('activity_start', sa.Date(), nullable=True),
        sa.Column('iva_condition', sa.String(length=30), nullable=False, server_default='monotributo'),
        sa.Column('point_of_sale', sa.Integer(), nullable=True),
        sa.Column('environment', sa.String(length=15), nullable=False, server_default='homologacion'),
        sa.Column('cf_id_threshold', sa.Numeric(14, 2), nullable=True),
        sa.Column('default_iva_rate', sa.Numeric(5, 2), nullable=False, server_default='21'),
        sa.Column('homo_private_key', sa.Text(), nullable=True),
        sa.Column('homo_csr', sa.Text(), nullable=True),
        sa.Column('homo_certificate', sa.Text(), nullable=True),
        sa.Column('homo_cert_expires_at', sa.DateTime(), nullable=True),
        sa.Column('prod_private_key', sa.Text(), nullable=True),
        sa.Column('prod_csr', sa.Text(), nullable=True),
        sa.Column('prod_certificate', sa.Text(), nullable=True),
        sa.Column('prod_cert_expires_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'arca_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('service', sa.String(length=20), nullable=False),
        sa.Column('environment', sa.String(length=15), nullable=False),
        sa.Column('token', sa.Text(), nullable=False),
        sa.Column('sign', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('service', 'environment', name='uq_arca_tokens_service_env'),
    )
    op.create_table(
        'fiscal_customers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('doc_type', sa.String(length=5), nullable=False),
        sa.Column('doc_number', sa.String(length=11), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('iva_condition', sa.String(length=30), nullable=False),
        sa.Column('address', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('doc_type', 'doc_number', name='uq_fiscal_customers_doc'),
    )
    op.create_table(
        'invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kind', sa.String(length=15), nullable=False),
        sa.Column('voucher_type', sa.Integer(), nullable=False),
        sa.Column('environment', sa.String(length=15), nullable=False),
        sa.Column('point_of_sale', sa.Integer(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('sale_id', sa.Integer(), sa.ForeignKey('pos_sales.id'), nullable=True),
        sa.Column('related_invoice_id', sa.Integer(), sa.ForeignKey('invoices.id'), nullable=True),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('fiscal_customers.id'), nullable=True),
        sa.Column('receiver_doc_type', sa.Integer(), nullable=False),
        sa.Column('receiver_doc_number', sa.String(length=11), nullable=False),
        sa.Column('receiver_name', sa.String(length=120), nullable=False),
        sa.Column('receiver_iva_condition', sa.String(length=30), nullable=False),
        sa.Column('receiver_address', sa.String(length=200), nullable=True),
        sa.Column('detail_mode', sa.String(length=10), nullable=False),
        sa.Column('lines', sa.JSON(), nullable=False),
        sa.Column('total', sa.Numeric(14, 2), nullable=False),
        sa.Column('net', sa.Numeric(14, 2), nullable=False),
        sa.Column('iva', sa.Numeric(14, 2), nullable=False),
        sa.Column('iva_rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('voucher_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=10), nullable=False),
        sa.Column('cae', sa.String(length=20), nullable=True),
        sa.Column('cae_due', sa.Date(), nullable=True),
        sa.Column('arca_result', sa.JSON(), nullable=True),
        sa.Column('request', sa.JSON(), nullable=False),
        sa.Column('error', sa.String(length=500), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('authorized_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_invoices_sale_id', 'invoices', ['sale_id'])
    op.create_index('ix_invoices_related_invoice_id', 'invoices', ['related_invoice_id'])
    op.create_index('uq_invoices_authorized_number', 'invoices',
                    ['environment', 'point_of_sale', 'voucher_type', 'number'], unique=True,
                    postgresql_where=sa.text("status = 'authorized'"),
                    sqlite_where=sa.text("status = 'authorized'"))
    op.create_table(
        'invoice_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), sa.ForeignKey('invoices.id'), nullable=False),
        sa.Column('payment_id', sa.Integer(), sa.ForeignKey('pos_payments.id'), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_invoice_payments_invoice_id', 'invoice_payments', ['invoice_id'])
    op.create_index('ix_invoice_payments_payment_id', 'invoice_payments', ['payment_id'])
    with op.batch_alter_table('payment_methods') as batch:
        batch.add_column(sa.Column('invoiced_externally', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.execute("UPDATE payment_methods SET invoiced_externally = false WHERE kind = 'cash'")


def downgrade():
    with op.batch_alter_table('payment_methods') as batch:
        batch.drop_column('invoiced_externally')
    op.drop_index('ix_invoice_payments_payment_id', table_name='invoice_payments')
    op.drop_index('ix_invoice_payments_invoice_id', table_name='invoice_payments')
    op.drop_table('invoice_payments')
    op.drop_index('uq_invoices_authorized_number', table_name='invoices')
    op.drop_index('ix_invoices_related_invoice_id', table_name='invoices')
    op.drop_index('ix_invoices_sale_id', table_name='invoices')
    op.drop_table('invoices')
    op.drop_table('fiscal_customers')
    op.drop_table('arca_tokens')
    op.drop_table('fiscal_settings')
```

Agregar el índice único parcial también al modelo, para que `db.create_all()` (tests) lo cree. En `Invoice`:

```python
    __table_args__ = (db.Index('uq_invoices_authorized_number', 'environment', 'point_of_sale', 'voucher_type',
                               'number', unique=True, postgresql_where=db.text("status = 'authorized'"),
                               sqlite_where=db.text("status = 'authorized'")),)
```

y quitar `index=True` de `sale_id` y `related_invoice_id` en el modelo, sumando en ese `__table_args__` `db.Index('ix_invoices_sale_id', 'sale_id')` y `db.Index('ix_invoices_related_invoice_id', 'related_invoice_id')`, así los nombres coinciden con la migración.

- [ ] **Step 6: Correr**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_fiscal_models.py tests/test_migration_chain.py tests/test_pos_config_api.py tests/test_pos_models.py tests/test_pos_payments.py`
Expected: todos pasan.

- [ ] **Step 7: Commit**

```bash
git -C <worktree> add backend/app/models backend/migrations/versions/b4a0_add_fiscal_invoicing.py backend/app/routes/pos_config.py backend/requirements.txt backend/tests/test_fiscal_models.py backend/tests/test_migration_chain.py
git -C <worktree> commit -m "feat(fiscal): invoicing models, migration and externally invoiced payment methods"
```

---

### Task 2: Montos facturables y detalle (lógica pura)

**Files:**
- Create: `backend/app/services/fiscal/__init__.py` (vacío), `backend/app/services/fiscal/amounts.py`, `backend/tests/test_fiscal_amounts.py`

**Interfaces:**
- Consumes: nada de la base. Recibe objetos con atributos:
  - venta: `total`, `number`, `items`, `discounts` y `payments`;
  - ítem: `id`, `status`, `quantity`, `line_total`;
  - descuento: `item_id`, `amount`, `cancelled_at`;
  - pago: `id`, `payment_method_id`, `amount`, `cancelled_at`.
- Produces:
  - `invoiceable_payments(sale, external_method_ids) -> list[payment]`;
  - `invoiceable_amount(sale, external_method_ids) -> Decimal`;
  - `build_lines(sale, amount, describe) -> (detail_mode, lines)`, donde `lines` es `[{'qty': str, 'description': str, 'unit_price': str, 'amount': str}]` y `describe(item) -> str`;
  - `split_iva(total, rate, discriminated) -> (net, iva)`.

- [ ] **Step 1: Tests que fallan.** Crear `backend/tests/test_fiscal_amounts.py`:

```python
from decimal import Decimal
from types import SimpleNamespace as NS

from app.services.fiscal.amounts import build_lines, invoiceable_amount, invoiceable_payments, split_iva

D = Decimal


def _sale(items, discounts=(), payments=(), total=None):
    total = total if total is not None else sum((i.line_total for i in items), D('0')) - sum(
        (d.amount for d in discounts), D('0'))
    return NS(total=D(total), number=7, items=list(items), discounts=list(discounts), payments=list(payments))


def _item(item_id, qty, line_total, status='confirmed'):
    return NS(id=item_id, status=status, quantity=D(qty), line_total=D(line_total))


def _pay(pay_id, method_id, amount, cancelled=False):
    return NS(id=pay_id, payment_method_id=method_id, amount=D(amount), cancelled_at='x' if cancelled else None)


def describe(item):
    return f'Producto {item.id}'


def test_only_active_payments_of_non_external_methods_count():
    sale = _sale([_item(1, 1, '18000')], payments=[_pay(1, 1, '10000'), _pay(2, 2, '8000'),
                                                   _pay(3, 1, '500', cancelled=True)])
    assert [p.id for p in invoiceable_payments(sale, {2})] == [1]
    assert invoiceable_amount(sale, {2}) == D('10000.00')
    assert invoiceable_amount(sale, {1, 2}) == D('0.00')


def test_full_amount_lists_items_partial_uses_generic_line():
    sale = _sale([_item(1, 2, '6000'), _item(2, 1, '2000'), _item(3, 1, '900', status='cancelled')])
    mode, lines = build_lines(sale, D('8000'), describe)
    assert mode == 'items'
    assert lines == [{'qty': '2', 'description': 'Producto 1', 'unit_price': '3000.00', 'amount': '6000.00'},
                     {'qty': '1', 'description': 'Producto 2', 'unit_price': '2000.00', 'amount': '2000.00'}]
    mode, lines = build_lines(sale, D('5000'), describe)
    assert mode == 'generic'
    assert lines == [{'qty': '1', 'description': 'Consumo – Venta #7', 'unit_price': '5000.00',
                      'amount': '5000.00'}]


def test_item_and_sale_discounts_are_reflected_in_lines():
    items = [_item(1, 1, '1000'), _item(2, 1, '3000')]
    discounts = [NS(item_id=1, amount=D('100'), cancelled_at=None),
                 NS(item_id=None, amount=D('390'), cancelled_at=None),
                 NS(item_id=2, amount=D('999'), cancelled_at='x')]
    sale = _sale(items, discounts[:2])
    assert sale.total == D('3510')
    mode, lines = build_lines(sale, D('3510'), describe)
    assert mode == 'items'
    # 900 y 3000 efectivos; el descuento de venta (390) se reparte 90/300.
    assert [l['amount'] for l in lines] == ['810.00', '2700.00']


def test_items_absorb_rounding_in_last_line():
    items = [_item(1, 3, '1000'), _item(2, 1, '1000'), _item(3, 1, '1000')]
    discounts = [NS(item_id=None, amount=D('100'), cancelled_at=None)]
    sale = _sale(items, discounts)
    mode, lines = build_lines(sale, sale.total, describe)
    assert sum(D(l['amount']) for l in lines) == sale.total == D('2900')
    assert lines[0]['unit_price'] == '333.33'


def test_split_iva():
    assert split_iva(D('121'), D('21'), True) == (D('100.00'), D('21.00'))
    assert split_iva(D('1000'), D('21'), True) == (D('826.45'), D('173.55'))
    assert split_iva(D('1000'), D('21'), False) == (D('1000.00'), D('0.00'))
```

- [ ] **Step 2: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_fiscal_amounts.py`
Expected: `ModuleNotFoundError: No module named 'app.services.fiscal'`.

- [ ] **Step 3: Implementar.** Crear `backend/app/services/fiscal/__init__.py` vacío y `backend/app/services/fiscal/amounts.py`:

```python
"""Montos de una factura: qué pagos cubre, cuánto se factura y con qué renglones. Funciones puras."""
from decimal import Decimal

from app.services.pos.pricing import ZERO, money


def _qty(value):
    value = Decimal(value)
    return str(int(value)) if value == value.to_integral_value() else format(value.normalize(), 'f')


def invoiceable_payments(sale, external_method_ids):
    """Pagos activos cuyo medio no factura otro sistema."""
    return [p for p in sale.payments
            if p.cancelled_at is None and p.payment_method_id not in external_method_ids]


def invoiceable_amount(sale, external_method_ids):
    return money(sum((p.amount for p in invoiceable_payments(sale, external_method_ids)), ZERO))


def _line(qty, description, amount):
    unit = money(Decimal(amount) / Decimal(qty)) if Decimal(qty) else money(amount)
    return {'qty': _qty(qty), 'description': description, 'unit_price': f'{unit:.2f}',
            'amount': f'{money(amount):.2f}'}


def _effective_amounts(sale):
    """Importe de cada ítem confirmado con sus descuentos de ítem y su parte de los descuentos de venta.

    La suma da exactamente sale.total: el redondeo del reparto queda en el último renglón.
    """
    items = [i for i in sale.items if i.status == 'confirmed']
    active = [d for d in sale.discounts if d.cancelled_at is None]
    effective = []
    for item in items:
        item_disc = sum((d.amount for d in active if d.item_id == item.id), ZERO)
        effective.append(money(item.line_total - item_disc))
    sale_disc = money(sum((d.amount for d in active if d.item_id is None), ZERO))
    base = sum(effective, ZERO)
    amounts = []
    for index, value in enumerate(effective):
        if index == len(effective) - 1:
            amounts.append(money(Decimal(sale.total) - sum(amounts, ZERO)))
        else:
            share = money(sale_disc * value / base) if base else ZERO
            amounts.append(money(value - share))
    return list(zip(items, amounts))


def build_lines(sale, amount, describe):
    """('items', renglones) si se factura el total de la venta; ('generic', [Consumo – Venta #N]) si es parcial."""
    amount = money(amount)
    if amount == money(sale.total) and any(i.status == 'confirmed' for i in sale.items):
        return 'items', [_line(item.quantity, describe(item), value) for item, value in _effective_amounts(sale)]
    return 'generic', [_line(1, f'Consumo – Venta #{sale.number}', amount)]


def split_iva(total, rate, discriminated):
    """(neto, IVA). Sin discriminar (Factura C): todo es neto."""
    total = money(total)
    if not discriminated:
        return total, ZERO
    net = money(total / (1 + Decimal(rate) / 100))
    return net, money(total - net)
```

- [ ] **Step 4: Correr**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_fiscal_amounts.py`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git -C <worktree> add backend/app/services/fiscal backend/tests/test_fiscal_amounts.py
git -C <worktree> commit -m "feat(fiscal): invoiceable amount and invoice lines"
```

---

### Task 3: Receptor, tipo de comprobante, configuración y credenciales

**Files:**
- Create: `backend/app/services/fiscal/receivers.py`, `backend/app/services/fiscal/settings.py`, `backend/tests/fiscal_helpers.py`, `backend/tests/test_fiscal_receivers.py`, `backend/tests/test_fiscal_settings.py`

**Interfaces:**
- Consumes: modelos de la Task 1.
- Produces:
  - **`receivers`:**
    - `DOC_TYPES = {'CUIT': 80, 'CUIL': 86, 'DNI': 96}`, `ANONYMOUS_DOC_TYPE = 99`;
    - `RECEIVER_IVA_IDS = {'responsable_inscripto': 1, 'exento': 4, 'consumidor_final': 5, 'monotributo': 6}`;
    - `valid_cuit(number) -> bool`;
    - `normalize_receiver(data, total, threshold, emitter_condition) -> dict` con `{'doc_type_code', 'doc_type', 'doc_number', 'name', 'iva_condition', 'address'}`. Si `data` es `None`, es consumidor final anónimo. Lanza `bad_request`;
    - `voucher_type_for(emitter_condition, receiver_condition, credit_note=False) -> int`.
  - **`settings`:**
    - `get_settings(lock=False) -> FiscalSettings | None`, `get_or_create_settings() -> FiscalSettings`;
    - `encrypt_key(pem: str) -> str`, `decrypt_key(token: str) -> str` (`PosError` si no se puede);
    - `generate_csr(settings, environment) -> str`, que guarda la clave cifrada y el CSR y borra el certificado del entorno;
    - `save_certificate(settings, environment, pem) -> datetime`;
    - `missing(settings) -> list[str]`;
    - `require_ready(settings) -> None`, que lanza `PosError("Falta configurar la facturación: …")`;
    - `active_credentials(settings) -> (cert_pem, key_pem)`;
    - `settings_to_dict(settings) -> dict`.
  - **`tests/fiscal_helpers.py`:**
    - `make_key_and_cert(cuit='20123456786', days=365) -> (key_pem, cert_pem)`;
    - `configure_fiscal(environment='homologacion', **overrides) -> FiscalSettings`, con CUIT 20123456786, punto de venta 5, monotributo y certificado válido;
    - `closed_sale(user, cat, table, amount_cash=None, amount_card=None)`: venta de salón con dos medialunas ($1800) cobrada en efectivo y/o débito, cerrada.

- [ ] **Step 1: Tests que fallan.** Crear `backend/tests/fiscal_helpers.py`:

```python
"""Fábricas compartidas por los tests de facturación."""
from datetime import datetime, timedelta

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from app.extensions import db
from app.services.fiscal import settings as fiscal_settings
from app.services.pos import payment_service, sale_service

CUIT = '20123456786'


def make_key_and_cert(cuit=CUIT, days=365, key=None):
    key = key or rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'galia'),
                      x509.NameAttribute(NameOID.SERIAL_NUMBER, f'CUIT {cuit}')])
    start = datetime.utcnow() - timedelta(days=1)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(start)
            .not_valid_after(start + timedelta(days=days)).sign(key, hashes.SHA256()))
    key_pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption()).decode()
    return key_pem, cert.public_bytes(serialization.Encoding.PEM).decode()


def configure_fiscal(environment='homologacion', **overrides):
    settings = fiscal_settings.get_or_create_settings()
    settings.cuit = CUIT
    settings.business_name = 'Galia Café'
    settings.address = 'Av. Siempreviva 742'
    settings.gross_income = 'Exento'
    settings.activity_start = datetime(2020, 1, 1).date()
    settings.iva_condition = 'monotributo'
    settings.point_of_sale = 5
    settings.environment = environment
    key_pem, cert_pem = make_key_and_cert()
    settings.set_credential(environment, 'private_key', fiscal_settings.encrypt_key(key_pem))
    fiscal_settings.save_certificate(settings, environment, cert_pem)
    for name, value in overrides.items():
        setattr(settings, name, value)
    db.session.commit()
    return settings


def closed_sale(user, cat, table, amount_cash=None, amount_card=None):
    """Mesa con 2 medialunas ($1800) cobrada; sin montos: todo en efectivo."""
    sale = sale_service.open_sale(user, 'salon', table_id=table.id, people=1)
    sale_service.add_item(user, sale.id, cat.unidad.id, quantity=2)
    sale_service.confirm_batch(user, sale.id)
    sale_service.request_bill(user, sale.id)
    if amount_cash is None and amount_card is None:
        amount_cash = 1800
    if amount_card:
        payment_service.add_payment(user, sale.id, cat.debito.id, amount_card)
    if amount_cash:
        payment_service.add_payment(user, sale.id, cat.efectivo.id, amount_cash)
    return sale
```

Crear `backend/tests/test_fiscal_receivers.py`:

```python
from decimal import Decimal

import pytest

from app.services.fiscal.receivers import normalize_receiver, valid_cuit, voucher_type_for
from app.services.pos.errors import PosError


def test_cuit_check_digit():
    assert valid_cuit('20123456786') is True
    assert valid_cuit('20123456780') is False
    assert valid_cuit('2012345678') is False
    assert valid_cuit('abc') is False


def test_anonymous_consumer_below_threshold_only():
    receiver = normalize_receiver(None, Decimal('1000'), Decimal('5000'), 'monotributo')
    assert receiver == {'doc_type_code': 99, 'doc_type': None, 'doc_number': '0', 'name': 'Consumidor final',
                        'iva_condition': 'consumidor_final', 'address': None}
    assert normalize_receiver(None, Decimal('1000'), None, 'monotributo')['doc_type_code'] == 99
    with pytest.raises(PosError) as error:
        normalize_receiver(None, Decimal('5000'), Decimal('5000'), 'monotributo')
    assert error.value.status == 400 and 'identificar al cliente' in error.value.message


def test_identified_receivers_are_validated():
    dni = normalize_receiver({'doc_type': 'DNI', 'doc_number': '30.123.456', 'name': ' Ana ',
                              'iva_condition': 'consumidor_final'}, Decimal('1'), None, 'monotributo')
    assert dni['doc_type_code'] == 96 and dni['doc_number'] == '30123456' and dni['name'] == 'Ana'
    cuit = normalize_receiver({'doc_type': 'CUIT', 'doc_number': '20-12345678-6', 'name': 'Proveedor SA',
                               'iva_condition': 'responsable_inscripto', 'address': 'Calle 1'},
                              Decimal('1'), None, 'monotributo')
    assert cuit['doc_type_code'] == 80 and cuit['doc_number'] == '20123456786'
    bad_cases = [
        {'doc_type': 'DNI', 'doc_number': '123', 'name': 'X', 'iva_condition': 'consumidor_final'},
        {'doc_type': 'CUIT', 'doc_number': '20123456780', 'name': 'X', 'iva_condition': 'monotributo'},
        {'doc_type': 'DNI', 'doc_number': '30123456', 'name': 'X', 'iva_condition': 'monotributo'},
        {'doc_type': 'DNI', 'doc_number': '30123456', 'name': '', 'iva_condition': 'consumidor_final'},
        {'doc_type': 'PAS', 'doc_number': '30123456', 'name': 'X', 'iva_condition': 'consumidor_final'},
        {'doc_type': 'DNI', 'doc_number': '30123456', 'name': 'X', 'iva_condition': 'otra'},
    ]
    for data in bad_cases:
        with pytest.raises(PosError):
            normalize_receiver(data, Decimal('1'), None, 'monotributo')


def test_voucher_type_matrix():
    assert voucher_type_for('monotributo', 'responsable_inscripto') == 11
    assert voucher_type_for('monotributo', 'consumidor_final', credit_note=True) == 13
    assert voucher_type_for('responsable_inscripto', 'responsable_inscripto') == 1
    assert voucher_type_for('responsable_inscripto', 'consumidor_final') == 6
    assert voucher_type_for('responsable_inscripto', 'monotributo', credit_note=True) == 8
```

Crear `backend/tests/test_fiscal_settings.py`:

```python
from datetime import datetime, timedelta

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import serialization

from app.services.fiscal import settings as fs
from app.services.pos.errors import PosError
from fiscal_helpers import configure_fiscal, make_key_and_cert
from pos_helpers import pos_app  # noqa: F401


def test_key_encryption_round_trip_and_is_not_plaintext(pos_app):
    key_pem, _ = make_key_and_cert()
    token = fs.encrypt_key(key_pem)
    assert 'PRIVATE KEY' not in token and fs.decrypt_key(token) == key_pem


def test_undecryptable_key_reports_clear_error(pos_app):
    settings = configure_fiscal()
    pos_app.config['SECRET_KEY'] = 'otra-clave'
    with pytest.raises(PosError) as error:
        fs.active_credentials(settings)
    assert 'no se puede leer' in error.value.message
    assert any('no se puede leer' in item for item in fs.missing(settings))


def test_generate_csr_and_save_matching_certificate(pos_app):
    settings = configure_fiscal()
    csr_pem = fs.generate_csr(settings, 'produccion')
    csr = x509.load_pem_x509_csr(csr_pem.encode())
    assert csr.is_signature_valid
    assert 'CUIT 20123456786' in csr.subject.rfc4514_string()
    assert settings.prod_certificate is None and settings.prod_private_key
    _other_key, other_cert = make_key_and_cert()
    with pytest.raises(PosError) as error:
        fs.save_certificate(settings, 'produccion', other_cert)
    assert 'no corresponde' in error.value.message
    key = serialization.load_pem_private_key(fs.decrypt_key(settings.prod_private_key).encode(), None)
    _same_key_pem, cert_pem = make_key_and_cert(key=key, days=30)
    expires = fs.save_certificate(settings, 'produccion', cert_pem)
    assert expires > datetime.utcnow() + timedelta(days=28)
    with pytest.raises(PosError):
        fs.save_certificate(settings, 'produccion', 'no es un certificado')


def test_missing_lists_what_is_not_configured(pos_app):
    settings = fs.get_or_create_settings()
    missing = fs.missing(settings)
    assert any('CUIT' in item for item in missing) and any('punto de venta' in item for item in missing)
    assert any('certificado' in item for item in missing)
    with pytest.raises(PosError) as error:
        fs.require_ready(settings)
    assert error.value.message.startswith('Falta configurar la facturación')
    ready = configure_fiscal()
    assert fs.missing(ready) == []
    ready.homo_cert_expires_at = datetime.utcnow() - timedelta(days=1)
    assert any('venció' in item for item in fs.missing(ready))


def test_settings_to_dict_hides_secrets(pos_app):
    data = fs.settings_to_dict(configure_fiscal())
    assert data['cuit'] == '20123456786' and data['credentials']['homologacion']['has_certificate'] is True
    assert 'PRIVATE' not in str(data) and data['missing'] == []
```

- [ ] **Step 2: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_fiscal_receivers.py tests/test_fiscal_settings.py`
Expected: `ModuleNotFoundError` (`receivers`, `settings`).

- [ ] **Step 3: Receptor.** Crear `backend/app/services/fiscal/receivers.py`:

```python
"""Receptor de la factura y tipo de comprobante."""
import re
from decimal import Decimal

from app.models.fiscal import RECEIVER_CONDITIONS
from app.services.pos.errors import bad_request
from app.utils.validation import clean_str

DOC_TYPES = {'CUIT': 80, 'CUIL': 86, 'DNI': 96}
ANONYMOUS_DOC_TYPE = 99
RECEIVER_IVA_IDS = {'responsable_inscripto': 1, 'exento': 4, 'consumidor_final': 5, 'monotributo': 6}
CUIT_WEIGHTS = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)


def valid_cuit(number):
    if not isinstance(number, str) or not re.fullmatch(r'\d{11}', number):
        return False
    remainder = 11 - sum(int(d) * w for d, w in zip(number[:10], CUIT_WEIGHTS)) % 11
    check = 0 if remainder == 11 else remainder
    return check != 10 and check == int(number[10])


def normalize_receiver(data, total, threshold, emitter_condition):
    """Receptor validado. `data` None = consumidor final sin identificar (solo debajo del umbral)."""
    if data is None:
        if threshold is not None and Decimal(total) >= Decimal(threshold):
            raise bad_request(f'Para facturas desde ${Decimal(threshold):,.0f} hay que identificar al cliente'
                              .replace(',', '.'))
        return {'doc_type_code': ANONYMOUS_DOC_TYPE, 'doc_type': None, 'doc_number': '0',
                'name': 'Consumidor final', 'iva_condition': 'consumidor_final', 'address': None}
    if not isinstance(data, dict):
        raise bad_request('Los datos del cliente son inválidos')
    doc_type = data.get('doc_type')
    if doc_type not in DOC_TYPES:
        raise bad_request('El tipo de documento tiene que ser DNI, CUIT o CUIL')
    number = re.sub(r'\D', '', str(data.get('doc_number') or ''))
    if doc_type == 'DNI' and not 7 <= len(number) <= 8:
        raise bad_request('El DNI tiene que tener 7 u 8 dígitos')
    if doc_type in ('CUIT', 'CUIL') and not valid_cuit(number):
        raise bad_request(f'El {doc_type} es inválido')
    condition = data.get('iva_condition')
    if condition not in RECEIVER_CONDITIONS:
        raise bad_request('Elegí la condición frente al IVA del cliente')
    if condition in ('responsable_inscripto', 'monotributo') and doc_type != 'CUIT':
        raise bad_request('Para esa condición frente al IVA hace falta el CUIT')
    name = clean_str(data.get('name'), 120)
    if not name:
        raise bad_request('Indicá el nombre o la razón social del cliente')
    address = clean_str(data.get('address'), 200)
    return {'doc_type_code': DOC_TYPES[doc_type], 'doc_type': doc_type, 'doc_number': number, 'name': name,
            'iva_condition': condition, 'address': address}


def voucher_type_for(emitter_condition, receiver_condition, credit_note=False):
    if emitter_condition == 'monotributo':
        return 13 if credit_note else 11
    if receiver_condition == 'responsable_inscripto':
        return 3 if credit_note else 1
    return 8 if credit_note else 6
```

- [ ] **Step 4: Configuración.** Crear `backend/app/services/fiscal/settings.py`:

```python
"""Configuración fiscal y credenciales de ARCA (clave cifrada con una clave derivada de SECRET_KEY)."""
import base64
from datetime import datetime, timedelta

from cryptography import x509
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.x509.oid import NameOID
from flask import current_app

from app.extensions import db
from app.models.fiscal import ENVIRONMENTS, SETTINGS_ID, FiscalSettings
from app.services.pos.common import now
from app.services.pos.errors import PosError, bad_request

UNREADABLE = 'La clave del certificado no se puede leer: generá un certificado nuevo'
EXPIRY_WARNING = timedelta(days=30)


def get_settings(lock=False):
    query = FiscalSettings.query.filter_by(id=SETTINGS_ID)
    if lock:
        query = query.with_for_update().populate_existing()
    return query.first()


def get_or_create_settings():
    settings = get_settings()
    if settings is None:
        settings = FiscalSettings(id=SETTINGS_ID, iva_condition='monotributo', environment='homologacion',
                                  default_iva_rate=21)
        db.session.add(settings)
        db.session.flush()
    return settings


def _fernet():
    secret = current_app.config['SECRET_KEY'].encode()
    key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b'galia-fiscal-key').derive(secret)
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_key(pem):
    return _fernet().encrypt(pem.encode()).decode()


def decrypt_key(token):
    try:
        return _fernet().decrypt(token.encode()).decode()
    except (InvalidToken, ValueError, AttributeError):
        raise PosError(UNREADABLE)


def _check_environment(environment):
    if environment not in ENVIRONMENTS:
        raise bad_request('El entorno tiene que ser homologación o producción')


def generate_csr(settings, environment):
    """Clave RSA 2048 nueva y pedido de certificado para subir a ARCA. Borra el certificado anterior del entorno."""
    _check_environment(environment)
    if not settings.cuit or not settings.business_name:
        raise bad_request('Completá el CUIT y la razón social antes de generar el pedido')
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COUNTRY_NAME, 'AR'),
                         x509.NameAttribute(NameOID.ORGANIZATION_NAME, settings.business_name[:64]),
                         x509.NameAttribute(NameOID.COMMON_NAME, 'galia'),
                         x509.NameAttribute(NameOID.SERIAL_NUMBER, f'CUIT {settings.cuit}')])
    csr = x509.CertificateSigningRequestBuilder().subject_name(subject).sign(key, hashes.SHA256())
    key_pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption()).decode()
    csr_pem = csr.public_bytes(serialization.Encoding.PEM).decode()
    settings.set_credential(environment, 'private_key', encrypt_key(key_pem))
    settings.set_credential(environment, 'csr', csr_pem)
    settings.set_credential(environment, 'certificate', None)
    settings.set_credential(environment, 'cert_expires_at', None)
    settings.updated_at = now()
    return csr_pem


def save_certificate(settings, environment, pem):
    """Valida que el certificado sea PEM, corresponda a la clave del entorno y no esté vencido."""
    _check_environment(environment)
    try:
        cert = x509.load_pem_x509_certificate((pem or '').strip().encode())
    except ValueError:
        raise bad_request('Eso no es un certificado válido: pegá el contenido completo, con BEGIN y END')
    encrypted = settings.credential(environment, 'private_key')
    if not encrypted:
        raise bad_request('Primero generá el pedido de certificado (CSR)')
    key = serialization.load_pem_private_key(decrypt_key(encrypted).encode(), password=None)
    if cert.public_key().public_numbers() != key.public_key().public_numbers():
        raise bad_request('El certificado no corresponde a la clave de Galia: subí el CSR que generó Galia')
    expires = cert.not_valid_after
    if expires <= datetime.utcnow():
        raise bad_request(f'El certificado venció el {expires:%d/%m/%Y}')
    settings.set_credential(environment, 'certificate', cert.public_bytes(serialization.Encoding.PEM).decode())
    settings.set_credential(environment, 'cert_expires_at', expires)
    settings.updated_at = now()
    return expires


def _credential_problem(settings):
    environment = settings.environment
    if not settings.credential(environment, 'private_key') or not settings.credential(environment, 'certificate'):
        return f'certificado de {"homologación" if environment == "homologacion" else "producción"}'
    expires = settings.credential(environment, 'cert_expires_at')
    if expires and expires <= datetime.utcnow():
        return f'el certificado venció el {expires:%d/%m/%Y}: generá uno nuevo'
    try:
        decrypt_key(settings.credential(environment, 'private_key'))
    except PosError:
        return UNREADABLE.lower()
    return None


def missing(settings):
    if settings is None:
        return ['CUIT y datos del emisor', 'punto de venta', 'certificado']
    items = []
    if not settings.cuit or not settings.business_name or not settings.address or not settings.activity_start:
        items.append('CUIT y datos del emisor')
    if not settings.point_of_sale:
        items.append('punto de venta')
    problem = _credential_problem(settings)
    if problem:
        items.append(problem)
    return items


def require_ready(settings):
    items = missing(settings)
    if items:
        raise PosError(f'Falta configurar la facturación: {", ".join(items)}')


def active_credentials(settings):
    environment = settings.environment
    cert = settings.credential(environment, 'certificate')
    encrypted = settings.credential(environment, 'private_key')
    if not cert or not encrypted:
        raise PosError('Falta configurar la facturación: certificado')
    return cert, decrypt_key(encrypted)


def settings_to_dict(settings):
    def creds(environment):
        expires = settings.credential(environment, 'cert_expires_at')
        return {'has_key': bool(settings.credential(environment, 'private_key')),
                'has_csr': bool(settings.credential(environment, 'csr')),
                'has_certificate': bool(settings.credential(environment, 'certificate')),
                'expires_at': expires.isoformat() if expires else None,
                'expires_soon': bool(expires and expires - datetime.utcnow() < EXPIRY_WARNING)}

    return {
        'cuit': settings.cuit, 'business_name': settings.business_name, 'address': settings.address,
        'gross_income': settings.gross_income,
        'activity_start': settings.activity_start.isoformat() if settings.activity_start else None,
        'iva_condition': settings.iva_condition, 'point_of_sale': settings.point_of_sale,
        'environment': settings.environment,
        'cf_id_threshold': f'{settings.cf_id_threshold:.2f}' if settings.cf_id_threshold is not None else None,
        'default_iva_rate': f'{settings.default_iva_rate:.2f}',
        'credentials': {env: creds(env) for env in ENVIRONMENTS},
        'missing': missing(settings),
    }
```

- [ ] **Step 5: Correr**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_fiscal_receivers.py tests/test_fiscal_settings.py`
Expected: todos pasan. `pos_app` restaura la configuración al terminar cada test: crea una app nueva por test, así que cambiar `SECRET_KEY` no se filtra a otros tests.

- [ ] **Step 6: Commit**

```bash
git -C <worktree> add backend/app/services/fiscal backend/tests/fiscal_helpers.py backend/tests/test_fiscal_receivers.py backend/tests/test_fiscal_settings.py
git -C <worktree> commit -m "feat(fiscal): receiver validation, voucher types and encrypted ARCA credentials"
```

---

### Task 4: Cliente de ARCA (WSAA, WSFEv1) y `FakeArca`

**Files:**
- Create:
  - `backend/app/services/fiscal/arca/__init__.py`, `wsaa.py`, `wsfe.py`, `fake.py`;
  - `backend/tests/test_fiscal_arca.py`.

**Interfaces:**
- Consumes: `settings.active_credentials`, `FiscalSettings`, `ArcaToken`.
- Produces:
  - **Errores:** `ArcaUnavailable(Exception)`, `ArcaRejected(Exception)` con `.errors: list[{'code', 'msg'}]` (en `arca/__init__.py`).
  - **`wsaa`:**
    - `build_tra(service, moment) -> str`;
    - `sign_tra(tra, cert_pem, key_pem) -> str` (CMS en base64);
    - `parse_login(xml) -> (token, sign, expires_at_utc_naive)`;
    - `credentials(settings, login=None) -> (token, sign)`: usa `ArcaToken` y, si no hay o vence en menos de 10 minutos, llama a `login(cms)` (por defecto, SOAP `LoginCms`) y guarda en una transacción propia.
  - **`wsfe`:**
    - `build_detail(invoice_fields) -> dict`, el `FECAEDetRequest` puro;
    - `parse_cae_response(dict) -> CaeResult(result, cae, cae_due, observations, errors)`;
    - `parse_query_response(dict) -> dict | None`;
    - `WsfeClient(environment, cuit, token, sign)` con `dummy()`, `last_authorized(pos, type)`, `request_cae(pos, type, detail)` y `query(type, pos, number)`.
  - **Gateway** (interfaz común para el real y el falso):
    - `dummy() -> dict`;
    - `last_authorized(pos, type) -> int`;
    - `request_cae(pos, type, detail) -> CaeResult`;
    - `query(type, pos, number) -> dict | None`, con claves `cae`, `cae_due`, `total`, `doc_type`, `doc_number`.
  - **`arca.get_gateway(settings) -> gateway`:** `FakeArca` si `FISCAL_FAKE_ARCA=1` y la base es SQLite; si no, `WsfeClient` con las credenciales del WSAA.
  - **`FakeArca`** (en `fake.py`): `mode` (`approve` | `reject` | `timeout` | `timeout_after_issue`), `issued` (dict compartido por clase y protegido con lock) y `reset()`.

- [ ] **Step 1: Tests que fallan.** Crear `backend/tests/test_fiscal_arca.py`:

```python
import base64
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs7

from app.models import ArcaToken
from app.services.fiscal import arca
from app.services.fiscal.arca import ArcaRejected, wsaa, wsfe
from app.services.fiscal.arca.fake import FakeArca
from fiscal_helpers import configure_fiscal, make_key_and_cert
from pos_helpers import pos_app  # noqa: F401


def test_tra_and_signed_cms_contains_tra_and_certificate():
    tra = wsaa.build_tra('wsfe', datetime(2026, 10, 14, 15, 0, 0))
    assert '<service>wsfe</service>' in tra and '<uniqueId>' in tra
    assert '2026-10-14T11:50:00-03:00' in tra and '2026-10-14T12:10:00-03:00' in tra
    key_pem, cert_pem = make_key_and_cert()
    der = base64.b64decode(wsaa.sign_tra(tra, cert_pem, key_pem))
    assert tra.encode() in der
    certs = pkcs7.load_der_pkcs7_certificates(der)
    assert certs[0].public_bytes(serialization.Encoding.PEM).decode() == cert_pem


def test_parse_login_response():
    xml = ('<?xml version="1.0"?><loginTicketResponse version="1.0"><header>'
           '<expirationTime>2026-10-15T03:00:00.123-03:00</expirationTime></header>'
           '<credentials><token>TOK</token><sign>SIG</sign></credentials></loginTicketResponse>')
    token, sign, expires = wsaa.parse_login(xml)
    assert (token, sign) == ('TOK', 'SIG') and expires == datetime(2026, 10, 15, 6, 0, 0, 123000)


def test_credentials_are_cached_until_near_expiry(pos_app):
    settings = configure_fiscal()
    calls = []

    def login(cms):
        calls.append(cms)
        expiry = (datetime.utcnow() + timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M:%S') + '+00:00'
        return (f'<loginTicketResponse><header><expirationTime>{expiry}</expirationTime></header>'
                f'<credentials><token>T{len(calls)}</token><sign>S</sign></credentials></loginTicketResponse>')

    assert wsaa.credentials(settings, login=login) == ('T1', 'S')
    assert wsaa.credentials(settings, login=login) == ('T1', 'S')
    assert len(calls) == 1 and ArcaToken.query.count() == 1
    token = ArcaToken.query.one()
    token.expires_at = datetime.utcnow() + timedelta(minutes=5)
    assert wsaa.credentials(settings, login=login) == ('T2', 'S')


def test_build_detail_for_invoice_and_credit_note():
    fields = {'number': 42, 'voucher_date': datetime(2026, 10, 14).date(), 'doc_type_code': 99,
              'doc_number': '0', 'total': Decimal('1800.00'), 'net': Decimal('1800.00'), 'iva': Decimal('0.00'),
              'iva_rate': Decimal('0'), 'discriminated': False, 'receiver_iva_id': 5, 'associated': None}
    detail = wsfe.build_detail(fields)
    assert detail == {'Concepto': 1, 'DocTipo': 99, 'DocNro': 0, 'CbteDesde': 42, 'CbteHasta': 42,
                      'CbteFch': '20261014', 'ImpTotal': 1800.0, 'ImpTotConc': 0, 'ImpNeto': 1800.0,
                      'ImpOpEx': 0, 'ImpIVA': 0.0, 'ImpTrib': 0, 'MonId': 'PES', 'MonCotiz': 1,
                      'CondicionIVAReceptorId': 5}
    fields.update({'discriminated': True, 'iva_rate': Decimal('21'), 'net': Decimal('1487.60'),
                   'iva': Decimal('312.40'),
                   'associated': {'type': 6, 'pos': 5, 'number': 41, 'cuit': '20123456786',
                                  'date': datetime(2026, 10, 13).date()}})
    detail = wsfe.build_detail(fields)
    assert detail['Iva'] == {'AlicIva': [{'Id': 5, 'BaseImp': 1487.6, 'Importe': 312.4}]}
    assert detail['CbtesAsoc'] == {'CbteAsoc': [{'Tipo': 6, 'PtoVta': 5, 'Nro': 41, 'Cuit': '20123456786',
                                                 'CbteFch': '20261013'}]}


def test_parse_cae_response_approved_rejected_and_errors():
    approved = {'FeCabResp': {'Resultado': 'A'}, 'FeDetResp': {'FECAEDetResponse': [
        {'Resultado': 'A', 'CAE': '75123456789012', 'CAEFchVto': '20261024',
         'Observaciones': {'Obs': [{'Code': 10217, 'Msg': 'Aviso'}]}}]}, 'Errors': None}
    result = wsfe.parse_cae_response(approved)
    assert result.result == 'A' and result.cae == '75123456789012'
    assert result.cae_due == datetime(2026, 10, 24).date() and result.observations == [{'code': 10217, 'msg': 'Aviso'}]
    rejected = {'FeCabResp': {'Resultado': 'R'}, 'FeDetResp': {'FECAEDetResponse': [
        {'Resultado': 'R', 'CAE': '', 'CAEFchVto': '',
         'Observaciones': {'Obs': [{'Code': 10015, 'Msg': 'Documento inválido'}]}}]}, 'Errors': None}
    result = wsfe.parse_cae_response(rejected)
    assert result.result == 'R' and result.observations[0]['msg'] == 'Documento inválido'
    with pytest.raises(ArcaRejected) as error:
        wsfe.parse_cae_response({'FeCabResp': None, 'FeDetResp': None,
                                 'Errors': {'Err': [{'Code': 600, 'Msg': 'Token inválido'}]}})
    assert error.value.errors == [{'code': 600, 'msg': 'Token inválido'}]


def test_parse_query_response():
    found = {'ResultGet': {'CodAutorizacion': '751', 'FchVto': '20261024', 'ImpTotal': 1800.0, 'DocTipo': 99,
                           'DocNro': 0, 'Resultado': 'A'}, 'Errors': None}
    assert wsfe.parse_query_response(found) == {'cae': '751', 'cae_due': datetime(2026, 10, 24).date(),
                                                'total': Decimal('1800.00'), 'doc_type': 99, 'doc_number': '0'}
    assert wsfe.parse_query_response({'ResultGet': None, 'Errors': {'Err': [{'Code': 602, 'Msg': 'No existen'}]}}) \
        is None


def test_fake_gateway_only_with_sqlite_and_flag(pos_app, monkeypatch):
    settings = configure_fiscal()
    monkeypatch.setenv('FISCAL_FAKE_ARCA', '1')
    assert isinstance(arca.get_gateway(settings), FakeArca)
    FakeArca.reset()
    fake = FakeArca()
    assert fake.last_authorized(5, 11) == 0
    result = fake.request_cae(5, 11, {'CbteDesde': 1, 'ImpTotal': 10.0, 'DocTipo': 99, 'DocNro': 0})
    assert result.result == 'A' and fake.last_authorized(5, 11) == 1
    assert fake.query(11, 5, 1)['cae'] == result.cae and fake.query(11, 5, 2) is None
```

- [ ] **Step 2: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_fiscal_arca.py`
Expected: `ModuleNotFoundError: No module named 'app.services.fiscal.arca'`.

- [ ] **Step 3: Paquete y gateway.** Crear `backend/app/services/fiscal/arca/__init__.py`:

```python
"""Acceso a ARCA. `get_gateway` devuelve el cliente real (WSAA + WSFEv1) o FakeArca para desarrollo."""
import os

from app.extensions import db


class ArcaUnavailable(Exception):
    """ARCA no respondió (red, timeout, SOAP Fault)."""


class ArcaRejected(Exception):
    """ARCA respondió con errores (no con un comprobante rechazado)."""

    def __init__(self, errors):
        super().__init__('; '.join(f"{e['code']}: {e['msg']}" for e in errors))
        self.errors = errors


def fake_enabled():
    return os.getenv('FISCAL_FAKE_ARCA') == '1' and db.engine.dialect.name == 'sqlite'


def get_gateway(settings):
    if fake_enabled():
        from app.services.fiscal.arca.fake import FakeArca
        # Para el preview: FISCAL_FAKE_ARCA_MODE=timeout|reject|timeout_after_issue simula fallas de ARCA.
        FakeArca.mode = os.getenv('FISCAL_FAKE_ARCA_MODE', 'approve')
        return FakeArca()
    from app.services.fiscal.arca import wsaa, wsfe
    token, sign = wsaa.credentials(settings)
    return wsfe.WsfeClient(settings.environment, settings.cuit, token, sign)
```

- [ ] **Step 4: WSAA.** Crear `backend/app/services/fiscal/arca/wsaa.py`:

```python
"""WSAA: acceso a los web services de ARCA. El ticket (token + sign) dura 12 h y se guarda en arca_tokens."""
import base64
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import pytz
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs7

from app.extensions import db
from app.models import ArcaToken
from app.services.fiscal import settings as fiscal_settings
from app.services.fiscal.arca import ArcaRejected, ArcaUnavailable
from app.utils.timezone_utils import ARGENTINA_TZ

SERVICE = 'wsfe'
RENEW_BEFORE = timedelta(minutes=10)
URLS = {'homologacion': 'https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl',
        'produccion': 'https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl'}


def build_tra(service, moment):
    """Ticket de requerimiento de acceso. `moment` en UTC naive."""
    local = pytz.utc.localize(moment).astimezone(ARGENTINA_TZ)
    fmt = lambda value: value.isoformat(timespec='seconds')  # noqa: E731
    return ('<?xml version="1.0" encoding="UTF-8"?><loginTicketRequest version="1.0"><header>'
            f'<uniqueId>{int(moment.replace(tzinfo=timezone.utc).timestamp())}</uniqueId>'
            f'<generationTime>{fmt(local - timedelta(minutes=10))}</generationTime>'
            f'<expirationTime>{fmt(local + timedelta(minutes=10))}</expirationTime>'
            f'</header><service>{service}</service></loginTicketRequest>')


def sign_tra(tra, cert_pem, key_pem):
    """CMS (PKCS#7) con el TRA adentro, firmado con SHA-256, en base64."""
    cert = x509.load_pem_x509_certificate(cert_pem.encode())
    key = serialization.load_pem_private_key(key_pem.encode(), password=None)
    der = (pkcs7.PKCS7SignatureBuilder().set_data(tra.encode()).add_signer(cert, key, hashes.SHA256())
           .sign(serialization.Encoding.DER, []))
    return base64.b64encode(der).decode()


def parse_login(xml):
    root = ET.fromstring(xml)
    token = root.findtext('credentials/token')
    sign = root.findtext('credentials/sign')
    expiration = root.findtext('header/expirationTime')
    if not token or not sign or not expiration:
        raise ArcaRejected([{'code': 'wsaa', 'msg': 'Respuesta del WSAA incompleta'}])
    expires = datetime.fromisoformat(expiration).astimezone(timezone.utc).replace(tzinfo=None)
    return token, sign, expires


def _soap_login(environment):
    def login(cms):
        from zeep import Client
        from zeep.exceptions import Fault
        from zeep.transports import Transport
        try:
            client = Client(URLS[environment], transport=Transport(timeout=10, operation_timeout=30))
            return client.service.loginCms(in0=cms)
        except Fault as fault:
            message = str(fault.message or fault)
            if 'alreadyAuthenticated' in message or 'ya posee un TA valido' in message:
                raise ArcaRejected([{'code': 'wsaa', 'msg': (
                    'ARCA ya entregó un acceso a este certificado que Galia no tiene guardado; '
                    'esperá unos minutos (hasta 12 h) o generá otro certificado')}])
            raise ArcaRejected([{'code': 'wsaa', 'msg': message}])
        except Exception as exc:  # red, timeout, WSDL
            raise ArcaUnavailable(str(exc))
    return login


def credentials(settings, login=None):
    """(token, sign) vigentes para wsfe en el entorno activo. Guarda el ticket apenas llega (commit propio)."""
    environment = settings.environment
    row = ArcaToken.query.filter_by(service=SERVICE, environment=environment).first()
    if row is not None and row.expires_at - RENEW_BEFORE > datetime.utcnow():
        return row.token, row.sign
    cert_pem, key_pem = fiscal_settings.active_credentials(settings)
    cms = sign_tra(build_tra(SERVICE, datetime.utcnow()), cert_pem, key_pem)
    token, sign, expires = parse_login((login or _soap_login(environment))(cms))
    if row is None:
        row = ArcaToken(service=SERVICE, environment=environment, token=token, sign=sign, expires_at=expires)
        db.session.add(row)
    else:
        row.token, row.sign, row.expires_at = token, sign, expires
    db.session.commit()
    return token, sign
```

- [ ] **Step 5: WSFEv1.** Crear `backend/app/services/fiscal/arca/wsfe.py`:

```python
"""WSFEv1: último comprobante, pedido de CAE y consulta. El armado y la lectura son funciones puras."""
from collections import namedtuple
from datetime import datetime
from decimal import Decimal

from app.services.fiscal.arca import ArcaRejected, ArcaUnavailable

URLS = {'homologacion': 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL',
        'produccion': 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'}
IVA_IDS = {Decimal('0'): 3, Decimal('10.5'): 4, Decimal('21'): 5, Decimal('27'): 6}
NOT_FOUND_CODE = 602

CaeResult = namedtuple('CaeResult', 'result cae cae_due observations errors')


def _date(value):
    return value.strftime('%Y%m%d')


def _parse_date(value):
    return datetime.strptime(str(value), '%Y%m%d').date() if value else None


def _amount(value):
    return float(Decimal(value).quantize(Decimal('0.01')))


def _messages(container, key):
    items = (container or {}).get(key) if isinstance(container, dict) else None
    return [{'code': item.get('Code'), 'msg': item.get('Msg')} for item in (items or [])]


def build_detail(fields):
    """FECAEDetRequest de un comprobante. `fields`: number, voucher_date, doc_type_code, doc_number, total,
    net, iva, iva_rate, discriminated, receiver_iva_id, associated (dict o None)."""
    detail = {
        'Concepto': 1, 'DocTipo': fields['doc_type_code'], 'DocNro': int(fields['doc_number'] or 0),
        'CbteDesde': fields['number'], 'CbteHasta': fields['number'], 'CbteFch': _date(fields['voucher_date']),
        'ImpTotal': _amount(fields['total']), 'ImpTotConc': 0, 'ImpNeto': _amount(fields['net']), 'ImpOpEx': 0,
        'ImpIVA': _amount(fields['iva']), 'ImpTrib': 0, 'MonId': 'PES', 'MonCotiz': 1,
        'CondicionIVAReceptorId': fields['receiver_iva_id'],
    }
    if fields['discriminated']:
        detail['Iva'] = {'AlicIva': [{'Id': IVA_IDS[Decimal(fields['iva_rate']).normalize()],
                                      'BaseImp': _amount(fields['net']), 'Importe': _amount(fields['iva'])}]}
    associated = fields.get('associated')
    if associated:
        detail['CbtesAsoc'] = {'CbteAsoc': [{'Tipo': associated['type'], 'PtoVta': associated['pos'],
                                             'Nro': associated['number'], 'Cuit': associated['cuit'],
                                             'CbteFch': _date(associated['date'])}]}
    return detail


def parse_cae_response(data):
    errors = _messages(data.get('Errors'), 'Err')
    details = ((data.get('FeDetResp') or {}).get('FECAEDetResponse') or [])
    if errors and not details:
        raise ArcaRejected(errors)
    detail = details[0]
    observations = _messages(detail.get('Observaciones'), 'Obs')
    return CaeResult(detail.get('Resultado'), detail.get('CAE') or None, _parse_date(detail.get('CAEFchVto')),
                     observations, errors)


def parse_query_response(data):
    errors = _messages(data.get('Errors'), 'Err')
    if any(e['code'] == NOT_FOUND_CODE for e in errors):
        return None
    if errors:
        raise ArcaRejected(errors)
    result = data.get('ResultGet') or {}
    if not result.get('CodAutorizacion'):
        return None
    return {'cae': str(result['CodAutorizacion']), 'cae_due': _parse_date(result.get('FchVto')),
            'total': Decimal(str(result.get('ImpTotal'))).quantize(Decimal('0.01')),
            'doc_type': int(result.get('DocTipo')), 'doc_number': str(result.get('DocNro'))}


class WsfeClient:
    def __init__(self, environment, cuit, token, sign):
        self.environment = environment
        self.auth = {'Token': token, 'Sign': sign, 'Cuit': int(cuit)}
        self._client = None

    def _service(self):
        from zeep import Client
        from zeep.transports import Transport
        if self._client is None:
            self._client = Client(URLS[self.environment], transport=Transport(timeout=10, operation_timeout=30))
        return self._client.service

    def _call(self, name, **kwargs):
        from zeep.helpers import serialize_object
        try:
            response = getattr(self._service(), name)(**kwargs)
        except Exception as exc:  # red, timeout, SOAP Fault
            raise ArcaUnavailable(str(exc))
        return serialize_object(response, dict) or {}

    def dummy(self):
        return self._call('FEDummy')

    def last_authorized(self, pos, voucher_type):
        data = self._call('FECompUltimoAutorizado', Auth=self.auth, PtoVta=pos, CbteTipo=voucher_type)
        errors = _messages(data.get('Errors'), 'Err')
        if errors:
            raise ArcaRejected(errors)
        return int(data.get('CbteNro') or 0)

    def request_cae(self, pos, voucher_type, detail):
        data = self._call('FECAESolicitar', Auth=self.auth, FeCAEReq={
            'FeCabReq': {'CantReg': 1, 'PtoVta': pos, 'CbteTipo': voucher_type},
            'FeDetReq': {'FECAEDetRequest': [detail]}})
        return parse_cae_response(data)

    def query(self, voucher_type, pos, number):
        data = self._call('FECompConsultar', Auth=self.auth,
                          FeCompConsReq={'CbteTipo': voucher_type, 'CbteNro': number, 'PtoVta': pos})
        return parse_query_response(data)
```

- [ ] **Step 6: FakeArca.** Crear `backend/app/services/fiscal/arca/fake.py`:

```python
"""ARCA de mentira para tests y para el preview local (FISCAL_FAKE_ARCA=1 con SQLite). Nunca en producción."""
import threading
from datetime import date, timedelta
from decimal import Decimal

from app.services.fiscal.arca import ArcaUnavailable
from app.services.fiscal.arca.wsfe import CaeResult


class FakeArca:
    issued = {}  # (pos, type) -> {number: {'cae', 'cae_due', 'total', 'doc_type', 'doc_number'}}
    mode = 'approve'
    _lock = threading.Lock()

    @classmethod
    def reset(cls, mode='approve'):
        with cls._lock:
            cls.issued = {}
            cls.mode = mode

    def dummy(self):
        return {'AppServer': 'OK', 'DbServer': 'OK', 'AuthServer': 'OK'}

    def last_authorized(self, pos, voucher_type):
        with self._lock:
            return max(self.issued.get((pos, voucher_type), {}) or [0])

    def request_cae(self, pos, voucher_type, detail):
        mode = type(self).mode
        if mode == 'timeout':
            raise ArcaUnavailable('timeout (simulado)')
        if mode == 'reject':
            return CaeResult('R', None, None, [{'code': 10015, 'msg': 'Documento del receptor inválido'}], [])
        number = detail['CbteDesde']
        with self._lock:
            book = self.issued.setdefault((pos, voucher_type), {})
            if number != max(book or [0]) + 1:
                return CaeResult('R', None, None, [{'code': 10016, 'msg': 'Número no correlativo'}], [])
            cae = f'7{pos:04d}{voucher_type:02d}{number:07d}'
            book[number] = {'cae': cae, 'cae_due': date.today() + timedelta(days=10),
                            'total': Decimal(str(detail['ImpTotal'])).quantize(Decimal('0.01')),
                            'doc_type': detail['DocTipo'], 'doc_number': str(detail['DocNro'])}
        if mode == 'timeout_after_issue':
            raise ArcaUnavailable('timeout después de autorizar (simulado)')
        return CaeResult('A', cae, book[number]['cae_due'], [], [])

    def query(self, voucher_type, pos, number):
        with self._lock:
            found = self.issued.get((pos, voucher_type), {}).get(number)
            return dict(found) if found else None
```

- [ ] **Step 7: Correr**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_fiscal_arca.py`
Expected: 8 passed. Si `pkcs7.load_der_pkcs7_certificates` no está disponible en `cryptography` 42.0.8, verificar que existe con `PY -c "from cryptography.hazmat.primitives.serialization import pkcs7; print(pkcs7.load_der_pkcs7_certificates)"`; en 42 está disponible.

- [ ] **Step 8: Commit**

```bash
git -C <worktree> add backend/app/services/fiscal/arca backend/tests/test_fiscal_arca.py
git -C <worktree> commit -m "feat(fiscal): ARCA WSAA and WSFEv1 client with a fake gateway"
```

---

### Task 5: Emitir facturas (dos fases), resolver `pending` y documento impreso

**Files:**
- Create: `backend/app/services/fiscal/invoice_service.py`, `backend/app/services/fiscal/invoice_documents.py`, `backend/tests/test_fiscal_issue.py`
- Modify: `backend/app/services/pos/print_documents.py` (`item_description`)

**Interfaces:**
- Consumes:
  - `amounts`, `receivers`, `settings`, `arca.get_gateway`, `wsfe.build_detail`, `FakeArca`;
  - `print_service.cashier_printer` y `add_job`;
  - `common.load_sale`, `common.now`, `common.parse_id`, `get_current_date_argentina`.
- Produces:
  - **`invoice_service`:**
    - `PENDING_GRACE = timedelta(seconds=120)`;
    - `preview(sale_id) -> dict`;
    - `issue(user, sale_id, customer_data) -> Invoice` (status `authorized` | `pending` | `rejected`);
    - `resolve(invoice) -> Invoice` y `verify(user, invoice_id) -> Invoice`;
    - `reprint(user, invoice_id) -> Invoice`;
    - `active_invoice(sale_id) -> Invoice | None`, `pending_invoice(sale_id) -> Invoice | None`;
    - `invoice_to_dict(invoice) -> dict`, que incluye `print_warning`, tomado del atributo transitorio `invoice.print_warning`;
    - `print_invoice(invoice, user, settings=None) -> str | None` (aviso si no hay impresora).
  - **`invoice_documents`:**
    - `qr_url(invoice, cuit) -> str`;
    - `invoice_document(invoice, settings) -> dict`, con la estructura de documento de impresión más la clave `qr`.
  - **`print_documents.item_description(item) -> str`:** el texto del ítem con sus modificadores, separados por coma.

- [ ] **Step 1: Tests que fallan.** Crear `backend/tests/test_fiscal_issue.py`:

```python
import base64
import json
from datetime import datetime, timedelta

import pytest

from app.extensions import db
from app.models import FiscalCustomer, Invoice
from app.models.pos import PrintJob
from app.services.fiscal import arca, invoice_service
from app.services.fiscal.arca.fake import FakeArca
from app.services.fiscal.invoice_documents import qr_url
from app.services.pos.errors import PosError
from fiscal_helpers import closed_sale, configure_fiscal
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401
from print_helpers import make_printer


@pytest.fixture
def ctx(pos_app, monkeypatch):
    FakeArca.reset()
    monkeypatch.setattr(arca, 'get_gateway', lambda settings: FakeArca())
    user = make_user('caja@test.com', modules=('POS', 'Anular'))
    cat = make_catalog()
    _salon, t1, t2 = make_floor()
    settings = configure_fiscal()
    printer = make_printer('Térmica caja', cashier=True)
    return user, cat, t1, t2, settings, printer


def test_preview_full_and_partial(ctx):
    user, cat, t1, t2, _s, _p = ctx
    full = closed_sale(user, cat, t1)
    data = invoice_service.preview(full.id)
    assert data['amount'] == '1800.00' and data['detail_mode'] == 'items' and data['letter'] == 'C'
    assert data['ready'] is True and data['active_invoice'] is None
    partial = closed_sale(user, cat, t2, amount_cash=1000, amount_card=800)
    data = invoice_service.preview(partial.id)
    assert data['amount'] == '1000.00' and data['detail_mode'] == 'generic'
    assert data['lines'][0]['description'] == f'Consumo – Venta #{partial.number}'


def test_issue_authorized_prints_and_saves_customer(ctx):
    user, cat, t1, _t2, settings, printer = ctx
    sale = closed_sale(user, cat, t1)
    invoice = invoice_service.issue(user, sale.id, {'doc_type': 'DNI', 'doc_number': '30123456', 'name': 'Ana',
                                                    'iva_condition': 'consumidor_final'})
    assert invoice.status == 'authorized' and invoice.number == 1 and invoice.cae
    assert invoice.label == 'Factura C 00005-00000001' and invoice.voucher_type == 11
    assert [p.amount for p in invoice.payments] == [invoice.total]
    assert FiscalCustomer.query.one().name == 'Ana'
    job = PrintJob.query.filter_by(kind='invoice').one()
    assert job.printer_id == printer.id and job.document['title'] == 'FACTURA C'
    assert 'CAE ' + invoice.cae in job.document['footer'] and job.document['qr'].startswith(
        'https://www.afip.gob.ar/fe/qr/?p=')
    assert 'SIN VALIDEZ FISCAL – PRUEBA' in job.document['footer']
    assert invoice_service.active_invoice(sale.id).id == invoice.id
    with pytest.raises(PosError) as error:
        invoice_service.issue(user, sale.id, None)
    assert 'ya tiene la Factura C 00005-00000001' in error.value.message


def test_rejected_frees_the_number(ctx):
    user, cat, t1, t2, _s, _p = ctx
    FakeArca.reset('reject')
    sale = closed_sale(user, cat, t1)
    invoice = invoice_service.issue(user, sale.id, None)
    assert invoice.status == 'rejected' and 'Documento del receptor inválido' in invoice.error
    FakeArca.mode = 'approve'
    again = invoice_service.issue(user, sale.id, None)
    assert again.status == 'authorized' and again.number == 1


def test_timeout_leaves_pending_and_verify_rejects_when_arca_never_got_it(ctx):
    user, cat, t1, t2, _s, _p = ctx
    FakeArca.reset('timeout')
    sale = closed_sale(user, cat, t1)
    invoice = invoice_service.issue(user, sale.id, None)
    assert invoice.status == 'pending'
    other = closed_sale(user, cat, t2)
    with pytest.raises(PosError) as error:
        invoice_service.issue(user, other.id, None)
    assert 'emitiéndose' in error.value.message
    FakeArca.mode = 'approve'
    resolved = invoice_service.verify(user, invoice.id)
    assert resolved.status == 'rejected' and resolved.error == 'No llegó a ARCA'


def test_timeout_after_arca_issued_resolves_to_authorized(ctx):
    user, cat, t1, t2, _s, _p = ctx
    FakeArca.reset('timeout_after_issue')
    sale = closed_sale(user, cat, t1)
    invoice = invoice_service.issue(user, sale.id, None)
    assert invoice.status == 'pending'
    FakeArca.mode = 'approve'
    invoice.created_at = datetime.utcnow() - timedelta(seconds=121)
    db.session.commit()
    # La próxima emisión resuelve el pending viejo antes de reservar: queda autorizado con el CAE de ARCA.
    nxt = invoice_service.issue(user, closed_sale(user, cat, t2).id, None)
    db.session.refresh(invoice)
    assert invoice.status == 'authorized' and invoice.cae == FakeArca.issued[(5, 11)][1]['cae']
    assert nxt.number == 2 and nxt.status == 'authorized'
    assert PrintJob.query.filter_by(kind='invoice').count() == 2


def test_cannot_invoice_open_sale_external_only_or_unconfigured(ctx):
    user, cat, t1, t2, settings, _p = ctx
    from app.services.pos import sale_service
    open_sale = sale_service.open_sale(user, 'salon', table_id=t1.id, people=1)
    with pytest.raises(PosError) as error:
        invoice_service.issue(user, open_sale.id, None)
    assert error.value.message == 'Solo se factura una venta cerrada'
    card_only = closed_sale(user, cat, t2, amount_card=1800)
    with pytest.raises(PosError) as error:
        invoice_service.issue(user, card_only.id, None)
    assert error.value.message == 'Todo lo cobrado en esta venta lo factura otro sistema'
    settings.point_of_sale = None
    db.session.commit()
    assert invoice_service.preview(card_only.id)['ready'] is False


def test_invoice_without_cashier_printer_still_authorizes(ctx):
    user, cat, t1, _t2, _s, printer = ctx
    printer.is_active = False
    db.session.commit()
    invoice = invoice_service.issue(user, closed_sale(user, cat, t1).id, None)
    data = invoice_service.invoice_to_dict(invoice)
    assert invoice.status == 'authorized' and data['print_warning'] == 'No hay impresora de caja configurada'


def test_qr_url_payload(ctx):
    user, cat, t1, _t2, _s, _p = ctx
    invoice = invoice_service.issue(user, closed_sale(user, cat, t1).id, None)
    payload = json.loads(base64.b64decode(qr_url(invoice, '20123456786').split('?p=')[1]))
    assert payload == {'ver': 1, 'fecha': invoice.voucher_date.isoformat(), 'cuit': 20123456786, 'ptoVta': 5,
                       'tipoCmp': 11, 'nroCmp': 1, 'importe': 1800.0, 'moneda': 'PES', 'ctz': 1,
                       'tipoDocRec': 99, 'nroDocRec': 0, 'tipoCodAut': 'E', 'codAut': int(invoice.cae)}
```

- [ ] **Step 2: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_fiscal_issue.py`
Expected: ImportError (`invoice_service`).

- [ ] **Step 3: Descripción de ítems.** En `backend/app/services/pos/print_documents.py`, agregar después de `_details`:

```python
def item_description(item):
    """Texto del ítem con sus modificadores, para comprobantes fiscales."""
    modifiers = [modifier.option_name for modifier in item.modifiers]
    return f'{_text(item)} ({", ".join(modifiers)})' if modifiers else _text(item)
```

- [ ] **Step 4: Documento.** Crear `backend/app/services/fiscal/invoice_documents.py`:

```python
"""Factura y nota de crédito impresas en la térmica de caja, con el QR de ARCA."""
import base64
import json
from decimal import Decimal

CONDITION_LABELS = {'monotributo': 'Responsable Monotributo', 'responsable_inscripto': 'IVA Responsable Inscripto',
                    'consumidor_final': 'Consumidor Final', 'exento': 'IVA Exento'}
DOC_LABELS = {80: 'CUIT', 86: 'CUIL', 96: 'DNI'}
QR_BASE = 'https://www.afip.gob.ar/fe/qr/?p='


def _money(value):
    return f'{Decimal(value):.2f}'


def qr_url(invoice, cuit):
    payload = {'ver': 1, 'fecha': invoice.voucher_date.isoformat(), 'cuit': int(cuit),
               'ptoVta': invoice.point_of_sale, 'tipoCmp': invoice.voucher_type, 'nroCmp': invoice.number,
               'importe': float(Decimal(invoice.total)), 'moneda': 'PES', 'ctz': 1,
               'tipoDocRec': invoice.receiver_doc_type, 'nroDocRec': int(invoice.receiver_doc_number or 0),
               'tipoCodAut': 'E', 'codAut': int(invoice.cae)}
    encoded = base64.b64encode(json.dumps(payload, separators=(',', ':')).encode()).decode()
    return f'{QR_BASE}{encoded}'


def invoice_document(invoice, settings):
    title = ('NOTA DE CRÉDITO ' if invoice.is_credit_note else 'FACTURA ') + invoice.letter
    header = [settings.business_name, f'CUIT {settings.cuit}', f'IIBB {settings.gross_income or "-"}',
              f'Inicio de actividades {settings.activity_start:%d/%m/%Y}' if settings.activity_start else None,
              settings.address, CONDITION_LABELS.get(settings.iva_condition), f'Cód. {invoice.voucher_type:03d}',
              f'P.V. {invoice.point_of_sale:05d} Nº {invoice.number:08d}', f'Fecha {invoice.voucher_date:%d/%m/%Y}',
              f'Cliente: {invoice.receiver_name}']
    if invoice.receiver_doc_type in DOC_LABELS:
        header.append(f'{DOC_LABELS[invoice.receiver_doc_type]} {invoice.receiver_doc_number}')
    header.append(CONDITION_LABELS[invoice.receiver_iva_condition])
    if invoice.receiver_address:
        header.append(invoice.receiver_address)
    if invoice.related is not None:
        header.append(f'Anula {invoice.related.label}')
    lines = [{'qty': line['qty'], 'text': line['description'], 'amount': line['amount'], 'details': [],
              'strike': False} for line in invoice.lines]
    totals = []
    if Decimal(invoice.iva):
        totals += [{'label': 'Neto', 'amount': _money(invoice.net)},
                   {'label': f'IVA {Decimal(invoice.iva_rate).normalize()}%', 'amount': _money(invoice.iva)}]
    totals.append({'label': 'TOTAL', 'amount': _money(invoice.total)})
    footer = [f'CAE {invoice.cae}', f'Vto. CAE {invoice.cae_due:%d/%m/%Y}']
    if invoice.environment == 'homologacion':
        footer.append('SIN VALIDEZ FISCAL – PRUEBA')
    return {'title': title, 'header': [h for h in header if h], 'lines': lines, 'totals': totals,
            'footer': footer, 'qr': qr_url(invoice, settings.cuit)}
```

- [ ] **Step 5: Servicio.** Crear `backend/app/services/fiscal/invoice_service.py`:

```python
"""Comprobantes ARCA: vista previa, emisión en dos fases, resolución de pendientes, nota de crédito, listado.

Fase 1 (transacción con la fila de fiscal_settings bloqueada): valida, resuelve pendientes viejos, toma el
próximo número de ARCA y guarda el comprobante 'pending'. Fase 2 (sin transacción abierta): pide el CAE.
Si la respuesta no llega, el comprobante queda 'pending' y se resuelve consultando a ARCA (nunca a ciegas).
"""
import logging
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace

from app.extensions import db
from app.models import FiscalCustomer, Invoice, InvoicePayment, PaymentMethod
from app.models.fiscal import VOUCHER_TYPES
from app.services.fiscal import amounts, arca, receivers
from app.services.fiscal import settings as fiscal_settings
from app.services.fiscal.arca import ArcaRejected, ArcaUnavailable, wsfe
from app.services.fiscal.invoice_documents import invoice_document
from app.services.pos import print_documents, print_service
from app.services.pos.common import load_sale, now, parse_id
from app.services.pos.errors import PosError, not_found
from app.utils.timezone_utils import get_current_date_argentina

logger = logging.getLogger(__name__)
PENDING_GRACE = timedelta(seconds=120)
UNAVAILABLE = 'ARCA no responde, probá en unos minutos'
NOT_CONFIRMED = 'No pudimos confirmar con ARCA. Tocá Verificar en unos segundos'


def _external_ids():
    return {m.id for m in PaymentMethod.query.filter_by(invoiced_externally=True)}


def _authorized_credit_note(invoice):
    return Invoice.query.filter_by(related_invoice_id=invoice.id, status='authorized').first()


def active_invoice(sale_id):
    """Factura autorizada de la venta sin nota de crédito autorizada (como máximo una)."""
    for invoice in Invoice.query.filter_by(sale_id=sale_id, kind='invoice', status='authorized') \
            .order_by(Invoice.id.desc()):
        if _authorized_credit_note(invoice) is None:
            return invoice
    return None


def pending_invoice(sale_id):
    return Invoice.query.filter_by(sale_id=sale_id, status='pending').order_by(Invoice.id.desc()).first()


def _discriminated(settings):
    return settings.iva_condition == 'responsable_inscripto'


def preview(sale_id):
    sale = load_sale(parse_id(sale_id, 'La venta'))
    settings = fiscal_settings.get_settings()
    amount = amounts.invoiceable_amount(sale, _external_ids())
    mode, lines = amounts.build_lines(sale, amount, print_documents.item_description) if amount else (None, [])
    condition = settings.iva_condition if settings else 'monotributo'
    voucher_type = receivers.voucher_type_for(condition, 'consumidor_final')
    active = active_invoice(sale.id)
    pending = pending_invoice(sale.id)
    db.session.commit()
    return {
        'sale_id': sale.id, 'sale_status': sale.status, 'total': f'{sale.total:.2f}', 'amount': f'{amount:.2f}',
        'detail_mode': mode, 'lines': lines, 'voucher_type': voucher_type,
        'letter': VOUCHER_TYPES[voucher_type][1],
        'requires_id_from': (f'{settings.cf_id_threshold:.2f}'
                             if settings and settings.cf_id_threshold is not None else None),
        'ready': not fiscal_settings.missing(settings), 'missing': fiscal_settings.missing(settings),
        'environment': settings.environment if settings else 'homologacion',
        'active_invoice': invoice_to_dict(active) if active else None,
        'pending_invoice': invoice_to_dict(pending) if pending else None,
    }


def _save_customer(receiver):
    if receiver['doc_type'] is None:
        return None
    customer = FiscalCustomer.query.filter_by(doc_type=receiver['doc_type'],
                                              doc_number=receiver['doc_number']).first()
    if customer is None:
        customer = FiscalCustomer(doc_type=receiver['doc_type'], doc_number=receiver['doc_number'],
                                  created_at=now())
        db.session.add(customer)
    customer.name = receiver['name']
    customer.iva_condition = receiver['iva_condition']
    customer.address = receiver['address']
    customer.updated_at = now()
    db.session.flush()
    return customer


def _detail_fields(invoice, settings, associated=None):
    return {'number': invoice.number, 'voucher_date': invoice.voucher_date,
            'doc_type_code': invoice.receiver_doc_type, 'doc_number': invoice.receiver_doc_number,
            'total': invoice.total, 'net': invoice.net, 'iva': invoice.iva, 'iva_rate': invoice.iva_rate,
            'discriminated': _discriminated(settings),
            'receiver_iva_id': receivers.RECEIVER_IVA_IDS[invoice.receiver_iva_condition], 'associated': associated}


def resolve(invoice, gateway):
    """Decide un 'pending' preguntándole a ARCA si ese número quedó autorizado. No hace commit."""
    found = gateway.query(invoice.voucher_type, invoice.point_of_sale, invoice.number)
    if found is None:
        invoice.status = 'rejected'
        invoice.error = 'No llegó a ARCA'
        return invoice
    request = invoice.request or {}
    if found['total'] != Decimal(invoice.total).quantize(Decimal('0.01')) or \
            int(found['doc_number'] or 0) != int(request.get('DocNro') or 0):
        logger.error('ARCA tiene otro comprobante en %s: %s', invoice.label, found)
        invoice.status = 'rejected'
        invoice.error = 'ARCA tiene otro comprobante con ese número'
        invoice.arca_result = {'query': {k: str(v) for k, v in found.items()}}
        return invoice
    invoice.status = 'authorized'
    invoice.cae = found['cae']
    invoice.cae_due = found['cae_due']
    invoice.authorized_at = now()
    invoice.error = None
    return invoice


def _resolve_stale(settings, voucher_type, gateway):
    pending = Invoice.query.filter_by(environment=settings.environment, point_of_sale=settings.point_of_sale,
                                      voucher_type=voucher_type, status='pending').all()
    for invoice in pending:
        if invoice.created_at > now() - PENDING_GRACE:
            raise PosError('Hay una factura emitiéndose, probá en unos segundos')
        resolve(invoice, gateway)
        if invoice.status == 'authorized':
            print_invoice(invoice, None, settings)


def _reserve(user, settings, gateway, sale, kind, voucher_type, receiver, mode, lines, total, payments,
             related=None, customer=None):
    """Fase 1: número de ARCA + comprobante 'pending' con el pedido completo. Hace commit."""
    _resolve_stale(settings, voucher_type, gateway)
    number = gateway.last_authorized(settings.point_of_sale, voucher_type) + 1
    rate = Decimal(settings.default_iva_rate) if _discriminated(settings) else Decimal('0')
    net, iva = amounts.split_iva(total, rate, _discriminated(settings))
    invoice = Invoice(kind=kind, voucher_type=voucher_type, environment=settings.environment,
                      point_of_sale=settings.point_of_sale, number=number, sale_id=sale.id if sale else None,
                      related_invoice_id=related.id if related else None,
                      customer_id=customer.id if customer else None,
                      receiver_doc_type=receiver['doc_type_code'], receiver_doc_number=receiver['doc_number'],
                      receiver_name=receiver['name'], receiver_iva_condition=receiver['iva_condition'],
                      receiver_address=receiver['address'], detail_mode=mode, lines=lines, total=total, net=net,
                      iva=iva, iva_rate=rate, voucher_date=get_current_date_argentina(), status='pending',
                      request={}, created_by=user.id, created_at=now())
    associated = None
    if related is not None:
        associated = {'type': related.voucher_type, 'pos': related.point_of_sale, 'number': related.number,
                      'cuit': settings.cuit, 'date': related.voucher_date}
    invoice.request = wsfe.build_detail(_detail_fields(invoice, settings, associated))
    db.session.add(invoice)
    for payment_id, amount in payments:
        invoice.payments.append(InvoicePayment(payment_id=payment_id, amount=amount))
    db.session.commit()
    return invoice


def _request_cae(invoice, settings, gateway, user):
    """Fase 2: pedido de CAE. Siempre deja el comprobante guardado (commit)."""
    try:
        result = gateway.request_cae(invoice.point_of_sale, invoice.voucher_type, invoice.request)
    except ArcaUnavailable as exc:
        logger.warning('ARCA sin respuesta para %s: %s', invoice.label, exc)
        invoice.error = NOT_CONFIRMED
        db.session.commit()
        return invoice
    except ArcaRejected as exc:
        logger.warning('ARCA devolvió errores para %s: %s', invoice.label, exc)
        invoice.status = 'rejected'
        invoice.arca_result = {'errors': exc.errors}
        invoice.error = f'ARCA rechazó la factura: {exc.errors[0]["msg"]}' if exc.errors else UNAVAILABLE
        db.session.commit()
        return invoice
    invoice.arca_result = {'observations': result.observations, 'errors': result.errors}
    if result.result == 'A':
        invoice.status = 'authorized'
        invoice.cae = result.cae
        invoice.cae_due = result.cae_due
        invoice.authorized_at = now()
        invoice.error = None
        db.session.flush()
        print_invoice(invoice, user, settings)
    else:
        invoice.status = 'rejected'
        messages = [o['msg'] for o in result.observations] or [e['msg'] for e in result.errors]
        invoice.error = f'ARCA rechazó la factura: {"; ".join(messages) or "sin detalle"}'
    db.session.commit()
    return invoice


def print_invoice(invoice, user, settings=None):
    """Encola la impresión en la impresora de caja. Sin impresora, deja el aviso en `invoice.print_warning`
    (atributo de la instancia, no columna: solo vive en este pedido) y lo devuelve. No hace commit.
    `user` None (pendiente resuelto durante otra emisión): el trabajo queda a nombre de quien emitió."""
    settings = settings or fiscal_settings.get_settings()
    printer = print_service.cashier_printer()
    if printer is None:
        invoice.print_warning = 'No hay impresora de caja configurada'
        return invoice.print_warning
    author = user or SimpleNamespace(id=invoice.created_by)  # add_job solo usa user.id
    print_service.add_job('invoice', printer, author, invoice_document(invoice, settings), invoice.sale)
    invoice.print_warning = None
    return None


def _gateway_or_error(settings):
    try:
        return arca.get_gateway(settings)
    except ArcaUnavailable as exc:
        logger.warning('WSAA sin respuesta: %s', exc)
        raise PosError(UNAVAILABLE)
    except ArcaRejected as exc:
        raise PosError(f'ARCA rechazó el acceso: {exc.errors[0]["msg"]}')


def issue(user, sale_id, customer_data):
    settings = fiscal_settings.get_settings()
    fiscal_settings.require_ready(settings)
    gateway = _gateway_or_error(settings)  # WSAA antes del lock: el token se guarda con su propio commit
    try:
        settings = fiscal_settings.get_settings(lock=True)
        sale = load_sale(parse_id(sale_id, 'La venta'))
        if sale.status != 'closed':
            raise PosError('Solo se factura una venta cerrada')
        active = active_invoice(sale.id)
        if active is not None:
            raise PosError(f'La venta ya tiene la {active.label}')
        if pending_invoice(sale.id) is not None:
            raise PosError('Hay una factura sin confirmar en esta venta: verificala antes')
        external = _external_ids()
        payments = amounts.invoiceable_payments(sale, external)
        total = amounts.invoiceable_amount(sale, external)
        if not total:
            raise PosError('Todo lo cobrado en esta venta lo factura otro sistema')
        receiver = receivers.normalize_receiver(customer_data, total, settings.cf_id_threshold,
                                                settings.iva_condition)
        voucher_type = receivers.voucher_type_for(settings.iva_condition, receiver['iva_condition'])
        mode, lines = amounts.build_lines(sale, total, print_documents.item_description)
        customer = _save_customer(receiver)
        invoice = _reserve(user, settings, gateway, sale, 'invoice', voucher_type, receiver, mode, lines, total,
                           [(p.id, p.amount) for p in payments], customer=customer)
    except ArcaUnavailable as exc:
        db.session.rollback()
        logger.warning('ARCA sin respuesta al reservar: %s', exc)
        raise PosError(UNAVAILABLE)
    except ArcaRejected as exc:
        db.session.rollback()
        raise PosError(f'ARCA rechazó el pedido: {exc.errors[0]["msg"]}')
    return _request_cae(invoice, settings, gateway, user)


def _load_invoice(invoice_id):
    invoice = db.session.get(Invoice, parse_id(invoice_id, 'El comprobante'))
    if invoice is None:
        raise not_found('El comprobante no existe')
    return invoice


def verify(user, invoice_id):
    invoice = _load_invoice(invoice_id)
    if invoice.status != 'pending':
        return invoice
    settings = fiscal_settings.get_settings()
    gateway = _gateway_or_error(settings)
    try:
        resolve(invoice, gateway)
    except (ArcaUnavailable, ArcaRejected) as exc:
        db.session.rollback()
        logger.warning('No se pudo verificar %s: %s', invoice.label, exc)
        raise PosError(UNAVAILABLE)
    if invoice.status == 'authorized':
        print_invoice(invoice, user, settings)
    db.session.commit()
    return invoice


def reprint(user, invoice_id):
    invoice = _load_invoice(invoice_id)
    if invoice.status != 'authorized':
        raise PosError('Solo se reimprime un comprobante autorizado')
    warning = print_invoice(invoice, user)
    if warning:
        raise PosError(warning)
    db.session.commit()
    return invoice


def invoice_to_dict(invoice):
    credit_note = _authorized_credit_note(invoice) if invoice.kind == 'invoice' else None
    return {
        'id': invoice.id, 'kind': invoice.kind, 'voucher_type': invoice.voucher_type, 'letter': invoice.letter,
        'label': invoice.label, 'environment': invoice.environment, 'point_of_sale': invoice.point_of_sale,
        'number': invoice.number, 'sale_id': invoice.sale_id,
        'sale_number': invoice.sale.number if invoice.sale else None,
        'related_invoice_id': invoice.related_invoice_id,
        'related_label': invoice.related.label if invoice.related else None,
        'receiver': {'doc_type': invoice.receiver_doc_type, 'doc_number': invoice.receiver_doc_number,
                     'name': invoice.receiver_name, 'iva_condition': invoice.receiver_iva_condition,
                     'address': invoice.receiver_address},
        'detail_mode': invoice.detail_mode, 'lines': invoice.lines, 'total': f'{invoice.total:.2f}',
        'net': f'{invoice.net:.2f}', 'iva': f'{invoice.iva:.2f}', 'voucher_date': invoice.voucher_date.isoformat(),
        'status': invoice.status, 'cae': invoice.cae,
        'cae_due': invoice.cae_due.isoformat() if invoice.cae_due else None, 'error': invoice.error,
        'arca_result': invoice.arca_result, 'request': invoice.request,
        'created_at': invoice.created_at.isoformat(),
        'authorized_at': invoice.authorized_at.isoformat() if invoice.authorized_at else None,
        'is_active': invoice.kind == 'invoice' and invoice.status == 'authorized' and credit_note is None,
        'credit_note_label': credit_note.label if credit_note else None,
        'print_warning': getattr(invoice, 'print_warning', None),
    }
```

- [ ] **Step 6: Correr**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_fiscal_issue.py tests/test_fiscal_arca.py`
Expected: todos pasan.

Aclaración: `print_invoice` recibe `user=None` cuando resuelve un `pending` viejo durante otra emisión. En ese caso el trabajo queda a nombre de `created_by` del comprobante.

- [ ] **Step 7: Commit**

```bash
git -C <worktree> add backend/app/services/fiscal backend/app/services/pos/print_documents.py backend/tests/test_fiscal_issue.py
git -C <worktree> commit -m "feat(fiscal): two-phase invoice issuing with pending recovery and printed invoice"
```

---

### Task 6: Nota de crédito, bloqueos de anulación y campo `invoice` de la venta

**Files:**
- Create: `backend/app/services/fiscal/guard.py`, `backend/tests/test_fiscal_cancel.py`
- Modify:
  - `backend/app/services/fiscal/invoice_service.py` (`cancel`);
  - `backend/app/services/pos/sale_service.py` (`cancel_sale`), `backend/app/services/pos/payment_service.py` (`cancel_payment`);
  - `backend/app/services/pos/serializers.py` (`invoice`).

**Interfaces:**
- Consumes: `invoice_service._reserve`, `_request_cae`, `active_invoice`, `pending_invoice` (Task 5); `common.require_module`.
- Produces:
  - `invoice_service.cancel(user, invoice_id) -> Invoice`, la nota de crédito;
  - `guard.ensure_sale_can_be_cancelled(sale)` y `guard.ensure_payment_can_be_cancelled(payment)`, que lanzan `PosError` 409;
  - `guard.sale_invoice_summary(sale_id) -> {'id', 'label', 'status', 'is_active'} | None`;
  - `sale_to_dict(...)['invoice']`, solo cuando `include_items=True`.

- [ ] **Step 1: Tests que fallan.** Crear `backend/tests/test_fiscal_cancel.py`:

```python
import pytest

from app.models.pos import PrintJob
from app.services.fiscal import arca, invoice_service
from app.services.fiscal.arca.fake import FakeArca
from app.services.pos import payment_service, sale_service
from app.services.pos.errors import PosError
from app.services.pos.serializers import sale_to_dict
from fiscal_helpers import closed_sale, configure_fiscal
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401
from print_helpers import make_printer


@pytest.fixture
def ctx(pos_app, monkeypatch):
    FakeArca.reset()
    monkeypatch.setattr(arca, 'get_gateway', lambda settings: FakeArca())
    user = make_user('caja@test.com', modules=('POS', 'Anular'))
    cat = make_catalog()
    _salon, t1, t2 = make_floor()
    configure_fiscal()
    make_printer('Térmica caja', cashier=True)
    return user, cat, t1, t2


def test_credit_note_cancels_invoice_and_allows_reinvoicing(ctx):
    user, cat, t1, _t2 = ctx
    sale = closed_sale(user, cat, t1)
    invoice = invoice_service.issue(user, sale.id, None)
    credit = invoice_service.cancel(user, invoice.id)
    assert credit.status == 'authorized' and credit.voucher_type == 13 and credit.number == 1
    assert credit.related_invoice_id == invoice.id and credit.total == invoice.total
    assert credit.request['CbtesAsoc']['CbteAsoc'][0]['Nro'] == invoice.number
    assert invoice_service.active_invoice(sale.id) is None
    docs = [j.document['title'] for j in PrintJob.query.filter_by(kind='invoice').order_by(PrintJob.id)]
    assert docs == ['FACTURA C', 'NOTA DE CRÉDITO C']
    with pytest.raises(PosError):
        invoice_service.cancel(user, invoice.id)
    again = invoice_service.issue(user, sale.id, None)
    assert again.status == 'authorized' and again.number == 2


def test_credit_note_requires_anular(ctx):
    user, cat, t1, _t2 = ctx
    invoice = invoice_service.issue(user, closed_sale(user, cat, t1).id, None)
    cashier = make_user('caja2@test.com', modules=('POS',))
    with pytest.raises(PosError) as error:
        invoice_service.cancel(cashier, invoice.id)
    assert error.value.status == 403


def test_invoiced_sale_and_covered_payments_cannot_be_cancelled(ctx):
    user, cat, t1, t2 = ctx
    sale = closed_sale(user, cat, t1, amount_cash=1000, amount_card=800)
    invoice = invoice_service.issue(user, sale.id, None)
    cash_payment = next(p for p in sale.payments if p.payment_method_id == cat.efectivo.id)
    card_payment = next(p for p in sale.payments if p.payment_method_id == cat.debito.id)
    with pytest.raises(PosError) as error:
        payment_service.cancel_payment(user, cash_payment.id, 'Error')
    assert error.value.status == 409 and invoice.label in error.value.message
    with pytest.raises(PosError) as error:
        sale_service.cancel_sale(user, sale.id, 'Error')
    assert invoice.label in error.value.message
    payment_service.cancel_payment(user, card_payment.id, 'Se cobró mal')
    invoice_service.cancel(user, invoice.id)
    payment_service.cancel_payment(user, cash_payment.id, 'Ahora sí')


def test_pending_invoice_blocks_cancellation(ctx):
    user, cat, t1, _t2 = ctx
    FakeArca.reset('timeout')
    sale = closed_sale(user, cat, t1)
    invoice_service.issue(user, sale.id, None)
    with pytest.raises(PosError) as error:
        sale_service.cancel_sale(user, sale.id, 'Error')
    assert 'sin confirmar' in error.value.message


def test_sale_dict_carries_invoice_summary(ctx):
    user, cat, t1, _t2 = ctx
    sale = closed_sale(user, cat, t1)
    assert sale_to_dict(sale)['invoice'] is None
    invoice = invoice_service.issue(user, sale.id, None)
    summary = sale_to_dict(sale)['invoice']
    assert summary == {'id': invoice.id, 'label': invoice.label, 'status': 'authorized', 'is_active': True}
    assert 'invoice' not in sale_to_dict(sale, include_items=False)
```

- [ ] **Step 2: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_fiscal_cancel.py`
Expected: `AttributeError: ... 'cancel'` y fallas de bloqueo.

- [ ] **Step 3: Guard.** Crear `backend/app/services/fiscal/guard.py`:

```python
"""Bloqueos de la venta por facturas: no se anula lo que tiene una factura vigente o sin confirmar."""
from app.models import Invoice, InvoicePayment
from app.services.pos.errors import PosError


def _active(sale_id):
    for invoice in Invoice.query.filter_by(sale_id=sale_id, kind='invoice', status='authorized') \
            .order_by(Invoice.id.desc()):
        if Invoice.query.filter_by(related_invoice_id=invoice.id, status='authorized').first() is None:
            return invoice
    return None


def _pending(sale_id):
    return Invoice.query.filter_by(sale_id=sale_id, status='pending').first()


def ensure_sale_can_be_cancelled(sale):
    if _pending(sale.id) is not None:
        raise PosError('Hay una factura sin confirmar en esta venta: verificala antes')
    active = _active(sale.id)
    if active is not None:
        raise PosError(f'La venta tiene la {active.label}: anulala con una nota de crédito antes')


def ensure_payment_can_be_cancelled(payment):
    if _pending(payment.sale_id) is not None:
        raise PosError('Hay una factura sin confirmar en esta venta: verificala antes')
    active = _active(payment.sale_id)
    if active is not None and InvoicePayment.query.filter_by(invoice_id=active.id,
                                                             payment_id=payment.id).first():
        raise PosError(f'La venta tiene la {active.label}: anulala con una nota de crédito antes')


def sale_invoice_summary(sale_id):
    invoice = _pending(sale_id) or _active(sale_id)
    if invoice is None:
        return None
    return {'id': invoice.id, 'label': invoice.label, 'status': invoice.status,
            'is_active': invoice.status == 'authorized'}
```

- [ ] **Step 4: Bloqueos y serializador.**
  - En `backend/app/services/pos/sale_service.py`, en `cancel_sale`, después de `sale = load_sale(sale_id)`, agregar:

```python
    guard.ensure_sale_can_be_cancelled(sale)
```

  y el import `from app.services.fiscal import guard` (junto a los demás imports).
  - En `backend/app/services/pos/payment_service.py`, en `cancel_payment`, después de `db.session.refresh(payment)`, agregar `guard.ensure_payment_can_be_cancelled(payment)` con el mismo import.
  - En `backend/app/services/pos/serializers.py`, dentro de `if include_items:` de `sale_to_dict`, agregar:

```python
        data['invoice'] = guard.sale_invoice_summary(sale.id)
```

  con `from app.services.fiscal import guard` al principio del archivo. `guard` solo importa modelos y errores, así que no hay import circular.

- [ ] **Step 5: Nota de crédito.** En `backend/app/services/fiscal/invoice_service.py`, agregar `from app.services.pos.common import require_module` (sumarlo al import existente de `common`) y al final:

```python
def cancel(user, invoice_id):
    """'Anular factura': nota de crédito por el total de una factura vigente."""
    require_module(user, 'Anular', 'No tenés permiso para anular facturas')
    settings = fiscal_settings.get_settings()
    fiscal_settings.require_ready(settings)
    gateway = _gateway_or_error(settings)
    try:
        settings = fiscal_settings.get_settings(lock=True)
        invoice = db.session.get(Invoice, parse_id(invoice_id, 'El comprobante'))
        if invoice is None:
            raise not_found('El comprobante no existe')
        if invoice.kind != 'invoice' or invoice.status != 'authorized' or _authorized_credit_note(invoice):
            raise PosError('Solo se anula una factura vigente')
        if Invoice.query.filter_by(related_invoice_id=invoice.id, status='pending').first():
            raise PosError('Hay una nota de crédito sin confirmar para esta factura: verificala antes')
        if invoice.environment != settings.environment:
            raise PosError('La factura es de otro entorno: cambiá el entorno en Ajustes → Facturación')
        voucher_type = receivers.voucher_type_for(settings.iva_condition, invoice.receiver_iva_condition,
                                                  credit_note=True)
        receiver = {'doc_type_code': invoice.receiver_doc_type, 'doc_number': invoice.receiver_doc_number,
                    'name': invoice.receiver_name, 'iva_condition': invoice.receiver_iva_condition,
                    'address': invoice.receiver_address}
        credit = _reserve(user, settings, gateway, invoice.sale, 'credit_note', voucher_type, receiver,
                          invoice.detail_mode, invoice.lines, Decimal(invoice.total),
                          [(p.payment_id, p.amount) for p in invoice.payments], related=invoice,
                          customer=db.session.get(FiscalCustomer, invoice.customer_id)
                          if invoice.customer_id else None)
    except ArcaUnavailable as exc:
        db.session.rollback()
        logger.warning('ARCA sin respuesta al reservar la nota de crédito: %s', exc)
        raise PosError(UNAVAILABLE)
    except ArcaRejected as exc:
        db.session.rollback()
        raise PosError(f'ARCA rechazó el pedido: {exc.errors[0]["msg"]}')
    return _request_cae(credit, settings, gateway, user)
```

- [ ] **Step 6: Correr**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_fiscal_cancel.py tests/test_fiscal_issue.py tests/test_pos_cancellations.py tests/test_pos_payments.py tests/test_pos_cash_payments.py tests/test_pos_sales_api.py`
Expected: todos pasan (si `test_pos_sales_api.py` no existe con ese nombre, correr `tests/test_pos_*.py`).

- [ ] **Step 7: Commit**

```bash
git -C <worktree> add backend/app/services backend/tests/test_fiscal_cancel.py
git -C <worktree> commit -m "feat(fiscal): credit notes and cancellation guards for invoiced sales"
```

---

### Task 7: API de facturación y configuración

**Files:**
- Create: `backend/app/routes/fiscal.py`, `backend/tests/test_fiscal_api.py`, `backend/tests/test_fiscal_concurrency_pg.py`, `backend/tests/test_fiscal_homologacion.py`
- Modify: `backend/app/__init__.py`, `backend/app/services/fiscal/invoice_service.py` (`list_invoices`, `search_customers`), `backend/app/services/fiscal/settings.py` (`update_settings`)

**Interfaces:**
- Consumes: todo `invoice_service`, `settings`, `arca` (Tasks 3 a 6).
- Produces: las rutas de la tabla del spec, con prefijo `/api/v1/fiscal`:
  - **Ventas** (POS):
    - `GET /sales/<id>/preview` → `preview()`;
    - `POST /sales/<id>/invoice` → `invoice_to_dict`, con 201, 202 o 409 (este último con `{'error', 'invoice'}`);
    - `GET /sales/<id>/invoices` → `{'invoices': [...]}`.
  - **Comprobantes:**
    - `POST /invoices/<id>/verify` (POS) → dict;
    - `POST /invoices/<id>/cancel` (POS; además "Anular" en el servicio) → dict, con 201, 202 o 409;
    - `POST /invoices/<id>/reprint` (POS) → dict;
    - `GET /invoices?from=YYYY-MM-DD&to=YYYY-MM-DD&kind=&status=&page=` (POS) → `{'invoices', 'page', 'pages', 'total', 'environment'}`;
    - `GET /invoices/<id>` (POS) → dict.
  - **Clientes:** `GET /customers?q=` (POS) → `{'customers': [...]}`.
  - **Configuración** (admin):
    - `GET /settings` → `settings_to_dict`, o los valores vacíos con `missing`;
    - `PUT /settings` → `settings_to_dict`;
    - `POST /settings/<env>/csr` → `{'csr': pem}`;
    - `PUT /settings/<env>/certificate {certificate}` → `settings_to_dict`;
    - `POST /settings/test` → `{'ok': True, 'last_number': n, 'label': 'Último comprobante: C 00005-00000041'}`.

- [ ] **Step 1: Tests que fallan.** Crear `backend/tests/test_fiscal_api.py`:

```python
import pytest

from app.extensions import db
from app.services.fiscal import arca
from app.services.fiscal.arca.fake import FakeArca
from fiscal_helpers import closed_sale, configure_fiscal, make_key_and_cert
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401
from print_helpers import make_printer

BASE = '/api/v1/fiscal'


@pytest.fixture
def ctx(pos_app, monkeypatch):
    FakeArca.reset()
    monkeypatch.setattr(arca, 'get_gateway', lambda settings: FakeArca())
    client = pos_app.test_client()
    user = make_user('caja@test.com', modules=('POS', 'Anular'))
    headers = auth_headers(client, user)
    cat = make_catalog()
    _salon, t1, t2 = make_floor()
    make_printer('Térmica caja', cashier=True)
    return client, headers, user, cat, t1, t2


def test_invoice_flow_through_the_api(ctx):
    client, headers, user, cat, t1, _t2 = ctx
    configure_fiscal()
    sale = closed_sale(user, cat, t1)
    preview = client.get(f'{BASE}/sales/{sale.id}/preview', headers=headers).get_json()
    assert preview['amount'] == '1800.00' and preview['ready'] is True
    issued = client.post(f'{BASE}/sales/{sale.id}/invoice', json={'customer': {
        'doc_type': 'CUIT', 'doc_number': '20123456786', 'name': 'Cliente SA',
        'iva_condition': 'responsable_inscripto'}}, headers=headers)
    assert issued.status_code == 201 and issued.get_json()['label'] == 'Factura C 00005-00000001'
    invoice_id = issued.get_json()['id']
    sale_data = client.get(f'/api/v1/pos/sales/{sale.id}', headers=headers).get_json()
    assert sale_data['invoice']['label'] == 'Factura C 00005-00000001'
    customers = client.get(f'{BASE}/customers?q=2012', headers=headers).get_json()['customers']
    assert customers[0]['name'] == 'Cliente SA'
    assert client.get(f'{BASE}/customers?q=clie', headers=headers).get_json()['customers'][0]['doc_type'] == 'CUIT'
    assert client.post(f'{BASE}/invoices/{invoice_id}/reprint', headers=headers).status_code == 200
    listed = client.get(f'{BASE}/invoices', headers=headers).get_json()
    assert listed['total'] == 1 and listed['environment'] == 'homologacion'
    cancelled = client.post(f'{BASE}/invoices/{invoice_id}/cancel', headers=headers)
    assert cancelled.status_code == 201 and cancelled.get_json()['kind'] == 'credit_note'
    filtered = client.get(f'{BASE}/invoices?kind=credit_note', headers=headers).get_json()
    assert [i['kind'] for i in filtered['invoices']] == ['credit_note']
    assert len(client.get(f'{BASE}/sales/{sale.id}/invoices', headers=headers).get_json()['invoices']) == 2


def test_pending_and_rejected_status_codes(ctx):
    client, headers, user, cat, t1, t2 = ctx
    configure_fiscal()
    FakeArca.reset('reject')
    rejected = client.post(f'{BASE}/sales/{closed_sale(user, cat, t1).id}/invoice', json={}, headers=headers)
    assert rejected.status_code == 409 and 'ARCA rechazó' in rejected.get_json()['error']
    FakeArca.reset('timeout')
    pending = client.post(f'{BASE}/sales/{closed_sale(user, cat, t2).id}/invoice', json={}, headers=headers)
    assert pending.status_code == 202 and pending.get_json()['status'] == 'pending'
    FakeArca.mode = 'approve'
    verified = client.post(f"{BASE}/invoices/{pending.get_json()['id']}/verify", headers=headers)
    assert verified.status_code == 200 and verified.get_json()['status'] == 'rejected'


def test_unconfigured_and_validation_errors(ctx):
    client, headers, user, cat, t1, _t2 = ctx
    sale = closed_sale(user, cat, t1)
    response = client.post(f'{BASE}/sales/{sale.id}/invoice', json={}, headers=headers)
    assert response.status_code == 409 and response.get_json()['error'].startswith('Falta configurar')
    configure_fiscal()
    bad = client.post(f'{BASE}/sales/{sale.id}/invoice', json={'customer': {'doc_type': 'DNI',
                                                                          'doc_number': '1'}}, headers=headers)
    assert bad.status_code == 400


def test_permissions(ctx):
    client, _headers, user, cat, t1, _t2 = ctx
    configure_fiscal()
    waiter = auth_headers(client, make_user('mozo@test.com', modules=('Camarero', 'Cobrar')))
    sale = closed_sale(user, cat, t1)
    assert client.get(f'{BASE}/sales/{sale.id}/preview', headers=waiter).status_code == 403
    assert client.get(f'{BASE}/settings', headers=waiter).status_code == 403
    pos_only = auth_headers(client, make_user('caja2@test.com', modules=('POS',)))
    invoice_id = client.post(f'{BASE}/sales/{sale.id}/invoice', json={}, headers=pos_only).get_json()['id']
    assert client.post(f'{BASE}/invoices/{invoice_id}/cancel', headers=pos_only).status_code == 403
    assert client.get(f'{BASE}/settings', headers=pos_only).status_code == 403


def test_settings_admin_flow(ctx):
    client, _headers, *_rest = ctx
    admin = auth_headers(client, make_user('admin@test.com', role='admin'))
    empty = client.get(f'{BASE}/settings', headers=admin).get_json()
    assert empty['missing'] and empty['environment'] == 'homologacion'
    bad = client.put(f'{BASE}/settings', json={'cuit': '20123456780'}, headers=admin)
    assert bad.status_code == 400
    saved = client.put(f'{BASE}/settings', json={
        'cuit': '20123456786', 'business_name': 'Galia Café', 'address': 'Calle 1', 'gross_income': 'Exento',
        'activity_start': '2020-01-01', 'iva_condition': 'monotributo', 'point_of_sale': 5,
        'cf_id_threshold': '10000000', 'default_iva_rate': '21'}, headers=admin)
    assert saved.status_code == 200 and saved.get_json()['missing'] == ['certificado de homologación']
    csr = client.post(f'{BASE}/settings/homologacion/csr', headers=admin).get_json()['csr']
    assert csr.startswith('-----BEGIN CERTIFICATE REQUEST-----')
    _key, other_cert = make_key_and_cert()
    wrong = client.put(f'{BASE}/settings/homologacion/certificate', json={'certificate': other_cert}, headers=admin)
    assert wrong.status_code == 400 and 'no corresponde' in wrong.get_json()['error']
    assert client.post(f'{BASE}/settings/staging/csr', headers=admin).status_code == 400
    assert client.put(f'{BASE}/settings', json={'environment': 'produccion'}, headers=admin).status_code == 200
    assert client.put(f'{BASE}/settings', json={'point_of_sale': 0}, headers=admin).status_code == 400


def test_connection_test_endpoint(ctx):
    client, _headers, *_rest = ctx
    configure_fiscal()
    admin = auth_headers(client, make_user('admin@test.com', role='admin'))
    result = client.post(f'{BASE}/settings/test', headers=admin).get_json()
    assert result == {'ok': True, 'last_number': 0, 'label': 'Último comprobante: C 00005-00000000'}
```

Crear `backend/tests/test_fiscal_concurrency_pg.py`:

```python
import os
import threading

import pytest

from app import create_app
from app.config import Config, config
from app.extensions import db
from app.models import Invoice
from app.services.fiscal import arca, invoice_service
from app.services.fiscal.arca.fake import FakeArca
from app.services.pos.errors import PosError
from fiscal_helpers import closed_sale, configure_fiscal
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


def test_two_cashiers_never_get_the_same_number(pg_app, monkeypatch):
    FakeArca.reset()
    monkeypatch.setattr(arca, 'get_gateway', lambda settings: FakeArca())
    with pg_app.app_context():
        user = make_user('caja@test.com', modules=('POS',))
        cat = make_catalog()
        _salon, t1, t2 = make_floor()
        configure_fiscal()
        sale_ids = [closed_sale(user, cat, t1).id, closed_sale(user, cat, t2).id]
        user_id = user.id

    barrier = threading.Barrier(2)
    results = [None, None]

    def run(index):
        with pg_app.app_context():
            from app.models import User
            barrier.wait()
            try:
                results[index] = invoice_service.issue(db.session.get(User, user_id), sale_ids[index], None).status
            except PosError as exc:
                results[index] = exc.message
            db.session.remove()

    threads = [threading.Thread(target=run, args=(i,)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    with pg_app.app_context():
        numbers = [i.number for i in Invoice.query.filter_by(status='authorized')]
    assert len(numbers) == len(set(numbers)) and numbers
    assert all(r == 'authorized' or 'emitiéndose' in r for r in results)
```

Crear `backend/tests/test_fiscal_homologacion.py`:

```python
"""Emite una Factura C y su nota de crédito reales en homologación de ARCA. Solo con credenciales de prueba."""
import os

import pytest

from app.extensions import db
from app.services.fiscal import invoice_service
from app.services.fiscal import settings as fs
from fiscal_helpers import closed_sale
from pos_helpers import make_catalog, make_floor, make_user, pos_app  # noqa: F401
from print_helpers import make_printer

NEEDED = ('ARCA_HOMO_CUIT', 'ARCA_HOMO_CERT', 'ARCA_HOMO_KEY', 'ARCA_HOMO_POS')
pytestmark = pytest.mark.skipif(not all(os.getenv(n) for n in NEEDED),
                                reason='Sin credenciales de homologación de ARCA')


def test_real_invoice_and_credit_note_in_homologacion(pos_app):
    settings = fs.get_or_create_settings()
    settings.cuit = os.environ['ARCA_HOMO_CUIT']
    settings.business_name = 'Galia (prueba)'
    settings.address = 'Prueba 123'
    settings.activity_start = __import__('datetime').date(2020, 1, 1)
    settings.point_of_sale = int(os.environ['ARCA_HOMO_POS'])
    settings.environment = 'homologacion'
    settings.homo_private_key = fs.encrypt_key(open(os.environ['ARCA_HOMO_KEY']).read())
    fs.save_certificate(settings, 'homologacion', open(os.environ['ARCA_HOMO_CERT']).read())
    db.session.commit()
    user = make_user('caja@test.com', modules=('POS', 'Anular'))
    cat = make_catalog()
    _salon, t1, _t2 = make_floor()
    make_printer('Térmica caja', cashier=True)
    invoice = invoice_service.issue(user, closed_sale(user, cat, t1).id, None)
    assert invoice.status == 'authorized', invoice.error
    credit = invoice_service.cancel(user, invoice.id)
    assert credit.status == 'authorized', credit.error
```

- [ ] **Step 2: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_fiscal_api.py`
Expected: 404 en las rutas.

- [ ] **Step 3: Listado, clientes y configuración (servicio).** Agregar al final de `backend/app/services/fiscal/invoice_service.py`:

```python
LIST_PAGE_SIZE = 50


def list_invoices(date_from=None, date_to=None, kind=None, status=None, page=1):
    """Comprobantes del entorno activo, más nuevos primero. Fechas por día de comprobante (Argentina)."""
    settings = fiscal_settings.get_settings()
    environment = settings.environment if settings else 'homologacion'
    query = Invoice.query.filter_by(environment=environment)
    if date_from:
        query = query.filter(Invoice.voucher_date >= date_from)
    if date_to:
        query = query.filter(Invoice.voucher_date <= date_to)
    if kind in ('invoice', 'credit_note'):
        query = query.filter_by(kind=kind)
    if status in ('pending', 'authorized', 'rejected'):
        query = query.filter_by(status=status)
    total = query.count()
    rows = query.order_by(Invoice.id.desc()).offset((page - 1) * LIST_PAGE_SIZE).limit(LIST_PAGE_SIZE).all()
    return {'invoices': [invoice_to_dict(i) for i in rows], 'page': page,
            'pages': max(1, -(-total // LIST_PAGE_SIZE)), 'total': total, 'environment': environment}


def sale_invoices(sale_id):
    rows = Invoice.query.filter_by(sale_id=parse_id(sale_id, 'La venta')).order_by(Invoice.id).all()
    return [invoice_to_dict(i) for i in rows]


def get_invoice(invoice_id):
    return invoice_to_dict(_load_invoice(invoice_id))


def search_customers(q):
    text = (q or '').strip()
    if len(text) < 2:
        return []
    digits = ''.join(ch for ch in text if ch.isdigit())
    query = FiscalCustomer.query
    if digits and len(digits) == len(text.replace('-', '').replace('.', '')):
        query = query.filter(FiscalCustomer.doc_number.startswith(digits))
    else:
        query = query.filter(FiscalCustomer.name.ilike(f'%{text}%'))
    return [c.to_dict() for c in query.order_by(FiscalCustomer.name).limit(10)]


def test_connection():
    settings = fiscal_settings.get_settings()
    fiscal_settings.require_ready(settings)
    gateway = _gateway_or_error(settings)
    voucher_type = receivers.voucher_type_for(settings.iva_condition, 'consumidor_final')
    try:
        gateway.dummy()
        last = gateway.last_authorized(settings.point_of_sale, voucher_type)
    except ArcaUnavailable:
        raise PosError(UNAVAILABLE)
    except ArcaRejected as exc:
        raise PosError(f'ARCA respondió: {exc.errors[0]["msg"]}')
    letter = VOUCHER_TYPES[voucher_type][1]
    return {'ok': True, 'last_number': last,
            'label': f'Último comprobante: {letter} {settings.point_of_sale:05d}-{last:08d}'}
```

`test_connection` empieza con `test_`, pero pytest no lo recoge porque vive en `app/`.

Agregar al final de `backend/app/services/fiscal/settings.py`:

```python
from datetime import date  # noqa: E402
from decimal import Decimal, InvalidOperation  # noqa: E402

from app.models.fiscal import EMITTER_CONDITIONS  # noqa: E402
from app.services.fiscal.receivers import valid_cuit  # noqa: E402
from app.utils.validation import clean_str  # noqa: E402


def _decimal(value, label, minimum=Decimal('0')):
    if value in (None, ''):
        return None
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        raise bad_request(f'{label} es inválido')
    if number < minimum:
        raise bad_request(f'{label} es inválido')
    return number


def update_settings(data):
    settings = get_or_create_settings()
    if 'cuit' in data:
        cuit = ''.join(ch for ch in str(data['cuit'] or '') if ch.isdigit())
        if not valid_cuit(cuit):
            raise bad_request('El CUIT es inválido')
        settings.cuit = cuit
    for field, limit in (('business_name', 120), ('address', 200), ('gross_income', 40)):
        if field in data:
            setattr(settings, field, clean_str(data[field], limit))
    if 'activity_start' in data:
        try:
            settings.activity_start = date.fromisoformat(data['activity_start']) if data['activity_start'] else None
        except (TypeError, ValueError):
            raise bad_request('La fecha de inicio de actividades es inválida')
    if 'iva_condition' in data:
        if data['iva_condition'] not in EMITTER_CONDITIONS:
            raise bad_request('La condición frente al IVA es inválida')
        settings.iva_condition = data['iva_condition']
    if 'point_of_sale' in data:
        value = data['point_of_sale']
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 99999:
            raise bad_request('El punto de venta tiene que ser un número entre 1 y 99999')
        settings.point_of_sale = value
    if 'environment' in data:
        _check_environment(data['environment'])
        settings.environment = data['environment']
    if 'cf_id_threshold' in data:
        settings.cf_id_threshold = _decimal(data['cf_id_threshold'], 'El umbral de identificación')
    if 'default_iva_rate' in data:
        rate = _decimal(data['default_iva_rate'], 'La alícuota de IVA')
        if rate not in (Decimal('0'), Decimal('10.5'), Decimal('21'), Decimal('27')):
            raise bad_request('La alícuota tiene que ser 0, 10,5, 21 o 27')
        settings.default_iva_rate = rate
    settings.updated_at = now()
    return settings
```

(Si al implementarlo las líneas `# noqa: E402` molestan, mover esos imports al bloque de imports de arriba: no hay ciclo, porque `receivers` no importa `settings`.)

- [ ] **Step 4: Rutas.** Crear `backend/app/routes/fiscal.py`:

```python
"""API de facturación electrónica ARCA."""
import logging
from datetime import date

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import DataError, IntegrityError

from app.extensions import db
from app.services.fiscal import invoice_service
from app.services.fiscal import settings as fiscal_settings
from app.services.pos.errors import PosError, bad_request
from app.utils.decorators import admin_required, module_required
from app.utils.jwt_utils import token_required
from app.utils.validation import json_object

logger = logging.getLogger(__name__)
bp = Blueprint('fiscal', __name__, url_prefix='/api/v1/fiscal')
STATUS_CODES = {'authorized': 201, 'pending': 202}


def _body():
    return json_object() or {}


def _run(action, status=200):
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
        return jsonify({'error': 'Otra operación modificó la facturación al mismo tiempo, probá de nuevo'}), 409
    except DataError:
        db.session.rollback()
        return jsonify({'error': 'Algún valor es demasiado grande'}), 400
    except Exception:
        db.session.rollback()
        logger.exception('Error inesperado en la facturación')
        return jsonify({'error': 'Error interno, probá de nuevo'}), 500
    return jsonify(payload), status


def _issued(action):
    """Emisión: 201 autorizado, 202 pendiente, 409 rechazado (con el comprobante)."""
    def wrapped():
        invoice = action()
        data = invoice_service.invoice_to_dict(invoice)
        if invoice.status == 'rejected':
            raise PosError(invoice.error or 'ARCA rechazó el comprobante', invoice=data)
        return data
    response = _run(wrapped)
    body, code = response
    if code == 200:
        return body, STATUS_CODES.get(body.get_json()['status'], 200)
    return response


def _date_arg(name):
    value = request.args.get(name)
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise bad_request('La fecha es inválida')


@bp.route('/sales/<int:sale_id>/preview', methods=['GET'])
@token_required
@module_required('POS')
def preview(current_user, sale_id):
    return _run(lambda: invoice_service.preview(sale_id))


@bp.route('/sales/<int:sale_id>/invoice', methods=['POST'])
@token_required
@module_required('POS')
def issue(current_user, sale_id):
    return _issued(lambda: invoice_service.issue(current_user, sale_id, _body().get('customer')))


@bp.route('/sales/<int:sale_id>/invoices', methods=['GET'])
@token_required
@module_required('POS')
def sale_invoices(current_user, sale_id):
    return _run(lambda: {'invoices': invoice_service.sale_invoices(sale_id)})


@bp.route('/invoices/<int:invoice_id>/verify', methods=['POST'])
@token_required
@module_required('POS')
def verify(current_user, invoice_id):
    return _run(lambda: invoice_service.invoice_to_dict(invoice_service.verify(current_user, invoice_id)))


@bp.route('/invoices/<int:invoice_id>/cancel', methods=['POST'])
@token_required
@module_required('POS')
def cancel(current_user, invoice_id):
    return _issued(lambda: invoice_service.cancel(current_user, invoice_id))


@bp.route('/invoices/<int:invoice_id>/reprint', methods=['POST'])
@token_required
@module_required('POS')
def reprint(current_user, invoice_id):
    return _run(lambda: invoice_service.invoice_to_dict(invoice_service.reprint(current_user, invoice_id)))


@bp.route('/invoices', methods=['GET'])
@token_required
@module_required('POS')
def list_invoices(current_user):
    def action():
        page = request.args.get('page', '1')
        if not page.isdigit() or int(page) < 1:
            raise bad_request('La página es inválida')
        return invoice_service.list_invoices(_date_arg('from'), _date_arg('to'), request.args.get('kind'),
                                             request.args.get('status'), int(page))
    return _run(action)


@bp.route('/invoices/<int:invoice_id>', methods=['GET'])
@token_required
@module_required('POS')
def get_invoice(current_user, invoice_id):
    return _run(lambda: invoice_service.get_invoice(invoice_id))


@bp.route('/customers', methods=['GET'])
@token_required
@module_required('POS')
def customers(current_user):
    return _run(lambda: {'customers': invoice_service.search_customers(request.args.get('q'))})


@bp.route('/settings', methods=['GET'])
@token_required
@admin_required
def get_settings(current_user):
    def action():
        settings = fiscal_settings.get_or_create_settings()
        db.session.commit()
        return fiscal_settings.settings_to_dict(settings)
    return _run(action)


@bp.route('/settings', methods=['PUT'])
@token_required
@admin_required
def put_settings(current_user):
    def action():
        settings = fiscal_settings.update_settings(_body())
        db.session.commit()
        return fiscal_settings.settings_to_dict(settings)
    return _run(action)


@bp.route('/settings/<environment>/csr', methods=['POST'])
@token_required
@admin_required
def generate_csr(current_user, environment):
    def action():
        csr = fiscal_settings.generate_csr(fiscal_settings.get_or_create_settings(), environment)
        db.session.commit()
        return {'csr': csr}
    return _run(action)


@bp.route('/settings/<environment>/certificate', methods=['PUT'])
@token_required
@admin_required
def save_certificate(current_user, environment):
    def action():
        settings = fiscal_settings.get_or_create_settings()
        fiscal_settings.save_certificate(settings, environment, _body().get('certificate'))
        db.session.commit()
        return fiscal_settings.settings_to_dict(settings)
    return _run(action)


@bp.route('/settings/test', methods=['POST'])
@token_required
@admin_required
def test_connection(current_user):
    return _run(invoice_service.test_connection)
```

En `backend/app/__init__.py`, sumar `fiscal` a la lista del `from app.routes import …` y, después de `app.register_blueprint(pos_print.bp)`:

```python
    app.register_blueprint(fiscal.bp)
```

- [ ] **Step 5: Correr**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_fiscal_api.py tests/test_fiscal_concurrency_pg.py tests/test_fiscal_homologacion.py tests/test_route_access_coverage.py`
Expected: pasan; los de PostgreSQL y homologación quedan `skipped`.

- [ ] **Step 6: Suite completa contra la línea base** (cwd `backend/`):

```
PY -m pytest -q -p no:cacheprovider -rfE > <scratch>/fiscal_pytest.txt
PY scripts/compare_baseline.py <scratch>/fiscal_pytest.txt ../docs/superpowers/plans/2026-10-08-pos-base-test-baseline.txt
```

Expected: `Sin fallas nuevas.`

- [ ] **Step 7: Commit**

```bash
git -C <worktree> add backend/app/routes/fiscal.py backend/app/__init__.py backend/app/services/fiscal backend/tests/test_fiscal_api.py backend/tests/test_fiscal_concurrency_pg.py backend/tests/test_fiscal_homologacion.py
git -C <worktree> commit -m "feat(fiscal): invoicing and settings API"
```

---

### Task 8: Frontend, datos: cliente de la API, formulario de factura y QR en ESC/POS

**Files:**
- Create: `frontend/src/pos/fiscal/invoiceForm.js`, `frontend/src/pos/fiscal/invoiceForm.test.js`
- Modify:
  - `frontend/src/pos/api/posApi.js`, `frontend/src/pos/hooks/keys.js`;
  - `frontend/src/pos/print/escpos.js`, `escpos.test.js`, `printStatus.js`;
  - `frontend/src/pos/utils/permissions.js`, `permissions.test.js`.

**Interfaces:**
- Consumes: la API de la Task 7.
- Produces:
  - **`posFiscalApi`:**
    - de la venta: `preview(saleId)`, `issue(saleId, customer)`, `saleInvoices(saleId)`;
    - de los comprobantes: `verify(id)`, `cancel(id)`, `reprint(id)`, `list(params)`, `get(id)`;
    - de clientes: `customers(q)`;
    - de configuración: `settings()`, `saveSettings(body)`, `generateCsr(env)`, `saveCertificate(env, certificate)`, `testConnection()`.
  - **`posKeys`:** `fiscalPreview(id)`, `fiscalSaleInvoices(id)`, `fiscalInvoices(params)`, `fiscalSettings`.
  - **`invoiceForm`:**
    - `cuitIsValid(digits)`;
    - `validateCustomer(form) -> string | null` (mensaje de error);
    - `customerPayload(form) -> object | null` (`null` = consumidor final);
    - `previewSummary(preview) -> string`;
    - `DOC_TYPES`, `IVA_CONDITIONS` (opciones con etiqueta).
  - **`escpos`:** `qrCommand(data) -> string`. `renderEscPos` imprime el QR si `doc.qr`; `renderText` agrega la línea `QR: <url>`.
  - **`saleActions`:**
    - `invoice`: `perms.pos`, venta `closed` y sin `sale.invoice`;
    - `invoiceActions`: `perms.pos` con `sale.invoice`;
    - `cancelInvoice`: `perms.pos && perms.cancel` con `sale.invoice?.is_active`.

- [ ] **Step 1: Tests que fallan.** Crear `frontend/src/pos/fiscal/invoiceForm.test.js`:

```js
import { describe, expect, it } from 'vitest'
import { cuitIsValid, customerPayload, previewSummary, validateCustomer } from './invoiceForm'

const base = { mode: 'identified', docType: 'DNI', docNumber: '30.123.456', name: 'Ana', ivaCondition: 'consumidor_final', address: '' }

describe('cuitIsValid', () => {
  it('valida el dígito verificador', () => {
    expect(cuitIsValid('20123456786')).toBe(true)
    expect(cuitIsValid('20123456780')).toBe(false)
    expect(cuitIsValid('201234')).toBe(false)
  })
})

describe('validateCustomer', () => {
  it('acepta consumidor final y un DNI válido', () => {
    expect(validateCustomer({ mode: 'anonymous' })).toBeNull()
    expect(validateCustomer(base)).toBeNull()
  })
  it('rechaza datos incompletos o inválidos', () => {
    expect(validateCustomer({ ...base, docNumber: '123' })).toBe('El DNI tiene que tener 7 u 8 dígitos')
    expect(validateCustomer({ ...base, docType: 'CUIT', docNumber: '20-12345678-0' })).toBe('El CUIT es inválido')
    expect(validateCustomer({ ...base, name: ' ' })).toBe('Indicá el nombre o la razón social')
    expect(validateCustomer({ ...base, ivaCondition: 'monotributo' })).toBe('Para esa condición hace falta el CUIT')
  })
})

describe('customerPayload', () => {
  it('limpia el documento y devuelve null para consumidor final', () => {
    expect(customerPayload({ mode: 'anonymous' })).toBeNull()
    expect(customerPayload({ ...base, address: ' Calle 1 ' })).toEqual({
      doc_type: 'DNI', doc_number: '30123456', name: 'Ana', iva_condition: 'consumidor_final', address: 'Calle 1',
    })
  })
})

describe('previewSummary', () => {
  it('explica qué se factura', () => {
    expect(previewSummary({ amount: '18000.00', total: '18000.00', detail_mode: 'items' })).toBe('Se facturan los ítems · $ 18.000')
    expect(previewSummary({ amount: '10000.00', total: '18000.00', detail_mode: 'generic' }))
      .toBe('Se factura $ 10.000 de $ 18.000 (lo demás lo factura otro sistema)')
    expect(previewSummary({ amount: '0.00', total: '18000.00', detail_mode: null }))
      .toBe('Todo lo cobrado en esta venta lo factura otro sistema')
  })
})
```

En `frontend/src/pos/print/escpos.test.js`, agregar al final:

```js
describe('QR de ARCA', () => {
  it('arma la secuencia GS ( k con el largo correcto y muestra la URL en simulación', () => {
    const url = 'https://www.afip.gob.ar/fe/qr/?p=abc'
    const cmd = qrCommand(url)
    expect(cmd.startsWith('\x1d(k\x04\x001A2\x00')).toBe(true)
    const len = url.length + 3
    expect(cmd).toContain(`\x1d(k${String.fromCharCode(len % 256)}${String.fromCharCode(Math.floor(len / 256))}1P0${url}`)
    expect(cmd.endsWith('\x1d(k\x03\x001Q0')).toBe(true)
    const doc = { ...bill, qr: url }
    expect(renderEscPos(doc, 80)).toContain(cmd)
    expect(renderText(doc, 80).join('\n')).toContain(url)
  })
})
```

y sumar `qrCommand` al import de ese archivo.

En `frontend/src/pos/utils/permissions.test.js`, dentro de `describe('saleActions', …)`:

```js
  it('ofrece facturar una venta cerrada sin factura y anularla con Anular', () => {
    const closed = sale({ status: 'closed', balance: 0, paid_total: 1000, invoice: null })
    expect(saleActions(closed, cashier)).toMatchObject({ invoice: true, invoiceActions: false, cancelInvoice: false })
    const invoiced = { ...closed, invoice: { id: 1, label: 'Factura C 00005-00000001', status: 'authorized', is_active: true } }
    expect(saleActions(invoiced, cashier)).toMatchObject({ invoice: false, invoiceActions: true, cancelInvoice: true })
    expect(saleActions(invoiced, waiter)).toMatchObject({ invoice: false, invoiceActions: false, cancelInvoice: false })
  })
```

y actualizar el test existente `'una venta cerrada solo permite anular pagos e imprimir el ticket'`: su lista esperada pasa a `['cancelPayment', 'history', 'invoice', 'printReceipt']`, porque el `sale()` de prueba no trae `invoice`.

- [ ] **Step 2: Correr y ver que fallen**

Run (cwd `frontend/`): `npx vitest run src/pos/fiscal src/pos/print/escpos.test.js src/pos/utils/permissions.test.js`
Expected: FAIL (no existe `invoiceForm`, ni `qrCommand`, ni las acciones nuevas).

- [ ] **Step 3: Formulario.** Crear `frontend/src/pos/fiscal/invoiceForm.js`:

```js
import { formatMoney } from '../utils/money'

export const DOC_TYPES = [['DNI', 'DNI'], ['CUIT', 'CUIT'], ['CUIL', 'CUIL']]
export const IVA_CONDITIONS = [
  ['consumidor_final', 'Consumidor final'],
  ['monotributo', 'Monotributo'],
  ['responsable_inscripto', 'Responsable inscripto'],
  ['exento', 'Exento'],
]

const digits = (value) => String(value ?? '').replace(/\D/g, '')
const WEIGHTS = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]

export function cuitIsValid(value) {
  const d = digits(value)
  if (d.length !== 11) return false
  const remainder = 11 - (WEIGHTS.reduce((sum, w, i) => sum + w * Number(d[i]), 0) % 11)
  const check = remainder === 11 ? 0 : remainder
  return check !== 10 && check === Number(d[10])
}

// Mismas reglas que el backend (receivers.normalize_receiver), para avisar antes de ir a ARCA.
export function validateCustomer(form) {
  if (form.mode === 'anonymous') return null
  const d = digits(form.docNumber)
  if (form.docType === 'DNI' && (d.length < 7 || d.length > 8)) return 'El DNI tiene que tener 7 u 8 dígitos'
  if (form.docType !== 'DNI' && !cuitIsValid(d)) return `El ${form.docType} es inválido`
  if (!String(form.name ?? '').trim()) return 'Indicá el nombre o la razón social'
  if (['monotributo', 'responsable_inscripto'].includes(form.ivaCondition) && form.docType !== 'CUIT') {
    return 'Para esa condición hace falta el CUIT'
  }
  return null
}

export function customerPayload(form) {
  if (form.mode === 'anonymous') return null
  return {
    doc_type: form.docType,
    doc_number: digits(form.docNumber),
    name: String(form.name).trim(),
    iva_condition: form.ivaCondition,
    address: String(form.address ?? '').trim() || null,
  }
}

export function previewSummary(preview) {
  if (!Number(preview.amount)) return 'Todo lo cobrado en esta venta lo factura otro sistema'
  if (preview.detail_mode === 'items') return `Se facturan los ítems · ${formatMoney(preview.amount)}`
  return `Se factura ${formatMoney(preview.amount)} de ${formatMoney(preview.total)} (lo demás lo factura otro sistema)`
}
```

Si `formatMoney('18000.00')` no devuelve `'$ 18.000'` (revisar `frontend/src/pos/utils/money.js`), ajustar las expectativas de `previewSummary` al formato real de `formatMoney`, sin cambiar la función.

- [ ] **Step 4: QR en ESC/POS.** En `frontend/src/pos/print/escpos.js`, agregar después de `renderText`:

```js
// QR de ARCA (modelo 2, módulo 6, corrección M): guardar los datos y después imprimirlos.
export function qrCommand(data) {
  const len = data.length + 3
  return `${GS}(k\x04\x001A2\x00` + `${GS}(k\x03\x001C\x06` + `${GS}(k\x03\x001E1`
    + `${GS}(k${String.fromCharCode(len % 256)}${String.fromCharCode(Math.floor(len / 256))}1P0${data}`
    + `${GS}(k\x03\x001Q0`
}
```

En `renderText`, reemplazar el `return` por:

```js
  const lines = [...wrap(doc.title ?? '', cols).map((t) => center(t, cols)), ...headerLines(doc, cols), ...bodyLines(doc, cols)]
  if (doc.qr) lines.push('', ...wrap(`QR: ${doc.qr}`, cols))
  return lines
```

En `renderEscPos`, reemplazar la última concatenación (`out += \`${bodyLines(doc, cols).join('\n')}\n\n\n\n${GS}V\x01\``) por:

```js
  out += `${bodyLines(doc, cols).join('\n')}\n`
  if (doc.qr) out += `${ESC}a\x01${qrCommand(doc.qr)}\n${ESC}a\x00`
  out += `\n\n\n${GS}V\x01`
```

En `frontend/src/pos/print/printStatus.js`, sumar `invoice: 'Factura'` a `KIND_LABELS`.

- [ ] **Step 5: Permisos.** En `frontend/src/pos/utils/permissions.js`, dentro del objeto de `saleActions`, agregar:

```js
    invoice: perms.pos && sale.status === 'closed' && !sale.invoice,
    invoiceActions: perms.pos && Boolean(sale.invoice),
    cancelInvoice: perms.pos && perms.cancel && Boolean(sale.invoice?.is_active),
```

- [ ] **Step 6: API y claves.** En `frontend/src/pos/api/posApi.js`, agregar al final:

```js
export const posFiscalApi = {
  preview: (saleId) => data(api.get(`/fiscal/sales/${saleId}/preview`)),
  issue: (saleId, customer) => data(api.post(`/fiscal/sales/${saleId}/invoice`, { customer })),
  saleInvoices: (saleId) => data(api.get(`/fiscal/sales/${saleId}/invoices`)).then((d) => d.invoices),
  verify: (id) => data(api.post(`/fiscal/invoices/${id}/verify`)),
  cancel: (id) => data(api.post(`/fiscal/invoices/${id}/cancel`)),
  reprint: (id) => data(api.post(`/fiscal/invoices/${id}/reprint`)),
  list: (params) => data(api.get('/fiscal/invoices', { params })),
  get: (id) => data(api.get(`/fiscal/invoices/${id}`)),
  customers: (q) => data(api.get('/fiscal/customers', { params: { q } })).then((d) => d.customers),
  settings: () => data(api.get('/fiscal/settings')),
  saveSettings: (body) => data(api.put('/fiscal/settings', body)),
  generateCsr: (env) => data(api.post(`/fiscal/settings/${env}/csr`)).then((d) => d.csr),
  saveCertificate: (env, certificate) => data(api.put(`/fiscal/settings/${env}/certificate`, { certificate })),
  testConnection: () => data(api.post('/fiscal/settings/test')),
}
```

En `frontend/src/pos/hooks/keys.js`, agregar dentro de `posKeys`:

```js
  fiscal: ['pos', 'fiscal'],
  fiscalPreview: (id) => ['pos', 'fiscal', 'preview', id],
  fiscalSaleInvoices: (id) => ['pos', 'fiscal', 'sale', id],
  fiscalInvoices: (params) => ['pos', 'fiscal', 'list', params],
  fiscalSettings: ['pos', 'fiscal', 'settings'],
```

- [ ] **Step 7: Verificar**

Run: `npx vitest run src/pos/fiscal src/pos/print src/pos/utils/permissions.test.js`, después `npm test` y `npm run build`.
Expected: todo pasa.

- [ ] **Step 8: Commit**

```bash
git -C <worktree> add frontend/src/pos
git -C <worktree> commit -m "feat(fiscal): fiscal API client, invoice form logic and ESC/POS QR"
```

---

### Task 9: Facturar desde la caja

**Files:**
- Create: `frontend/src/pos/fiscal/InvoiceModal.jsx`, `frontend/src/pos/fiscal/InvoiceTag.jsx`
- Modify: `frontend/src/pos/sale/SaleFooter.jsx`, `frontend/src/pos/sale/SalePanel.jsx`, `frontend/src/pos/modals/PaymentModal.jsx`

**Interfaces:**
- Consumes:
  - `posFiscalApi`, `posKeys`, `invoiceForm` y las acciones `invoice`, `invoiceActions` y `cancelInvoice` (Task 8);
  - `Modal` (`../ui/Modal`), `btn`, `useToast`, `errorMessage`, `formatMoney`.
- Produces:
  - `InvoiceModal({ saleId, onClose, onDone })`;
  - `InvoiceTag({ sale, canCancel })`.

- [ ] **Step 1: Modal.** Crear `frontend/src/pos/fiscal/InvoiceModal.jsx`:

```jsx
import { useEffect, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { posFiscalApi } from '../api/posApi'
import { posKeys } from '../hooks/keys'
import Modal from '../ui/Modal'
import { btn } from '../ui/buttons'
import { useToast } from '../ui/Toasts'
import { errorMessage } from '../utils/errors'
import { DOC_TYPES, IVA_CONDITIONS, customerPayload, previewSummary, validateCustomer } from './invoiceForm'

const EMPTY = { mode: 'anonymous', docType: 'DNI', docNumber: '', name: '', ivaCondition: 'consumidor_final', address: '' }

export default function InvoiceModal({ saleId, onClose, onDone }) {
  const queryClient = useQueryClient()
  const toast = useToast()
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)
  const [suggestions, setSuggestions] = useState([])
  const { data: preview, isLoading, isError } = useQuery({
    queryKey: posKeys.fiscalPreview(saleId), queryFn: () => posFiscalApi.preview(saleId),
  })
  const set = (patch) => { setForm((f) => ({ ...f, ...patch })); setError('') }

  useEffect(() => {
    const q = form.mode === 'identified' ? (form.docNumber || form.name).trim() : ''
    if (q.length < 2) { setSuggestions([]); return undefined }
    const id = setTimeout(() => { posFiscalApi.customers(q).then(setSuggestions).catch(() => setSuggestions([])) }, 250)
    return () => clearTimeout(id)
  }, [form.mode, form.docNumber, form.name])

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: posKeys.sale(saleId) })
    queryClient.invalidateQueries({ queryKey: posKeys.fiscal })
  }

  const submit = async () => {
    const problem = validateCustomer(form)
    if (problem) return setError(problem)
    setBusy(true)
    try {
      const invoice = await posFiscalApi.issue(saleId, customerPayload(form))
      setResult(invoice)
      refresh()
      if (invoice.print_warning) toast.error(invoice.print_warning)
    } catch (err) {
      const invoice = err?.response?.data?.invoice
      if (invoice) refresh()
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const verify = async () => {
    setBusy(true)
    try {
      setResult(await posFiscalApi.verify(result.id))
      refresh()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const testMode = preview?.environment === 'homologacion'
  const title = `Facturar${testMode ? ' · PRUEBA' : ''}`

  if (result) {
    const pending = result.status === 'pending'
    return (
      <Modal title={title} onClose={() => { onDone?.(result); onClose() }} size="sm"
        footer={(
          <div className="grid grid-cols-2 gap-2">
            {pending
              ? <button type="button" className={btn('secondary')} disabled={busy} onClick={verify}>Verificar</button>
              : <span />}
            <button type="button" className={btn('primary')} onClick={() => { onDone?.(result); onClose() }}>Listo</button>
          </div>
        )}>
        {pending ? (
          <p className="rounded-lg bg-amber-50 p-3 text-amber-900">No pudimos confirmar con ARCA. Tocá Verificar en unos segundos.</p>
        ) : result.status === 'authorized' ? (
          <div className="space-y-1 py-2 text-center">
            <p className="text-lg font-semibold">{result.label}</p>
            <p className="text-sm text-gray-600">CAE {result.cae}</p>
            <p className="text-sm text-gray-600">Se está imprimiendo en caja.</p>
          </div>
        ) : (
          <p className="rounded-lg bg-red-50 p-3 text-red-800">{result.error}</p>
        )}
        {error && <p className="mt-2 text-sm text-red-700">{error}</p>}
      </Modal>
    )
  }

  return (
    <Modal title={title} onClose={onClose} size="md"
      footer={(
        <button type="button" className={btn('primary', 'w-full')} disabled={busy || isLoading || !preview?.ready || !Number(preview?.amount)}
          onClick={submit}>{busy ? 'Emitiendo…' : 'Emitir factura'}</button>
      )}>
      {isLoading && <p className="text-gray-500">Calculando…</p>}
      {isError && <p className="text-red-700">No se pudo preparar la factura.</p>}
      {preview && (
        <div className="space-y-4">
          {!preview.ready && (
            <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900">Falta configurar la facturación: {preview.missing.join(', ')}</p>
          )}
          <p className="font-medium">{previewSummary(preview)}</p>
          <div className="flex gap-2">
            {[['anonymous', 'Consumidor final'], ['identified', 'Con datos']].map(([mode, label]) => (
              <button key={mode} type="button" onClick={() => set({ mode })}
                className={btn(form.mode === mode ? 'primary' : 'secondary', 'flex-1')}>{label}</button>
            ))}
          </div>
          {form.mode === 'anonymous' && preview.requires_id_from && (
            <p className="text-xs text-gray-500">Desde ${Number(preview.requires_id_from).toLocaleString('es-AR')} hay que identificar al cliente.</p>
          )}
          {form.mode === 'identified' && (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <label className="text-sm">Documento
                <div className="mt-1 flex gap-2">
                  <select value={form.docType} onChange={(e) => set({ docType: e.target.value })} className="rounded border px-2 py-2">
                    {DOC_TYPES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                  </select>
                  <input value={form.docNumber} inputMode="numeric" onChange={(e) => set({ docNumber: e.target.value })}
                    className="w-full rounded border px-2 py-2" />
                </div>
              </label>
              <label className="text-sm">Nombre o razón social
                <input value={form.name} onChange={(e) => set({ name: e.target.value })} className="mt-1 w-full rounded border px-2 py-2" />
              </label>
              {suggestions.length > 0 && (
                <ul className="col-span-full divide-y rounded border text-sm">
                  {suggestions.map((c) => (
                    <li key={c.id}>
                      <button type="button" className="w-full px-3 py-2 text-left hover:bg-gray-50"
                        onClick={() => { set({ docType: c.doc_type, docNumber: c.doc_number, name: c.name, ivaCondition: c.iva_condition, address: c.address ?? '' }); setSuggestions([]) }}>
                        {c.name} · {c.doc_type} {c.doc_number}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              <label className="text-sm">Condición frente al IVA
                <select value={form.ivaCondition} onChange={(e) => set({ ivaCondition: e.target.value })} className="mt-1 w-full rounded border px-2 py-2">
                  {IVA_CONDITIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
              <label className="text-sm">Domicilio (opcional)
                <input value={form.address} onChange={(e) => set({ address: e.target.value })} className="mt-1 w-full rounded border px-2 py-2" />
              </label>
            </div>
          )}
          {error && <p className="text-sm text-red-700">{error}</p>}
        </div>
      )}
    </Modal>
  )
}
```

Antes de escribirlo, revisar en `frontend/src/pos/ui/Modal.jsx` los valores que acepta `size`. Si `md` no existe, usar el que corresponda (`sm`/`lg`).

- [ ] **Step 2: Etiqueta de factura.** Crear `frontend/src/pos/fiscal/InvoiceTag.jsx`:

```jsx
import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { posFiscalApi } from '../api/posApi'
import { posKeys } from '../hooks/keys'
import { useToast } from '../ui/Toasts'
import { errorMessage } from '../utils/errors'

// Factura de la venta en el pie: reimprimir, verificar (si está sin confirmar) y anular (nota de crédito).
export default function InvoiceTag({ sale, canCancel }) {
  const queryClient = useQueryClient()
  const toast = useToast()
  const [busy, setBusy] = useState(false)
  const invoice = sale.invoice
  const run = async (fn, success) => {
    setBusy(true)
    try {
      const result = await fn()
      if (result?.status === 'rejected') toast.error(result.error)
      else if (success) toast.success(typeof success === 'function' ? success(result) : success)
      queryClient.invalidateQueries({ queryKey: posKeys.sale(sale.id) })
      queryClient.invalidateQueries({ queryKey: posKeys.fiscal })
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }
  const cancel = () => {
    if (!window.confirm(`¿Anular la ${invoice.label}? Se emite una nota de crédito por el total.`)) return
    run(() => posFiscalApi.cancel(invoice.id), (r) => (r.status === 'pending' ? 'Nota de crédito sin confirmar: verificala' : `${r.label} emitida`))
  }
  const pending = invoice.status === 'pending'
  return (
    <div className="flex flex-wrap items-center gap-3 text-sm">
      <span className={`rounded-full px-2 py-0.5 font-medium ${pending ? 'bg-amber-100 text-amber-900' : 'bg-green-100 text-green-800'}`}>
        {pending ? 'Factura sin confirmar' : invoice.label}
      </span>
      {pending ? (
        <button type="button" disabled={busy} className="underline" onClick={() => run(() => posFiscalApi.verify(invoice.id), 'Verificada')}>Verificar</button>
      ) : (
        <button type="button" disabled={busy} className="underline" onClick={() => run(() => posFiscalApi.reprint(invoice.id), 'Enviada a imprimir')}>Reimprimir</button>
      )}
      {canCancel && !pending && (
        <button type="button" disabled={busy} className="text-red-700 underline" onClick={cancel}>Anular factura</button>
      )}
    </div>
  )
}
```

- [ ] **Step 3: Pie de la venta.** En `frontend/src/pos/sale/SaleFooter.jsx`, importar `InvoiceTag from '../fiscal/InvoiceTag'` y reemplazar el bloque de venta no activa por:

```jsx
  if (!['open', 'billing'].includes(sale.status)) {
    return (
      <div className="space-y-2 border-t bg-gray-50 px-4 py-3 text-sm text-gray-700">
        <div className="flex items-center justify-between gap-2">
          <span>{sale.status === 'closed' ? `Cerrada · cobrado ${formatMoney(sale.paid_total)}` : `Anulada: ${sale.cancel_reason ?? ''}`}</span>
          <div className="flex gap-2">
            {actions.invoice && (
              <button type="button" className={btn('secondary', 'min-h-[40px]')} onClick={handlers.invoice}>Facturar</button>
            )}
            {actions.printReceipt && (
              <button type="button" className={btn('secondary', 'min-h-[40px]')} onClick={handlers.printReceipt}>Imprimir ticket</button>
            )}
          </div>
        </div>
        {actions.invoiceActions && <InvoiceTag sale={sale} canCancel={actions.cancelInvoice} />}
      </div>
    )
  }
```

- [ ] **Step 4: Panel y cobro.**
  - En `frontend/src/pos/sale/SalePanel.jsx`:
    - importar `InvoiceModal from '../fiscal/InvoiceModal'`;
    - en `handlers`, agregar `invoice: () => setModal({ type: 'invoice' }),`;
    - junto a los otros modales, agregar `{modal?.type === 'invoice' && <InvoiceModal saleId={sale.id} onClose={closeModal} />}`.
  - En `frontend/src/pos/modals/PaymentModal.jsx`:
    - importar `InvoiceModal from '../fiscal/InvoiceModal'` y `usePosPermissions` (si no está ya importado; lo está como `perms`);
    - agregar el estado `const [invoicing, setInvoicing] = useState(false)`;
    - en el bloque `if (closedChange !== null)`, antes del `return`, agregar `if (invoicing) return <InvoiceModal saleId={sale.id} onClose={onSaleClosed} />`;
    - cambiar el `footer` del modal "Venta cerrada" a tres botones:

```jsx
        footer={(
          <div className={`grid gap-2 ${perms.pos ? 'grid-cols-3' : 'grid-cols-2'}`}>
            <button type="button" className={btn('secondary')} onClick={() => posPrintApi.printReceipt(sale.id)
              .then(() => toast.success('Ticket enviado a imprimir'))
              .catch((printError) => toast.error(errorMessage(printError)))}>Imprimir ticket</button>
            {perms.pos && <button type="button" className={btn('secondary')} onClick={() => setInvoicing(true)}>Facturar</button>}
            <button type="button" className={btn('primary')} onClick={onSaleClosed}>Listo</button>
          </div>
        )}
```

- [ ] **Step 5: Verificar**

Run: `npm test` y `npm run build`.
Expected: todo pasa.

- [ ] **Step 6: Commit**

```bash
git -C <worktree> add frontend/src/pos
git -C <worktree> commit -m "feat(fiscal): invoice from the cashier, invoice tag and credit note"
```

---

### Task 10: Ajustes → Facturación, Comprobantes y medios de pago

**Files:**
- Create: `frontend/src/pages/admin/FiscalSettings.jsx`, `frontend/src/pages/Invoices.jsx`, `docs/pos/facturacion-arca.md`
- Modify: `frontend/src/pages/admin/PosSettings.jsx`, `frontend/src/App.jsx`, `frontend/src/components/layout/Sidebar.jsx`

**Interfaces:**
- Consumes: `posFiscalApi`, `posKeys` (Task 8).
- Produces:
  - las rutas `/admin/fiscal` (admin) y `/fiscal/invoices` (POS);
  - la columna "Lo factura otro sistema" en Medios de pago.

- [ ] **Step 1: Medios de pago.** En `frontend/src/pages/admin/PosSettings.jsx`, en `TABS['payment-methods']`:
  - `emptyItem` pasa a `{ name: '', kind: 'cash', position: 0, is_active: true, invoiced_externally: false }`;
  - sumar a `fields`, antes de `is_active`: `{ key: 'invoiced_externally', label: 'Lo factura otro sistema', type: 'checkbox' },`.

- [ ] **Step 2: Configuración fiscal.** Crear `frontend/src/pages/admin/FiscalSettings.jsx`:

```jsx
import { useEffect, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { posFiscalApi } from '@/pos/api/posApi'
import { posKeys } from '@/pos/hooks/keys'
import { errorMessage } from '@/pos/utils/errors'

const ENVS = [['homologacion', 'Homologación (pruebas)'], ['produccion', 'Producción']]
const CONDITIONS = [['monotributo', 'Monotributo (Factura C)'], ['responsable_inscripto', 'Responsable inscripto (Factura A/B)']]
const card = 'space-y-3 rounded-xl bg-white p-5 shadow-sm'
const input = 'mt-1 w-full rounded border px-3 py-2'

function download(name, text) {
  const url = URL.createObjectURL(new Blob([text], { type: 'application/pkcs10' }))
  const link = document.createElement('a')
  link.href = url
  link.download = name
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export default function FiscalSettings() {
  const queryClient = useQueryClient()
  const { data: settings, isLoading } = useQuery({ queryKey: posKeys.fiscalSettings, queryFn: posFiscalApi.settings })
  const [form, setForm] = useState(null)
  const [certEnv, setCertEnv] = useState('homologacion')
  const [certificate, setCertificate] = useState('')
  const [message, setMessage] = useState(null)

  useEffect(() => {
    if (settings) {
      setForm({
        cuit: settings.cuit ?? '', business_name: settings.business_name ?? '', address: settings.address ?? '',
        gross_income: settings.gross_income ?? '', activity_start: settings.activity_start ?? '',
        iva_condition: settings.iva_condition, point_of_sale: settings.point_of_sale ?? '',
        cf_id_threshold: settings.cf_id_threshold ?? '', default_iva_rate: settings.default_iva_rate,
      })
    }
  }, [settings])

  const act = async (fn, ok) => {
    setMessage(null)
    try {
      const result = await fn()
      queryClient.invalidateQueries({ queryKey: posKeys.fiscalSettings })
      setMessage({ ok: true, text: typeof ok === 'function' ? ok(result) : ok })
      return result
    } catch (err) {
      setMessage({ ok: false, text: errorMessage(err) })
      return null
    }
  }

  if (isLoading || !form) return <p className="p-6">Cargando…</p>
  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })
  const saveEmitter = () => act(() => posFiscalApi.saveSettings({
    ...form, point_of_sale: form.point_of_sale === '' ? undefined : Number(form.point_of_sale),
    cf_id_threshold: form.cf_id_threshold === '' ? null : form.cf_id_threshold,
  }), 'Datos guardados')
  const creds = settings.credentials[certEnv]
  const switchEnv = (env) => {
    if (env === 'produccion' && !window.confirm('Las facturas van a tener validez fiscal. ¿Pasar a producción?')) return
    act(() => posFiscalApi.saveSettings({ environment: env }), 'Entorno cambiado')
  }

  return (
    <div className="max-w-3xl space-y-5">
      <h1 className="text-3xl">Facturación</h1>
      {settings.environment === 'homologacion' && (
        <p className="rounded-lg bg-amber-50 p-3 text-amber-900">Modo pruebas (homologación): las facturas no tienen validez fiscal.</p>
      )}
      {settings.missing.length > 0 && (
        <p className="rounded-lg bg-red-50 p-3 text-red-800">Falta: {settings.missing.join(', ')}</p>
      )}
      {message && <p className={`rounded-lg p-3 ${message.ok ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>{message.text}</p>}

      <section className={card}>
        <h2 className="text-lg font-semibold">1. Emisor y punto de venta</h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <label className="text-sm">CUIT<input className={input} value={form.cuit} onChange={set('cuit')} /></label>
          <label className="text-sm">Razón social<input className={input} value={form.business_name} onChange={set('business_name')} /></label>
          <label className="text-sm">Domicilio comercial<input className={input} value={form.address} onChange={set('address')} /></label>
          <label className="text-sm">Ingresos brutos<input className={input} value={form.gross_income} onChange={set('gross_income')} /></label>
          <label className="text-sm">Inicio de actividades<input type="date" className={input} value={form.activity_start} onChange={set('activity_start')} /></label>
          <label className="text-sm">Condición frente al IVA
            <select className={input} value={form.iva_condition} onChange={set('iva_condition')}>
              {CONDITIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </label>
          <label className="text-sm">Punto de venta (RECE – web services)<input type="number" className={input} value={form.point_of_sale} onChange={set('point_of_sale')} /></label>
          <label className="text-sm">Identificar al consumidor final desde $<input type="number" className={input} value={form.cf_id_threshold} onChange={set('cf_id_threshold')} /></label>
          <label className="text-sm">Alícuota de IVA (solo A/B)
            <select className={input} value={Number(form.default_iva_rate)} onChange={set('default_iva_rate')}>
              {[0, 10.5, 21, 27].map((r) => <option key={r} value={r}>{r}%</option>)}
            </select>
          </label>
        </div>
        <button type="button" className="rounded bg-galia-plum px-4 py-2 text-galia-cream" onClick={saveEmitter}>Guardar</button>
      </section>

      <section className={card}>
        <h2 className="text-lg font-semibold">2. Certificado</h2>
        <div className="flex gap-2">
          {ENVS.map(([env, label]) => (
            <button key={env} type="button" onClick={() => setCertEnv(env)}
              className={`rounded px-3 py-1.5 text-sm ${certEnv === env ? 'bg-galia-plum text-galia-cream' : 'bg-gray-100'}`}>{label}</button>
          ))}
        </div>
        <p className="text-sm text-gray-700">
          {creds.has_certificate
            ? `Certificado cargado. Vence el ${new Date(creds.expires_at).toLocaleDateString('es-AR')}.`
            : 'Sin certificado.'}
          {creds.expires_soon && <span className="ml-2 font-semibold text-red-700">Vence pronto: generá uno nuevo.</span>}
        </p>
        <ol className="list-decimal space-y-2 pl-5 text-sm">
          <li>
            <button type="button" className="underline"
              onClick={() => act(() => posFiscalApi.generateCsr(certEnv), 'Pedido generado y descargado').then((csr) => csr && download(`galia-${certEnv}.csr`, csr))}>
              Generar pedido de certificado (CSR)
            </button>{' '}
            y subilo en ARCA: {certEnv === 'homologacion' ? 'WSASS (homologación)' : '"Administración de certificados digitales"'}, asociándolo al servicio "Facturación electrónica".
          </li>
          <li>
            Pegá el certificado que te da ARCA:
            <textarea rows={6} className={`${input} font-mono text-xs`} value={certificate} onChange={(e) => setCertificate(e.target.value)}
              placeholder="-----BEGIN CERTIFICATE-----" />
            <button type="button" className="mt-2 rounded bg-galia-plum px-4 py-2 text-galia-cream"
              onClick={() => act(() => posFiscalApi.saveCertificate(certEnv, certificate), 'Certificado guardado').then((r) => r && setCertificate(''))}>
              Guardar certificado
            </button>
          </li>
        </ol>
      </section>

      <section className={card}>
        <h2 className="text-lg font-semibold">3. Entorno y prueba</h2>
        <div className="flex flex-wrap gap-2">
          {ENVS.map(([env, label]) => (
            <button key={env} type="button" onClick={() => switchEnv(env)}
              className={`rounded px-3 py-1.5 text-sm ${settings.environment === env ? 'bg-galia-plum text-galia-cream' : 'bg-gray-100'}`}>{label}</button>
          ))}
          <button type="button" className="ml-auto rounded border px-3 py-1.5 text-sm"
            onClick={() => act(posFiscalApi.testConnection, (r) => `Conectado. ${r.label}`)}>Probar conexión</button>
        </div>
      </section>
    </div>
  )
}
```

- [ ] **Step 3: Comprobantes.** Crear `frontend/src/pages/Invoices.jsx`:

```jsx
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { posFiscalApi } from '@/pos/api/posApi'
import { posKeys } from '@/pos/hooks/keys'
import { errorMessage } from '@/pos/utils/errors'
import { formatMoney } from '@/pos/utils/money'

const STATUS = { authorized: 'Autorizado', pending: 'Sin confirmar', rejected: 'Rechazado' }

export default function Invoices() {
  const queryClient = useQueryClient()
  const [filters, setFilters] = useState({ from: '', to: '', kind: '', status: '', page: 1 })
  const [detail, setDetail] = useState(null)
  const [message, setMessage] = useState('')
  const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== ''))
  const { data, isLoading, isError } = useQuery({ queryKey: posKeys.fiscalInvoices(params), queryFn: () => posFiscalApi.list(params) })
  const set = (key) => (e) => setFilters({ ...filters, [key]: e.target.value, page: 1 })
  const act = async (fn, ok) => {
    setMessage('')
    try {
      await fn()
      setMessage(ok)
      queryClient.invalidateQueries({ queryKey: posKeys.fiscal })
    } catch (err) {
      setMessage(errorMessage(err))
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-3xl">Comprobantes</h1>
      {data?.environment === 'homologacion' && (
        <p className="rounded-lg bg-amber-50 p-3 text-amber-900">Modo pruebas (homologación): sin validez fiscal.</p>
      )}
      <div className="flex flex-wrap gap-3 text-sm">
        <label>Desde <input type="date" value={filters.from} onChange={set('from')} className="ml-1 rounded border px-2 py-1" /></label>
        <label>Hasta <input type="date" value={filters.to} onChange={set('to')} className="ml-1 rounded border px-2 py-1" /></label>
        <select value={filters.kind} onChange={set('kind')} className="rounded border px-2 py-1">
          <option value="">Todos los tipos</option><option value="invoice">Facturas</option><option value="credit_note">Notas de crédito</option>
        </select>
        <select value={filters.status} onChange={set('status')} className="rounded border px-2 py-1">
          <option value="">Todos los estados</option>
          {Object.entries(STATUS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </div>
      {message && <p className="text-sm text-gray-700">{message}</p>}
      {isLoading && <p>Cargando…</p>}
      {isError && <p className="text-red-700">No se pudieron cargar los comprobantes.</p>}
      {data && (
        <div className="overflow-x-auto rounded-xl bg-white shadow-sm">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr><th className="p-2">Fecha</th><th className="p-2">Comprobante</th><th className="p-2">Cliente</th><th className="p-2 text-right">Total</th><th className="p-2">Estado</th><th className="p-2">Venta</th><th className="p-2" /></tr>
            </thead>
            <tbody className="divide-y">
              {data.invoices.map((inv) => (
                <tr key={inv.id}>
                  <td className="p-2">{new Date(`${inv.voucher_date}T12:00:00`).toLocaleDateString('es-AR')}</td>
                  <td className="p-2"><button type="button" className="underline" onClick={() => setDetail(inv)}>{inv.label}</button></td>
                  <td className="p-2">{inv.receiver.name}</td>
                  <td className="p-2 text-right">{formatMoney(inv.total)}</td>
                  <td className="p-2">{STATUS[inv.status]}{inv.credit_note_label ? ' · anulada' : ''}</td>
                  <td className="p-2">{inv.sale_number ? `#${inv.sale_number}` : '-'}</td>
                  <td className="space-x-2 p-2 text-right">
                    {inv.status === 'authorized' && <button type="button" className="underline" onClick={() => act(() => posFiscalApi.reprint(inv.id), 'Enviado a imprimir')}>Reimprimir</button>}
                    {inv.status === 'pending' && <button type="button" className="underline" onClick={() => act(() => posFiscalApi.verify(inv.id), 'Verificado')}>Verificar</button>}
                  </td>
                </tr>
              ))}
              {data.invoices.length === 0 && <tr><td colSpan={7} className="p-4 text-center text-gray-500">Sin comprobantes.</td></tr>}
            </tbody>
          </table>
          <div className="flex items-center justify-end gap-2 p-2 text-sm">
            <button type="button" disabled={filters.page <= 1} onClick={() => setFilters({ ...filters, page: filters.page - 1 })}>Anterior</button>
            <span>{data.page} / {data.pages}</span>
            <button type="button" disabled={filters.page >= data.pages} onClick={() => setFilters({ ...filters, page: filters.page + 1 })}>Siguiente</button>
          </div>
        </div>
      )}
      {detail && (
        <section className="space-y-2 rounded-xl bg-white p-4 text-sm shadow-sm">
          <div className="flex justify-between"><h2 className="font-semibold">{detail.label}</h2><button type="button" onClick={() => setDetail(null)}>Cerrar</button></div>
          <p>Cliente: {detail.receiver.name} · CAE {detail.cae ?? '-'} {detail.cae_due ? `(vence ${detail.cae_due})` : ''}</p>
          {detail.related_label && <p>Anula: {detail.related_label}</p>}
          {detail.error && <p className="text-red-700">{detail.error}</p>}
          <ul>{detail.lines.map((l, i) => <li key={i}>{l.qty} x {l.description} · {formatMoney(l.amount)}</li>)}</ul>
          {detail.sale_id && <Link className="underline" to={`/pos?sale=${detail.sale_id}`}>Ir a la venta</Link>}
          <details><summary>Pedido y respuesta de ARCA</summary><pre className="overflow-x-auto text-xs">{JSON.stringify({ request: detail.request, arca: detail.arca_result }, null, 2)}</pre></details>
        </section>
      )}
    </div>
  )
}
```

Antes de dejar el link "Ir a la venta", revisar en el código del POS cómo se abre una venta por URL (`SalonPage` usa `?sale=`). Si en `/pos` no se lee `?sale`, apuntar a `/pos/salon/<salon_id>?sale=<id>` cuando la venta tiene mesa, o quitar el link y dejar solo el número.

- [ ] **Step 4: Rutas y menú.**
  - En `frontend/src/App.jsx`, importar `FiscalSettings from './pages/admin/FiscalSettings'` e `Invoices from './pages/Invoices'`, y agregar dentro del layout principal:

```jsx
            <Route path="/fiscal/invoices" element={<RoleProtectedRoute moduleName="POS"><Invoices /></RoleProtectedRoute>} />
            <Route path="/admin/fiscal" element={<RoleProtectedRoute adminOnly><FiscalSettings /></RoleProtectedRoute>} />
```

  - En `frontend/src/components/layout/Sidebar.jsx`:
    - en Finanzas, después de "Cajas": `{ to: '/fiscal/invoices', icon: FileText, label: 'Comprobantes', module: 'POS' },`;
    - después de "Ajustes del POS": `{ to: '/admin/fiscal', icon: Receipt, label: 'Facturación', adminOnly: true },`;
    - verificar que `FileText` y `Receipt` estén en el import de `lucide-react` de ese archivo (ya se usan en el menú).

- [ ] **Step 5: Guía.** Crear `docs/pos/facturacion-arca.md`:

````markdown
# Facturación electrónica con ARCA

Galia emite desde la caja la factura que pide un cliente, sobre una venta cobrada. Solo factura lo cobrado con medios que **no** factura otro sistema (en Ajustes del POS → Medios de pago, la columna "Lo factura otro sistema").

## 1. Punto de venta para Galia

En ARCA ("Administración de puntos de venta y domicilios"), dar de alta un punto de venta nuevo del tipo **"RECE para aplicativo y web services"**. Anotar el número.

## 2. Configurar en Galia (admin)

**Ajustes → Facturación:**

1. **Emisor:** CUIT, razón social, domicilio, ingresos brutos, inicio de actividades y condición (hoy, Monotributo). Cargar el punto de venta del paso 1. Guardar.
2. **Certificado de homologación** (pruebas):
   1. Tocar "Generar pedido de certificado (CSR)". Se descarga `galia-homologacion.csr`.
   2. En ARCA, entrar a **WSASS – Autogestión de certificados de homologación**. Crear un certificado con ese CSR y autorizarlo para el servicio **wsfe**.
   3. Pegar el certificado en Galia y "Guardar certificado".
3. **Probar conexión:** tiene que decir "Conectado. Último comprobante: …".
4. Probar facturas y notas de crédito en homologación (salen con "SIN VALIDEZ FISCAL – PRUEBA").
5. **Producción:**
   1. En la pestaña Producción, generar el CSR.
   2. En ARCA, "Administración de certificados digitales": crear el certificado con ese CSR.
   3. En "Administrador de relaciones de clave fiscal", asociarlo al servicio **"Facturación electrónica"**.
   4. Pegar el certificado en Galia, pasar el entorno a **Producción** y probar la conexión.

La clave privada la genera Galia y queda guardada cifrada. Si alguien cambia `SECRET_KEY` en Render, Galia avisa que no la puede leer, y hay que repetir el paso del certificado.

## 3. Facturar

En la caja, en una venta cerrada:
1. Tocar **Facturar** (también aparece al terminar de cobrar).
2. Elegir Consumidor final o Con datos (DNI o CUIT; los clientes se sugieren solos).
3. Tocar **Emitir factura**. Sale impresa en la térmica de caja, con el QR.

- **"No pudimos confirmar con ARCA":** tocar **Verificar** en unos segundos. Galia pregunta a ARCA si la factura quedó hecha y nunca emite dos veces.
- **Anular factura:** emite la nota de crédito; hace falta el permiso "Anular". Mientras la venta tenga factura, no se puede anular la venta ni los pagos que cubre la factura.

**Finanzas → Comprobantes:** lista facturas y notas de crédito, con sus estados, la opción de reimprimir y la de verificar las que quedaron sin confirmar.
````

- [ ] **Step 6: Verificar**

Run: `npm test` y `npm run build`.
Expected: todo pasa.

- [ ] **Step 7: Commit**

```bash
git -C <worktree> add frontend/src docs/pos/facturacion-arca.md
git -C <worktree> commit -m "feat(fiscal): fiscal settings page, invoices list and payment method flag"
```

---

### Task 11: Verificación final

**Files:** ninguno (preview fuera del repo).

- [ ] **Step 1: Suites.** Backend completo contra la línea base (como en la Task 7, Step 6) y frontend con `npm test` y `npm run build`.
Expected: `Sin fallas nuevas.` y todo verde.

- [ ] **Step 2: Preview.** Base SQLite descartable:
  - correr `prep_caja_preview.py` (scratchpad) con `DATABASE_URL` nuevo y `POS_DEMO_SEED=1`;
  - levantar el backend con `FISCAL_FAKE_ARCA=1` en segundo plano, igual que en el sub-proyecto 3 (el `launch.json` compartido no se puede editar desde la worktree), y el frontend con `npm --prefix ../frontend run dev`;
  - abrir `/pos/impresion` en modo simulación en otra pestaña.

- [ ] **Step 3: Verificación manual** (como admin):
  1. **Ajustes → Facturación:** cargar el emisor (CUIT válido de prueba `20123456786`) y el punto de venta 5, y generar el CSR (se descarga). Para tener un certificado que corresponda a esa clave sin ARCA, correr un script del scratchpad. El script:
     - corre con cwd `backend/`, la misma `DATABASE_URL`, y `sys.path` con `tests/`;
     - descifra la clave de homologación con `settings.decrypt_key`;
     - crea el certificado con `fiscal_helpers.make_key_and_cert(key=<esa clave>)`;
     - lo imprime.
     Pegarlo en la UI y "Guardar certificado". "Probar conexión" tiene que decir "Conectado. Último comprobante: C 00005-00000000".
  2. **Medios de pago:** efectivo sin marcar y débito marcado.
  3. **Venta en efectivo:** cobrar y Facturar → Consumidor final. Sale la Factura C con CAE y aparece impresa en la simulación, con el QR.
  4. **Venta mixta** (efectivo + débito): el modal dice "Se factura $X de $Y". Emitir con un DNI; el cliente queda guardado y se sugiere en la venta siguiente.
  5. **Anular factura:** la nota de crédito sale impresa. Después, anular el pago en efectivo: con la factura vigente da 409, y después de la nota de crédito funciona.
  6. **Finanzas → Comprobantes:** filtros, detalle y reimprimir.
  7. **Pendiente:**
     - reiniciar el backend con `FISCAL_FAKE_ARCA_MODE=timeout`, emitir y ver la etiqueta "Factura sin confirmar" y el aviso del modal;
     - comprobar que anular la venta responde "Hay una factura sin confirmar…";
     - reiniciar sin esa variable y tocar "Verificar": queda rechazada con "No llegó a ARCA", y la venta se puede facturar de nuevo.

     El camino contrario (ARCA lo había autorizado) no se puede ver en el preview, porque `FakeArca` vive en memoria y se pierde al reiniciar. Lo cubre `test_timeout_after_arca_issued_resolves_to_authorized`.
