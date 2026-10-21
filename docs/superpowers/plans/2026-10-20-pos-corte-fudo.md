# Corte con Fudo (sub-proyecto 6) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apagar Fudo sin perder la historia. Se importan todas las ventas de Fudo con sus productos, se agrega el reporte "Ventas por producto", la carta pasa al catálogo de Galia, hay un modo práctica y dos interruptores de corte, y una guía de caja para el equipo.

**Architecture:**
- **Importación:** un servicio importa ventas de Fudo mes por mes, con sus ítems, en una tabla propia (`fudo_sale_items`). Lleva un control por mes (`fudo_import_months`) y corre como corrida de `fudo_sync_runs`.
- **Reporte:** une esos ítems con los `pos_sale_items` de Galia.
- **Interruptores:** una fila de configuración (`operation_settings`) guarda "Catálogo en Galia", "Fudo apagado" y "Modo práctica". Lo de práctica queda marcado con `is_practice` en `pos_sales` y `cash_sessions`, y cada camino que toca números reales lo verifica en el backend.
- **Carta:** se vincula al catálogo de Galia (`product_variant_id`, `product_category_id`) y el cron la sincroniza desde ahí.

**Tech Stack:** Flask, SQLAlchemy 2, Alembic, pytest, React 18, React Query 5, Tailwind, Vitest.

**Spec:** `docs/superpowers/specs/2026-10-20-pos-corte-fudo-design.md`

## Global Constraints

- **Worktree:** `C:\Users\onofr\Desktop\galia-app\.claude\worktrees\pos-base`, rama `feature/pos-corte-fudo`. Las rutas del plan son relativas a esa raíz.
- **Python** (`PY`): `C:\Users\onofr\Desktop\galia-app\backend\venv\Scripts\python.exe`. Tests con cwd = `backend/`: `PY -m pytest -q -p no:cacheprovider <archivos>`.
- **Frontend:** con cwd `frontend/` corren `npm test`, `npm run build` y `npx vitest run <archivo>`. Vitest corre en entorno node y solo prueba lógica pura.
- **Git:** solo con `git -C <worktree>`, un comando por llamada. El sandbox rechaza `cd && git` y los heredocs complejos.
- **Línea base:**
  - Comando: `PY scripts/compare_baseline.py <salida> ../docs/superpowers/plans/2026-10-08-pos-base-test-baseline.txt`.
  - Criterio: `Sin fallas nuevas.`
- **Dependencia: PR #23** (`fix/reports-dates`).
  - Trae `business_date()` en `app/utils/timezone_utils.py` (UTC → Argentina con corte a las 6 h) y la migración `b5c0_sales_business_date`.
  - **Antes de la Task 1**, el PR tiene que estar mergeado en `main`, y `main` mergeado en esta rama.
  - Si no está mergeado, se para y se avisa: es una dependencia externa.
- **Migración nueva:** `b6a0_fudo_cutover`, con `down_revision` igual a la cabeza vigente (`b5c0_sales_business_date` con #23). Agregar el test en `tests/test_migration_chain.py`.
- **Fudo (v1alpha1, JSON:API):**
  - sin `fields[...]` no devuelve atributos;
  - páginas de hasta 500;
  - ventas: `GET /sales` con `filter[createdAt]=and(gte.<iso>,lte.<iso>)` y `filter[saleState]=in.(CLOSED,CANCELED)`;
  - `include=items,items.product,items.product.productCategory`;
  - `fields[sale]=closedAt,createdAt,total,saleType,saleState,people,customerName,comment,items`;
  - `fields[item]=quantity,price,canceled,status,product,createdAt`;
  - `fields[product]=name,productCategory`;
  - `fields[productCategory]=name`.
  - Los nombres salen de la OpenAPI (`github.com/api-evangelist/fudo`) y **se confirman con `scripts/inspect_fudo_sales.py` antes de importar en producción**.
- **Lo que decidió el dueño:**
  - **Monto** del reporte: cantidad × precio, **sin descontar** los descuentos de la venta. En Galia es `pos_sale_items.line_total`.
  - **Modo práctica** dentro de la Galia real.
  - **La carta conserva** nombre, descripción, foto y orden de sus ítems. Del catálogo salen precio, categoría y estado.
- **Textos de la interfaz:**
  - Mensajes en castellano rioplatense.
  - Franja de práctica: `PRÁCTICA: nada de esto cuenta`.
  - Encabezado de documentos de práctica: `PRÁCTICA`.
  - Errores:
    - `Fudo está apagado`;
    - `El catálogo ya se maneja en Galia`;
    - `En modo práctica no se factura`;
    - `En modo práctica no se cobra con el Point`.
- **Errores en el backend:** `PosError` (409) y `bad_request` (400) de `app.services.pos.errors`.

## Review Focus

1. **Un mes de Fudo con más de una página de ventas** (más de 500): se importan todas y el control del mes coincide con Fudo. Lo cubre la Task 3 (`test_import_month_paginates`).
2. **Una venta que Fudo anuló después de importada:** al reimportar, el encabezado pasa a `Cancelada` y sus ítems dejan de contar en el reporte. Lo cubren la Task 3 (`test_reimport_updates_cancelled_sale`) y la Task 4 (`test_ranking_excludes_cancelled`).
3. **Gasto desde una caja de práctica y venta de práctica cerrada:** no se crea `Expense`, no hay fila en `sales` y no se mueve stock. Lo cubre la Task 5 (`test_practice_does_not_touch_real_numbers`).
4. **Ítem de Fudo cuyo producto no está vinculado a Galia, o se borró en Galia:** el reporte lo muestra con el nombre guardado al importar. Lo cubre la Task 4 (`test_ranking_unlinked_fudo_product_by_name`).
5. **Variante de Galia desactivada después de pasar la carta al catálogo:** la variante de la carta queda `inactive` (alerta), el ítem no se borra, y el texto que puso el dueño no cambia. Lo cubre la Task 6 (`test_sync_from_catalog_keeps_owner_text_and_flags_inactive`).

---

### Task 1: Cliente de ventas de Fudo, parser puro y script de inspección

**Files:**
- Modify: `backend/app/utils/fudo_client.py`
- Create:
  - `backend/app/services/fudo_sale_parsing.py`
  - `backend/scripts/inspect_fudo_sales.py`
  - `backend/tests/fudo_sale_fakes.py`
  - `backend/tests/test_fudo_sale_parsing.py`

**Interfaces:**
- Produces:
  - `FudoClient.get_sales_page(start_iso: str, end_iso: str, page_number: int, page_size: int = 500) -> dict`, que devuelve `data` e `included`, con los `include` y `fields` de Global Constraints;
  - `FudoClient.first_sale_date() -> date | None`, la venta más antigua (`sort=createdAt`, `page[size]=1`);
  - `fudo_sale_parsing.index_included(included: list) -> dict[(type, id), dict]`;
  - `fudo_sale_parsing.parse_sale(raw: dict, included: dict) -> tuple[dict, list[dict]]`:
    - encabezado con las claves de `Sale` (`external_id` int, `fecha` = `business_date(cerrada or creacion)`, `creacion`, `cerrada`, `estado` en `Cerrada`/`Cancelada`/`Abierta`, `total` Decimal, `tipo_venta`, `personas`, `cliente`, `comentario`, `origen='Fudo'`, `id_origen=str(id)`, `source='fudo'`);
    - ítems con `fudo_item_id`, `fudo_product_id`, `product_name`, `category_name`, `quantity` Decimal, `unit_price` Decimal, `line_total` Decimal y `canceled` bool;
  - `FUDO_ITEM_PRICE_IS_UNIT = True`;
  - `tests/fudo_sale_fakes.py`:
    - `fudo_sale(id, closed_at, total, state='CLOSED', items=())`;
    - `fudo_item(id, product_id, quantity, price, canceled=False)`;
    - `fudo_product(id, name, category_id)`;
    - `fudo_category(id, name)`;
    - `FakeSalesClient(pages_by_month)`, que implementa `get_sales_page` y `first_sale_date`.

- [ ] **Step 1: Tests que fallan** en `tests/test_fudo_sale_parsing.py`:
  - `test_parse_closed_sale_with_items`:
    - una venta `CLOSED` cerrada `2026-03-10T02:30:00Z` y total `5400`, con dos ítems (2 × 900 `Medialuna`, categoría `Panadería`; 1 × 3600 `Latte`);
    - encabezado con `external_id == 123`, `estado == 'Cerrada'`, `fecha == date(2026, 3, 9)` (antes de las 6 h de Argentina) y `total == Decimal('5400.00')`;
    - ítems con `line_total` `1800.00` y `3600.00`, y `product_name`/`category_name` resueltos desde `included`.
  - `test_parse_cancelled_sale_and_cancelled_item`: `saleState='CANCELED'` da `estado == 'Cancelada'`, y un ítem con `canceled: true` da `canceled is True`.
  - `test_parse_item_without_product_in_included`: el producto no viene en `included`, así que da `product_name == 'Producto <id>'` y `category_name is None`, sin error.
  - `test_parse_rejects_sale_without_dates`: sin `closedAt` ni `createdAt` levanta `ValueError('fecha vacía')`.
- [ ] **Step 2:** `PY -m pytest -q -p no:cacheprovider tests/test_fudo_sale_parsing.py` → falla con ImportError.
- [ ] **Step 3: Implementar.**
  - **Cliente:** `get_sales_page` arma los parámetros exactos de Global Constraints; `first_sale_date` usa `sort=createdAt`, `page[size]=1`, `fields[sale]=createdAt` y devuelve la fecha en Argentina.
  - **Parser:** puro, sin acceso a la base. Usa `business_date` de `app.utils.timezone_utils` (del PR #23).
  - **Mapeo de `saleType`:** `TABLE` → `Local`, `COUNTER` → `Mostrador`, `DELIVERY` → `Delivery`, `TAKE_AWAY` → `Para llevar`; cualquier otro → `Local`.
  - **Script `inspect_fudo_sales.py`:** igual que `inspect_fudo_expenses.py`.
    - Pide una página de 5 ventas del último mes con los `include`/`fields` y, para cada tipo (`Sale`, `Item`, `Product`, `ProductCategory`), imprime los nombres de atributos y relaciones con un valor de ejemplo.
    - Nunca imprime `customerName`, `comment` ni nada de clientes.
    - Al final informa si `price × quantity` coincide con algún total de línea, para confirmar `FUDO_ITEM_PRICE_IS_UNIT`.
- [ ] **Step 4:** los tests pasan, junto con `tests/test_fudo_client_products.py`.
- [ ] **Step 5: Commit** `feat(fudo): sales client with items, pure sale parser and inspection script`.

---

### Task 2: Modelos y migración `b6a0_fudo_cutover`

**Files:**
- Create:
  - `backend/app/models/fudo_import.py` (`FudoSaleItem`, `FudoImportMonth`);
  - `backend/app/models/operation_settings.py`;
  - `backend/app/services/cutover.py`;
  - `backend/migrations/versions/b6a0_fudo_cutover.py`;
  - `backend/tests/test_cutover_models.py`.
- Modify:
  - `backend/app/models/__init__.py`;
  - `backend/app/models/sale.py` (relación `fudo_items`);
  - `backend/app/models/pos/sale.py` (`PosSale.is_practice`);
  - `backend/app/models/pos/cash.py` (`CashSession.is_practice`);
  - `backend/app/models/menu.py` (`MenuItemVariant.product_variant_id`, `MenuCategory.product_category_id`);
  - `backend/app/models/product_variant.py` (`menu_ignored`);
  - `backend/tests/test_migration_chain.py`.

**Interfaces:**
- Produces:
  - **`FudoSaleItem`** (`fudo_sale_items`):
    - columnas: `id`; `sale_id` FK `sales.id` con `ondelete CASCADE`; `fudo_item_id` String(30) único; `fudo_product_id` String(20) con índice; `product_name` String(200); `category_name` String(100) nullable; `quantity` Numeric(10,3); `unit_price` Numeric(12,2); `line_total` Numeric(12,2); `canceled` Boolean; `product_variant_id` FK `product_variants.id` nullable con `ondelete SET NULL`;
    - `Sale.fudo_items` relationship con `cascade='all, delete-orphan'`.
  - **`FudoImportMonth`** (`fudo_import_months`):
    - columnas: `month` Date PK (día 1); `status` (`pending`|`done`|`error`); `fudo_count` Integer; `fudo_total` Numeric(14,2); `galia_count` Integer; `galia_total` Numeric(14,2); `errors` JSON; `imported_at` DateTime; `run_id` FK `fudo_sync_runs.id` nullable;
    - propiedad `matches` → `fudo_count == galia_count and fudo_total == galia_total`.
  - **`OperationSettings`** (`operation_settings`): fila única `id=1` con `catalog_in_galia`, `fudo_off` y `practice_mode` (Boolean, default false), más `updated_at` y `updated_by`.
  - **`PosSale.is_practice`** y **`CashSession.is_practice`**: Boolean, not null, `server_default false`, con índice.
  - **Carta:**
    - `MenuItemVariant.product_variant_id`: FK `product_variants.id`, único, nullable, `ondelete SET NULL`;
    - `MenuCategory.product_category_id`: FK `product_categories.id`, único, nullable, `ondelete SET NULL`.
  - **`ProductVariant.menu_ignored`:** Boolean, default false.
  - **`app.services.cutover`:**
    - lectura: `get_settings() -> OperationSettings` (crea la fila si falta), `catalog_in_galia() -> bool`, `fudo_off() -> bool`, `practice_mode() -> bool`;
    - guardas: `require_fudo_on()` (PosError `Fudo está apagado`) y `require_fudo_catalog()` (PosError `El catálogo ya se maneja en Galia`).

- [ ] **Step 1: Tests que fallan** en `tests/test_cutover_models.py`:
  - `test_settings_singleton_defaults`: dos llamadas a `get_settings()` devuelven `id == 1`, y los tres flags valen `False`.
  - `test_fudo_item_cascade_and_unique`: borrar el `Sale` borra sus `FudoSaleItem`, y un `fudo_item_id` repetido levanta `IntegrityError`.
  - `test_require_fudo_on_and_catalog`: con `fudo_off=True`, `require_fudo_on()` levanta PosError (409) con ese mensaje; lo mismo con `catalog_in_galia` y `require_fudo_catalog()`.
  - `test_month_matches`.

  Además, en `test_migration_chain.py`: `test_fudo_cutover_follows_<cabeza>`.
- [ ] **Step 2:** los tests fallan.
- [ ] **Step 3: Implementar** los modelos y la migración. La migración es simétrica; usar `batch_alter_table` para las columnas nuevas y `server_default` false en los booleanos.
- [ ] **Step 4:** pasan `tests/test_cutover_models.py`, `tests/test_migration_chain.py`, `tests/test_menu_models.py` y `tests/test_pos_cash_models.py`.
- [ ] **Step 5: Commit** `feat(cutover): import, settings and practice models with migration b6a0`.

---

### Task 3: Importación de ventas de Fudo por mes

**Files:**
- Create:
  - `backend/app/services/fudo_sales_import.py`;
  - `backend/tests/test_fudo_sales_import.py`.
- Modify:
  - `backend/app/services/fudo_sync_runs.py` (`run_sales_import`);
  - `backend/app/routes/fudo_sync.py`: reemplazar `parse_fudo_sale` y `_sync_sales_background`, ajustar `/sync/sales` y agregar rutas;
  - `backend/tests/test_route_access_coverage.py`, si hace falta.

**Interfaces:**
- Consumes:
  - de la Task 1: `get_sales_page`, `first_sale_date`, `index_included`, `parse_sale`;
  - de la Task 2: `FudoSaleItem`, `FudoImportMonth`, `cutover.require_fudo_on`.
- Produces:
  - **`fudo_sales_import.import_month(client, month: date, run_id=None) -> dict`:**
    - pagina hasta que la página tenga menos de 500;
    - hace upsert del encabezado por `external_id` (actualiza todos los campos);
    - **reemplaza** los ítems de esa venta;
    - vincula `product_variant_id` por `ProductVariant.fudo_product_id`;
    - una venta que falla no frena: va a `errors` con id y mensaje;
    - escribe `FudoImportMonth` con `fudo_*` (lo que vino) y `galia_*` (`Sale` del mes con `source='fudo'` y estado `Cerrada`);
    - devuelve `{month, fudo_count, fudo_total, galia_count, galia_total, created, updated, total_changed, errors}`, donde `total_changed` cuenta los encabezados que existían y cambiaron de total o de estado.
  - **`fudo_sales_import.import_history(client, from_month: date | None = None, force: bool = False, run_id=None) -> dict`:**
    - recorre desde `from_month`, o desde `first_sale_date()`, hasta el mes actual;
    - saltea los meses `done`, salvo que `force` sea true o sea uno de los dos últimos meses;
    - commitea mes por mes, así que es reanudable;
    - devuelve `{months: [...], errors: n, changed_months: [...]}`.
  - **`fudo_sales_import.import_range(client, start: date, end: date, run_id=None)`:** llama a `import_month` para cada mes que toca el rango.
  - **`fudo_sync_runs.run_sales_import(app, run_id, mode, params, client_factory)`:** con `mode` en `history` o `range`; usa `kind='sales'`.
  - **Rutas:**
    - `POST /api/v1/fudo/sync/sales?start_date&end_date` (rango, 202 con `run_id`);
    - `POST /api/v1/fudo/sync/sales/history?from_month=YYYY-MM&force=false` (202);
    - `GET /api/v1/fudo/import/months`, que devuelve `{months: [{month, status, fudo_count, fudo_total, galia_count, galia_total, matches, errors}]}`;
    - todas son admin y llaman a `require_fudo_on()` (409 si Fudo está apagado).

- [ ] **Step 1: Tests que fallan** en `tests/test_fudo_sales_import.py` (con `FakeSalesClient`):
  - `test_import_month_creates_sales_and_items`: 2 ventas; los `Sale` tienen `source == 'fudo'`, los `FudoSaleItem` tienen sus `line_total`, y `FudoImportMonth.matches` es true.
  - `test_import_month_paginates`: una página de 500 y otra de 3 → 503 ventas; `fudo_count == galia_count == 503`.
  - `test_import_twice_is_idempotent`: la segunda corrida no crea ni duplica ítems.
  - `test_reimport_updates_cancelled_sale`: una venta pasa a `CANCELED` → `estado == 'Cancelada'`, `total_changed == 1` y `galia_count` baja en 1.
  - `test_links_variant_by_fudo_product_id`: hay una `ProductVariant(fudo_product_id='77')` y el ítem queda con ese `product_variant_id`; un producto sin vínculo queda con `None`.
  - `test_bad_sale_does_not_stop_month`: una venta sin fechas va a `errors` y el resto se importa.
  - `test_history_resumes_and_skips_done_months`: tres meses; el primero ya está `done` y tiene más de dos meses de antigüedad, así que no se pide a Fudo.
  - `test_sync_routes_blocked_when_fudo_off`: `POST /fudo/sync/sales/history` responde 409 con `Fudo está apagado`.
- [ ] **Step 2:** los tests fallan.
- [ ] **Step 3: Implementar.** El hilo en segundo plano sigue el patrón de `run_expenses_sync`. Cambia el modal de ventas del frontend: `fudoService.syncSales` ahora recibe `run_id`, como el de gastos. Ajustar `FudoSyncSalesModal.jsx` para que muestre la corrida con `syncRunSummary`.
- [ ] **Step 4:** pasan `tests/test_fudo_sales_import.py`, `tests/test_fudo_sync_runs.py` y `tests/test_route_access_coverage.py`, y `npm test` en el frontend.
- [ ] **Step 5: Commit** `feat(fudo): month-by-month sales import with items, idempotent and resumable`.

---

### Task 4: Reporte "Ventas por producto" (backend)

**Files:**
- Create:
  - `backend/app/services/reports/product_sales.py` (crear `backend/app/services/reports/__init__.py` si no existe);
  - `backend/tests/test_product_sales_report.py`.
- Modify: `backend/app/routes/reports.py`.

**Interfaces:**
- Consumes: `FudoSaleItem` y `Sale` (Task 2 y 3), `PosSaleItem`, `PosSale.is_practice`.
- Produces:
  - **`product_sales.ranking(month_a: date, month_b: date) -> dict`:**
    - estructura: `{months: ['2026-09', '2026-10'], products: [{key, name, category, a: {quantity, amount}, b: {...}, variants: [{name, a, b}]}], totals: {a, b}}`;
    - montos y cantidades como strings con 2 y 3 decimales.
  - **`product_sales.daily(key: str, month_a: date, month_b: date) -> dict`:** `{days: [{day, a: {quantity, amount}, b: {...}}]}`, día 1 a 31 de cada mes.
  - **Clave de producto:**
    - `p:<Product.id>` para ítems de Galia y ítems de Fudo con `product_variant_id`;
    - `f:<fudo_product_id>` para ítems de Fudo sin vínculo, con el nombre del ítem importado más reciente.
  - **Variantes:** por nombre de variante (Galia) o `product_name` (Fudo sin vínculo).
  - **Qué cuenta:**
    - Fudo: `Sale.source == 'fudo'`, `estado == 'Cerrada'`, `FudoSaleItem.canceled` false, por `Sale.fecha`;
    - Galia: `PosSale.status == 'closed'`, `is_practice` false, ítems `confirmed`, por `PosSale.business_date`, monto `line_total`.
  - **Rutas:** `GET /api/v1/reports/products?month_a=YYYY-MM&month_b=YYYY-MM` y `GET /api/v1/reports/products/<key>/daily?...`, ambas con `@module_required('Reports')`. Un parámetro inválido responde 400.

- [ ] **Step 1: Tests que fallan** en `tests/test_product_sales_report.py`:
  - `test_ranking_mixes_fudo_and_galia`: septiembre con 3 medialunas de Fudo (vinculadas al `Product` Medialuna) y octubre con 2 del POS; un solo producto `p:<id>` con `a.quantity == '3.000'` y `b.quantity == '2.000'`.
  - `test_amount_is_without_sale_discount`: una venta del POS con un descuento de venta del 20 % cuenta el `line_total` completo.
  - `test_ranking_excludes_cancelled`: no cuentan una venta de Fudo `Cancelada`, un ítem de Fudo `canceled`, un ítem del POS `cancelled` ni una venta del POS `cancelled`.
  - `test_ranking_excludes_practice`: no cuenta una venta del POS cerrada con `is_practice=True`.
  - `test_ranking_unlinked_fudo_product_by_name`: un ítem de Fudo sin vínculo aparece con la clave `f:99` y `name == 'Torta vieja'`.
  - `test_variants_breakdown`: Latte Chico y Grande se suman en el producto y aparecen separados en `variants`.
  - `test_daily_detail`: `daily('p:<id>', ...)` devuelve los días con sus valores.
  - `test_routes_permission_and_validation`: sin el módulo Reports responde 403, y `month_a=2026-13` responde 400.
- [ ] **Step 2:** los tests fallan.
- [ ] **Step 3: Implementar** con dos consultas agregadas (Fudo y Galia) por día, producto y variante, unidas en Python. No cargar ítems uno por uno.
- [ ] **Step 4:** pasan `tests/test_product_sales_report.py` y `tests/test_route_access_coverage.py`.
- [ ] **Step 5: Commit** `feat(reports): product sales ranking comparing two months (Fudo + POS)`.

---

### Task 5: Modo práctica (backend)

**Files:**
- Create:
  - `backend/app/services/pos/practice.py`;
  - `backend/tests/test_pos_practice.py`.
- Modify:
  - `backend/app/services/cutover.py` (`set_flags`);
  - `backend/app/services/pos/sale_service.py` (`open_sale` marca la venta);
  - `backend/app/services/pos/cash_service.py` (`open_session` marca la caja, `_create_expense` no corre en práctica, `list_sessions` y `unassigned_payments` excluyen práctica);
  - `backend/app/services/pos/projection.py` (`project`/`unproject` no hacen nada en práctica);
  - `backend/app/services/pos/stock_hooks.py` (`consume`/`restore` ignoran ítems de ventas de práctica);
  - `backend/app/services/pos/print_documents.py` (título con `PRÁCTICA`);
  - `backend/app/services/fiscal/invoice_service.py` (`issue` rechaza);
  - `backend/app/services/mercadopago/point_service.py` (`start` rechaza);
  - `backend/app/routes/mercadopago.py` (`point-config` da `enabled: false` en práctica);
  - `backend/app/services/mercadopago/reconciliation_service.py` (`_galia_payments` excluye práctica);
  - `backend/app/services/pos/serializers.py` (`sale_to_dict` agrega `is_practice`).

**Interfaces:**
- Consumes: de la Task 2, `cutover.practice_mode()`, `PosSale.is_practice` y `CashSession.is_practice`.
- Produces:
  - **`cutover.set_flags(user, catalog_in_galia=None, fudo_off=None, practice_mode=None) -> OperationSettings`**, que exige admin.
    - **Prender `practice_mode`:**
      - error si hay una `CashSession` real abierta: `Cerrá la caja antes de entrar en modo práctica`;
      - error si hay una `PosSale` real en `open` o `billing`: `Hay ventas reales abiertas`.
    - **Apagarlo:**
      - error si hay una caja de práctica abierta: `Cerrá la caja de práctica antes de salir`;
      - error si hay ventas de práctica abiertas: `Hay ventas de práctica abiertas`.
    - **`fudo_off=True`:** exige `catalog_in_galia` y si no da el error `Primero pasá el catálogo a Galia`.
    - **`catalog_in_galia=True`:** llama a `menu_catalog_sync.link_to_catalog()` (Task 6). Hasta que exista, se importa de forma diferida dentro de la función.
  - **`practice.clear_practice(user) -> dict`:**
    - es admin y exige `practice_mode` apagado;
    - borra todo lo de ventas y cajas de práctica y sus dependencias (ítems, modificadores, descuentos, pagos, eventos, trabajos de impresión, movimientos, conteos, eventos de caja);
    - devuelve los conteos `{sales, cash_sessions}`.

- [ ] **Step 1: Tests que fallan** en `tests/test_pos_practice.py`:
  - `test_practice_does_not_touch_real_numbers`, con el modo prendido:
    - se abre una caja (queda `is_practice`);
    - una venta (queda `is_practice`) con una medialuna con stock;
    - se confirma, se cobra en efectivo y se cierra;
    - un gasto de caja.
    - Resultado: el stock no cambió, no hay `Sale` ni `Expense` nuevos y `list_sessions` no muestra la caja.
  - `test_practice_blocks_invoice_and_point`: `invoice_service.issue` sobre una venta de práctica levanta `En modo práctica no se factura`, y `point_service.start` levanta `En modo práctica no se cobra con el Point`.
  - `test_practice_print_header`: `receipt_document(sale)` y `order_document(...)` de una venta de práctica tienen `PRÁCTICA` en el título.
  - `test_toggle_rules`:
    - no se puede prender con una caja real abierta;
    - no se puede apagar con una caja de práctica abierta;
    - `fudo_off` sin catálogo da error.
  - `test_clear_practice`: después de apagar el modo, `clear_practice` borra las ventas y cajas de práctica y no toca las reales.
  - `test_reconciliation_ignores_practice_payments`: un pago de práctica con un medio de MercadoPago no aparece en `day()`.
- [ ] **Step 2:** los tests fallan.
- [ ] **Step 3: Implementar** los guardas del lado del backend, cada uno en el archivo indicado. Las rutas de admin para `set_flags` y `clear_practice` van en la Task 7.
- [ ] **Step 4:** pasan `tests/test_pos_practice.py` y `tests/test_pos_*.py`, `tests/test_fiscal_*.py` y `tests/test_mp_*.py`, sin fallas nuevas.
- [ ] **Step 5: Commit** `feat(pos): practice mode that never touches real numbers`.

---

### Task 6: Carta sobre el catálogo de Galia

**Files:**
- Create:
  - `backend/app/services/menu_catalog_sync.py`;
  - `backend/tests/test_menu_catalog_sync.py`.
- Modify:
  - `backend/app/tasks/menu_tasks.py`;
  - `backend/app/routes/menu.py` ("sincronizar" de la carta, y `ignore` de ítems);
  - `backend/app/services/menu_sync_service.py` (`alert_variants` y `new_items` siguen sirviendo con `fudo_status` como estado del vínculo).

**Interfaces:**
- Consumes: de la Task 2, `MenuItemVariant.product_variant_id`, `MenuCategory.product_category_id`, `ProductVariant.menu_ignored` y `cutover.catalog_in_galia()`.
- Produces:
  - **`menu_catalog_sync.link_to_catalog() -> dict`**, idempotente:
    - vincula por `fudo_product_id` y `fudo_category_id`;
    - devuelve `{variants_linked, variants_unlinked, categories_linked}`;
    - las variantes sin vínculo quedan con `fudo_status='missing'`, así que aparecen en la bandeja.
  - **`menu_catalog_sync.sync_from_catalog() -> dict`**, con la misma forma que `sync_fudo_products` (`price_changes`, `alerts`, `categories_created`, `items_created`):
    - **precio:** el de `ProductVariant.price`;
    - **estado:** `ok`, `inactive` (variante o producto inactivo) o `missing` (sin `product_variant_id`);
    - **categoría:** `MenuCategory.product_category_id` según `Product.category_id` de la primera variante vinculada; las categorías nuevas de Galia se crean al final, sin grupo;
    - **variantes nuevas:** cada `ProductVariant` activa, no ignorada y sin vínculo se suma al ítem de la carta que ya tiene otra variante del mismo `Product`. Si no hay ninguno, crea un `MenuItem` oculto con `name=Product.name` y `label=variant.name`, o `None` si el producto tiene una sola variante;
    - **nunca cambia** `MenuItem.name`, `description`, imagen, tags ni orden.
  - **`menu_tasks.sync_and_publish(client, storage)`:**
    - usa `sync_from_catalog()` si `cutover.catalog_in_galia()`, y si no `sync_fudo_products(client)`;
    - el `__main__` no crea `FudoClient` si el catálogo está en Galia;
    - la regla de publicación automática no cambia.
  - **Rutas de la carta:**
    - el endpoint que hoy llama a `sync_fudo_products` (`menu.py:613`) llama a `sync_from_catalog()` con el catálogo en Galia;
    - `POST /items/<id>/ignore` marca `ProductVariant.menu_ignored` en lugar de `FudoProduct.ignored` con el catálogo en Galia.

- [ ] **Step 1: Tests que fallan** en `tests/test_menu_catalog_sync.py` (fakes de `tests/menu_fakes.py` y `pos_helpers.make_catalog`):
  - `test_link_to_catalog_by_fudo_ids`: un ítem de la carta con `fudo_product_id='77'` y una `ProductVariant` con el mismo id quedan vinculados; los demás quedan `missing`; correrlo dos veces da lo mismo.
  - `test_sync_from_catalog_updates_price_and_publishes_flag`: se cambia el precio en Galia → `price_changes == 1`, y `sync_and_publish` publica si no había borradores.
  - `test_sync_from_catalog_keeps_owner_text_and_flags_inactive`: el dueño renombró el ítem y le puso descripción; se desactiva la variante en Galia → `fudo_status == 'inactive'`, el ítem sigue existiendo y el nombre y la descripción no cambian.
  - `test_new_galia_product_creates_hidden_item`: un `Product` nuevo con dos variantes crea un `MenuItem` oculto con dos variantes etiquetadas.
  - `test_ignored_variant_not_recreated`.
  - `test_tasks_use_catalog_when_switched`: con `catalog_in_galia` en true, `sync_and_publish(None, storage)` no llama a Fudo.
- [ ] **Step 2:** los tests fallan.
- [ ] **Step 3: Implementar.**
- [ ] **Step 4:** pasan `tests/test_menu_catalog_sync.py`, `tests/test_menu_*.py` y `tests/test_public_menu.py`.
- [ ] **Step 5: Commit** `feat(menu): build the digital menu from the Galia catalog`.

---

### Task 7: API de corte y bloqueo de Fudo

**Files:**
- Create:
  - `backend/app/routes/cutover.py`;
  - `backend/tests/test_cutover_api.py`.
- Modify:
  - `backend/app/__init__.py`;
  - `backend/app/routes/products.py` (`products.py:424`: `require_fudo_catalog()`);
  - `backend/app/routes/fudo_sync.py` (`/sync/expenses`: `require_fudo_on()`);
  - `backend/app/routes/menu.py`, con el catálogo en Galia ya resuelto en la Task 6. Con Fudo apagado y sin catálogo no se llega, porque `fudo_off` exige catálogo.

**Interfaces:**
- Produces:
  - `GET /api/v1/system/cutover`: devuelve `{catalog_in_galia, fudo_off, practice_mode}` a cualquier usuario autenticado, porque el frontend lo necesita para la franja y los botones;
  - `PUT /api/v1/system/cutover`: admin, llama a `set_flags`;
  - `POST /api/v1/system/cutover/clear-practice`: admin, llama a `clear_practice`;
  - las respuestas de error usan el `status` del `PosError`.

- [ ] **Step 1: Tests que fallan** en `tests/test_cutover_api.py`:
  - `test_get_cutover_any_user`.
  - `test_put_requires_admin`.
  - `test_enable_catalog_links_menu`: el PUT con `catalog_in_galia` en true deja la carta vinculada.
  - `test_product_sync_blocked_with_catalog_in_galia`: la ruta de sync de productos responde 409 con `El catálogo ya se maneja en Galia`.
  - `test_expenses_sync_blocked_when_fudo_off`.
  - `test_clear_practice_route`.
- [ ] **Step 2:** los tests fallan.
- [ ] **Step 3: Implementar.** Agregar `cutover.get_cutover` a la lista de rutas con control de acceso, si `test_route_access_coverage` lo pide.
- [ ] **Step 4:** pasan `tests/test_cutover_api.py` y `tests/test_route_access_coverage.py`.
  - Después, **la suite completa** contra la línea base: `Sin fallas nuevas.`
- [ ] **Step 5: Commit** `feat(cutover): cutover switches API and Fudo blocking`.

---

### Task 8: Reporte "Ventas por producto" (frontend)

**Files:**
- Create:
  - `frontend/src/reports/productRanking.js` (+ `.test.js`);
  - `frontend/src/pages/ProductSalesReport.jsx`.
- Modify:
  - `frontend/src/App.jsx` (ruta `/reports/products`, módulo `Reports`);
  - `frontend/src/components/layout/Sidebar.jsx` (en Análisis: `{ to: '/reports/products', label: 'Ventas por producto', module: 'Reports' }`);
  - `frontend/src/services/` (un `reportsService.productSales(monthA, monthB)` y `productDaily(key, monthA, monthB)`, siguiendo el servicio de reportes existente).

**Interfaces:**
- Consumes: las rutas de la Task 4.
- Produces (`productRanking.js`):
  - `rankProducts(products, measure: 'amount'|'quantity') -> products` ordenados por `b[measure]` descendente, y a igualdad por nombre;
  - `variation(a, b) -> number | null`: el % redondeado a entero, `null` si `a` es 0;
  - `barWidths(products, measure) -> [{key, a: pct, b: pct}]`: el máximo de los dos meses es 100;
  - `defaultMonths(today) -> [prev, current]` en formato `YYYY-MM`.

- [ ] **Step 1: Tests que fallan** en `productRanking.test.js`, con orden por monto y por cantidad, `variation(100, 121) === 21`, `variation(0, 5) === null`, el máximo en 100 y `defaultMonths(new Date('2026-10-20')) → ['2026-09', '2026-10']`.
- [ ] **Step 2:** `npx vitest run src/reports` falla.
- [ ] **Step 3: Implementar la lógica y la página** según el boceto "B" elegido por el dueño:
  - dos selectores de mes y el selector `Ver: monto | cantidad`;
  - una fila por producto, con dos barras (gris para el mes A, color de marca para el B) y la variación en verde ▲ o rojo ▼;
  - al tocar un producto se despliegan las variantes y el detalle día por día (`productDaily`);
  - estados de carga, error y "sin ventas".
- [ ] **Step 4:** pasan `npm test` y `npm run build`.
- [ ] **Step 5: Commit** `feat(reports): product sales ranking page`.

---

### Task 9: Pantalla "Corte con Fudo", franja de práctica y botones de Fudo

**Files:**
- Create:
  - `frontend/src/pages/admin/FudoCutover.jsx`;
  - `frontend/src/services/cutoverService.js`;
  - `frontend/src/hooks/useCutover.js`;
  - `frontend/src/pos/ui/PracticeBanner.jsx`.
- Modify:
  - `frontend/src/App.jsx` y `Sidebar.jsx` (Sistema → "Corte con Fudo", admin);
  - las pantallas del POS, Camarero y la caja (mostrar `PracticeBanner`);
  - el botón "Facturar" del POS (oculto si `sale.is_practice`);
  - los botones "Sincronizar con Fudo" de Ventas, Gastos, Productos y Carta (ocultos según los interruptores; en la carta, con el catálogo en Galia el botón dice "Actualizar desde el catálogo").

**Interfaces:**
- Consumes: las rutas de las Tasks 3 y 7.
- Produces:
  - `useCutover()`: un hook con React Query (`['cutover']`, `staleTime` de 60 s) que devuelve `{catalog_in_galia, fudo_off, practice_mode}`.

- [ ] **Step 1: Pantalla "Corte con Fudo"**, en cuatro bloques y en este orden:
  1. **Historia de Fudo:**
     - botón "Importar historia" (`POST /fudo/sync/sales/history`), con el seguimiento de la corrida;
     - tabla de meses con estado, ventas y total de Fudo y de Galia, y ✓ o ⚠ según `matches`;
     - aviso de los meses con totales cambiados.
  2. **Modo práctica:**
     - interruptor con confirmación;
     - botón "Borrar práctica", habilitado solo con el modo apagado y con confirmación;
     - los errores del backend se muestran tal cual.
  3. **Catálogo en Galia:** interruptor con confirmación ("Desde ahora los precios y productos se editan en Galia; Fudo deja de actualizarlos") y el resultado del vínculo de la carta (variantes sin vínculo → enlace a la bandeja de la carta).
  4. **Fudo apagado:** interruptor deshabilitado mientras el catálogo no esté en Galia, con confirmación.
- [ ] **Step 2: Franja de práctica.** `PracticeBanner` muestra `PRÁCTICA: nada de esto cuenta` cuando `practice_mode` está prendido, arriba del POS, Camarero y la caja, con un estilo bien visible (fondo ámbar).
- [ ] **Step 3: Botones.** Ocultar "Sincronizar con Fudo" con `fudo_off` y la sync de productos con `catalog_in_galia`, y ocultar "Facturar" en ventas de práctica.
- [ ] **Step 4:** pasan `npm test` y `npm run build`.
- [ ] **Step 5: Commit** `feat(cutover): Fudo cutover page, practice banner and Fudo buttons`.

---

### Task 10: Guía de caja y verificación final

**Files:**
- Create: `docs/pos/guia-caja.md`, y `docs/pos/img/` si se capturan imágenes.
- Modify: `docs/pos/` (enlace desde las guías existentes, si hay un índice).

- [ ] **Step 1: Guía** `docs/pos/guia-caja.md`, corta y para imprimir.
  - Cubre:
    - abrir la caja (fondo inicial);
    - cobrar en efectivo, con tarjeta y con el Point;
    - anular un pago;
    - movimientos (gasto, retiro, ingreso);
    - cerrar la caja y el arqueo;
    - qué hacer si el arqueo no cierra;
    - qué hacer si Galia falla: pasar a Fudo y **no** cargar la misma venta en los dos sistemas;
    - qué es la franja de práctica.
  - Usar los nombres exactos de botones y pantallas de Galia.
  - Si hay un navegador que guarde capturas (MCP de Playwright `browser_take_screenshot`), agregar capturas del preview en `docs/pos/img/`. Si no, la guía va sin imágenes, y se anota en el ledger.
- [ ] **Step 2: Suites completas.** Backend contra la línea base, `npm test` y `npm run build`.
- [ ] **Step 3: Preview** con SQLite, Fudo simulado y `POS_DEMO_SEED=1`. Para la historia, un script del scratchpad que usa `FakeSalesClient` con 3 meses.
  - Importar la historia → la tabla de meses queda en ✓.
  - Reporte por producto → comparar dos meses, el toggle monto/cantidad y el detalle diario.
  - Modo práctica → franja visible, abrir la caja, una venta cobrada en efectivo, cerrar la caja; el reporte y Cajas no la muestran; apagar y "Borrar práctica".
  - "Catálogo en Galia" → cambiar un precio en Productos y "Actualizar desde el catálogo" en la carta; el precio cambia en la carta.
  - "Fudo apagado" → desaparecen los botones de sincronizar con Fudo.
- [ ] **Step 4: Commit** `docs(pos): cash register guide for the team`.
