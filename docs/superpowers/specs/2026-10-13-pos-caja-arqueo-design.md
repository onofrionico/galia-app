# Caja y arqueo (sub-proyecto 2) — Diseño

**Fecha:** 2026-10-13
**Rama:** `feature/pos-caja-arqueo` (desde `main`, con el sub-proyecto 1 completo: 1a, 1b y 1c)
**Antecede:**
- `docs/superpowers/specs/2026-10-09-pos-sales-engine-design.md` (1a: ventas, pagos y API `/api/v1/pos`)
- `docs/superpowers/specs/2026-10-10-pos-caja-design.md` (1b: POS de caja web)
- `docs/superpowers/specs/2026-10-10-pos-camarero-design.md` (1c: Camarero en el celular)

## Contexto

El POS nativo reemplaza a Fudo. El sub-proyecto 1 dejó el cobro funcionando: `pos_payments` guarda cada pago con su medio (`payment_methods.kind`: `cash`, `card`, `transfer`, `other`), el monto aplicado y, en efectivo, lo recibido y el vuelto. Falta el concepto de **caja**: apertura con fondo, movimientos de efectivo, cierre con arqueo por medio de pago e historial.

El módulo Gastos ya tiene los campos `expenses.de_caja` y `expenses.caja`, que hoy vienen de la importación de Fudo. Los gastos pagados con efectivo de la caja se registran ahí.

## Decisiones de producto

- **Cajas:** hoy una sola caja física, pero el modelo admite varias.
- **Cobrar sin caja:** se puede cobrar siempre, aunque no haya caja abierta. El pago queda asociado a la sesión abierta en ese momento, o sin caja si no hay ninguna.
- **Arqueo visible:** al cerrar se muestra lo esperado por medio de pago, se carga lo contado al lado y la diferencia se calcula en vivo.
- **Movimientos:** fondo inicial al abrir, gastos pagados con efectivo de la caja (que crean el gasto en el módulo Gastos), retiros e ingresos que no son ventas. Sin propinas, como se decidió en el 1a.
- **Permisos:** el módulo `POS` existente abre, cierra y registra movimientos. Anular movimientos y reabrir sesiones cerradas queda para admin.
- **Cierre:** se bloquea mientras haya ventas abiertas o en cobro.
- **Interfaz:** la operación de la caja vive en `/pos`; el historial, en Galia (Finanzas → Cajas).

## Enfoque

Tablas propias para cajas, sesiones, movimientos, conteos y eventos. Cada pago guarda la sesión abierta al registrarse y, si se anula, la sesión abierta al anularse. Lo esperado sale de consultas exactas por sesión, no de rangos horarios, y una sesión cerrada nunca cambia.

Se descartaron:
- **Arqueo por rango horario, sin tocar los pagos:** con dos cajas abiertas es ambiguo, y un pago en el borde del horario puede caer en la sesión equivocada.
- **Movimientos como filas de `expenses`:** mezcla retiros e ingresos con gastos y ensucia los reportes de gastos.

## Modelo de datos

Una migración nueva, `b2a0_add_cash_registers`, con `down_revision = 'b1b1_add_pos_cash_ui_support'`.

### `cash_registers`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | PK | |
| `name` | String(60) | único |
| `position` | Integer | orden, por defecto 0 |
| `is_active` | Boolean | por defecto true |

La migración carga "Caja principal". Las cajas no se administran desde la UI en este sub-proyecto: con una sola caja no hace falta.

### `cash_sessions`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | PK | |
| `register_id` | FK `cash_registers` | índice |
| `status` | String(10) | `open` o `closed` |
| `opened_at`, `opened_by` | DateTime (UTC), FK `users` | |
| `opening_float` | Numeric(12,2) | fondo inicial, ≥ 0 |
| `closed_at`, `closed_by` | DateTime, FK `users` | nulos mientras está abierta |
| `closing_note` | String(500) | nula |

Índice único parcial: una sola sesión `open` por caja (`UNIQUE(register_id) WHERE status = 'open'`, en PostgreSQL y en SQLite). Además, el servicio lo valida con bloqueo de fila.

### `cash_movements`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | PK | |
| `session_id` | FK `cash_sessions` | índice |
| `kind` | String(20) | `opening_float`, `expense`, `withdrawal`, `deposit` |
| `amount` | Numeric(12,2) | > 0, salvo `opening_float`, que puede ser 0; el signo sale del tipo |
| `reason` | String(255) | obligatorio, salvo `opening_float` |
| `expense_id` | FK `expenses` | solo en `expense` |
| `created_by`, `created_at` | FK `users`, DateTime | |
| `cancelled_by`, `cancelled_at`, `cancel_reason` | | anulación (solo admin) |

Signo para el efectivo: `opening_float` y `deposit` suman; `expense` y `withdrawal` restan.

### `cash_session_counts`

Se escribe al cerrar, una fila por cada medio de pago con esperado o contado distinto de cero, y siempre una para el efectivo.

| Columna | Tipo |
|---|---|
| `id` | PK |
| `session_id` | FK `cash_sessions` |
| `payment_method_id` | FK `payment_methods` |
| `method_name` | String(50) (copia) |
| `expected`, `counted`, `difference` | Numeric(12,2) (`difference = counted − expected`) |

Única por (`session_id`, `payment_method_id`).

### `cash_events`

Auditoría: `id`, `register_id`, `session_id` (nulo), `kind` (`opened`, `movement_added`, `movement_cancelled`, `closed`, `reopened`), `user_id`, `created_at`, `payload` (JSON). Su `id` máximo sirve también como versión para el polling (ver API).

### Cambios en `pos_payments`

- `cash_session_id` FK `cash_sessions`, nula, con índice: la sesión abierta al registrar el pago.
- `cancel_cash_session_id` FK `cash_sessions`, nula, con índice: la sesión abierta al anular el pago.

Los pagos anteriores a la migración quedan con ambas en nulo, es decir, sin caja.

## Reglas

### Sesión actual

`cash_service.current_session_id()` devuelve el id de la única sesión `open`, o `None` si no hay ninguna o hay más de una. Con más de una caja abierta, los pagos quedan sin caja: asignar caja por dispositivo queda para cuando exista una segunda caja.

`payment_service.add_payment` guarda `cash_session_id = current_session_id()`. `payment_service.cancel_payment` guarda `cancel_cash_session_id = current_session_id()`. El resto del cobro no cambia.

### Abrir

- Requiere `POS`. Pide caja activa y `opening_float` ≥ 0 (con `parse_decimal`, cuantizado a 0,01).
- Bloquea la fila de la caja (`SELECT … FOR UPDATE`). Si ya tiene una sesión `open`, responde 409.
- Crea la sesión, el movimiento `opening_float` y el evento `opened`.

### Movimientos

- Requieren `POS` y una sesión `open` (si no, 409).
- `kind` ∈ {`expense`, `withdrawal`, `deposit`}; `amount` > 0; `reason` obligatorio (hasta 255 caracteres).
- **`expense`** pide además `category_id`, una categoría de gasto activa (400 si no lo es), y opcionalmente `supplier_id`, un proveedor existente. En la misma transacción crea un `Expense` con:
  - `fecha` = día comercial de Argentina (`get_current_date_argentina`);
  - `importe` = monto;
  - `comentario` = motivo;
  - `category_id` y `supplier_id`, y `proveedor` con el nombre del proveedor si viene;
  - `de_caja = true`, `caja` = nombre de la caja, `medio_pago = 'Efectivo'`, `estado_pago = 'Pagado'`;
  - `creado_por` = email del usuario.
- Evento `movement_added`.

### Anular un movimiento

- Requiere admin. Pide motivo, y la sesión del movimiento debe estar `open` (anular en una sesión cerrada es 409: hay que reabrirla). `opening_float` no se anula.
- Marca `cancelled_*`. Si es un gasto, marca `Expense.cancelado = true`.
- Evento `movement_cancelled`.

### Lo esperado (`session_summary`)

Por medio de pago:
- **cobrado:** suma de `amount` de los pagos con `cash_session_id = sesión`, sin importar si después se anularon;
- **anulado:** suma de `amount` de los pagos con `cancel_cash_session_id = sesión`;
- **esperado** = cobrado − anulado.

Un pago cobrado y anulado en la misma sesión da neto 0. Un pago anulado en otra sesión descuenta en la de la anulación. Así una sesión cerrada nunca cambia.

Para el efectivo (medios con `kind = 'cash'`), el esperado suma los movimientos activos:
fondo + cobrado − anulado − gastos − retiros + ingresos.

El resumen devuelve también el desglose del efectivo, los movimientos y la cantidad de ventas `open`/`billing` (que bloquean el cierre). En una sesión cerrada devuelve los conteos guardados.

`amount` es el monto aplicado a la venta. El vuelto no entra a la caja, así que no se resta aparte.

### Cerrar

- Requiere `POS`. Bloquea la fila de la sesión. Si no está `open`, responde 409.
- Si hay ventas `open` o `billing`, responde 409 con el mensaje "Hay n ventas abiertas. Cobralas o anulalas antes de cerrar" y `open_sales: n`.
- `counts`: una entrada por medio de pago, con `counted` ≥ 0. Debe incluir el efectivo. Para los medios del resumen que no vengan, se toma contado = esperado. Un medio que no existe da 400.
- Si alguna diferencia es distinta de 0, la nota (`note`) es obligatoria (400).
- Guarda los conteos (esperado recalculado en el servidor, contado y diferencia), `closed_*`, `closing_note`, el estado `closed` y el evento `closed`, con las diferencias en el payload.

### Reabrir

- Requiere admin y pide motivo. La caja no puede tener otra sesión `open` (409).
- Borra los conteos, limpia `closed_*` y `closing_note`, pone el estado `open` y registra el evento `reopened`.

### Pagos sin caja

Pagos con `cash_session_id` nulo, filtrados por fecha de creación (día de Argentina). Los anteriores a la migración también aparecen.

## API

Blueprint `pos_cash`, con prefijo `/api/v1/pos/cash`. Rutas delgadas, lógica en `services/pos/cash_service.py`, errores con `PosError` (400, 403, 404, 409) en castellano.

| Método y ruta | Permiso | Qué hace |
|---|---|---|
| `GET /registers` | `POS` | Cajas activas, cada una con `open_session` (id, `opened_at`, `opened_by`) o nulo |
| `POST /sessions` `{register_id, opening_float}` | `POS` | Abrir; devuelve el resumen |
| `GET /sessions/current?register_id=` | `POS` | Resumen de la sesión abierta de esa caja, o 404 |
| `GET /sessions/<id>` | `POS` | Resumen, movimientos, conteos y eventos |
| `POST /sessions/<id>/movements` `{kind, amount, reason, category_id?, supplier_id?}` | `POS` | Movimiento; devuelve el resumen |
| `POST /movements/<id>/cancel` `{reason}` | admin | Anular movimiento; devuelve el resumen |
| `POST /sessions/<id>/close` `{counts: [{payment_method_id, counted}], note}` | `POS` | Cerrar; devuelve el resumen con los conteos |
| `POST /sessions/<id>/reopen` `{reason}` | admin | Reabrir; devuelve el resumen |
| `GET /sessions?from=&to=&register_id=&page=` | `POS` | Historial por fecha de apertura (día de Argentina), 50 por página, de la más nueva a la más vieja. Cada fila: caja, apertura, cierre, total cobrado neto, diferencia en efectivo, estado |
| `GET /unassigned-payments?from=&to=` | `POS` | Pagos sin caja, con venta (número y mesa), medio, monto, usuario y fecha |
| `GET /expense-categories` | `POS` | Categorías de gasto activas, para el modal de gasto |

`GET /pos/changes` (1b) suma `cash_version`, el id máximo de `cash_events` (0 si no hay). La UI invalida las consultas de caja cuando cambia.

`GET /suppliers` ya existe con el permiso `Suppliers`; el modal de gasto usa un campo de proveedor opcional que solo aparece si el usuario tiene ese permiso.

## Interfaz

### `/pos` (caja web)

- **Barra superior** (`PosTopBar`):
  - indicador "Caja abierta · desde HH:MM" en verde, o "Caja cerrada" en gris; lo leen todos los usuarios con `POS` o `Camarero`;
  - solapa "Caja" a `/pos/caja`, solo con `POS`.
- **`/pos/caja` (`CashPage`)**, con caja cerrada:
  - botón "Abrir caja" que abre `OpenSessionModal`: fondo inicial con `NumericKeypad` (1b), confirmar;
  - debajo, el resumen de la última sesión cerrada (`GET /sessions?…&page=1`, primer elemento).
- **Con caja abierta:**
  - encabezado: caja, quién abrió y cuándo, fondo;
  - tarjetas por medio de pago con el neto cobrado; la de efectivo muestra el desglose (fondo + ventas − anulaciones − gastos − retiros + ingresos = esperado);
  - lista de movimientos (hora, tipo, monto, motivo, usuario); los anulados se ven tachados; admin tiene "Anular" en los activos;
  - botones:
    - "Gasto" (`MovementModal` con categoría y proveedor opcional);
    - "Retiro" e "Ingreso" (`MovementModal` con monto y motivo);
    - "Cerrar caja".
- **Cerrar caja (`CloseSessionModal`):**
  - **con ventas abiertas:** mensaje de bloqueo con la cantidad y un enlace "Ir al plano";
  - **sin ventas abiertas:**
    - tabla por medio de pago con el esperado, un campo "Contado" (vacío al empezar; el `NumericKeypad` carga el campo enfocado) y la diferencia en vivo (roja si falta, ámbar si sobra, gris si es 0);
    - "Confirmar cierre" se habilita cuando el efectivo tiene valor y, si hay alguna diferencia, la nota está completa;
    - los medios sin valor cargado se envían con contado = esperado;
  - al confirmar, el modal muestra el resumen del cierre y la página vuelve a "caja cerrada".
- **Cobro:** `PaymentModal` (1b, que también usa el 1c) muestra arriba un aviso ámbar "No hay caja abierta: este pago queda sin caja" cuando no hay caja abierta. No bloquea.
- **Errores y toasts:** los del 1b.

### Galia (Finanzas → "Cajas", `/cash-sessions`)

- Entrada en el Sidebar, en Finanzas, con módulo `POS`.
- **`CashSessions`:**
  - filtros desde/hasta (por defecto, los últimos 7 días);
  - tabla: caja, apertura (usuario y hora), cierre (usuario y hora), cobrado neto, diferencia de efectivo (con color), estado;
  - paginación;
  - solapa "Pagos sin caja" con su tabla.
- **`CashSessionDetail` (`/cash-sessions/:id`):**
  - resumen, conteos con diferencias, movimientos y línea de tiempo de eventos;
  - admin tiene "Reabrir", con motivo.

### Celular (1c)

Sin pantalla de caja. El aviso de "sin caja" aparece en el cobro porque usa el mismo `PaymentModal`.

## Sincronización

- `posKeys` suma `cash` (`['pos','cash']`) como prefijo de las consultas de caja: registros, sesión actual y detalle.
- `usePosChanges` guarda el último `cash_version` y, si cambia, invalida `['pos','cash']`. El indicador de la barra y el aviso del cobro se actualizan solos en unos 3 s.
- Las mutations de caja escriben en caché el resumen devuelto, sin actualizaciones optimistas.

## Estructura del código

### Backend

- `backend/app/models/pos/cash.py`: `CashRegister`, `CashSession`, `CashMovement`, `CashSessionCount`, `CashEvent`, exportados en `app.models.pos`.
- `backend/app/models/pos/payments.py`: las dos columnas nuevas en `PosPayment`.
- `backend/app/services/pos/cash_service.py`: `current_session_id`, `open_session`, `add_movement`, `cancel_movement`, `session_summary`, `close_session`, `reopen_session`, `list_sessions`, `unassigned_payments`.
- `backend/app/services/pos/cash_serializers.py`: serialización de sesión, movimiento, conteo y evento.
- `backend/app/services/pos/payment_service.py`: asignación de sesión al cobrar y al anular.
- `backend/app/routes/pos_cash.py`: blueprint, registrado en `app/__init__.py`.
- `backend/app/routes/pos_floor.py`: `cash_version` en `/changes`.
- `backend/migrations/versions/b2a0_add_cash_registers.py`.

### Frontend

- `frontend/src/pos/api/posApi.js`: `posCashApi` con un método por endpoint.
- `frontend/src/pos/hooks/keys.js`, `usePosChanges.js`: clave `cash` e invalidación por `cash_version`.
- `frontend/src/pos/hooks/useCash.js`: `useRegisters`, `useCurrentSession`, `useCashSession`, `useCashMutation`.
- `frontend/src/pos/cash/`: `CashPage.jsx`, `CashSummaryCards.jsx`, `MovementList.jsx`, `OpenSessionModal.jsx`, `MovementModal.jsx`, `CloseSessionModal.jsx`, `CashStatusBadge.jsx`.
- `frontend/src/pos/utils/cashMath.js`: diferencias, totales y validación del cierre, más su test.
- `frontend/src/pos/layout/PosTopBar.jsx`: indicador y solapa.
- `frontend/src/pos/modals/PaymentModal.jsx`: aviso de "sin caja".
- `frontend/src/pages/CashSessions.jsx`, `frontend/src/pages/CashSessionDetail.jsx`, más rutas en `App.jsx` y la entrada en `Sidebar.jsx`.

## Pruebas y verificación

### Backend (pytest, TDD)

- **Abrir:**
  - con el fondo;
  - una segunda apertura de la misma caja da 409;
  - sin `POS` da 403;
  - un fondo negativo o inválido da 400;
  - una caja inactiva da 400.
- **Movimientos:**
  - de cada tipo;
  - el gasto crea un `Expense` con `de_caja`, `caja`, categoría, proveedor, fecha, `medio_pago` y `estado_pago`;
  - motivo obligatorio;
  - categoría inválida da 400;
  - sin sesión o con la sesión cerrada da 409.
- **Anular un movimiento:**
  - solo admin (403 si no lo es);
  - en un gasto marca `cancelado`;
  - en una sesión cerrada da 409;
  - `opening_float` no se anula.
- **Pagos:**
  - toman la sesión abierta;
  - sin sesión quedan en nulo;
  - con dos sesiones abiertas (dos cajas) quedan en nulo;
  - al anular se registra `cancel_cash_session_id`.
- **Resumen:**
  - esperado por medio de pago;
  - desglose del efectivo con vuelto (cuenta el monto aplicado);
  - anulación en la misma sesión (neto 0) y en otra sesión (descuenta en la nueva; la cerrada no cambia);
  - movimientos anulados no cuentan.
- **Cerrar:**
  - con ventas `open` o `billing` da 409 con `open_sales`;
  - guarda conteos y diferencias, con el esperado calculado en el servidor;
  - nota obligatoria con diferencia;
  - los medios omitidos toman contado = esperado;
  - una sesión ya cerrada da 409.
- **Reabrir:**
  - solo admin;
  - borra los conteos;
  - con otra sesión abierta en la caja da 409.
- **Historial:** filtros por fecha y caja, paginación, totales por fila.
- **Pagos sin caja:** filtro por fecha.
- **`/changes`:** incluye `cash_version`.
- **Concurrencia** en PostgreSQL (`test_pos_cash_concurrency_pg.py`, que corre solo con `POS_PG_TEST_URL`): dos aperturas simultáneas de la misma caja y dos cierres simultáneos de la misma sesión. En los dos casos una gana y la otra da 409.
- **Generales:**
  - test de la cadena de migraciones con `b2a0` después de `b1b1`;
  - test de cobertura de rutas;
  - sin fallas nuevas respecto de la línea base.

### Frontend

- **Vitest** para `cashMath`:
  - diferencia por medio de pago;
  - desglose del efectivo;
  - validación del cierre: efectivo obligatorio, nota obligatoria con diferencia, contado vacío = esperado;
  - texto del indicador.
- `npm test` y `npm run build` OK.

### Verificación manual

En el preview sobre SQLite, como en el 1b y el 1c:

1. Abrir caja con fondo; el indicador de la barra cambia.
2. Cobrar en efectivo con vuelto y con débito; las tarjetas se actualizan.
3. Gasto (aparece en Gastos con `de_caja`), retiro e ingreso; admin anula uno.
4. Intentar cerrar con una mesa abierta: bloqueado.
5. Cobrar la mesa; cerrar con una diferencia en efectivo (nota obligatoria).
6. Ver la sesión en Finanzas → Cajas y reabrirla como admin.
7. Cobrar sin caja: aviso en el cobro y fila en "Pagos sin caja".
8. Con una sesión nueva abierta, anular un pago de la sesión anterior: descuenta en la nueva y la anterior no cambia.
9. Otra pestaña con `/pos` ve el cambio de estado de la caja en unos 3 s.

## Despliegue

La migración crea las tablas, carga "Caja principal" y agrega dos columnas nulas a `pos_payments`. Se verifica sobre SQLite con el test de la cadena. Correrla en PostgreSQL (upgrade, downgrade, upgrade) queda pendiente, junto con `b1a4` y `b1b1`, antes de deployar a Render.

## Fuera de alcance

- Impresión del cierre o "ticket Z" (sub-proyecto 3).
- Asignar caja por dispositivo y administrar varias cajas desde la UI.
- Cierres de lote de MercadoPago (sub-proyecto 5).
- Reportes de caja más allá del historial.
- Facturación (sub-proyecto 4).
