# Apertura de caja con hora anterior — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Abrir la caja con una fecha y hora anterior. La caja toma los pagos y las anulaciones sin caja desde esa hora y sigue abierta normalmente.

**Architecture:** `cash_service.open_session` acepta `opened_at` opcional. Si es anterior a ahora, en la misma transacción asigna a la sesión los `PosPayment` sin caja del período y guarda `registered_at`. `add_movement` acepta `expense_date` para los gastos. El resto del arqueo (resumen, cierre) no cambia, porque ya calcula por sesión.

**Tech Stack:** Flask + SQLAlchemy + Alembic (pytest sobre SQLite), React + Vite + Vitest.

**Spec:** `docs/superpowers/specs/2026-11-27-caja-apertura-pasada-design.md`

## Global Constraints

- Migración `b9b0_cash_backdated_open`, `down_revision = 'b9a0_vouchers'`.
- Fechas en la base: UTC naive (`common.now()` = `datetime.utcnow()`). La UI manda hora de Argentina con offset (`-03:00`). Si llega sin offset, se interpreta como hora de Argentina (`ARGENTINA_TZ`).
- Errores en castellano con `bad_request` / `PosError`, como el resto de `cash_service`.
- Permiso: `POS` (el mismo de abrir hoy). Sin permiso nuevo.
- Textos exactos: "La hora de apertura es inválida", "La apertura no puede ser futura", "La apertura no puede ser anterior al último cierre (dd/mm HH:MM)" (hora de Argentina), "La fecha del gasto debe estar entre la apertura y hoy", etiqueta "cargada después", aviso "Va a tomar los pagos sin caja desde dd/mm HH:MM".
- Tolerancia de reloj para "futuro": 1 minuto.
- Trabajar en el worktree `C:\Users\onofr\Desktop\galia-caja-pasada` (rama `feature/caja-apertura-pasada`).

## Review Focus

- **Pago justo en el borde:** un pago con `created_at == opened_at` entra (intervalo cerrado a la izquierda). Un pago un segundo antes no entra. El test va en la Task 2.
- **Venta de práctica sin caja:** una caja real nunca toma pagos de ventas `is_practice`, y una de práctica nunca toma pagos reales. El test va en la Task 2.
- **Último cierre de otra caja:** el límite "no antes del último cierre" mira solo la misma caja. Una caja "Barra" cerrada más tarde no bloquea. El test va en la Task 2.
- **Hora sin offset desde la UI:** `"2026-11-26T08:00"` se toma como 08:00 de Argentina, o sea 11:00 UTC. El test va en la Task 2.
- **Fecha del gasto con apertura de hoy:** el campo no aparece en la UI, y si llega `expense_date` igual a hoy, se acepta. El test va en la Task 3.

---

### Task 1: Columna `registered_at` y serialización

**Files:**
- Create: `backend/migrations/versions/b9b0_cash_backdated_open.py`
- Modify: `backend/app/models/pos/cash.py` (`CashSession`)
- Modify: `backend/app/services/pos/cash_serializers.py` (`session_to_dict`, `register_to_dict`)
- Modify: `backend/app/services/pos/cash_service.py` (`list_sessions`: filas)
- Test: `backend/tests/test_migration_chain.py`, `backend/tests/test_pos_cash_service.py`

**Interfaces:**
- Produces: `CashSession.registered_at: DateTime | None`. En los dict de sesión, historial y `open_session` de la caja: `registered_at` (ISO o `None`) y `backdated: bool` (= `registered_at is not None`).

- [ ] **Step 1: Tests que fallan**

```python
# test_migration_chain.py
def test_cash_backdated_follows_vouchers():
    assert _revisions()['b9b0_cash_backdated_open'] == ['b9a0_vouchers']

# test_pos_cash_service.py
def test_normal_open_is_not_backdated(ctx):
    session = cash_service.open_session(user, make_register().id, 0)
    data = session_to_dict(session, cash_service.session_summary(session))
    assert data['registered_at'] is None and data['backdated'] is False
```
(Usar los fixtures existentes del archivo.)

- [ ] **Step 2:** `cd backend; python -m pytest tests/test_migration_chain.py tests/test_pos_cash_service.py -q`. Esperado: FAIL.
- [ ] **Step 3: Implementar.** La migración agrega `cash_sessions.registered_at` (`sa.DateTime`, nullable) con `op.add_column` y el downgrade la quita con `batch_alter_table` (SQLite). El modelo suma la columna. Los serializadores y `list_sessions` suman los dos campos.
- [ ] **Step 4:** Repetir el pytest del paso 2. Esperado: PASS.
- [ ] **Step 5: Commit** `feat(caja): columna registered_at para aperturas cargadas después`

### Task 2: Abrir con hora anterior

**Files:**
- Modify: `backend/app/services/pos/cash_service.py` (`open_session`, helper nuevo `parse_opened_at`)
- Modify: `backend/app/routes/pos_cash.py` (`POST /sessions` pasa `data.get('opened_at')`)
- Test: `backend/tests/test_pos_cash_backdated.py` (nuevo; fixtures como en `test_pos_cash_payments.py`: `ctx`, `_billed_sale`)

**Interfaces:**
- Consumes: `CashSession.registered_at` (Task 1).
- Produces:
  - `parse_opened_at(value) -> datetime | None` (UTC naive). Si recibe `None` o `''`, devuelve `None`. Si el valor es inválido, da 400.
  - `open_session(user, register_id, opening_float, opened_at=None) -> CashSession`.

**Lógica de `open_session` cuando `opened_at` viene:**
1. Validar: no futuro (`> now() + 1 min` → 400). Buscar la última sesión cerrada de la misma caja y con el mismo `is_practice`. Si `opened_at < closed_at` → 400 con la fecha en hora de Argentina.
2. Si `opened_at < now()`: la sesión lleva `opened_at` y `registered_at = now()`, y el movimiento `opening_float` lleva `created_at = opened_at`.
3. Tomar los pagos con un UPDATE sobre `PosPayment` unido a `PosSale` (filtrar por subquery de ids de ventas con `is_practice == session.is_practice`):
   - `cash_session_id IS NULL AND created_at >= opened_at` → `cash_session_id = session.id`;
   - `cancel_cash_session_id IS NULL AND cancelled_at >= opened_at` → `cancel_cash_session_id = session.id`.
4. El evento `opened` suma `backdated=True`, `opened_at`, `registered_at`, `payments_taken` (cantidad), `payments_total`, `cancellations_taken` y `cancellations_total`.

Sin `opened_at`, todo queda igual que hoy.

- [ ] **Step 1: Tests que fallan** (`test_pos_cash_backdated.py`). Para fechar pagos, cobrarlos sin caja y ajustar `created_at` / `cancelled_at` con `db.session.commit()`.
  - `test_backdated_open_takes_unassigned_payments`: dos pagos sin caja de $900 a las 08:00 y 09:00 (hora de Argentina), apertura a las 08:00 → los dos con `cash_session_id == session.id`. En el resumen, el efectivo `collected == 1800.0` y `registered_at is not None`.
  - `test_payment_before_opening_is_not_taken`: pago a las 07:59:59, apertura a las 08:00 → sigue `None`. Pago a las 08:00:00 exacto → se toma.
  - `test_takes_unassigned_cancellations`: pago de otra sesión (cerrada antes) anulado sin caja después de la apertura → `cancel_cash_session_id == session.id` y el resumen `cancelled == 900.0`.
  - `test_does_not_take_payments_of_other_sessions`: un pago con sesión no cambia.
  - `test_practice_payments_not_taken`: una venta `is_practice=True` sin caja no se toma en una caja real.
  - `test_future_opening_rejected`: `now() + 5 min` → `PosError` con status 400 "La apertura no puede ser futura". `now() + 30 s` se acepta.
  - `test_before_last_close_rejected`: misma caja cerrada a las 10:00 y apertura a las 09:00 → 400 que contiene "anterior al último cierre". Otra caja cerrada a las 10:00 no bloquea.
  - `test_naive_value_is_argentina_time`: `parse_opened_at('2026-11-26T08:00') == datetime(2026, 11, 26, 11, 0)`. `parse_opened_at('2026-11-26T08:00:00-03:00')` da lo mismo. `parse_opened_at('x')` → 400 "La hora de apertura es inválida".
  - `test_backdated_event_payload`: evento `opened` con `backdated is True` y `payments_taken == 2`.
  - `test_api_open_with_opened_at` (en el mismo archivo, con el cliente de test como en `test_pos_cash_api.py`): `POST /api/v1/pos/cash/sessions` con `opened_at` → 200 y `backdated: true`.
- [ ] **Step 2:** `python -m pytest tests/test_pos_cash_backdated.py -q`. Esperado: FAIL.
- [ ] **Step 3:** Implementar `parse_opened_at` (`datetime.fromisoformat`; si el valor es aware → `astimezone(pytz.utc)`; si es naive → `ARGENTINA_TZ.localize`; quitar tzinfo), `open_session` y la ruta.
- [ ] **Step 4:** `python -m pytest tests/test_pos_cash_backdated.py tests/test_pos_cash_service.py tests/test_pos_cash_payments.py tests/test_pos_cash_api.py tests/test_pos_cash_close.py -q`. Esperado: PASS.
- [ ] **Step 5: Commit** `feat(caja): abrir la caja con hora anterior tomando los pagos sin caja`

### Task 3: Fecha del gasto

**Files:**
- Modify: `backend/app/services/pos/cash_service.py` (`add_movement`, `_create_expense`)
- Modify: `backend/app/routes/pos_cash.py` (pasa `expense_date=data.get('expense_date')`)
- Test: `backend/tests/test_pos_cash_backdated.py`

**Interfaces:**
- Produces: `add_movement(user, session_id, kind, amount, reason, category_id=None, supplier_id=None, expense_date=None)`. `expense_date` es un string `YYYY-MM-DD` o `None`. Solo se usa con `kind == 'expense'` y en los demás tipos se ignora. `_create_expense(..., fecha)`.

- [ ] **Step 1: Tests que fallan**
  - `test_expense_with_past_date`: sesión abierta hace 2 días y gasto con `expense_date` de ayer → `Expense.fecha` es ayer.
  - `test_expense_date_out_of_range`: anterior al día de apertura o posterior a hoy → 400 "La fecha del gasto debe estar entre la apertura y hoy".
  - `test_expense_date_defaults_to_today`: sin `expense_date` → hoy (`get_current_date_argentina()`). Con apertura de hoy y `expense_date` = hoy → se acepta.
  - `test_expense_date_invalid`: `'x'` → 400.
- [ ] **Step 2:** `python -m pytest tests/test_pos_cash_backdated.py -q`. Esperado: FAIL en los nuevos.
- [ ] **Step 3:** Implementar. El día de apertura es `opened_at` convertido a hora de Argentina (`.date()`).
- [ ] **Step 4:** `python -m pytest tests -q -k cash`. Esperado: PASS.
- [ ] **Step 5: Commit** `feat(caja): fecha del gasto en cajas abiertas días antes`

### Task 4: Interfaz

**Files:**
- Modify: `frontend/src/pos/utils/cashMath.js` + `cashMath.test.js`
- Modify: `frontend/src/pos/cash/OpenSessionModal.jsx`, `frontend/src/pos/cash/MovementModal.jsx`, `frontend/src/pos/cash/CashPage.jsx`
- Modify: `frontend/src/pages/CashSessions.jsx`, `frontend/src/pages/CashSessionDetail.jsx`

**Interfaces:**
- Consumes:
  - API: `opened_at` en `posCashApi.open(body)` y `expense_date` en `posCashApi.addMovement(id, body)`, sin cambios en `posApi.js`.
  - Campos `backdated` y `registered_at` (Task 1).
- Produces (en `cashMath.js`):
  - `toArgentinaIso(localValue: string) -> string`: `'2026-11-26T08:00'` → `'2026-11-26T08:00:00-03:00'`.
  - `openedBeforeToday(session, today: string) -> boolean`: compara el día de Argentina de `opened_at` (UTC naive) con `today` (`YYYY-MM-DD`).
  - `argentinaDate(isoUtc) -> 'YYYY-MM-DD'`.

- [ ] **Step 1: Tests Vitest que fallan:**
  - `toArgentinaIso('2026-11-26T08:00') === '2026-11-26T08:00:00-03:00'`;
  - `argentinaDate('2026-11-27T02:30:00') === '2026-11-26'`;
  - `openedBeforeToday({ opened_at: '2026-11-26T11:00:00' }, '2026-11-27') === true`;
  - con `'2026-11-27T11:00:00'` → `false`.
- [ ] **Step 2:** `cd frontend; npx vitest run src/pos/utils/cashMath.test.js`. Esperado: FAIL.
- [ ] **Step 3: Implementar.**
  - `OpenSessionModal`: botón de texto "Abrir con hora anterior" que muestra un `<input type="datetime-local">` con `max` = ahora en hora local. Con valor, muestra el aviso "Va a tomar los pagos sin caja desde dd/mm HH:MM" y manda `opened_at: toArgentinaIso(valor)`.
  - `MovementModal`: si `kind === 'expense'` y `openedBeforeToday(session, hoy)`, muestra el campo "Fecha del gasto" (`<input type="date">`), con `min` = día de apertura, `max` = hoy y valor por defecto hoy, y manda `expense_date`.
  - `CashPage` (línea "Abierta …"): si la apertura no es de hoy, muestra fecha y hora, no solo la hora. Si `session.backdated`, suma la etiqueta "cargada después".
  - `CashSessions`: etiqueta "cargada después" en la celda de apertura.
  - `CashSessionDetail`: "cargada después el dd/mm HH:MM" con `registered_at`.
  - Estilos: los del sistema de diseño de Galia que ya usan esos archivos (etiqueta como los chips existentes, sin coral ni lima en el texto).
- [ ] **Step 4:** `npx vitest run` y `npm run build`. Esperado: todo verde, build OK.
- [ ] **Step 5: Commit** `feat(caja): abrir con hora anterior y fecha del gasto en la UI`

### Task 5: Verificación real y PR

- [ ] **Step 1:** Levantar el backend (SQLite) y el frontend del worktree con el preview y recorrer el flujo:
  1. cobrar dos ventas sin caja;
  2. abrir con hora anterior a la primera;
  3. ver que los pagos aparecen en la caja y salen de "Pagos sin caja";
  4. cargar un gasto con fecha de ayer (la caja abierta ayer) y verlo en Gastos con esa fecha;
  5. intentar una hora futura y una anterior al último cierre (error visible);
  6. cerrar con arqueo;
  7. ver "cargada después" en Finanzas → Cajas y en el detalle.

  Capturas como prueba.
- [ ] **Step 2:** `cd backend; python -m pytest -q`. Sin fallas nuevas respecto de `main`.
- [ ] **Step 3:** `git fetch; git merge origin/main`, push y PR a `main`. En la descripción va el checklist de deploy: correr `b9b0` en test (upgrade, downgrade, upgrade) y contar `cash_sessions` antes y después.
