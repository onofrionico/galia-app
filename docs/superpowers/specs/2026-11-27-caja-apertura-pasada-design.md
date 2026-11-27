# Abrir la caja con hora anterior — Diseño corto

**Fecha:** 2026-11-27
**Rama:** `feature/caja-apertura-pasada` (desde `origin/main`, 16766eb)
**Antecede:** `docs/superpowers/specs/2026-10-13-pos-caja-arqueo-design.md` (caja y arqueo, sub-proyecto 2)

## Por qué

Hubo días en que se cobró con el POS de Galia y nadie abrió la caja. Esos pagos quedaron en "Pagos sin caja" y no hay manera de arquearlos: `open_session` siempre toma la hora actual. Lo mismo pasa cuando la cajera se olvida de abrir a la mañana y abre más tarde.

## Qué se quiere

Poder **abrir la caja con una fecha y hora anterior**. La caja queda abierta como cualquier otra: toma los pagos sin caja desde esa hora y sigue tomando las ventas que se cobren de ahí en adelante. El cierre es el de siempre, cuando corresponda.

- **Objetivo:** que esos días se puedan arquear con lo esperado correcto (cobros, anulaciones, gastos, retiros e ingresos).
- **No objetivo:** cargar cajas ya cerradas del pasado ni ventas cobradas con Fudo.
- **Anti-objetivo:** que dos cajas se pisen, que un pago cambie de una caja a otra o que se pierda el rastro de que la apertura se cargó después.

## Enfoques

- **A. Formulario único que crea la caja ya cerrada** (día, horario, fondo, movimientos y conteos). Descartado: no deja la caja abierta, que es lo que se pidió.
- **B. Caja pasada "en carga"**, en un estado aparte, que se cierra con el cierre normal. Descartado: agrega un estado nuevo y tampoco deja la caja abierta tomando ventas.
- **C. Pasar los pagos sin caja a otra caja.** Descartado: mezcla días distintos.
- **Elegido: apertura con hora anterior.** El usuario lo pidió así ("la caja debería poder abrirse en el pasado pero siempre el cierre estaría abierto"). Reusa la apertura, los movimientos y el cierre que ya existen.

## Diseño

### Datos

Migración `b9b0_cash_backdated_open` con `down_revision = 'b9a0_vouchers'`:
- `cash_sessions.registered_at` DateTime nula: el momento real en que se registró la apertura. Solo se llena cuando `opened_at` es anterior. Nula = apertura normal.

### Apertura (`cash_service.open_session`)

- Acepta `opened_at` opcional (ISO, hora de Argentina desde la UI, guardado en UTC como el resto). Si no viene, es la hora actual, como hoy.
- Reglas, con 400 en castellano:
  - no puede ser futuro (se tolera un minuto de desfase de reloj);
  - no puede ser anterior al `closed_at` de la última sesión cerrada de **cualquier** caja del mismo modo (real o de práctica): "La apertura no puede ser anterior al último cierre (dd/mm HH:MM)". Los pagos sin caja no son de ninguna caja en particular, así que una caja nueva o que nunca se cerró no puede quedarse con pagos de días de otra;
  - si es anterior, no puede haber otra caja abierta del mismo modo: "Hay otra caja abierta: cerrala antes de abrir con hora anterior".
- Si es anterior, en la misma transacción:
  - `registered_at = now()`;
  - el movimiento `opening_float` lleva `created_at = opened_at`;
  - **toma los pagos sin caja** del período: `PosPayment` con `cash_session_id` nulo y `created_at` ∈ [`opened_at`, ahora], de ventas con el mismo `is_practice` que la sesión, quedan con `cash_session_id` = la sesión;
  - **toma las anulaciones sin caja** del período: `cancel_cash_session_id` nulo, `cancelled_at` ∈ [`opened_at`, ahora], mismo filtro → `cancel_cash_session_id` = la sesión;
  - el evento `opened` guarda en el payload `backdated: true`, `opened_at`, `registered_at` y la cantidad y el total de pagos y anulaciones tomados.
- Permiso: `POS`, igual que abrir hoy.
- El resumen, el cierre y el arqueo no cambian: lo esperado sale de las mismas consultas por sesión.

### Movimientos

- `add_movement` acepta `expense_date` opcional solo para `kind = 'expense'`: un día entre el día de apertura (Argentina) y hoy, ambos incluidos (400 si no). Por defecto, hoy. Es la `fecha` del `Expense` creado.
- Retiros e ingresos no llevan fecha: cuentan igual en la sesión.

### API

- `POST /api/v1/pos/cash/sessions` suma `opened_at` opcional.
- `POST /sessions/<id>/movements` suma `expense_date` opcional.
- Los serializadores de sesión e historial suman `registered_at` y `backdated` (booleano).

### Interfaz

- **`OpenSessionModal`** (`/pos/caja`): link "Abrir con hora anterior" que muestra un campo fecha y hora (`datetime-local`, con tope en ahora). Si se completa, el modal muestra antes de confirmar: "Va a tomar los pagos sin caja desde dd/mm HH:MM".
- **`MovementModal`** (gasto): campo "Fecha del gasto", por defecto hoy, solo si la caja se abrió un día anterior a hoy.
- **Encabezado de la caja abierta, `CashSessions` y `CashSessionDetail`:** la apertura muestra la etiqueta "cargada después", con la hora real de registro en el detalle.

## Pruebas

- **Backend (pytest, TDD):**
  - abrir sin `opened_at` funciona como hoy;
  - con `opened_at` anterior toma los pagos y las anulaciones sin caja del período, y no los de antes;
  - no toma pagos de otra sesión ni de práctica;
  - futuro → 400; anterior al último cierre → 400;
  - `registered_at` y el evento con `backdated`;
  - el resumen y el cierre arquean bien con los pagos tomados;
  - gasto con `expense_date` dentro y fuera del rango;
  - test de la cadena de migraciones.
- **Frontend:** `npm test` y `npm run build`.
- **Manual** en el preview sobre SQLite: cobrar sin caja, abrir con hora anterior, ver los pagos en la caja y desaparecer de "Pagos sin caja", cargar un gasto con fecha anterior, cerrar con arqueo y ver la marca en el historial.

## Despliegue

La migración agrega una columna nula. Siguiendo la regla de migraciones: correrla en la base de test (upgrade, downgrade, upgrade) y contar `cash_sessions` antes y después.

## Queda para el builder

Nombres de componentes y textos finos de la UI, siguiendo el sistema de diseño de Galia.

## Fuera de alcance

- Ventas cobradas con Fudo que no aparecen en la pestaña "Ventas" del POS: tema aparte.
- Cerrar una caja con hora anterior.
