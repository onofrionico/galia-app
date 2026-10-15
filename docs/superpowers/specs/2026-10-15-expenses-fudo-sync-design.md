# Gastos sincronizados con Fudo — diseño

Fecha: 2026-10-15 · Rama: `feature/expenses-fudo-sync`

## Objetivo

Que los gastos importados desde Fudo lleguen **bien enriquecidos**: con su proveedor vinculado a un `Supplier` de Galia, su categoría vinculada a una `ExpenseCategory`, y medio de pago / comprobante legibles — sin tener que armar un mapeo a mano en cada sincronización. El disparo sigue siendo manual (el modal existente).

### Lo que dijo el usuario
- Objetivo principal: enriquecimiento correcto; el disparo manual está bien.
- Proveedores: matchear o crear automáticamente.
- Categorías: automático, con posibilidad de re-vincular a mano (vínculo persistente).
- Re-sync: Fudo manda, salvo correcciones manuales de categoría/proveedor hechas en Galia.
- Enfoque A (servicio + vínculos como columnas + banderas de corrección + registro de corridas).

### Supuestos (a verificar)
- La respuesta de `GET /expenses?include=provider,expenseCategory,paymentMethod,receiptType,...` trae los recursos relacionados en `included` (JSON:API) y el proveedor tiene al menos `name` y posiblemente un número fiscal (CUIT). Los nombres exactos de los atributos se confirman en la Tarea 1 capturando una respuesta real.

## Situación actual

- `POST /api/v1/fudo/sync/expenses` (`backend/app/routes/fudo_sync.py`) corre en un hilo que crea su propia app con `create_app('production')`, recibe un `category_mapping` armado en cada corrida desde `FudoSyncExpensesModal`, y deduplica por `expenses.external_id`.
- `parse_fudo_expense` lee `providerName`, `paymentMethodName`, `cashRegisterName`, `receiptTypeName` como atributos planos e ignora `included`, por lo que esos datos probablemente quedan vacíos.
- Nunca asigna `supplier_id`: el módulo de Proveedores queda desconectado de los gastos de Fudo.
- El resultado solo va al log; el usuario no ve qué pasó.

## Alcance

**Dentro:** sync de gastos (servicio, vínculos, banderas de corrección, registro de corridas), ajustes en endpoints de gastos y categorías, modal de sync, badge de origen, re-vinculación de categorías.

**Fuera:** cron automático; sincronización de ventas (no se toca); escribir gastos de Galia hacia Fudo; tablas de mapeo N→1.

## Modelo de datos

Migración `b4a0_expenses_fudo_link` (down_revision `b3a0_add_print_stations`):

| Tabla | Columna | Tipo | Notas |
|---|---|---|---|
| `suppliers` | `fudo_provider_id` | `String(50)`, nullable, unique | vínculo 1 a 1 con el proveedor de Fudo |
| `expense_categories` | `fudo_category_id` | `String(50)`, nullable, unique | vínculo 1 a 1 con la categoría de Fudo |
| `expenses` | `source` | `String(10)`, not null, default `'galia'` | backfill `'fudo'` donde `external_id IS NOT NULL` |
| `expenses` | `category_overridden` | `Boolean`, not null, default false | |
| `expenses` | `supplier_overridden` | `Boolean`, not null, default false | |

Tabla nueva `fudo_sync_runs`:

| Columna | Tipo |
|---|---|
| `id` | Integer PK |
| `kind` | `String(20)` (`'expenses'`; preparado para otros) |
| `status` | `String(10)`: `running` / `ok` / `error` |
| `started_at`, `finished_at` | DateTime (UTC) |
| `params` | JSON (`start_date`, `end_date`) |
| `stats` | JSON |
| `error` | Text |
| `triggered_by` | FK `users.id`, nullable |

`to_dict` de `Expense` suma `source`, `category_overridden`, `supplier_overridden`; el de `Supplier` y `ExpenseCategory` suma su `fudo_*_id`.

## Reglas de vinculación

### Proveedor
Para cada gasto con proveedor en Fudo (`relationships.provider.data.id`):
1. `Supplier` con ese `fudo_provider_id` → usarlo.
2. Si no, buscar entre suppliers **sin** `fudo_provider_id`: primero por CUIT (normalizado a solo dígitos, si Fudo lo trae), luego por nombre (casefold, espacios colapsados, comparación en Python). Si hay match → asignarle `fudo_provider_id`.
3. Si no hay match → crear `Supplier(name, cuit, fudo_provider_id)`. Si el CUIT de Fudo ya pertenece a un supplier vinculado a otro proveedor de Fudo, se crea sin CUIT (evita violar el unique) y se registra un aviso en stats.
4. Gasto sin proveedor → `supplier_id = None`.

`expense.proveedor` (texto libre) se llena siempre con el nombre del proveedor en Fudo.

### Categoría
1. `ExpenseCategory` con ese `fudo_category_id` → usarla.
2. Si no, buscar entre categorías sin vínculo por nombre (casefold) → vincularla.
3. Si no → crearla con `expense_type` inferido por palabras clave. La lista de palabras clave de `Expense.from_csv_row` se extrae a una función compartida `infer_expense_type(name)`. Si el nombre ya existe (unique) pero vinculado a otra categoría de Fudo, se crea como `"<nombre> (Fudo)"`.
4. Gasto sin categoría → "Sin categoría" (se crea si no existe, como hoy).

**Re-vincular a mano:** el endpoint existente `PUT /api/v1/reports/expense-categories/<id>` (`routes/reports.py`) acepta `fudo_category_id` (o `null`). Al moverlo, se quita de la categoría que lo tenía. Los gastos ya importados no cambian hasta la próxima sync (donde se recalculan los no corregidos).

### Medio de pago y comprobante
Se resuelven desde `included` y se guardan como texto en `medio_pago`, `tipo_comprobante`; `numero_comprobante` desde el atributo correspondiente. Sin tablas nuevas.

## Correcciones manuales

- `PUT /expenses/<id>`: si el gasto es `source='fudo'` y cambia `category_id` → `category_overridden=True`; si cambia `supplier_id` → `supplier_overridden=True`.
- `POST /expenses/classify`: marca `category_overridden=True` en gastos `source='fudo'`.
- En la re-sync: si la bandera está activa, ese campo no se recalcula. Todo lo demás de origen Fudo (fecha, vencimiento, importe, estado de pago, cancelado, caja, de_caja, medio de pago, comprobante, comentario, proveedor texto) se pisa con Fudo.

## Flujo de sincronización

### Endpoint
`POST /api/v1/fudo/sync/expenses?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` (admin):
- Valida fechas: ambas obligatorias, formato correcto, `start ≤ end`, rango ≤ 366 días → si no, 400.
- Si existe una corrida `kind='expenses'` en `running` iniciada hace menos de 30 min → 409 con el `run_id` existente. Una `running` más vieja se considera muerta: se marca `error` ("corrida abandonada") y no bloquea.
- Crea `FudoSyncRun(status='running')`, lanza un hilo daemon con `current_app._get_current_object()` y responde 202 `{run_id}`.
- Se eliminan `update_existing` y el body `category_mapping`.

`GET /api/v1/fudo/sync/runs/<id>` y `GET /api/v1/fudo/sync/runs?kind=expenses&limit=5` (admin) devuelven las corridas.

### Servicio `app/services/expense_sync_service.py`
`sync_expenses(client, start_date, end_date) -> dict`:
1. Baja todas las páginas (`get_all_expenses` se adapta para devolver `data` y `included` juntos).
2. Arma un índice `included[(type, id)]`.
3. Por cada gasto: resuelve proveedor y categoría (cachés en memoria por corrida), mapea los campos y hace upsert por `external_id`. Un gasto existente sin cambios cuenta como `unchanged`.
4. Commit cada 200 gastos. Un error en un gasto hace `rollback` solo de ese gasto (savepoint con `begin_nested`), se registra y sigue.
5. Devuelve stats: `fetched, created, updated, unchanged, suppliers_created, suppliers_linked, categories_created, categories_linked, warnings[≤50], errors[≤50]`.

El hilo envuelve la llamada: al terminar guarda `stats` y `status='ok'`; ante una excepción global (auth/red) guarda `status='error'` y el mensaje. Lo ya commiteado se conserva y el reintento es idempotente.

`parse_fudo_expense` sale de la ruta y pasa al servicio como función pura (payload + índice de `included` → dict de campos).

## Interfaz

- **`FudoSyncExpensesModal`:** se elimina el paso de mapeo. Queda: rango de fechas → "Sincronizar". Tras el 202, consulta `GET /fudo/sync/runs/<id>` cada 2 s hasta que termine y muestra el resumen (creados, actualizados, sin cambios, proveedores y categorías nuevos/vinculados, avisos, errores). Al abrir muestra la última corrida. Ante 409 muestra "ya hay una sincronización en curso" y se engancha a esa corrida.
- **Lista de gastos:** badge "Fudo" cuando `source='fudo'`.
- **Categorías de gasto:** en el formulario de edición, un selector "Categoría de Fudo vinculada" alimentado por `GET /fudo/categories` (que se mantiene para esto).

## Errores

| Situación | Comportamiento |
|---|---|
| Fechas inválidas | 400 |
| Corrida en curso (< 30 min) | 409 + `run_id` |
| Credenciales faltantes / auth / red con Fudo | corrida `error` con mensaje; lo commiteado se conserva |
| Gasto mal formado | va a `errors`, la corrida sigue |
| Conflicto de unique (CUIT / nombre de categoría) | se resuelve según reglas, va a `warnings` |

## Tests (pytest, sin red)

Cliente fake + fixtures JSON (basadas en la captura real anonimizada de la Tarea 1):
- Proveedor: vínculo existente, match por CUIT, match por nombre, creación, gasto sin proveedor, conflicto de CUIT.
- Categoría: vínculo existente, match por nombre, creación con tipo inferido, sin categoría, conflicto de nombre.
- Re-sync respeta `category_overridden` / `supplier_overridden` y actualiza el resto.
- Idempotencia: dos corridas seguidas, la segunda no crea nada (`unchanged`).
- Gasto cancelado en Fudo → `cancelado=True`, estado "Cancelado".
- Error en un gasto no corta la corrida.
- `PUT /expenses/<id>` y `POST /classify` marcan banderas solo en gastos de Fudo.
- Endpoint: 400 por fechas, 409 por corrida concurrente, corrida abandonada no bloquea, `GET runs/<id>`.
- Re-vincular categoría mueve el `fudo_category_id`.

## Plan de arranque

Tarea 1: con credenciales reales, capturar una página de `/expenses` con sus `include` y una de `/expense-categories`, anonimizarlas (nombres/CUIT) y guardarlas como fixtures en `backend/tests/fixtures/fudo/`. Ajustar los nombres de atributos del diseño a lo observado antes de seguir.
