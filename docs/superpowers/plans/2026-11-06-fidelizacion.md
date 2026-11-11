# Fidelización ("cafecitos") — plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** programa de puntos "cafecitos" atado a las ventas del POS nativo: clientes autoregistrados con Google en la carta, acreditación automática al cerrar, canje por la caja, administración con historial y reportes.

**Architecture:** el libro de movimientos (`loyalty_movements`) es la única fuente de verdad del saldo; un paquete `app/services/loyalty/` lo escribe y el POS lo invoca desde sus puntos de cierre, reapertura y anulación ya existentes. Los clientes tienen su propia autenticación (token JWT con `typ='customer'`) separada de la de empleados, usada solo por endpoints `/api/public/loyalty/*` que consume una página nueva de la carta (`cafecitos.html`).

**Tech Stack:** Flask + SQLAlchemy + Alembic (backend, tests pytest con SQLite), React + Vite + React Query (frontend de gestión/POS), React + Vite + Tailwind (carta, `menu-site`), vitest.

**Spec:** `docs/superpowers/specs/2026-11-06-fidelizacion-design.md`

## Global Constraints

- Moneda del programa: "cafecitos", enteros. Sin vencimiento.
- Tipos de movimiento exactos: `earn`, `earn_reversal`, `redeem`, `redeem_reversal`, `adjustment`.
- Acreditación: por ítem confirmado no-canje, `floor(cantidad) × cafecitos de la variante` al cerrar; descuentos de precio no afectan.
- Ventas `is_practice` no generan movimientos.
- Canje: lo hace solo quien tiene el módulo `POS` (o admin). `Camarero` y `Cobrar` solos no pueden asociar cliente ni canjear.
- Configuración, premios, cafecitos por variante, ajustes y regenerar QR: solo módulo `Fidelizacion` (o admin). Todo cambio queda en `loyalty_change_log`.
- Ítem de canje: `unit_price = 0`, `modifiers_total = 0`, `line_total = 0`; recargos de modificadores regalados. Valor en pesos del canje = `variant.price + sum(price_delta)`.
- Período de activos: default 30 días, configurable.
- Visita = venta POS `closed`, no práctica, con `customer_id`; fecha = `business_date`.
- Buscador POS: desde 2 caracteres, objetivo < 300 ms con 10.000 clientes.
- El token de cliente nunca autentica en endpoints de empleados (y viceversa).
- Ajuste manual exige motivo y no puede dejar el saldo negativo; un canje tampoco. Una `earn_reversal` sí puede.
- Copia visible en la carta: sección "Mis cafecitos"; botón "Entrar con Google".
- Reporte 5.4 muestra la nota: "Las ventas sin cliente identificado, incluidas todas las importadas de Fudo, cuentan como no registradas."

## Review Focus

1. **Token de cliente presentado a un endpoint de empleados** (o al revés): debe dar 401, nunca 500 ni acceso. Hoy `token_required` hace `data['user_id']` y un token sin esa clave reventaría con KeyError → test en Task 5.
2. **Venta que se cierra, se reabre al anular un pago y se vuelve a cerrar:** el saldo final debe ser igual a una sola acreditación → test en Task 3.
3. **Mismo saldo canjeado en dos ventas abiertas a la vez:** el segundo canje debe fallar si no alcanza (descuento al agregar, con bloqueo de fila del cliente) → test en Task 3.
4. **Split de una venta con cliente y un ítem de canje:** la venta nueva hereda `customer_id`; anular el ítem de canje movido devuelve los cafecitos una sola vez → test en Task 3.
5. **Búsqueda con acentos/mayúsculas y homónimos** ("lucia" encuentra "Lucía Pérez"; dos homónimos muestran mail/teléfono enmascarados distintos) → test en Task 4.

---

### Task 1: Modelos, migración y módulo `Fidelizacion`

**Files:**
- Create: `backend/app/models/loyalty.py`
- Modify: `backend/app/models/__init__.py` (exportar los modelos nuevos)
- Modify: `backend/app/models/product_variant.py` (columna `cafecitos`)
- Modify: `backend/app/models/pos/sale.py` (`PosSale.customer_id`, `PosSaleItem.reward_id`)
- Create: `backend/migrations/versions/b7a0_loyalty.py` (`down_revision = 'b6c0_printer_chars_per_line'`; si al momento de mergear ya existe otra revisión hija de `b6c0`, reencadenar)
- Test: `backend/tests/test_loyalty_models.py`, `backend/tests/loyalty_helpers.py`

**Interfaces:**
- Produces (tablas/modelos):
  - `Customer` (`customers`): `id`, `google_sub` (único, nullable=False), `email` (índice), `first_name`, `last_name`, `phone` (nullable, índice), `search_text` (String, índice; nombre+apellido+email+teléfono normalizados sin acentos y en minúsculas), `qr_token` (String(32), único, generado con `secrets.token_urlsafe(24)`), `terms_accepted_at` (DateTime, not null), `promo_opt_in_at` (DateTime, nullable), `created_at`, `updated_at`. Método `full_name` (property). Función `normalize_search(text) -> str` en el mismo módulo.
  - `Reward` (`loyalty_rewards`): `id`, `name`, `product_variant_id` (FK), `cost` (Integer > 0), `is_active`, `position`, timestamps.
  - `LoyaltyMovement` (`loyalty_movements`): `id`, `customer_id` (FK, índice), `kind` (String(20)), `amount` (Integer, con signo), `pos_sale_id` (FK nullable, índice), `pos_sale_item_id` (FK nullable, índice), `reward_id` (FK nullable), `reward_cost` (Integer nullable), `pesos_value` (Numeric(12,2) nullable), `reversal_of_id` (FK a sí misma, nullable), `reason` (String(255) nullable), `user_id` (FK users, nullable), `created_at` (índice).
  - `LoyaltySettings` (`loyalty_settings`, fila única): `id`, `active_days` (Integer, default 30), `updated_at`, `updated_by`. Classmethod `LoyaltySettings.get() -> LoyaltySettings` que crea la fila si no existe.
  - `LoyaltyChangeLog` (`loyalty_change_log`): `id`, `entity` (String(30): `variant`, `reward`, `settings`, `adjustment`, `customer`), `entity_id`, `field`, `old_value` (Text), `new_value` (Text), `reason`, `user_id`, `created_at`.
  - `ProductVariant.cafecitos`: Integer, not null, default 0, server_default '0'.
  - `PosSale.customer_id`: FK `customers.id`, nullable, índice. Relación `PosSale.customer`.
  - `PosSaleItem.reward_id`: FK `loyalty_rewards.id`, nullable. Property `is_redemption` (`reward_id is not None`).
  - La migración inserta el módulo `('Fidelizacion', 'Fidelización', 'Clientes, cafecitos, premios y reportes', '/fidelizacion')`, mismo patrón que `POS_MODULES` en `b1a4_add_pos_sales_engine.py`.
- `backend/tests/loyalty_helpers.py`: `make_customer(first='Lucía', last='Pérez', email='lu@test.com', phone=None) -> Customer`, `make_reward(variant, cost, name=None) -> Reward`, `balance_of(customer) -> int` (suma directa de `amount`). Reutiliza `pos_app`, `make_user`, `make_catalog`, `make_floor` de `pos_helpers`.

- [ ] **Step 1: Write failing tests** — `test_customer_gets_unique_qr_token_and_search_text` (crear cliente "Lucía Pérez", `lu@test.com`, tel `1155550032` → `qr_token` de ≥ 24 caracteres; `search_text` contiene `"lucia perez"`, `"lu@test.com"` y `"1155550032"`); `test_variant_cafecitos_defaults_to_zero`; `test_settings_get_creates_single_row_with_30_days` (dos llamadas → misma fila, `active_days == 30`); `test_redemption_item_flag` (`PosSaleItem(reward_id=r.id).is_redemption is True`).
- [ ] **Step 2: Run** `cd backend && pytest tests/test_loyalty_models.py -v` → FAIL (import error).
- [ ] **Step 3: Implement** modelos, columnas y migración (upgrade y downgrade). `search_text` se recalcula en un listener `before_insert`/`before_update` de `Customer`; `normalize_search` usa `unicodedata.normalize('NFKD')` y descarta los caracteres combinables.
- [ ] **Step 4: Run** `pytest tests/test_loyalty_models.py -v` → PASS; `pytest tests/test_pos_models.py -q` → PASS.
- [ ] **Step 5: Commit** `git commit -m "Fidelización: modelos, migración b7a0 y módulo"`

### Task 2: Servicio de wallet

**Files:**
- Create: `backend/app/services/loyalty/__init__.py`, `backend/app/services/loyalty/wallet.py`, `backend/app/services/loyalty/errors.py`
- Test: `backend/tests/test_loyalty_wallet.py`

**Interfaces:**
- Consumes: modelos de Task 1.
- Produces (`app/services/loyalty/wallet.py`; ninguna hace commit salvo `adjust`):
  - `class LoyaltyError(PosError)` en `errors.py` (así las rutas POS existentes ya lo traducen a 400).
  - `balance(customer_id: int) -> int`
  - `lock_customer(customer_id: int) -> Customer` — `SELECT … FOR UPDATE` (`with_for_update()`), no-op en SQLite.
  - `earn_preview(sale: PosSale) -> int` — cafecitos que sumaría la venta con sus ítems no cancelados y no-canje.
  - `credit_sale(sale: PosSale, user: User) -> int` — si `sale.customer_id` y no `is_practice`, crea un `earn` por ítem confirmado no-canje con `amount > 0` (`pos_sale_item_id` seteado). Devuelve el total acreditado.
  - `reverse_sale_credits(sale: PosSale, user: User) -> int` — por cada `earn` de la venta sin reversa, crea `earn_reversal` (`amount` negado, `reversal_of_id`).
  - `redeem(sale: PosSale, item: PosSaleItem, reward: Reward, user: User) -> LoyaltyMovement` — bloquea al cliente, falla con `LoyaltyError('Le faltan N cafecitos')` si `balance < reward.cost`; crea `redeem` con `amount = -cost`, `reward_cost = cost`, `pesos_value = variant.price + sum(price_delta de las opciones del ítem)`.
  - `reverse_redemption(item: PosSaleItem, user: User) -> LoyaltyMovement | None` — si hay un `redeem` del ítem sin reversa, crea `redeem_reversal`.
  - `adjust(user: User, customer_id: int, amount: int, reason: str) -> LoyaltyMovement` — motivo obligatorio (`LoyaltyError('El ajuste necesita un motivo')`), `amount != 0`, rechaza si deja saldo < 0; escribe `LoyaltyChangeLog(entity='adjustment', entity_id=customer_id, field='balance', old_value, new_value, reason)`; hace commit.

- [ ] **Step 1: Write failing tests** — con un cliente y el catálogo de `make_catalog` (taza de Cortado con `cafecitos=2`, medialuna `cafecitos=1`):
  - `test_credit_sale_counts_confirmed_non_redemption_items` — 2 cortados + 3 medialunas confirmados + 1 medialuna cancelada → `credit_sale == 7`, `balance == 7`.
  - `test_credit_ignores_discounts_and_floors_fractional_quantity` — cortesía 100% en un cortado, cantidad `1.5` de medialuna → `2 + 1 == 3`.
  - `test_practice_sale_does_not_credit` → 0 movimientos.
  - `test_reverse_sale_credits_is_idempotent` — dos llamadas → una sola reversa; `balance == 0`.
  - `test_redeem_rejects_when_short` — saldo 5, premio de 8 → `LoyaltyError` con "Le faltan 3 cafecitos".
  - `test_redeem_records_cost_and_pesos_value` — premio cortado (8) con almendras (+300) → `reward_cost == 8`, `pesos_value == Decimal('2300')`.
  - `test_adjust_requires_reason_and_cannot_go_negative` y `test_adjust_writes_change_log`.
  - `test_earn_reversal_may_leave_negative_balance` — acreditar 7, canjear 7 (premio de 7), revertir acreditación → `balance == -7`.
- [ ] **Step 2: Run** `pytest tests/test_loyalty_wallet.py -v` → FAIL.
- [ ] **Step 3: Implement** `wallet.py` con las firmas de arriba.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `git commit -m "Fidelización: servicio de wallet"`

### Task 3: Enganche con el POS (cliente en la venta, canje, cierres y anulaciones)

**Files:**
- Create: `backend/app/services/loyalty/pos_hooks.py`
- Modify: `backend/app/services/pos/closing.py` (`close_sale_rows`)
- Modify: `backend/app/services/pos/payment_service.py` (`cancel_payment`, rama `was_closed`)
- Modify: `backend/app/services/pos/sale_service.py` (`cancel_sale` rama `closed`, `cancel_sale_rows`, `cancel_item`, `delete_item`, `split_sale`)
- Modify: `backend/app/services/pos/serializers.py` (venta serializada)
- Test: `backend/tests/test_loyalty_pos_hooks.py`

**Interfaces:**
- Consumes: `wallet.*` de Task 2.
- Produces (`pos_hooks.py`):
  - `set_customer(user, sale_id: int, customer_id: int | None) -> PosSale` — venta `open`/`billing`; si la venta tiene ítems de canje no cancelados y el cliente cambia → `LoyaltyError('Anulá los canjes antes de cambiar el cliente')`; completa `customer_name` con `full_name` si estaba vacío; `audit.record(sale, user, 'customer_set', customer_id=…)`; commit.
  - `add_redemption(user, sale_id: int, reward_id: int, modifier_option_ids: list[int] | None) -> PosSale` — venta `open` con cliente; premio activo; agrega un `PosSaleItem` como `sale_service.add_item` (mismos modificadores validados) pero con `unit_price=0`, `modifiers_total=0`, `line_total=0`, `reward_id`; llama `wallet.redeem`; `audit.record(…, 'redemption_added', …)`; commit. Extraer de `add_item` un helper `_build_item(user, variant, quantity, options, note) -> PosSaleItem` para no duplicar.
  - Llamadas en el POS: `close_sale_rows` → `wallet.credit_sale`; `cancel_payment` con `was_closed` → `wallet.reverse_sale_credits`; `cancel_sale` con venta `closed` → `wallet.reverse_sale_credits`; `cancel_sale_rows`, `cancel_item` y `delete_item` → `wallet.reverse_redemption` para cada ítem de canje afectado; `split_sale` → la venta nueva copia `customer_id`.
  - El serializer de venta agrega `customer: {id, full_name, balance} | null`, `cafecitos_preview: int`, y por ítem `is_redemption: bool`.

- [ ] **Step 1: Write failing tests**
  - `test_closing_sale_with_customer_credits` (vía `payment_service.add_payment` hasta cerrar) → `balance == earn_preview previo`.
  - `test_reopen_by_cancelling_payment_then_reclose_credits_once` (Review Focus 2) → tras cerrar, anular pago y volver a cobrar: `balance` igual a una acreditación; hay exactamente un `earn_reversal`.
  - `test_cancel_closed_sale_reverses_credits_and_redemptions`.
  - `test_redemption_item_is_free_and_does_not_earn` — línea en $0 con almendras; al cerrar, el ítem de canje no genera `earn`.
  - `test_concurrent_redemptions_cannot_spend_twice` (Review Focus 3) — saldo 8, dos ventas abiertas con el mismo cliente, canje de 8 en ambas → la segunda falla con `LoyaltyError`.
  - `test_cancel_or_delete_redemption_item_refunds_once`.
  - `test_split_keeps_customer_and_refunds_moved_redemption_once` (Review Focus 4).
  - `test_cannot_change_customer_with_active_redemption`.
  - `test_serialized_sale_includes_customer_and_preview`.
- [ ] **Step 2: Run** `pytest tests/test_loyalty_pos_hooks.py -v` → FAIL.
- [ ] **Step 3: Implement** `pos_hooks.py` y las llamadas en los servicios POS.
- [ ] **Step 4: Run** `pytest tests/test_loyalty_pos_hooks.py tests/test_pos_*.py -q` → PASS (los tests POS existentes siguen verdes).
- [ ] **Step 5: Commit** `git commit -m "Fidelización: cafecitos en el cierre, reapertura, anulación y canje del POS"`

### Task 4: API del POS (buscar cliente, asociar, premios, canjear)

**Files:**
- Create: `backend/app/routes/loyalty_pos.py` (blueprint `loyalty_pos`, prefijo `/api/v1/loyalty`)
- Create: `backend/app/services/loyalty/search.py`
- Modify: `backend/app/__init__.py` (registrar blueprint)
- Test: `backend/tests/test_loyalty_pos_api.py`

**Interfaces:**
- Consumes: `pos_hooks.set_customer`, `pos_hooks.add_redemption`, `wallet.balance`.
- Produces:
  - `search.find_customers(q: str, limit: int = 20) -> list[Customer]` — si `q` coincide exacto con un `qr_token` devuelve ese cliente; si no, `normalize_search(q)` con ≥ 2 caracteres, `search_text LIKE %q%` por cada palabra, orden por apellido/nombre.
  - `search.mask_email('lucia@gmail.com') -> 'lu…@gmail.com'`, `search.mask_phone('1155550032') -> '11…0032'`.
  - Rutas (todas `@token_required` + `@module_required('POS')`):
    - `GET /api/v1/loyalty/customers/search?q=` → `[{id, full_name, email_masked, phone_masked, balance}]`
    - `GET /api/v1/loyalty/rewards` → premios activos `[{id, name, cost, product_variant_id, product_id}]`
    - `PUT /api/v1/loyalty/pos-sales/<sale_id>/customer` body `{customer_id: int | null}` → venta serializada
    - `POST /api/v1/loyalty/pos-sales/<sale_id>/redemptions` body `{reward_id, modifier_option_ids}` → venta serializada

- [ ] **Step 1: Write failing tests** — `test_search_ignores_accents_and_case` ("lucia" encuentra "Lucía Pérez"); `test_homonyms_show_distinct_masked_contacts` (Review Focus 5); `test_search_by_qr_token_returns_exact_customer`; `test_search_requires_two_chars` (`q='l'` → `[]`); `test_waiter_without_pos_module_gets_403` (usuario con `Camarero` solo → 403 en las cuatro rutas); `test_set_customer_and_redeem_via_api`.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** `search.py` y `loyalty_pos.py`.
- [ ] **Step 4: Run** `pytest tests/test_loyalty_pos_api.py -v` → PASS.
- [ ] **Step 5: Commit** `git commit -m "Fidelización: API del POS para clientes y canjes"`

### Task 5: Autenticación de clientes y API pública de la wallet

**Files:**
- Create: `backend/app/services/loyalty/customer_auth.py`
- Create: `backend/app/routes/loyalty_public.py` (blueprint `loyalty_public`, prefijo `/api/public/loyalty`)
- Modify: `backend/app/utils/jwt_utils.py` (`token_required` rechaza tokens sin `user_id` o con `typ == 'customer'` con 401)
- Modify: `backend/app/config.py` (`GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')`)
- Modify: `backend/app/__init__.py`
- Test: `backend/tests/test_loyalty_public_api.py`

**Interfaces:**
- Produces (`customer_auth.py`):
  - `verify_google_credential(credential: str) -> dict` — `GET https://oauth2.googleapis.com/tokeninfo?id_token=…` con `requests` (ya es dependencia), timeout 5 s; exige `aud == GOOGLE_CLIENT_ID`, `email_verified == 'true'`; devuelve `{sub, email, given_name, family_name}`; error → `LoyaltyError` → 401. Los tests la reemplazan con monkeypatch.
  - `issue_customer_token(customer: Customer) -> str` — JWT HS256 con `{'customer_id', 'typ': 'customer', 'exp': +90 días}`.
  - Decorador `customer_required` — lee `Authorization: Bearer`, exige `typ == 'customer'`, pasa `customer` a la vista; si no, 401.
- Rutas:
  - `POST /auth/google` body `{credential, accept_terms?: bool, promo_opt_in?: bool}` → cliente existente por `google_sub`: `{token, customer}`; nuevo sin `accept_terms` → 409 `{needs_terms: true, first_name}`; nuevo con `accept_terms` → crea y devuelve `{token, customer}` (201).
  - `GET /me` → `{first_name, last_name, email, phone, balance, qr_token, promo_opt_in: bool}`
  - `PATCH /me` body `{phone?, promo_opt_in?}` → `/me` actualizado.
  - `GET /me/movements?limit=50` → `[{date, kind, amount, label}]` con `label` en castellano: `compra`, `compra anulada`, `canje <premio>`, `canje anulado`, `ajuste`.
  - `GET /rewards` → premios activos `[{name, cost}]` (sin auth).

- [ ] **Step 1: Write failing tests** — `test_new_customer_needs_terms_then_registers` (409 y luego 201); `test_existing_customer_logs_in`; `test_promo_opt_in_defaults_false_and_can_change`; `test_me_returns_balance_and_qr`; `test_movements_labels`; `test_customer_token_rejected_by_staff_endpoint` (Review Focus 1: token de cliente en `GET /api/v1/loyalty/rewards` → 401, no 500); `test_staff_token_rejected_by_customer_endpoint` → 401.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `pytest tests/test_loyalty_public_api.py tests/test_access_control.py -v` → PASS.
- [ ] **Step 5: Commit** `git commit -m "Fidelización: login de clientes con Google y API de la wallet"`

### Task 6: API de administración y reportes

**Files:**
- Create: `backend/app/routes/loyalty_admin.py` (blueprint `loyalty_admin`, prefijo `/api/v1/loyalty/admin`; todo `@token_required` + `@module_required('Fidelizacion')`)
- Create: `backend/app/services/loyalty/admin.py`, `backend/app/services/loyalty/reports.py`
- Modify: `backend/app/__init__.py`
- Test: `backend/tests/test_loyalty_admin_api.py`, `backend/tests/test_loyalty_reports.py`

**Interfaces:**
- `admin.py` (todas escriben `LoyaltyChangeLog` por campo cambiado y hacen commit):
  - `set_variant_cafecitos(user, variant_ids: list[int], cafecitos: int) -> list[ProductVariant]` (≥ 0)
  - `create_reward(user, data) -> Reward`, `update_reward(user, reward_id, data) -> Reward`
  - `update_settings(user, active_days: int) -> LoyaltySettings` (1–365)
  - `regenerate_qr(user, customer_id) -> Customer`
- `reports.py` (fechas `date`; `period` = `(desde, hasta)` inclusivo sobre `business_date`):
  - `active_customers(today: date) -> list[dict]` — `{id, full_name, last_visit, visits}` con visita en `[today - active_days + 1, today]`.
  - `inactive_customers(today: date) -> list[dict]` — resto de clientes, `last_visit` o `None` (`never_visited: True`).
  - `redemptions(desde, hasta) -> {total, cafecitos, pesos, by_reward: [{reward, count, cafecitos, pesos}]}` — excluye `redeem` con reversa.
  - `registered_vs_unregistered(desde, hasta) -> {registered: {total, count, avg_ticket}, unregistered: {…}}` — `registered` desde `pos_sales` cerradas no práctica con `customer_id`; `unregistered` = total de la tabla `sales` del período (Galia + Fudo, `estado` no anulada) menos lo registrado. Ticket promedio = total / cantidad de ventas.
- Rutas: `GET/PUT /settings`, `GET/POST /rewards`, `PUT /rewards/<id>`, `GET /variants?q=` (variantes con `cafecitos`), `PUT /variants/cafecitos` body `{variant_ids, cafecitos}`, `GET /customers?q=` (con saldo), `GET /customers/<id>` (con movimientos), `POST /customers/<id>/adjustments` body `{amount, reason}`, `POST /customers/<id>/regenerate-qr`, `GET /change-log?entity=&limit=`, `GET /reports/active`, `GET /reports/inactive`, `GET /reports/redemptions?from=&to=`, `GET /reports/sales-comparison?from=&to=`.

- [ ] **Step 1: Write failing tests**
  - Admin: `test_pos_only_user_gets_403_on_admin_api`; `test_set_variant_cafecitos_logs_old_and_new`; `test_reward_cost_change_does_not_touch_past_redemptions`; `test_settings_validates_range`; `test_adjustment_endpoint_requires_reason`.
  - Reportes: `test_active_uses_configured_period` (visitas a 10 y 40 días; `active_days=30` → uno activo, uno inactivo; con `active_days=45` → ambos activos); `test_inactive_includes_never_visited`; `test_redemptions_excludes_reversed_and_uses_frozen_values`; `test_sales_comparison_counts_fudo_as_unregistered` (una `Sale` de origen Fudo sin cliente + una venta POS con cliente → montos y tickets separados); `test_practice_sales_excluded`.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `pytest tests/test_loyalty_admin_api.py tests/test_loyalty_reports.py -v` → PASS.
- [ ] **Step 5: Commit** `git commit -m "Fidelización: administración, historial y reportes"`

### Task 7: POS — cliente, buscador con QR y canje

**Files:**
- Create: `frontend/src/pos/loyalty/CustomerButton.jsx`, `frontend/src/pos/loyalty/CustomerSearchModal.jsx`, `frontend/src/pos/loyalty/RedeemModal.jsx`, `frontend/src/pos/loyalty/QrScanner.jsx`, `frontend/src/pos/loyalty/loyaltyFormat.js`
- Modify: `frontend/src/pos/api/posApi.js` (`searchCustomers(q)`, `getRewards()`, `setSaleCustomer(saleId, customerId)`, `addRedemption(saleId, rewardId, modifierOptionIds)`)
- Modify: `frontend/src/pos/sale/SaleHeader.jsx` (botón "👤 Cliente" o "👤 Nombre · N ☕ · +M"; botón "🎁 Canjear" si hay cliente)
- Modify: `frontend/src/pos/modals/PaymentModal.jsx` (si la venta no tiene cliente: bloque opcional "¿Cliente con cafecitos?" que abre el mismo buscador)
- Modify: `frontend/src/pos/utils/permissions.js` (`canLoyalty` = admin o módulo `POS`)
- Modify: `frontend/package.json` (lector de QR por cámara, librería a elección del builder)
- Test: `frontend/src/pos/loyalty/loyaltyFormat.test.js`, `frontend/src/pos/utils/permissions.test.js` (si no existe, crear)

**Interfaces:**
- Consumes: rutas de Task 4; venta serializada de Task 3 (`customer`, `cafecitos_preview`, `items[].is_redemption`).
- Produces: `loyaltyFormat.js` → `customerChip(customer, preview) -> string` (`'Lucía Pérez · 14 ☕ · +2'`), `missingFor(balance, cost) -> number` (`max(0, cost - balance)`).

- [ ] **Step 1: Write failing tests** — `customerChip({full_name:'Lucía Pérez', balance:14}, 2) === 'Lucía Pérez · 14 ☕ · +2'`; con preview 0 no muestra `+0`; `missingFor(14, 16) === 2`, `missingFor(14, 8) === 0`; `posPermissions({isAdmin:false, modules:['Camarero']}).canLoyalty === false`, con `['POS']` → `true`.
- [ ] **Step 2: Run** `cd frontend && npx vitest run src/pos/loyalty src/pos/utils` → FAIL.
- [ ] **Step 3: Implement** componentes. Buscador: debounce 200 ms, desde 2 caracteres; un valor tipeado/pegado de un lector USB se manda igual a `searchCustomers` (el backend resuelve el `qr_token`). `RedeemModal` lista premios con "faltan N" deshabilitados y pide los modificadores obligatorios con el selector ya existente del POS. Ítems con `is_redemption` muestran "(canje)" y $0. Todo oculto si `!canLoyalty`.
- [ ] **Step 4: Run** tests → PASS; `npm run build` sin errores. Verificar en el navegador con el preview del frontend: asociar cliente, ver chip, canjear, cobrar.
- [ ] **Step 5: Commit** `git commit -m "Fidelización: cliente y canje en el POS"`

### Task 8: Pantalla de administración `/fidelizacion`

**Files:**
- Create: `frontend/src/pages/Loyalty.jsx` (pestañas: Clientes, Premios, Cafecitos por producto, Reportes, Historial, Configuración)
- Create: `frontend/src/components/loyalty/*.jsx` (una por pestaña), `frontend/src/services/loyaltyService.js`
- Modify: `frontend/src/App.jsx` (`<Route path="/fidelizacion" element={<RoleProtectedRoute moduleName="Fidelizacion"><Loyalty /></RoleProtectedRoute>} />`) y el menú lateral donde se listan los módulos.
- Test: `frontend/src/services/loyaltyService.test.js` (arma bien las URLs y querystrings de reportes)

**Interfaces:**
- Consumes: rutas de Task 6.
- Comportamiento: Clientes = buscador + detalle con movimientos, botón "Ajustar" (cantidad con signo + motivo obligatorio; sugerencia de motivo "Sellos de tarjeta de papel") y "Regenerar QR" con confirmación. Cafecitos por producto = lista de variantes agrupadas por producto con input numérico y "aplicar a todas las variantes". Reportes = filtro por mes o rango, 4 bloques (5.1–5.4), con la nota de 5.4 de Global Constraints.

- [ ] **Step 1: Write failing test** — `reportsUrl('redemptions', {from:'2026-11-01', to:'2026-11-30'}) === '/api/v1/loyalty/admin/reports/redemptions?from=2026-11-01&to=2026-11-30'`; `monthRange('2026-02') → {from:'2026-02-01', to:'2026-02-28'}`.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** servicio y pantallas.
- [ ] **Step 4: Run** tests → PASS; `npm run build`; verificar en el navegador cada pestaña con datos de prueba.
- [ ] **Step 5: Commit** `git commit -m "Fidelización: pantalla de administración y reportes"`

### Task 9: "Mis cafecitos" en la carta

**Files:**
- Create: `menu-site/cafecitos.html`, `menu-site/src/cafecitos/main.jsx`, `menu-site/src/cafecitos/CafecitosApp.jsx`, `menu-site/src/cafecitos/api.js`, `menu-site/src/cafecitos/session.js`, `menu-site/src/cafecitos/labels.js`
- Modify: `menu-site/vite.config.js` (entrada `cafecitos`), `menu-site/package.json` (generador de QR a elección del builder), `menu-site/src/components/Header.jsx` o `Footer.jsx` (link "Mis cafecitos")
- Modify: `render.yaml` (rewrite `/cafecitos` → `/cafecitos.html` en `galia-carta`; env `VITE_API_URL` y `VITE_GOOGLE_CLIENT_ID` en `galia-carta`; `GOOGLE_CLIENT_ID` en `galia-backend`) y agregar el dominio de la carta a `CORS_ORIGINS` (nota en el PR, se setea en Render)
- Test: `menu-site/src/cafecitos/session.test.js`, `menu-site/src/cafecitos/labels.test.js`

**Interfaces:**
- Consumes: rutas de Task 5.
- Produces: `session.js` → `getToken()`, `setToken(t)`, `clearToken()` sobre `localStorage['galia.cafecitos.token']`, cada acceso dentro de try/catch (si falla, sesión en memoria). `labels.js` → `reachable(balance, rewards) -> {available: Reward[], next: [{reward, missing}]}`.
- Pantalla: sin sesión → explicación corta + botón "Entrar con Google" (Google Identity Services, `VITE_GOOGLE_CLIENT_ID`); si el backend responde `needs_terms` → casilla obligatoria de términos + casilla opcional sin tildar de promociones por mail → reenviar. Con sesión → saldo grande, QR del `qr_token`, "Te alcanza para" / "faltan N", movimientos, editar teléfono, cerrar sesión. 401 → borrar token y volver al inicio.

- [ ] **Step 1: Write failing tests** — `reachable(14, [{name:'Café',cost:8},{name:'Focaccia',cost:10},{name:'Torta',cost:16}])` → `available` = Café y Focaccia, `next = [{reward: Torta, missing: 2}]`; `session` sigue funcionando si `localStorage.setItem` tira excepción.
- [ ] **Step 2: Run** `cd menu-site && npm test` → FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `npm test` → PASS; `npm run build` genera `dist/cafecitos.html`; verificar en el navegador con el backend local (la credencial de Google se puede reemplazar en dev con el monkeypatch de los tests o con un Client ID de prueba).
- [ ] **Step 5: Commit** `git commit -m "Fidelización: Mis cafecitos en la carta"`

### Task 10: Verificación final

- [ ] **Step 1:** `cd backend && pytest -q` → todo verde (salvo los tests ya rotos conocidos de antes; listarlos en el PR).
- [ ] **Step 2:** `cd frontend && npm test && npm run build`; `cd menu-site && npm test && npm run build` → OK.
- [ ] **Step 3:** `flask db upgrade` contra una base Postgres descartable → la migración `b7a0` aplica y `flask db downgrade` la revierte.
- [ ] **Step 4:** Recorrido punta a punta en el navegador: registrarse en la carta → buscar en el POS → cobrar → ver saldo en la carta → canjear → anular la venta → saldo vuelve.
- [ ] **Step 5:** PR contra `main` desde `feature/fidelizacion`, con la lista de tareas del dueño: crear OAuth Client ID de Google, setear `GOOGLE_CLIENT_ID` / `VITE_GOOGLE_CLIENT_ID` / `VITE_API_URL` / `CORS_ORIGINS`, textos de términos y consentimiento, cargar cafecitos y premios iniciales.
