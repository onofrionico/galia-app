# Pronóstico de producción por turno: plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Una pestaña "Producción" en Reportes que, para un día (por defecto mañana), muestre cuántas unidades se esperan de cada producto en total y por turno (Desayuno, Almuerzo, Merienda), con los combos abiertos en sus componentes.

**Architecture:** Tres tablas nuevas (turnos, configuración de una fila y componentes por variante) en una migración idempotente. El cálculo vive en un servicio puro (`production_forecast.py`, sin base) que recibe ventas ya leídas y devuelve el pronóstico. Un endpoint en `reports.py` lee la base y llama al servicio. En el frontend hay una pestaña nueva en Reportes con un modal de configuración y una pestaña "Componentes" en el detalle del producto.

**Tech Stack:** Flask + SQLAlchemy + Flask-Migrate (alembic), pytest sobre SQLite en memoria (`create_app('testing')`), React + Vite + Tailwind, vitest.

**Spec:** `docs/superpowers/specs/2026-11-09-reports-franjas-design.md`

## Global Constraints

- Turnos iniciales: Desayuno 08:00–12:00, Almuerzo 12:00–16:00, Merienda 16:00–20:00. Intervalo `[inicio, fin)`: 12:00 es Almuerzo, 20:00 queda fuera de turno.
- Semanas comparables por defecto: 4. Ventana de feriados por defecto: 12 meses. Las dos se configuran desde la app; nada de valores de negocio fijos en el código salvo estos valores iniciales de la migración.
- Feriado = fila de `holidays` con `type` en (`national`, `local`) o `type` nulo. `special_event` no cuenta.
- Solo ventas `Sale.estado == 'Cerrada'`. El día es `Sale.fecha`. La hora del turno es `Sale.cerrada` (o `Sale.creacion` si es nula), guardada como UTC naive y pasada a Argentina con `convert_utc_to_argentina` (`app/utils/timezone_utils.py`).
- Número limpio: sin margen ni redondeo hacia arriba. El backend redondea a 1 decimal.
- Nada se borra físicamente: los turnos y los componentes se desactivan (`is_active = False`) y guardan `updated_by` y `updated_at`.
- Permisos: el reporte y su configuración usan `@module_required('Reports')`; los componentes, `@module_required('Products')`.
- Cadena de migraciones: la nueva revisión es `b7c0_production_forecast` con `down_revision = 'b7b0_fix_fudo_item_price'` (head actual de `main`).
- Textos de la UI en español rioplatense.

**Decisión del plan sobre el spec:** los componentes se cargan por **variante** (`product_variants`), no por producto. Los `sale_items` apuntan a una variante (`product_variant_id`) y el spec pide no mezclar variantes como Unidad y Docena. En la UI se carga desde la ficha del producto del combo; si el producto tiene una sola variante, el selector de variante del combo no se muestra.

## Review Focus

1. Venta con `cerrada` nula (por ejemplo, una venta vieja del POS): debe usar `creacion` y no romper. → Task 3, `test_sale_without_cerrada_uses_creacion`.
2. Un feriado que cae domingo no entra en "los últimos 4 domingos" ni del día normal ni del caso feriado. → Task 2, `test_sunday_holiday_not_counted_as_sunday`.
3. Combo vendido en Merienda: sus medialunas suman en Merienda, no en el turno de otro ítem. → Task 2, `test_components_keep_day_part_of_combo_sale`.
4. Día sin ningún comparable con ventas (local recién abierto, primer feriado del año): respuesta vacía con `based_on: []`, y la UI muestra un mensaje en lugar de ceros. → Task 3, `test_forecast_without_comparable_days_is_empty`; Task 5, estado vacío.
5. Guardar turnos que se pisan (Desayuno 8–13 y Almuerzo 12–16) se rechaza con 400 y un mensaje claro, y no se guarda nada a medias. → Task 4, `test_overlapping_day_parts_rejected`.

---

## Mapa de archivos

| Archivo | Responsabilidad |
|---|---|
| `backend/app/models/production.py` (nuevo) | `SalesDayPart`, `ProductionSettings`, `ProductComponent` |
| `backend/migrations/versions/b7c0_production_forecast.py` (nuevo) | Crear las 3 tablas y los valores iniciales, idempotente |
| `backend/app/services/production_forecast.py` (nuevo) | Cálculo puro: turno de una hora, días comparables, apertura de combos, pronóstico y promedios por día de la semana |
| `backend/app/routes/reports.py` | `GET /production-forecast`, `GET`/`PUT /production-settings` |
| `backend/app/routes/products.py` | `GET`/`PUT /<id>/components` |
| `backend/tests/test_production_forecast.py` (nuevo) | Tests del servicio puro |
| `backend/tests/test_production_routes.py` (nuevo) | Tests de los endpoints |
| `frontend/src/services/reportsService.js`, `productsService` existente | Llamadas nuevas |
| `frontend/src/components/reports/ProductionTab.jsx` (nuevo) | Pestaña del pronóstico |
| `frontend/src/components/reports/ProductionSettingsModal.jsx` (nuevo) | ABM de turnos y semanas |
| `frontend/src/components/reports/productionUtils.js` (+ `.test.js`) | Agrupar por categoría y filtrar |
| `frontend/src/components/products/ProductComponentsTab.jsx` (nuevo) | Componentes en la ficha del producto |
| `frontend/src/pages/Reports.jsx`, `frontend/src/pages/ProductDetail.jsx` | Agregar las pestañas |

---

### Task 1: Modelos y migración

**Files:**
- Create: `backend/app/models/production.py`
- Modify: `backend/app/models/__init__.py` (importar y agregar a `__all__`)
- Create: `backend/migrations/versions/b7c0_production_forecast.py`
- Test: `backend/tests/test_production_routes.py` (el primer test)

**Interfaces:**
- Produces:
  - `SalesDayPart`, tabla `sales_day_parts`: `id`, `name String(50) not null`, `start_time Time not null`, `end_time Time not null`, `position Integer not null default 0`, `is_active Boolean not null default True`, `updated_at DateTime`, `updated_by FK users.id null`. `to_dict()` → `{'id', 'name', 'start': 'HH:MM', 'end': 'HH:MM', 'position', 'is_active'}`.
  - `ProductionSettings`, tabla `production_settings`, una sola fila con `id = 1` (constante `PRODUCTION_SETTINGS_ID = 1`): `comparable_weeks Integer not null default 4`, `holiday_window_months Integer not null default 12`, `updated_at`, `updated_by`. Classmethod `get() -> ProductionSettings` que devuelve la fila 1 y, si no existe, la crea con los valores por defecto (sin commit).
  - `ProductComponent`, tabla `product_components`: `id`, `variant_id FK product_variants.id not null index` (el combo), `component_variant_id FK product_variants.id not null`, `quantity Numeric(10,3) not null`, `is_active Boolean not null default True`, `updated_at`, `updated_by`. `UniqueConstraint('variant_id', 'component_variant_id')`.

- [ ] **Step 1: Escribir el test que falla.** En `test_production_routes.py`, `test_settings_get_creates_defaults(pos_app)`: `ProductionSettings.get()` devuelve `comparable_weeks == 4` y `holiday_window_months == 12`; llamarlo dos veces deja una sola fila.
- [ ] **Step 2: Correrlo y ver que falle.** `cd backend && venv/Scripts/python.exe -m pytest tests/test_production_routes.py -v` → ImportError.
- [ ] **Step 3: Implementar los modelos** en `production.py` y registrarlos en `models/__init__.py`.
- [ ] **Step 4: Escribir la migración** `b7c0_production_forecast` (down_revision `b7b0_fix_fudo_item_price`). Crea cada tabla solo si no existe (`sa.inspect(op.get_bind()).has_table`). Inserta los 3 turnos (position 0, 1, 2) solo si `sales_day_parts` está vacía, y la fila 1 de `production_settings` solo si falta. No toca tablas existentes. `downgrade` borra las 3 tablas.
- [ ] **Step 5: Correr el test** → PASS.
- [ ] **Step 6: Verificar la migración en el Postgres local descartable** (puerto 55433, ver memoria del proyecto): `flask db upgrade` desde una base en `b7b0`; `select name, start_time, end_time from sales_day_parts order by position` devuelve los 3 turnos; repetir `downgrade` + `upgrade` y volver a correr el `upgrade` del SQL a mano (o `flask db stamp b7b0_fix_fudo_item_price && flask db upgrade`) confirma que no duplica filas; `flask db heads` muestra un solo head.
- [ ] **Step 7: Commit** `feat(reportes): modelos de turnos, configuración y componentes`.

### Task 2: Servicio de cálculo (puro)

**Files:**
- Create: `backend/app/services/production_forecast.py`
- Test: `backend/tests/test_production_forecast.py` (sin app ni base: datos en memoria)

**Interfaces:**
- Consumes: nada de la base; `convert_utc_to_argentina` de `app/utils/timezone_utils.py`.
- Produces (todo en `production_forecast.py`):
  - `@dataclass(frozen=True) DayPart(id: int, name: str, start: time, end: time)`
  - `@dataclass(frozen=True) SoldLine(fecha: date, moment_utc: datetime, key: tuple, quantity: Decimal, variant_id: int | None)`. `key` identifica la fila del reporte: `('v', variant_id)` si está vinculada; si no, `('n', product_name, variant_name, category_name)`.
  - `day_part_for(local: time, parts: list[DayPart]) -> int | None`: id del turno con `start <= local < end`, o `None`.
  - `comparable_days(target: date, sale_days: set[date], holidays: set[date], weeks: int, holiday_months: int) -> list[date]`, en orden descendente.
  - `expand_components(lines: list[SoldLine], components: dict[int, list[tuple[int, Decimal]]]) -> list[SoldLine]`: devuelve las líneas originales más, por cada línea cuyo `variant_id` tiene componentes, una línea por componente con `key = ('v', component_variant_id)`, `quantity = línea.quantity * cantidad`, la misma `fecha` y el mismo `moment_utc`, y marcada como derivada. Agregar a `SoldLine` el campo `from_combo: bool = False`. Un solo nivel: las líneas derivadas no se vuelven a abrir.
  - `forecast(lines: list[SoldLine], days: list[date], parts: list[DayPart]) -> dict[tuple, dict]`: por `key`, `{'total': float, 'por_turno': {part_id: float}, 'fuera_de_turno': float, 'desde_combos': float}`, cada valor igual a la suma sobre `days` ÷ `len(days)`, redondeado a 1 decimal. Las líneas con `fecha` fuera de `days` se ignoran. Si `days` está vacío devuelve `{}`. Solo incluye keys con `total > 0`.
  - `weekday_averages(lines: list[SoldLine], sale_days: set[date], holidays: set[date], until: date, weeks: int, holiday_months: int) -> dict[tuple, dict]`: por `key`, `{0..6: float, 'feriado': float | None}`. El día `d` de la semana promedia los días abiertos y no feriados con ese `weekday()` dentro de las `weeks` semanas anteriores a `until`. `'feriado'` promedia los feriados abiertos de los últimos `holiday_months` meses, o queda `None` si no hay.

`comparable_days`, regla exacta (spec, "Días comparables"):
```text
abierto(d) = d in sale_days
si target in holidays:
    feriados = [h in holidays con target - holiday_months meses <= h < target y abierto(h)]
    domingos = los últimos `weeks` días d < target con d.weekday() == 6, abierto(d) y d not in holidays
    resultado = feriados ∪ domingos
si no:
    resultado = los últimos `weeks` días d = target - 7k (k = 1, 2, ...) con abierto(d) y d not in holidays,
                buscando como mucho 52 semanas hacia atrás
```
"Meses hacia atrás" = mismo día del mes, `holiday_months` meses antes (`dateutil.relativedelta`, que ya está en requirements).

- [ ] **Step 1: Escribir los tests que fallan** en `test_production_forecast.py`:
  - `test_day_part_boundaries`: con los 3 turnos iniciales, `08:00 → Desayuno`, `11:59 → Desayuno`, `12:00 → Almuerzo`, `19:59 → Merienda`, `20:00 → None`, `07:30 → None`.
  - `test_comparable_days_normal_skips_holidays_and_closed_days`: target sábado 2026-11-14, `sale_days` = sábados 7/11, 31/10, 24/10, 17/10, 10/10; `holidays = {2026-10-10}`; `weeks=4` → `[11-07, 10-31, 10-24, 10-17]`. Con 10-24 fuera de `sale_days` → `[11-07, 10-31, 10-17, 10-03]` (agregar 10-03 a `sale_days`).
  - `test_comparable_days_holiday_uses_holidays_and_sundays`: target 2026-11-23 en `holidays`; feriados anteriores con ventas 2026-10-12 y 2025-11-24 (fuera de 12 meses → no entra; fecha límite 2025-11-23 inclusive), domingos abiertos 11-22, 11-15, 11-08, 11-01 → resultado `{10-12, 11-22, 11-15, 11-08, 11-01}`.
  - `test_sunday_holiday_not_counted_as_sunday`: domingo 11-15 en `holidays`; target normal domingo 11-29 con `weeks=2` y domingos abiertos 11-22, 11-15, 11-08 → `[11-22, 11-08]`.
  - `test_utc_moment_is_converted_to_local`: una línea con `moment_utc = datetime(2026, 11, 7, 13, 30)` (10:30 en Argentina) cae en Desayuno dentro de `forecast`.
  - `test_forecast_averages_and_counts_missing_as_zero`: dos días comparables; Medialuna vendió 10 en Desayuno el día 1 y 0 el día 2 → `total == 5.0`, `por_turno[desayuno] == 5.0`.
  - `test_forecast_out_of_shift`: una venta a las 21:00 local suma en `fuera_de_turno` y en `total`.
  - `test_components_keep_day_part_of_combo_sale`: combo (variant 50) con componente (variant 7, cantidad 2) vendido 3 veces a las 17:00 local, en un solo día comparable → key `('v', 7)`: `total == 6.0`, `por_turno[merienda] == 6.0`, `desde_combos == 6.0`; el combo `('v', 50)` también aparece con `total == 3.0`.
  - `test_components_one_level_only`: el componente 7 tiene a su vez componente 8 → la línea derivada de 7 no genera líneas de 8.
  - `test_weekday_averages`: con dos lunes abiertos (4 y 6 unidades) y un feriado (10 unidades) → `[0] == 5.0`, `['feriado'] == 10.0`; un día sin días abiertos queda en `0.0`.
- [ ] **Step 2: Correr y ver que fallen.** `venv/Scripts/python.exe -m pytest tests/test_production_forecast.py -v` → ImportError.
- [ ] **Step 3: Implementar** `production_forecast.py` con las firmas de arriba.
- [ ] **Step 4: Correr** → todos PASS.
- [ ] **Step 5: Commit** `feat(reportes): cálculo del pronóstico de producción por turno`.

### Task 3: Endpoint del pronóstico

**Files:**
- Modify: `backend/app/routes/reports.py` (al final, junto a `products_report`)
- Test: `backend/tests/test_production_routes.py`

**Interfaces:**
- Consumes: Task 1 (modelos) y Task 2 (todas las funciones).
- Produces: `GET /api/v1/reports/production-forecast?date=YYYY-MM-DD` (`@token_required`, `@module_required('Reports')`). Sin `date`, usa `get_current_date_argentina() + 1 día`. Respuesta:
```json
{
  "date": "2026-11-14", "is_holiday": false, "holiday_name": null,
  "day_parts": [{"id": 1, "name": "Desayuno", "start": "08:00", "end": "12:00", "position": 0, "is_active": true}],
  "based_on": ["2026-11-07", "2026-10-31"],
  "settings": {"comparable_weeks": 4, "holiday_window_months": 12},
  "coverage": {"ventas_con_detalle": 120, "ventas_total": 122},
  "products": [{"key": "v:7", "producto": "Medialuna", "variante": "Unidad", "categoria": "Panadería",
                "total": 40.0, "por_turno": {"1": 30.0, "2": 4.0, "3": 6.0}, "fuera_de_turno": 0.0,
                "desde_combos": 18.0, "semana": {"0": 30.0, "1": 28.0, "2": 0.0, "3": 0.0, "4": 0.0, "5": 45.0, "6": 50.0, "feriado": 52.0}}]
}
```
`products` va ordenado por `categoria` y, dentro de cada una, por `total` descendente. Categoría nula → `'Sin categoría'` (constante `SIN_CATEGORIA` que ya existe en el archivo).

Lectura de la base (un helper privado `_forecast_lines(start: date, end: date) -> tuple[list[SoldLine], set[date], dict]`):
- Ventas `Cerrada` con `fecha` en `[start, end]`, con `start = target - max(weeks × 7 × 13, holiday_months meses)`. Se busca hasta 52 semanas atrás para el caso normal, así que alcanza con `start = target - 365 días`, el valor que usa el plan.
- `sale_days` = fechas distintas de esas ventas (aunque no tengan ítems).
- Una `SoldLine` por `SaleItem`: `moment_utc = Sale.cerrada or Sale.creacion`. Nombres para mostrar: del `SaleItem` más reciente de cada key; para keys que solo aparecen por componentes, de `ProductVariant` → `Product.name`, `variant.name` y la categoría del producto.
- Componentes activos: `{variant_id: [(component_variant_id, quantity)]}`.
- Feriados: `Holiday` con `type` en (`national`, `local`) o nulo.
- `coverage`: ventas de los días `based_on` con al menos un ítem / total de ventas de esos días.

- [ ] **Step 1: Escribir los tests que fallan** (helpers de `pos_helpers`, ventas armadas como `_sale` de `tests/test_reports_products.py`, con `cerrada` en UTC):
  - `test_forecast_endpoint_shape_and_values`: 2 sábados con Medialuna (10 y 20 unidades, cerradas 12:00 UTC = 09:00 local) → `?date=` del sábado siguiente: `based_on` tiene 2 fechas, Medialuna `total == 15.0`, `por_turno[str(desayuno.id)] == 15.0`.
  - `test_forecast_excludes_cancelled_sales`: una venta `Cancelada` el mismo día no suma.
  - `test_sale_without_cerrada_uses_creacion`: venta con `cerrada=None` y `creacion` a las 18:00 UTC (15:00 local) cae en Almuerzo.
  - `test_forecast_expands_components`: variante combo con `ProductComponent` (componente Medialuna × 2), vendida 1 vez → Medialuna `desde_combos == 2.0`.
  - `test_forecast_holiday_flag`: `Holiday(date=target, name='Día X', type='national')` → `is_holiday` true, `holiday_name == 'Día X'`; con `type='special_event'` → false.
  - `test_forecast_without_comparable_days_is_empty`: sin ventas → 200, `based_on == []`, `products == []`.
  - `test_forecast_requires_reports_module`: usuario solo con `POS` → 403.
- [ ] **Step 2: Correr y ver que fallen** → 404.
- [ ] **Step 3: Implementar** el endpoint y `_forecast_lines`.
- [ ] **Step 4: Correr** `tests/test_production_routes.py` y `tests/test_reports_products.py` → PASS (el segundo, para confirmar que no se rompió nada).
- [ ] **Step 5: Commit** `feat(reportes): endpoint del pronóstico de producción`.

### Task 4: Configuración de turnos y componentes (backend)

**Files:**
- Modify: `backend/app/routes/reports.py` (`/production-settings`)
- Modify: `backend/app/routes/products.py` (`/<int:product_id>/components`)
- Test: `backend/tests/test_production_routes.py`

**Interfaces:**
- Produces:
  - `GET /api/v1/reports/production-settings` → `{"comparable_weeks": 4, "holiday_window_months": 12, "day_parts": [SalesDayPart.to_dict(), ...]}` (todos, activos e inactivos, por `position`).
  - `PUT /api/v1/reports/production-settings` con el mismo formato. Los turnos con `id` se actualizan; los que no tienen `id` se crean; los que faltan en el body **no se tocan** (para desactivar se manda `is_active: false`). Valida: `1 <= comparable_weeks <= 26`, `1 <= holiday_window_months <= 36`, nombre no vacío, `start < end` y sin solapamiento entre activos. Si falla, 400 `{"error": "<mensaje en español>"}` y no guarda nada. Pone `updated_by = current_user.id` y `updated_at = datetime.utcnow()` en lo que cambia.
  - `GET /api/v1/products/<product_id>/components` (`@module_required('Products')`) → `{"variants": [{"id", "name"}], "components": [{"id", "variant_id", "component_variant_id", "component_label": "Medialuna — Unidad", "quantity": 2.0}]}` (solo activos).
  - `PUT /api/v1/products/<product_id>/components` con `{"components": [{"variant_id", "component_variant_id", "quantity"}]}`: es el estado completo deseado. Por cada par `(variant_id, component_variant_id)`: si existe, lo actualiza y lo reactiva; si no, lo crea. Los activos del producto que no vienen en el body pasan a `is_active = False`. Valida que `variant_id` sea del producto, que `component_variant_id` exista y sea distinto de `variant_id`, y que `quantity > 0`; si no, 400. Guarda `updated_by` y `updated_at`.
  - `GET /api/v1/products/variants/search?q=` no hace falta si ya existe un listado de variantes que sirva; si no existe, agregar `GET /api/v1/products/variants?q=` → `[{"id", "label": "Producto — Variante"}]`, máximo 20, solo activos (`@module_required('Products')`).

- [ ] **Step 1: Escribir los tests que fallan:**
  - `test_settings_put_updates_and_creates`: cambia Desayuno a 07:30–12:00 y `comparable_weeks = 6` → GET refleja los cambios y `updated_by` es el usuario.
  - `test_overlapping_day_parts_rejected`: Desayuno 08:00–13:00 con Almuerzo 12:00–16:00 → 400, y la base sigue con los valores anteriores.
  - `test_day_part_deactivated_not_deleted`: `is_active: false` en Merienda → sigue en GET con `is_active` false; el pronóstico ya no tiene columna Merienda y esas ventas van a `fuera_de_turno`.
  - `test_components_put_replaces_and_soft_deletes`: crear 2 componentes, después mandar solo 1 → GET devuelve 1 y la fila del otro existe con `is_active` false.
  - `test_component_cannot_be_itself`: `component_variant_id == variant_id` → 400.
  - `test_components_require_products_module`: usuario solo con `Reports` → 403.
- [ ] **Step 2: Correr y ver que fallen.**
- [ ] **Step 3: Implementar** los endpoints.
- [ ] **Step 4: Correr** `tests/test_production_routes.py` → PASS.
- [ ] **Step 5: Commit** `feat(reportes): configuración de turnos y componentes de productos`.

### Task 5: Pestaña Producción en Reportes (frontend)

**Files:**
- Modify: `frontend/src/services/reportsService.js` (`getProductionForecast(date)`, `getProductionSettings()`, `updateProductionSettings(body)`)
- Create: `frontend/src/components/reports/productionUtils.js`, `productionUtils.test.js`
- Create: `frontend/src/components/reports/ProductionTab.jsx`, `ProductionSettingsModal.jsx`
- Modify: `frontend/src/pages/Reports.jsx` (un botón más en la barra de pestañas, `activeTab === 'production'`)

**Interfaces:**
- Consumes: Task 3 y Task 4 (formatos JSON de arriba).
- Produces: `groupByCategory(products: Product[], query: string) -> Array<{categoria: string, products: Product[]}>`, que filtra por nombre sin distinguir mayúsculas ni tildes y mantiene el orden que manda el backend. `formatUnits(n: number) -> string`: entero sin decimales, y si no `'23,5'`.

Comportamiento:
- La pestaña se llama **"Producción"**. No usa el filtro de mes de arriba (se oculta o se ignora con esta pestaña activa). Carga ella misma sus datos con su propio selector de día.
- El selector de día arranca en mañana (hora Argentina), con flechas ‹ › para moverse de a un día. Debajo dice "Basado en: sáb 7/11, sáb 31/10, …" y, si es feriado, "Feriado: <nombre> — se compara con feriados y domingos".
- Tabla por categoría con buscador. Columnas: Producto (más la variante si no es "Unidad" ni vacía) · Total · una columna por turno activo · "Fuera de turno" (solo si algún producto tiene más de 0). Si `desde_combos > 0`, debajo del total, en gris: "22 sueltas + 18 en combos".
- Botón "Ver semana" por fila (o vista alternativa) con los promedios lunes a domingo y feriado del campo `semana`.
- Estado vacío: si `based_on` está vacío, "Todavía no hay días comparables con ventas para este día".
- Botón ⚙ "Turnos" que abre `ProductionSettingsModal`: lista editable de turnos (nombre, inicio, fin, activo), "Agregar turno", semanas comparables y meses de feriados. Al guardar muestra el error del backend si hay 400 y recarga el pronóstico si sale bien.

- [ ] **Step 1: Escribir el test que falla** `productionUtils.test.js`: `groupByCategory` agrupa 3 productos de 2 categorías respetando el orden; `query 'medi'` encuentra "Medialuna"; `'cafe'` encuentra "Café" (tildes). `formatUnits(40) === '40'`, `formatUnits(23.5) === '23,5'`.
- [ ] **Step 2: Correr** `cd frontend && npx vitest run src/components/reports/productionUtils.test.js` → FAIL.
- [ ] **Step 3: Implementar** `productionUtils.js`, el servicio, `ProductionTab.jsx`, `ProductionSettingsModal.jsx` y la pestaña en `Reports.jsx`, siguiendo el estilo de `ProductsTab.jsx` (Tailwind, tarjetas blancas, `lucide-react`).
- [ ] **Step 4: Correr** el test → PASS; `npm run build` sin errores.
- [ ] **Step 5: Commit** `feat(reportes): pestaña Producción con pronóstico por turno`.

### Task 6: Componentes en la ficha del producto (frontend)

**Files:**
- Create: `frontend/src/components/products/ProductComponentsTab.jsx`
- Modify: `frontend/src/pages/ProductDetail.jsx` (pestaña `'componentes'` con el texto "Componentes", entre "Modificadores" e "Historial", solo si `product` existe)
- Modify: el service de productos existente (`getComponents(productId)`, `saveComponents(productId, components)`, `searchVariants(q)`)

**Interfaces:**
- Consumes: Task 4 (`/products/<id>/components` y la búsqueda de variantes).

Comportamiento: un texto explicativo ("Si este producto trae otros productos —por ejemplo, un combo con 2 medialunas— cargalos acá y el reporte de Producción los va a contar"). Filas: [variante del combo, solo si el producto tiene más de una] · componente (buscador de variantes) · cantidad · quitar. Botones "Agregar componente" y "Guardar", que manda el estado completo y muestra el error del backend.

- [ ] **Step 1: Implementar** la pestaña, siguiendo el patrón de `ProductModifiersTab.jsx`.
- [ ] **Step 2: Correr** `npm run build` → sin errores.
- [ ] **Step 3: Commit** `feat(productos): componentes de un producto para el reporte de producción`.

### Task 7: Prueba del flujo real y PR

- [ ] **Step 1: Suite backend.** `venv/Scripts/python.exe -m pytest tests/test_production_forecast.py tests/test_production_routes.py tests/test_reports_products.py -v` → todo PASS. Correr la suite completa y comparar contra la línea base de fallas previas (unas 73 que ya fallaban en `main`): no tiene que aparecer ninguna nueva.
- [ ] **Step 2: Levantar local contra el Postgres descartable** (puerto 55433) con la migración aplicada y ventas de prueba: 4 sábados con Medialuna en Desayuno y Merienda, un Combo Clásico con su componente cargado desde la ficha y un feriado. Abrir Reportes → Producción en el navegador: elegir el sábado siguiente y verificar a mano el total de Medialuna contra una consulta SQL a la base; cambiar un turno desde ⚙ y ver que la tabla se recalcule; cargar un turno solapado y ver el error.
- [ ] **Step 3: Chequeo en producción (solo lectura)** con el conector de Render: `select count(*) from product_components` no existe todavía (bien) y ningún nombre de tabla nuevo choca: `select table_name from information_schema.tables where table_name in ('sales_day_parts','production_settings','product_components')` → 0 filas.
- [ ] **Step 4: Actualizar con main** (`git fetch && git merge origin/main`), revisar que siga habiendo un solo head de alembic y abrir el PR solo cuando el usuario lo pida. Avisar que el PR de fidelización (#43, `b8a0_loyalty`) tiene que reencadenarse sobre `b7c0` si esto se mergea antes.
