# Corte con Fudo (sub-proyecto 6) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apagar Fudo sin perder la historia:
- toda la historia de ventas de Fudo, con sus productos;
- comparación de ventas por producto mes contra mes;
- carta sobre el catálogo de Galia;
- modo práctica;
- dos interruptores de corte;
- guía de caja para el equipo.

**Architecture:** se apoya en lo que ya trajo el PR #25 a `main`:
- la tabla `sale_items`, que guarda ítems de Fudo y del POS con la misma forma;
- la sync de ventas arreglada (`sale_fudo_parsing`, `sales_sync_service.apply_fudo_sales`);
- el script `scripts/inspect_fudo_sales.py`;
- `GET /reports/products` y la pestaña "Productos" de Reportes.

Sobre eso se agrega:
- **Importación de la historia:** mes por mes, con control por mes (`fudo_import_months`), como corrida de `fudo_sync_runs`.
- **Comparación de dos meses:** ranking con barras.
- **Configuración:** una fila (`operation_settings`) con "Catálogo en Galia", "Fudo apagado" y "Modo práctica".
- **Marca de práctica:** `is_practice` en `pos_sales` y `cash_sessions`, con guardas en el backend.
- **Vínculo de la carta con el catálogo:** `product_variant_id` y `product_category_id`.

**Tech Stack:** Flask, SQLAlchemy 2, Alembic, pytest, React 18, React Query 5, Tailwind, Vitest.

**Spec:** `docs/superpowers/specs/2026-10-20-pos-corte-fudo-design.md`. El spec del #25 (`docs/superpowers/specs/2026-10-20-reports-products-design.md`) explica `sale_items` y el reporte existente.

## Global Constraints

- **Worktree:** `C:\Users\onofr\Desktop\galia-app\.claude\worktrees\pos-base`, rama `feature/pos-corte-fudo`.
  - **Antes de la Task 1** hay que mergear `origin/main` en la rama: trae #23 (fecha comercial, `b5c0`) y #25 (`sale_items`, `b5d0`).
  - Rutas relativas a esa raíz.
- **Python** (`PY`): `C:\Users\onofr\Desktop\galia-app\backend\venv\Scripts\python.exe`. Los tests corren con cwd `backend/`: `PY -m pytest -q -p no:cacheprovider <archivos>`.
- **Frontend:** con cwd `frontend/`: `npm test`, `npm run build`, `npx vitest run <archivo>`. Vitest corre solo lógica pura, en entorno node.
- **Git:** solo `git -C <worktree>`, un comando por llamada.
- **Línea base:** `PY scripts/compare_baseline.py <salida> ../docs/superpowers/plans/2026-10-08-pos-base-test-baseline.txt` tiene que dar `Sin fallas nuevas.`
- **Migración nueva:** `b6a0_fudo_cutover`, con `down_revision` igual a la cabeza vigente (`b5d0_add_sale_items`). Lleva su test en `tests/test_migration_chain.py`.
- **Fudo:**
  - La importación de la historia pide `saleState` `in.(CLOSED,CANCELED)`. Así, una venta que Fudo anuló después de importada se actualiza a `Cancelada`.
  - El resto de los parámetros (`include`/`fields`) son los de `sale_fudo_parsing.request_params()`.
  - Los nombres se confirman con `scripts/inspect_fudo_sales.py` antes de importar en producción. Lo corre el dueño.
- **Qué cuenta en los reportes:**
  - `sales.estado == 'Cerrada'`.
  - Montos de `sale_items.total`: cantidad × precio, **sin descontar** los descuentos de la venta (decisión del dueño).
  - Las ventas de práctica nunca llegan a `sales` porque no se proyectan.
- **Textos de la interfaz:**
  - Franja: `PRÁCTICA: nada de esto cuenta`.
  - Encabezado de documentos de práctica: `PRÁCTICA`.
  - Errores:
    - `Fudo está apagado`
    - `El catálogo ya se maneja en Galia`
    - `En modo práctica no se factura`
    - `En modo práctica no se cobra con el Point`
- **Errores en el backend:** `PosError` (409) y `bad_request` (400) de `app.services.pos.errors`.

## Review Focus

1. **Un mes de Fudo con más de una página de ventas (más de 500):** se importan todas, y el control del mes coincide con Fudo. Lo cubre la Task 2 (`test_import_month_paginates`).
2. **Una venta que Fudo anuló después de importada:** al reimportar queda `Cancelada` y deja de contar en la comparación. Lo cubren la Task 2 (`test_reimport_updates_cancelled_sale`) y la Task 3 (`test_compare_excludes_cancelled`).
3. **Gasto desde una caja de práctica y venta de práctica cerrada:** no hay `Expense`, ni fila en `sales`, ni movimiento de stock. Lo cubre la Task 4 (`test_practice_does_not_touch_real_numbers`).
4. **Ítem de Fudo sin producto vinculado en Galia:** la comparación lo muestra con el nombre guardado. Lo cubre la Task 3 (`test_compare_unlinked_item_by_name`).
5. **Variante de Galia desactivada después del paso al catálogo:** queda `inactive` en la carta, el ítem no se borra y el texto del dueño no cambia. Lo cubre la Task 5 (`test_sync_from_catalog_keeps_owner_text_and_flags_inactive`).

---

### Task 1: Modelos, migración `b6a0_fudo_cutover` y servicio de interruptores

**Files:**
- Create:
  - `backend/app/models/operation_settings.py` (`OperationSettings`, `FudoImportMonth`)
  - `backend/app/services/cutover.py`
  - `backend/migrations/versions/b6a0_fudo_cutover.py`
  - `backend/tests/test_cutover_models.py`
- Modify:
  - `backend/app/models/__init__.py`
  - `backend/app/models/pos/sale.py` (`PosSale.is_practice`)
  - `backend/app/models/pos/cash.py` (`CashSession.is_practice`)
  - `backend/app/models/menu.py` (`MenuItemVariant.product_variant_id`, `MenuCategory.product_category_id`)
  - `backend/app/models/product_variant.py` (`menu_ignored`)
  - `backend/tests/test_migration_chain.py`

**Interfaces:**
- Produces:
  - **`OperationSettings`** (tabla `operation_settings`): fila única `id=1`.
    - Booleanos `catalog_in_galia`, `fudo_off` y `practice_mode` (default false).
    - `updated_at` y `updated_by` (FK `users.id`, nullable).
  - **`FudoImportMonth`** (tabla `fudo_import_months`):
    - Columnas:
      - `month`: Date, PK, día 1.
      - `status`: `pending`, `done` o `error`.
      - `fudo_count` y `galia_count`: Integer.
      - `fudo_total` y `galia_total`: Numeric(14,2).
      - `changed`: Integer, encabezados que ya existían y cambiaron de total o estado.
      - `errors`: JSON.
      - `imported_at`: DateTime.
      - `run_id`: FK `fudo_sync_runs.id`, nullable.
    - Propiedad `matches`: `fudo_count == galia_count and fudo_total == galia_total`.
  - **`PosSale.is_practice`** y **`CashSession.is_practice`**: Boolean, not null, `server_default false`, con índice.
  - **`MenuItemVariant.product_variant_id`**: FK `product_variants.id`, único, nullable, `ondelete SET NULL`.
  - **`MenuCategory.product_category_id`**: FK `product_categories.id`, único, nullable, `ondelete SET NULL`.
  - **`ProductVariant.menu_ignored`**: Boolean, not null, default false.
  - **`app.services.cutover`**:
    - `get_settings()`: crea la fila si falta.
    - Lectura: `catalog_in_galia()`, `fudo_off()` y `practice_mode()` devuelven bool.
    - `require_fudo_on()`: lanza `PosError('Fudo está apagado')`.
    - `require_fudo_catalog()`: lanza `PosError('El catálogo ya se maneja en Galia')`.

- [ ] **Step 1: Tests que fallan** en `tests/test_cutover_models.py`:
  - `test_settings_singleton_defaults`: dos llamadas devuelven `id == 1` y los flags quedan `False`.
  - `test_require_fudo_on_and_catalog`: con el flag prendido, levanta `PosError` (409) con el mensaje exacto.
  - `test_month_matches`.
  - `test_practice_flags_default_false`: una `PosSale` y una `CashSession` nuevas quedan `is_practice is False`.

  Además, en `test_migration_chain.py`: `test_fudo_cutover_follows_sale_items` (`b6a0_fudo_cutover` → `b5d0_add_sale_items`).
- [ ] **Step 2:** los tests fallan.
- [ ] **Step 3:** implementar los modelos y la migración (simétrica, `batch_alter_table`, booleanos con `server_default`).
- [ ] **Step 4:** pasan `tests/test_cutover_models.py`, `tests/test_migration_chain.py`, `tests/test_menu_models.py` y `tests/test_pos_cash_models.py`.
- [ ] **Step 5: Commit** `feat(cutover): settings, import months, practice flags and menu catalog links (b6a0)`.

---

### Task 2: Importación de la historia de Fudo, mes por mes

**Files:**
- Create:
  - `backend/app/services/fudo_sales_import.py`
  - `backend/tests/fudo_sale_fakes.py`
  - `backend/tests/test_fudo_sales_import.py`
- Modify:
  - `backend/app/utils/fudo_client.py`
  - `backend/app/services/fudo_sync_runs.py`
  - `backend/app/routes/fudo_sync.py`
  - `frontend/src/services/fudoService.js` (solo los métodos nuevos)

**Interfaces:**
- Consumes:
  - de main: `sales_sync_service.apply_fudo_sales(payload, update_existing)` y `sale_fudo_parsing.request_params()`;
  - de la Task 1: `FudoImportMonth` y `cutover.require_fudo_on`.
- Produces:
  - **`FudoClient.get_all_sales_with_included(start_date=None, end_date=None, states=('CLOSED',))`**: parámetro nuevo `states`, que da `filter[saleState]=in.(<states>)`. El comportamiento por defecto no cambia.
  - **`FudoClient.first_sale_date() -> date | None`**: la venta más antigua, con `sort=createdAt`, `page[size]=1` y `fields[sale]=createdAt`. Devuelve la fecha en Argentina.
  - **`fudo_sales_import.import_month(client, month: date, run_id=None) -> dict`**:
    1. pide el mes completo (`states=('CLOSED','CANCELED')`, de 00:00 del día 1 a 23:59:59 del último día, en UTC);
    2. aplica con `apply_fudo_sales(payload, update_existing=True)` y cuenta en `changed` los encabezados que existían y cambiaron de `total` o `estado`;
    3. calcula `fudo_*` sobre las ventas `CLOSED` recibidas;
    4. calcula `galia_*` sobre las `Sale` con `source='fudo'`, `estado='Cerrada'` y `fecha` en el mes;
    5. hace upsert de `FudoImportMonth` y commit.
    - Devuelve `{month, fudo_count, fudo_total, galia_count, galia_total, matches, changed, errors}`.
  - **`fudo_sales_import.import_history(client, from_month: date | None = None, force: bool = False, run_id=None) -> dict`**:
    - recorre desde `from_month`, o desde el mes de `first_sale_date()`, hasta el mes actual;
    - saltea los meses `done`, salvo que pidan `force` o sean los dos últimos;
    - hace commit por mes, así que es reanudable;
    - devuelve `{months: [...], errors: n, changed_months: ['YYYY-MM', ...]}`.
  - **`fudo_sync_runs.run_sales_history(app, run_id, from_month, force, client_factory)`**: corre con `kind='sales_history'`.
  - **Rutas** (admin, con `require_fudo_on()` en las POST; 409 si hay una corrida en curso):
    - `POST /api/v1/fudo/sync/sales/history?from_month=YYYY-MM&force=false`: responde 202 con `run_id`.
    - `GET /api/v1/fudo/import/months`: devuelve `{months: [...]}`, del más nuevo al más viejo.
  - `POST /fudo/sync/sales` (la ruta existente) también llama a `require_fudo_on()`.
  - **`tests/fudo_sale_fakes.py`**:
    - `fudo_sale(id, closed_at, total, state='CLOSED', items=())`
    - `fudo_item(id, product_id, quantity, price, canceled=False)`
    - `fudo_product(id, name, category_id)`
    - `fudo_category(id, name)`
    - `FakeSalesClient(sales_by_month: dict[str, list], first: date)`, con `get_all_sales_with_included(start_date, end_date, states)` y `first_sale_date()`.
  - Los payloads del fake tienen la forma que espera `sale_fudo_parsing`.

- [ ] **Step 1: Tests que fallan** en `tests/test_fudo_sales_import.py`:
  - `test_import_month_creates_sales_with_items`: 2 ventas → `Sale` con `source == 'fudo'`, sus `SaleItem` y `matches`.
  - `test_import_month_paginates`: el fake devuelve 503 ventas → `fudo_count == galia_count == 503`. Agregar además un test del cliente con dos páginas (500 + 3), siguiendo el patrón de `test_fudo_client_products.py`.
  - `test_import_twice_is_idempotent`: la segunda corrida no duplica `Sale` ni `SaleItem`, y `changed == 0`.
  - `test_reimport_updates_cancelled_sale`: la venta pasa a `CANCELED` → `estado == 'Cancelada'`, `changed == 1` y `galia_count` baja en 1.
  - `test_bad_sale_does_not_stop_month`: una venta inválida va a `errors` y el resto se importa.
  - `test_history_resumes_and_skips_done_months`: con 4 meses, el primero `done` no se vuelve a pedir y los dos últimos sí.
  - `test_history_route_blocked_when_fudo_off`: responde 409 `Fudo está apagado`.
- [ ] **Step 2:** los tests fallan.
- [ ] **Step 3:** implementar. El hilo sigue el patrón de `run_expenses_sync`. En `fudoService.js` agregar `importHistory(fromMonth, force)` y `importMonths()`.
- [ ] **Step 4:** pasan `tests/test_fudo_sales_import.py`, `tests/test_fudo_sync_runs.py`, `tests/test_reports_products.py` y `tests/test_route_access_coverage.py`.
- [ ] **Step 5: Commit** `feat(fudo): month-by-month sales history import with per-month control`.

---

### Task 3: Comparación de dos meses por producto (backend)

**Files:**
- Create:
  - `backend/app/services/reports_products_compare.py`
  - `backend/tests/test_reports_products_compare.py`
- Modify: `backend/app/routes/reports.py`

**Interfaces:**
- Consumes: `Sale`, `SaleItem` (main) y `ProductVariant.product_id`.
- Produces:
  - **`compare(month_a: date, month_b: date) -> dict`**:
    - Forma: `{months: ['2026-09', '2026-10'], products: [{key, name, category, a: {quantity, amount}, b: {...}, variants: [{name, a, b}]}], totals: {a, b}}`.
    - Cantidades como string con 3 decimales; montos con 2.
  - **`daily(key: str, month_a: date, month_b: date) -> dict`**: devuelve `{days: [{day: 1..31, a: {...}, b: {...}}]}`.
  - **Clave del producto:**
    - `p:<Product.id>` si `sale_items.product_variant_id` tiene valor (se agrupa por `ProductVariant.product_id`);
    - si no, `n:<product_name>`.
    - Nombre y categoría salen del ítem más reciente del grupo.
  - **Variantes:** `variant_name`, o `product_name` si no hay.
  - **Qué cuenta:** `Sale.estado == 'Cerrada'`, por `Sale.fecha`, sumando `sale_items.quantity` y `sale_items.total`.
  - **Rutas** (`@module_required('Reports')`; un mes inválido da 400):
    - `GET /api/v1/reports/products/compare?month_a=YYYY-MM&month_b=YYYY-MM`
    - `GET /api/v1/reports/products/compare/daily?key=...&month_a&month_b`

- [ ] **Step 1: Tests que fallan:**
  - `test_compare_mixes_fudo_and_pos`: en septiembre, 3 medialunas de una venta Fudo vinculada; en octubre, 2 del POS (proyectadas). Da un solo producto `p:<id>` con `a.quantity == '3.000'` y `b.quantity == '2.000'`.
  - `test_compare_amount_is_without_sale_discount`: una venta del POS con descuento de venta cuenta `line_total` completo.
  - `test_compare_excludes_cancelled`: no cuenta una `Sale` `Cancelada`.
  - `test_compare_unlinked_item_by_name`: un ítem sin variante aparece como `n:Torta vieja`.
  - `test_compare_variants_breakdown`: Latte Chico y Grande se suman, y aparecen separados en `variants`.
  - `test_compare_daily`.
  - `test_compare_routes_permission_and_validation`: 403 sin el módulo Reports y 400 con `month_a=2026-13`.
- [ ] **Step 2:** los tests fallan.
- [ ] **Step 3:** implementar con una consulta agregada por mes, día, clave y variante.
- [ ] **Step 4:** pasan los tests y `tests/test_reports_products.py`.
- [ ] **Step 5: Commit** `feat(reports): compare product sales between two months`.

---

### Task 4: Modo práctica (backend)

**Files:**
- Create:
  - `backend/app/services/pos/practice.py`
  - `backend/tests/test_pos_practice.py`
- Modify:
  - `backend/app/services/cutover.py`: agrega `set_flags`.
  - `backend/app/services/pos/sale_service.py`: `open_sale` marca la venta.
  - `backend/app/services/pos/cash_service.py`:
    - `open_session` marca la caja;
    - `_create_expense` no se llama en práctica;
    - `list_sessions` y `unassigned_payments` excluyen la práctica.
  - `backend/app/services/pos/projection.py`: `project`/`unproject` no hacen nada en práctica.
  - `backend/app/services/pos/stock_hooks.py`: `consume`/`restore` ignoran ítems de ventas de práctica.
  - `backend/app/services/pos/print_documents.py`: título con prefijo `PRÁCTICA` en los documentos de una venta de práctica.
  - `backend/app/services/fiscal/invoice_service.py`: `issue` rechaza.
  - `backend/app/services/mercadopago/point_service.py`: `start` rechaza.
  - `backend/app/routes/mercadopago.py`: `point-config` devuelve `enabled: false` con `practice_mode`.
  - `backend/app/services/mercadopago/reconciliation_service.py`: `_galia_payments` excluye la práctica.
  - `backend/app/services/pos/serializers.py`: `sale_to_dict` agrega `is_practice`.

**Interfaces:**
- Consumes: Task 1.
- Produces:
  - **`cutover.set_flags(user, catalog_in_galia=None, fudo_off=None, practice_mode=None) -> OperationSettings`**: solo admin; si no, `forbidden`.
    - Prender `practice_mode`:
      - con una caja real abierta: `Cerrá la caja antes de entrar en modo práctica`;
      - con ventas reales `open` o `billing`: `Hay ventas reales abiertas`.
    - Apagarlo:
      - con una caja de práctica abierta: `Cerrá la caja de práctica antes de salir`;
      - con ventas de práctica abiertas: `Hay ventas de práctica abiertas`.
    - `fudo_off=True` sin catálogo en Galia: `Primero pasá el catálogo a Galia`.
    - `catalog_in_galia=True` llama a `menu_catalog_sync.link_to_catalog()` (Task 5), con import diferido.
  - **`practice.clear_practice(user) -> dict`**:
    - exige admin y el modo apagado;
    - borra las ventas y cajas de práctica con todas sus dependencias;
    - devuelve `{sales, cash_sessions}`.

- [ ] **Step 1: Tests que fallan** en `tests/test_pos_practice.py`:
  - `test_practice_does_not_touch_real_numbers`: con el modo prendido, abrir caja, vender una medialuna con stock, confirmar, cobrar en efectivo, cerrar la venta y hacer un gasto de caja. Se cumple:
    - la caja y la venta quedan `is_practice`;
    - el stock no cambia;
    - no hay `Sale` ni `Expense` nuevos;
    - `list_sessions` no muestra la caja.
  - `test_practice_blocks_invoice_and_point`: con los mensajes exactos.
  - `test_practice_print_header`: `receipt_document` y `order_document` tienen `PRÁCTICA` en el título.
  - `test_toggle_rules`: las cuatro reglas de prender y apagar, más `fudo_off` sin catálogo.
  - `test_clear_practice`: borra solo lo de práctica.
  - `test_reconciliation_ignores_practice_payments`.
- [ ] **Step 2:** los tests fallan.
- [ ] **Step 3:** implementar los guardas en los archivos indicados.
- [ ] **Step 4:** pasan `tests/test_pos_practice.py`, `tests/test_pos_*.py`, `tests/test_fiscal_*.py` y `tests/test_mp_*.py`.
- [ ] **Step 5: Commit** `feat(pos): practice mode that never touches real numbers`.

---

### Task 5: Carta sobre el catálogo de Galia

**Files:**
- Create:
  - `backend/app/services/menu_catalog_sync.py`
  - `backend/tests/test_menu_catalog_sync.py`
- Modify:
  - `backend/app/tasks/menu_tasks.py`
  - `backend/app/routes/menu.py`: la ruta de sincronizar la carta y `POST /items/<id>/ignore`.

**Interfaces:**
- Consumes: de la Task 1, `cutover.catalog_in_galia()`, los FK nuevos de la carta y `menu_ignored`.
- Produces:
  - **`menu_catalog_sync.link_to_catalog() -> dict`** (idempotente):
    - vincula por `fudo_product_id` y `fudo_category_id`;
    - devuelve `{variants_linked, variants_unlinked, categories_linked}`;
    - las variantes sin vínculo quedan `fudo_status='missing'`, que sigue siendo el estado del vínculo.
  - **`menu_catalog_sync.sync_from_catalog() -> dict`**: misma forma que `sync_fudo_products` (`price_changes`, `alerts`, `categories_created`, `items_created`).
    - **Precio:** sale de `ProductVariant.price`.
    - **Estado:** `ok`; `inactive` si la variante o el producto están inactivos; `missing` si no hay vínculo.
    - **Categoría:** sale de `Product.category_id` de la primera variante vinculada. Las categorías nuevas se crean al final, sin grupo.
    - **Variantes nuevas:** una `ProductVariant` activa, no ignorada y sin vínculo se suma al ítem de la carta que ya tiene otra variante del mismo `Product`. Si no hay ninguno, crea un `MenuItem` oculto con `Product.name`. El `label` es el nombre de la variante, o `None` si el producto tiene una sola.
    - **Nunca cambia** `MenuItem.name`, la descripción, la imagen, los tags ni el orden.
  - **`menu_tasks.sync_and_publish(client, storage)`**:
    - con `catalog_in_galia()` usa `sync_from_catalog()`; si no, `sync_fudo_products(client)`;
    - `__main__` no instancia `FudoClient` en ese caso;
    - la regla de publicación no cambia.
  - **Rutas de la carta, con el catálogo en Galia:**
    - "sincronizar" llama a `sync_from_catalog()`;
    - `ignore` marca `ProductVariant.menu_ignored`.

- [ ] **Step 1: Tests que fallan:**
  - `test_link_to_catalog_by_fudo_ids`: idempotente.
  - `test_sync_from_catalog_updates_price_and_publishes`.
  - `test_sync_from_catalog_keeps_owner_text_and_flags_inactive`.
  - `test_new_galia_product_creates_hidden_item`: dos variantes con etiquetas.
  - `test_ignored_variant_not_recreated`.
  - `test_tasks_use_catalog_when_switched`: `sync_and_publish(None, storage)` no llama a Fudo.
- [ ] **Step 2:** los tests fallan.
- [ ] **Step 3:** implementar.
- [ ] **Step 4:** pasan los tests, `tests/test_menu_*.py` y `tests/test_public_menu.py`.
- [ ] **Step 5: Commit** `feat(menu): build the digital menu from the Galia catalog`.

---

### Task 6: API de corte y bloqueo de Fudo

**Files:**
- Create:
  - `backend/app/routes/cutover.py`
  - `backend/tests/test_cutover_api.py`
- Modify:
  - `backend/app/__init__.py`
  - `backend/app/routes/products.py`: la sync de productos llama a `require_fudo_catalog()`.
  - `backend/app/routes/fudo_sync.py`: `/sync/expenses` llama a `require_fudo_on()`.

**Interfaces:**
- Produces:
  - `GET /api/v1/system/cutover`: para cualquier usuario autenticado; devuelve `{catalog_in_galia, fudo_off, practice_mode}`.
  - `PUT /api/v1/system/cutover`: admin; llama a `set_flags`.
  - `POST /api/v1/system/cutover/clear-practice`: admin; llama a `clear_practice`.

- [ ] **Step 1: Tests que fallan:**
  - `test_get_cutover_any_user`
  - `test_put_requires_admin`
  - `test_enable_catalog_links_menu`
  - `test_product_sync_blocked_with_catalog_in_galia`: 409 con el mensaje exacto.
  - `test_expenses_sync_blocked_when_fudo_off`
  - `test_clear_practice_route`
- [ ] **Step 2:** los tests fallan.
- [ ] **Step 3:** implementar. Si `test_route_access_coverage` lo exige, agregar el GET a la lista correspondiente.
- [ ] **Step 4:** pasan los tests y `tests/test_route_access_coverage.py`. Después, **la suite completa contra la línea base**: tiene que dar `Sin fallas nuevas.`
- [ ] **Step 5: Commit** `feat(cutover): cutover switches API and Fudo blocking`.

---

### Task 7: Comparar meses en la pestaña "Productos" (frontend)

**Files:**
- Create:
  - `frontend/src/utils/productsCompare.js` (+ `.test.js`)
  - `frontend/src/components/reports/ProductsCompare.jsx`
- Modify:
  - `frontend/src/components/reports/ProductsTab.jsx`: agrega un selector de vista, "Período" (la actual) o "Comparar meses".
  - `frontend/src/services/reportsService.js`: agrega `productsCompare(monthA, monthB)` y `productsCompareDaily(key, monthA, monthB)`.

**Interfaces:**
- Consumes: las rutas de la Task 3.
- Produces (`productsCompare.js`):
  - `rankProducts(products, measure) -> products`: ordena por `b[measure]` de mayor a menor; a igualdad, por nombre.
  - `variation(a, b) -> number | null`: porcentaje entero; `null` si `a` es 0.
  - `barWidths(products, measure) -> [{key, a, b}]`: el máximo es 100.
  - `defaultMonths(today) -> [prev, current]`: en formato `YYYY-MM`.

- [ ] **Step 1: Tests que fallan** (Vitest):
  - los dos órdenes de `rankProducts`;
  - `variation(100, 121) === 21` y `variation(0, 5) === null`;
  - el máximo de `barWidths` es 100;
  - `defaultMonths(new Date('2026-10-20'))` devuelve `['2026-09', '2026-10']`.
- [ ] **Step 2:** `npx vitest run src/utils/productsCompare.test.js` falla.
- [ ] **Step 3: Implementar la vista** según el boceto "B" que eligió el dueño:
  - **Controles:** dos selectores de mes y `Ver: monto | cantidad`.
  - **Filas:** una por producto, con dos barras (gris para el mes A, color de marca para el B) y la variación (▲ en verde, ▼ en rojo).
  - **Al tocar un producto:** se ven sus variantes y el detalle día por día.
  - **Estados:** cargando, error y "sin ventas".
- [ ] **Step 4:** pasan `npm test` y `npm run build`.
- [ ] **Step 5: Commit** `feat(reports): compare months view in the products tab`.

---

### Task 8: Pantalla "Corte con Fudo", franja de práctica y botones de Fudo

**Files:**
- Create:
  - `frontend/src/pages/admin/FudoCutover.jsx`
  - `frontend/src/services/cutoverService.js`
  - `frontend/src/hooks/useCutover.js`
  - `frontend/src/pos/ui/PracticeBanner.jsx`
- Modify:
  - `frontend/src/App.jsx` y `Sidebar.jsx`: entrada Sistema → "Corte con Fudo", solo admin.
  - Pantallas del POS, Camarero y la caja: agregan la franja.
  - Botón "Facturar": se oculta si `sale.is_practice`.
  - Botones "Sincronizar con Fudo" de Ventas, Gastos, Productos y Carta: se ocultan según los interruptores. En la carta, con el catálogo en Galia, el botón dice "Actualizar desde el catálogo".

**Interfaces:**
- Consumes: Tasks 2 y 6.
- Produces: `useCutover()`, con React Query (`['cutover']`, `staleTime` de 60 s) → `{catalog_in_galia, fudo_off, practice_mode}`.

- [ ] **Step 1: Pantalla**, en este orden:
  1. **Historia de Fudo:**
     - "Importar historia", con el seguimiento de la corrida;
     - tabla de meses con ventas y total de Fudo y de Galia, y ✓ o ⚠;
     - aviso de los meses cuyos totales cambiaron.
  2. **Modo práctica:** interruptor con confirmación, y "Borrar práctica" habilitado solo con el modo apagado.
  3. **Catálogo en Galia:** confirmación "Desde ahora los precios y productos se editan en Galia; Fudo deja de actualizarlos", y el resultado del vínculo con un enlace a la bandeja de la carta.
  4. **Fudo apagado:** deshabilitado hasta que el catálogo esté en Galia.
- [ ] **Step 2:** `PracticeBanner` con el texto exacto, sobre fondo ámbar, arriba del POS, Camarero y la caja.
- [ ] **Step 3:** botones ocultos según los interruptores.
- [ ] **Step 4:** pasan `npm test` y `npm run build`.
- [ ] **Step 5: Commit** `feat(cutover): Fudo cutover page, practice banner and Fudo buttons`.

---

### Task 9: Guía de caja y verificación final

**Files:**
- Create: `docs/pos/guia-caja.md` (y `docs/pos/img/` si se capturan imágenes).

- [ ] **Step 1: Guía** corta, para imprimir, con los nombres exactos de botones y pantallas. Cubre:
  - abrir la caja;
  - cobrar en efectivo, con tarjeta y con el Point;
  - anular un pago;
  - movimientos de caja;
  - cerrar y arquear;
  - qué hacer si el arqueo no cierra;
  - qué hacer si falla Galia: pasar a Fudo y **no** cargar la misma venta en los dos;
  - qué significa la franja de práctica.

  Si hay un navegador que guarde capturas (MCP de Playwright `browser_take_screenshot`), agregar capturas del preview. Si no, la guía queda sin imágenes y se anota en el ledger.
- [ ] **Step 2: Suites completas:** backend contra la línea base, `npm test` y `npm run build`.
- [ ] **Step 3: Preview** con SQLite y `POS_DEMO_SEED=1`. La historia se importa desde un script del scratchpad que usa `FakeSalesClient` con 3 meses. Recorrer:
  - importar la historia → meses en ✓;
  - comparar dos meses (con los toggles de monto y cantidad, y el detalle);
  - modo práctica: franja, caja, una venta, cierre; no aparece en reportes ni en Cajas; después "Borrar práctica";
  - "Catálogo en Galia": cambiar un precio y "Actualizar desde el catálogo" → la carta cambia;
  - "Fudo apagado": desaparecen los botones de Fudo.
- [ ] **Step 4: Commit** `docs(pos): cash register guide for the team`.
