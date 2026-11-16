# Vouchers de descuento Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tandas de vouchers de descuento (monto fijo) con código único, impresos en hoja, canjeables una sola vez en el POS.

**Architecture:** Tablas `voucher_batches` y `vouchers`. El canje crea un `PosDiscount` (kind `amount`, alcance venta) con `voucher_id`; un índice único parcial sobre `pos_discounts.voucher_id` donde `cancelled_at IS NULL` impide dos canjes activos. El estado del voucher se deriva (no se guarda). Servicios en `app/services/vouchers/`, rutas en `app/routes/vouchers.py`, página admin y campo de código en el modal de descuento del POS.

**Tech Stack:** Flask, SQLAlchemy, Flask-Migrate, pytest (SQLite en tests); React, @tanstack/react-query, vitest; paquete `qrcode` para el QR.

**Spec:** `docs/superpowers/specs/2026-11-13-vouchers-descuento-design.md`

## Global Constraints

- Rutas bajo `/api/v1/vouchers`; errores de negocio con `PosError(message, status)` (`app.services.pos.errors`), mensajes en español rioplatense.
- Código: 10 caracteres de `ABCDEFGHJKMNPQRSTUVWXYZ23456789` con `secrets`, mostrado `GAL-XXXXX-XXXXX`; se guarda normalizado (sin prefijo ni guiones), único.
- Monto y vencimiento por tanda, nunca hardcodeados; el monto de una tanda no se edita. Tope de seguridad por tanda: constante `MAX_BATCH_QUANTITY = 500`.
- Vencimiento = fecha (`Date`) válida hasta el fin de ese día en hora Argentina (`get_current_date_argentina()`).
- Anular/quitar siempre deja rastro: voucher anulado con quién, cuándo y motivo; quitar un descuento de voucher exige motivo y queda en la auditoría de la venta.
- Módulo de permisos `Vouchers` (gestión; admin al principio). Canjear: módulo `POS` o `Cobrar`. Quitar un descuento de voucher: `POS` o `Cobrar`.
- Estados visibles: Disponible · En uso (descuento activo en venta abierta/en cobro) · Canjeado (descuento activo en venta cerrada) · Vencido · Anulado. Precedencia: anulado > canjeado/en uso > vencido > disponible.
- Migración `b9a0_vouchers`, `down_revision = 'b7c0_production_forecast'` (re-verificar la cabeza en `origin/main` antes de abrir el PR).
- Tests backend: desde `backend/`, `python -m pytest tests/<archivo> -v`. Tests frontend: desde `frontend/`, `npx vitest run <archivo>`.

## Review Focus

- Dos cajas aplican el mismo código a ventas distintas a la vez: la segunda recibe "ya está en uso", nunca dos descuentos activos (Task 2 y 4).
- Código tipeado con minúsculas, espacios, guiones o sin el prefijo `GAL`: se normaliza y encuentra el voucher (Task 1).
- Venta de práctica (`is_practice`): no se canjea, para no quemar un voucher real (Task 4).
- Voucher mayor al total de la venta: el descuento se topa en lo que resta y no queda total negativo ni "saldo a favor" (Task 4).
- Cancelar la venta, quitar el descuento o anular el pago de una venta cerrada libera el voucher; vencer o anular lo bloquea aunque nunca se haya usado (Task 4).

---

### Task 1: Códigos de voucher

**Files:**
- Create: `backend/app/services/vouchers/__init__.py` (vacío), `backend/app/services/vouchers/codes.py`
- Test: `backend/tests/test_voucher_codes.py`

**Interfaces:**
- Produces: `ALPHABET: str`, `CODE_LENGTH = 10`, `generate_code() -> str` (normalizado, 10 chars), `normalize_code(raw: str | None) -> str` (mayúsculas, solo alfanuméricos, quita un prefijo `GAL` inicial si quedan 13 caracteres), `format_code(code: str) -> str` (`GAL-XXXXX-XXXXX`).

- [ ] **Step 1: Write the failing tests** en `test_voucher_codes.py`: `test_generate_code_uses_safe_alphabet_and_length` (200 códigos, todos de largo 10 y con caracteres solo en `ALPHABET`, sin `0O1IL`), `test_generate_code_is_not_repeated` (1000 códigos distintos), `test_format_code` (`format_code('ABCDEFGHJK') == 'GAL-ABCDE-FGHJK'`), `test_normalize_accepts_any_typing` (`' gal-abcde-fghjk '`, `'abcdefghjk'`, `'GAL ABCDE FGHJK'` → `'ABCDEFGHJK'`), `test_normalize_empty` (`None` y `''` → `''`).
- [ ] **Step 2: Run** `python -m pytest tests/test_voucher_codes.py -v`. Expected: FAIL (módulo inexistente).
- [ ] **Step 3: Implement** `codes.py` con las firmas de Interfaces.
- [ ] **Step 4: Run** el mismo comando. Expected: PASS.
- [ ] **Step 5: Commit** `feat(vouchers): generación y normalización de códigos`.

### Task 2: Modelos, migración y módulo de permisos

**Files:**
- Create: `backend/app/models/vouchers.py`, `backend/migrations/versions/b9a0_vouchers.py`, `backend/tests/voucher_helpers.py`
- Modify: `backend/app/models/pos/discounts.py` (columna `voucher_id` + índice), `backend/app/models/__init__.py` (exportar `VoucherBatch`, `Voucher`, `VoucherChangeLog`)
- Test: `backend/tests/test_voucher_models.py`

**Interfaces:**
- Produces (modelos):
  - `VoucherBatch(id, name String(100), amount Numeric(12,2), min_sale_amount Numeric(12,2) null, expires_at Date, terms Text null, quantity Integer, created_by FK users, created_at DateTime)`, relación `vouchers`.
  - `Voucher(id, batch_id FK index, code String(20) unique index, voided_at null, voided_by null, void_reason String(255) null, created_at)`, relación `batch`.
  - `VoucherChangeLog(id, batch_id FK, user_id FK, field String(50), old_value String(100) null, new_value String(100) null, created_at)`.
  - `PosDiscount.voucher_id` (FK `vouchers.id`, nullable, index) y relación `voucher`; índice único parcial `uq_pos_discounts_active_voucher` sobre `voucher_id` con `postgresql_where` y `sqlite_where` = `cancelled_at IS NULL AND voucher_id IS NOT NULL`.
- Produces (helpers de test, `voucher_helpers.py`): reexporta `auth_headers, make_catalog, make_floor, make_user, pos_app` de `pos_helpers`; `make_batch(amount='1000', quantity=3, expires_at=None, min_sale_amount=None, name='Sorteo Instagram') -> VoucherBatch` (inserta directo, códigos con `generate_code`, vence en 30 días por defecto); `open_sale(user, catalog)` que crea una venta de mostrador con un ítem confirmado de `catalog.medialuna` y devuelve la venta (usar las funciones de `sale_service` como en `test_loyalty_pos_hooks.py`).

- [ ] **Step 1: Write the failing tests** en `test_voucher_models.py`: `test_batch_and_vouchers_persist`, `test_voucher_code_is_unique` (IntegrityError al repetir), `test_only_one_active_discount_per_voucher` (dos `PosDiscount` activos con el mismo `voucher_id` en ventas distintas → `IntegrityError` en el flush), `test_cancelled_discount_frees_voucher` (cancelar el primero con `cancelled_at` permite crear otro).
- [ ] **Step 2: Run** `python -m pytest tests/test_voucher_models.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** los modelos, la columna e índice y los helpers de test.
- [ ] **Step 4: Implement la migración** `b9a0_vouchers`: crea las tres tablas, agrega `pos_discounts.voucher_id` con FK e índice parcial (usar `batch_alter_table` como en `b8a0_loyalty`), inserta el módulo `Vouchers` (nombre `Vouchers`, display `Vouchers`, descripción "Tandas de vouchers de descuento", ruta `/vouchers`, categoría `Operations`) con permisos de rol admin `True` y employee `False`, copiando el patrón de `b8a0_loyalty.py`. `downgrade` borra permisos, módulo, índice, columna y tablas.
- [ ] **Step 5: Run** los tests del Step 2. Expected: PASS. Luego, contra una base descartable (nunca producción), `flask db upgrade`, `flask db downgrade -1`, `flask db upgrade` sin errores.
- [ ] **Step 6: Commit** `feat(vouchers): modelos, índice anti doble canje y migración`.

### Task 3: Servicio de tandas

**Files:**
- Create: `backend/app/services/vouchers/batches.py`
- Test: `backend/tests/test_voucher_batches.py`

**Interfaces:**
- Consumes: `generate_code`, modelos de Task 2, `PosError`/`bad_request`/`not_found`, `get_current_date_argentina`, `parse_decimal`/`clean_str` de `app.utils.validation`.
- Produces:
  - `MAX_BATCH_QUANTITY = 500`.
  - `create_batch(user, data: dict) -> VoucherBatch`: valida `name` (obligatorio, ≤100), `amount` (> 0, ≤ 100000000), `quantity` (entero 1..`MAX_BATCH_QUANTITY`), `expires_at` (ISO `AAAA-MM-DD`, no anterior a hoy en Argentina), `min_sale_amount` opcional (≥ 0), `terms` opcional; genera los códigos en la misma transacción reintentando colisiones; commit.
  - `voucher_status(voucher, discount_row, today) -> str` con valores `'available' | 'in_use' | 'redeemed' | 'expired' | 'voided'` según la precedencia del Global Constraints; `discount_row` es `(PosDiscount, PosSale) | None`.
  - `batch_detail(batch_id) -> dict` y `list_batches() -> list[dict]`: cada voucher con `id`, `code` (formateado), `status`, `sale_id`, `redeemed_at`; resumen con `issued`, `available`, `in_use`, `redeemed`, `expired`, `voided`, `discount_total` (suma de `amount` de descuentos activos en ventas cerradas). El detalle incluye `name, amount, min_sale_amount, expires_at, terms`.
  - `extend_expiry(user, batch_id, new_date: str) -> VoucherBatch`: solo permite una fecha posterior a la actual; escribe una fila en `VoucherChangeLog` (`field='expires_at'`).
  - `void_voucher(user, voucher_id, reason) -> Voucher`: motivo obligatorio; no anula uno ya canjeado/en uso (`PosError`); guarda `voided_at/by/void_reason`.

- [ ] **Step 1: Write the failing tests** en `test_voucher_batches.py`: `test_create_batch_generates_unique_codes` (cantidad pedida, códigos distintos), `test_create_batch_validates` (parametrizado: monto 0, cantidad 0, cantidad 501, vencimiento pasado, nombre vacío → `PosError` 400), `test_status_precedence` (anulado gana a vencido; vencido solo si no está usado), `test_extend_expiry_logs_change` (una fila de log con viejo y nuevo valor; fecha anterior falla), `test_void_requires_reason`, `test_cannot_void_redeemed_voucher`, `test_batch_summary_counts` (una tanda con un voucher canjeado en venta cerrada, uno en uso, uno anulado: contadores y `discount_total` correctos).
- [ ] **Step 2: Run** `python -m pytest tests/test_voucher_batches.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `batches.py`. Para los estados del listado, traer los descuentos activos de todos los vouchers de la tanda en una sola consulta (join `PosDiscount`/`PosSale`), sin N+1.
- [ ] **Step 4: Run** el mismo comando. Expected: PASS.
- [ ] **Step 5: Commit** `feat(vouchers): servicio de tandas, estados y anulación`.

### Task 4: Canje en el POS

**Files:**
- Create: `backend/app/services/vouchers/redeem.py`
- Modify: `backend/app/services/pos/discount_service.py` (`cancel_discount`), `backend/app/services/pos/serializers.py` (`discount_to_dict`), `frontend/src/pos/utils/events.js` (etiquetas)
- Test: `backend/tests/test_voucher_redeem.py`

**Interfaces:**
- Consumes: `normalize_code`, `format_code`, `voucher_status` (Task 3), `load_sale`, `require_status`, `recalc`, `close_if_settled`, `audit.record`, `ACTIVE_SALE_STATUSES`.
- Produces:
  - `redeem_voucher(user, sale_id: int, code: str) -> PosSale`: pasos del spec ("Canje en el POS"). Rechazos con `PosError` y estos mensajes: código vacío o inexistente → `'Código de voucher inválido'` (404); anulado → `'Ese voucher fue anulado'`; ya usado → `'Ese voucher ya fue canjeado el DD/MM/AAAA en la venta #N'` si su venta está cerrada, o `'Ese voucher ya está aplicado a la venta #N'` si está abierta/en cobro (409); vencido → `'Ese voucher venció el DD/MM/AAAA'`; mínimo → `'La venta tiene que llegar a $X para usar este voucher'`; venta de práctica → `'No se canjea en una venta de práctica'`. Crea `PosDiscount(kind='amount', value=batch.amount, voucher_id=…, reason=f'Voucher {batch.name}')`, `recalc`, mismo chequeo de total vs. pagado que `add_discount`, auditoría `voucher_redeemed` (payload `voucher_id`, `code`, `discount_id`, `amount`), `close_if_settled`, commit. Un `IntegrityError` al flush se traduce a `PosError('Ese voucher ya está en uso', 409)` tras rollback.
  - `cancel_discount(user, discount_id, reason=None)`: si `discount.voucher_id`, exige módulo `POS` o `Cobrar` (`check_module_access`) en lugar de `Descuentos`, exige `reason` (`'Indicá el motivo'`) y lo guarda en la auditoría `discount_cancelled`; el comportamiento para los demás descuentos no cambia.
  - `discount_to_dict` agrega `voucher_id` y `voucher_code` (formateado o `None`).
- [ ] **Step 1: Write the failing tests** en `test_voucher_redeem.py`: `test_redeem_applies_amount_discount` (total baja el monto del voucher; `discount_total` coincide; evento `voucher_redeemed`), `test_redeem_code_typed_loosely` (minúsculas con guiones), `test_unknown_code_rejected`, `test_voided_rejected`, `test_expired_rejected` (vencimiento ayer; hoy sí sirve), `test_min_sale_amount`, `test_voucher_larger_than_sale_is_capped` (total 0, sin negativos), `test_already_applied_other_sale_rejected` (mensaje con número de venta), `test_already_redeemed_after_close_rejected` (venta cobrada y cerrada; mensaje con "canjeado"), `test_same_sale_twice_rejected`, `test_two_vouchers_in_one_sale_ok`, `test_practice_sale_rejected`, `test_cancel_sale_frees_voucher`, `test_cancel_discount_frees_voucher_and_requires_reason`, `test_cashier_without_descuentos_module_can_redeem_and_remove` (usuario solo con `Cobrar`), `test_user_without_pos_or_cobrar_cannot_remove_voucher_discount`, `test_cancel_payment_reopens_sale_and_voucher_can_be_released`, `test_integrity_error_becomes_in_use_message` (monkeypatch del chequeo previo para forzar el choque con el índice).
- [ ] **Step 2: Run** `python -m pytest tests/test_voucher_redeem.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `redeem.py`, los cambios en `cancel_discount` y `discount_to_dict`, y las etiquetas `voucher_redeemed: 'Canjeó un voucher'` en `events.js`.
- [ ] **Step 4: Run** el comando del Step 2 y luego `python -m pytest tests -k "discount or pos" -q` para comprobar que no se rompió nada del POS. Expected: PASS.
- [ ] **Step 5: Commit** `feat(vouchers): canje en el POS con liberación al quitar o cancelar`.

### Task 5: API HTTP

**Files:**
- Create: `backend/app/routes/vouchers.py`
- Modify: `backend/app/__init__.py` (importar y registrar el blueprint, como `loyalty_admin`)
- Test: `backend/tests/test_voucher_api.py`

**Interfaces:**
- Consumes: servicios de Tasks 3 y 4, `_body` y `_respond` de `app.routes.pos_sales`.
- Produces (blueprint `vouchers`, prefijo `/api/v1/vouchers`):
  - `GET /batches`, `POST /batches` (201), `GET /batches/<int:batch_id>`, `PUT /batches/<int:batch_id>` (body `{expires_at}`), `POST /<int:voucher_id>/void` (body `{reason}`): todos con `@token_required` y `@module_required('Vouchers')`; los `PosError` se devuelven como `{'error': message}` con su status (errorhandler del blueprint con rollback).
  - `POST /pos-sales/<int:sale_id>/redeem` (body `{code}`): `@module_required('POS', 'Cobrar')`, responde con `_respond` (la venta completa).
  - Se agrega `reason` al body de `POST /api/v1/pos/discounts/<id>/cancel` en `pos_sales.py` y se pasa a `cancel_discount`.
- [ ] **Step 1: Write the failing tests** en `test_voucher_api.py`: `test_admin_creates_and_lists_batch`, `test_employee_without_module_gets_403` (gestión), `test_cashier_with_pos_can_redeem_but_not_manage`, `test_redeem_returns_sale_with_voucher_discount` (el JSON de la venta trae `discounts[0].voucher_code`), `test_second_redeem_returns_409`, `test_void_and_extend_endpoints`, `test_cancel_discount_endpoint_accepts_reason`, `test_batch_detail_exposes_codes_for_printing`.
- [ ] **Step 2: Run** `python -m pytest tests/test_voucher_api.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** el blueprint, su registro y el pasaje de `reason`.
- [ ] **Step 4: Run** el comando del Step 2 y `python -m pytest tests -q`. Expected: PASS (la suite completa del backend).
- [ ] **Step 5: Commit** `feat(vouchers): API de tandas y canje`.

### Task 6: Página admin e impresión

**Files:**
- Create: `frontend/src/services/voucherService.js`, `frontend/src/pages/Vouchers.jsx`, `frontend/src/components/vouchers/BatchForm.jsx`, `frontend/src/components/vouchers/BatchDetail.jsx`, `frontend/src/components/vouchers/PrintSheet.jsx`, `frontend/src/components/vouchers/voucherUtils.js`
- Modify: `frontend/src/App.jsx` (ruta `/vouchers` con `RoleProtectedRoute moduleName="Vouchers"`), `frontend/src/components/layout/Sidebar.jsx` (item "Vouchers", módulo `Vouchers`, grupo Finanzas), `frontend/package.json` (dependencia `qrcode`)
- Test: `frontend/src/components/vouchers/voucherUtils.test.js`

**Interfaces:**
- Produces:
  - `voucherService`: `listBatches()`, `getBatch(id)`, `createBatch(body)`, `extendExpiry(id, expiresAt)`, `voidVoucher(id, reason)` sobre `/vouchers/...` (mismo estilo que `loyaltyService`).
  - `voucherUtils.js`: `STATUS_LABEL` (`available: 'Disponible'`, `in_use: 'En uso'`, `redeemed: 'Canjeado'`, `expired: 'Vencido'`, `voided: 'Anulado'`), `chunk(list, size) -> list[]` (para armar páginas de 8), `formatExpiry(isoDate) -> 'DD/MM/AAAA'`.
- Comportamiento: lista de tandas con sus contadores y botón "Nueva tanda" (nombre, monto, cantidad, vencimiento, mínimo de consumo opcional, condiciones); detalle con tabla de vouchers y su estado, "Anular" con motivo, "Extender vencimiento" y botón "Imprimir"; `PrintSheet` renderiza solo los vouchers `available` en páginas A4 de 8 (2×4) con `@media print` (oculta el resto de la app), con marca de Galia (colores `galia-*`), nombre del concurso, monto, vencimiento, condiciones, código formateado grande y QR del código normalizado generado con `qrcode.toDataURL`, y llama a `window.print()`. Las fuentes de la marca siguen el estilo ya usado en la carta/home.

- [ ] **Step 1: Write the failing tests** en `voucherUtils.test.js`: `chunk([1..9], 8)` da `[[1..8],[9]]`; `chunk([], 8)` da `[]`; `formatExpiry('2026-12-31') === '31/12/2026'`; `STATUS_LABEL` cubre los cinco estados.
- [ ] **Step 2: Run** `npx vitest run src/components/vouchers/voucherUtils.test.js`. Expected: FAIL.
- [ ] **Step 3: Implement** `voucherUtils.js`, el servicio, la página, los componentes, `npm install qrcode`, y los cambios de ruta y barra lateral.
- [ ] **Step 4: Run** el test del Step 2 y `npm run lint`. Expected: PASS y sin warnings.
- [ ] **Step 5: Verify en el navegador** (`preview_start`, base local con datos de prueba): crear una tanda de 10, ver el detalle, abrir la vista de impresión y confirmar 2 páginas (8 + 2), con QR y código legibles. Mostrar una captura al usuario para que apruebe el diseño antes de imprimir una tanda real.
- [ ] **Step 6: Commit** `feat(vouchers): página admin e impresión en hoja`.

### Task 7: Canje en el POS (frontend)

**Files:**
- Modify: `frontend/src/pos/api/posApi.js`, `frontend/src/pos/modals/DiscountModal.jsx`, `frontend/src/pos/sale/SalePanel.jsx`, `frontend/src/pos/utils/permissions.js`
- Test: `frontend/src/pos/utils/permissions.test.js`

**Interfaces:**
- Produces: `posApi.redeemVoucher(saleId, code)` → `POST /vouchers/pos-sales/${saleId}/redeem`; `posApi.cancelDiscount(discountId, reason)` pasa `{ reason }`; `posPermissions` agrega `vouchers: pos || has('Cobrar')`.
- Comportamiento: en `DiscountModal` (solo venta, no ítem, y solo si `perms.vouchers`), una sección "Voucher" con un campo de código (se muestra en mayúsculas) y botón "Canjear" que llama a `run(sale.id, () => posApi.redeemVoucher(sale.id, code))`; el error del backend se muestra tal cual. En `SalePanel`, `removeDiscount` para un descuento con `voucher_id` abre `CancelReasonModal` (título "Quitar voucher") y llama a `cancelDiscount(discount.id, reason)`; el resto de los descuentos sigue igual. El ticket ya muestra el descuento por su `reason` ("Voucher <tanda>").

- [ ] **Step 1: Write the failing test** en `permissions.test.js`: `vouchers` es `true` para admin, para `POS` y para `Cobrar`, y `false` para solo `Camarero`.
- [ ] **Step 2: Run** `npx vitest run src/pos/utils/permissions.test.js`. Expected: FAIL.
- [ ] **Step 3: Implement** los cambios de `posApi`, `permissions`, `DiscountModal` y `SalePanel`.
- [ ] **Step 4: Run** `npx vitest run` y `npm run lint`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(vouchers): canje de voucher en el modal de descuento del POS`.

### Task 8: Prueba del flujo real

**Files:** ninguno nuevo (solo hallazgos a corregir en las tareas anteriores).

- [ ] **Step 1:** Levantar backend y frontend contra una base local descartable (`preview_start`), con usuario admin y una caja con permiso `Cobrar` sin `Descuentos`.
- [ ] **Step 2:** Recorrer el flujo: crear tanda → imprimir (captura) → abrir una venta → canjear el código → verificar total y ticket → intentar canjear el mismo código en otra venta (rechazado, con número de venta) → cancelar la venta → verificar que el voucher vuelve a "Disponible" → canjear de nuevo, cobrar y cerrar → verificar "Canjeado" y que ya no se puede usar → anular un voucher y probar que se rechaza → probar un vencido.
- [ ] **Step 3:** Probar la migración sobre una copia de la base de test con datos: conteos de `pos_discounts` iguales antes y después, `downgrade` y `upgrade` limpios (regla de migraciones del proyecto).
- [ ] **Step 4:** Merge de `origin/main` en la rama, re-verificar que `b9a0_vouchers` sigue colgando de la cabeza de `main` (`flask db heads` con una sola cabeza), correr `python -m pytest tests -q` y `npx vitest run`.
- [ ] **Step 5:** Abrir el PR y reportar al usuario qué se probó y qué no se pudo probar (por ejemplo, la impresión en papel real).
