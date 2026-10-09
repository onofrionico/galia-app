# POS: motor de venta (sub-proyecto 1a) — Diseño

**Fecha:** 2026-10-09
**Rama:** `feature/pos-sales` (desde `feature/pos-base`, PR #7)
**Antecede:** `docs/superpowers/specs/2026-10-07-pos-base-design.md` (permisos por módulo, catálogo de productos, `stock_service`)

## Contexto

Galia reemplaza a Fudo como POS (opción A). El sub-proyecto 1 ("núcleo de venta") se divide en tres ciclos:

| Ciclo | Entrega |
|---|---|
| **1a. Motor de venta** (este documento) | Modelo, reglas y API: salones y mesas, ventas de salón y mostrador, tandas, modificadores, notas, descuentos y plantillas, cobros con varios medios, mover de mesa, dividir cuenta, stock al confirmar, anulaciones con permiso y auditoría |
| 1b. POS de caja (web) | Plano de mesas, panel de venta, catálogo, cobro, mostrador y configuración |
| 1c. Camarero (celular) | Vista móvil para abrir mesas, cargar pedidos y cobrar con permiso |

Fuera del sub-proyecto 1: caja y arqueo (2), comanda, impresión y estado de cocina (3), facturación ARCA (4), MercadoPago integrado (5), corte con Fudo (6).

## Decisiones de producto

- **Transición:** corte directo. El día del corte se deja Fudo; el historial importado queda en `sales`. Hasta entonces el POS se usa en pruebas.
- **Tipos de venta:** salón (con mesa) y mostrador / para llevar. Sin delivery.
- **Dispositivos:** caja (computadora o tablet) más mozos con celular. El mozo puede cobrar solo si tiene el permiso `Cobrar`.
- **Ítems:** variante de producto, modificadores configurables (con recargo y descuento de insumo) y una nota libre.
- **Descuentos:** sobre la venta y sobre ítems, libres o por plantilla. Las plantillas pueden estar restringidas.
- **Cobros:** catálogo de medios de pago, varios pagos por venta, vuelto en efectivo. Sin propinas.
- **Stock:** se descuenta al confirmar cada tanda, sin bloquear (puede quedar negativo). Se devuelve al anular un ítem confirmado.
- **Anulaciones:** los ítems pendientes los borra cualquiera que cargue ventas. Anular ítems confirmados, pagos o ventas requiere el permiso `Anular` y un motivo. Toda cancelación, incluso de pendientes, queda auditada.
- **Operaciones de mesa:** mover una venta a otra mesa y dividir la cuenta por ítems. No se unen mesas.

## Enfoque

Modelo POS propio (tablas `pos_*`) para las ventas en curso. Al cerrar, cada venta se **proyecta** como una fila en `sales`, la tabla que leen los reportes actuales (ventas, GAO, Día/Hora, dashboard). Así los reportes no cambian, el historial de Fudo queda intacto y los ítems quedan disponibles para reportes nuevos.

Se descartaron:
- **Extender `sales`:** mezclaría `estado` (Fudo) con el estado del POS y obligaría a filtrar ventas abiertas en todos los reportes.
- **Adaptar los reportes para leer dos fuentes:** frágil y con mucho código tocado.

## Modelo de datos

Montos en `Numeric(12,2)` (o `(10,2)` para precios), calculados con `Decimal`. Cantidades de ítem en `Numeric(10,3)` para permitir dividir renglones. Timestamps en UTC.

### Configuración

- **`salons`**: `id`, `name` (único), `position`, `is_active`, timestamps.
- **`pos_tables`**: `id`, `salon_id` → `salons`, `number` (único por salón), `name`, `capacity`, `pos_x`, `pos_y`, `width`, `height`, `is_active`, timestamps. La ocupación **no se guarda**: una mesa está ocupada si tiene ventas abiertas o cobrando.
- **`modifier_groups`**: `id`, `name`, `min_select` (≥ 0), `max_select` (≥ 1 y ≥ `min_select`), `is_active`, timestamps.
- **`modifier_options`**: `id`, `group_id` → `modifier_groups`, `name`, `price_delta` (≥ 0), `supply_id` → `supplies` (nullable), `supply_quantity` (nullable; requerido si hay `supply_id`, > 0), `position`, `is_active`.
- **`product_modifier_groups`**: `product_id` → `products`, `group_id` → `modifier_groups`, `position`. PK compuesta.
- **`payment_methods`**: `id`, `name` (único), `kind` ∈ {`cash`, `card`, `transfer`, `other`}, `position`, `is_active`.
- **`discount_templates`**: `id`, `name`, `kind` ∈ {`percent`, `amount`}, `value` (> 0; ≤ 100 si es porcentaje), `scope` ∈ {`sale`, `item`}, `restricted` (bool), `is_active`.

### Venta

- **`pos_sales`**:
  - `id`, `number` (correlativo por día de apertura en hora Argentina, desde 1), `sale_type` ∈ {`salon`, `counter`}.
  - `table_id` → `pos_tables` (requerido si `salon`, nulo si `counter`), `people` (requerido ≥ 1 si `salon`), `customer_name`, `comment`, `waiter_id` → `users`.
  - `status` ∈ {`open`, `billing`, `closed`, `cancelled`}, con `opened_at`/`opened_by`, `billing_at`, `closed_at`/`closed_by`, `cancelled_at`/`cancelled_by`/`cancel_reason`.
  - `subtotal`, `discount_total`, `total`, `paid_total`. Se recalculan en el servidor ante cada cambio.
  - `split_from_id` → `pos_sales` (nullable), `sale_id` → `sales` (nullable; la fila proyectada).
  - Índices: `status`, `table_id`, `opened_at`.
- **`pos_sale_items`**:
  - `id`, `sale_id`, `product_variant_id`, con copia de `product_name`, `variant_name` y `unit_price`.
  - `quantity` (> 0), `modifiers_total` (suma de recargos por unidad), `note`, `line_total` = `quantity × (unit_price + modifiers_total)`.
  - `status` ∈ {`pending`, `confirmed`, `cancelled`}, `batch` (número de tanda al confirmar), `created_by`/`created_at`, `confirmed_by`/`confirmed_at`, `cancelled_by`/`cancelled_at`/`cancel_reason`.
- **`pos_sale_item_modifiers`**: `id`, `item_id`, `option_id`, copia de `group_name`, `option_name`, `price_delta`, `supply_id` y `supply_quantity`.
- **`pos_discounts`**: `id`, `sale_id`, `item_id` (nullable = descuento de venta), `template_id` (nullable), `kind`, `value`, `amount` (calculado), `reason`, `created_by`/`created_at`, `cancelled_by`/`cancelled_at`.
- **`pos_payments`**: `id`, `sale_id`, `payment_method_id`, copia de `method_name`, `amount` (aplicado a la venta), `tendered` y `change` (solo efectivo), `client_request_id` (único, nullable), `created_by`/`created_at`, `cancelled_by`/`cancelled_at`/`cancel_reason`.
- **`pos_sale_events`**: `id`, `sale_id`, `item_id` (nullable), `user_id`, `event_type`, `payload` (JSON), `created_at`. Índice por `sale_id`.

### Cambios a tablas existentes

- **`sales.source`**: `String(20)`, NOT NULL, default `'fudo'`. Valores `'fudo'` | `'galia'`.

## Reglas de negocio

### Ciclo de una venta

1. **Abrir.**
   - **Salón:** mesa activa sin ventas `open`/`billing`; si ya tiene una, 409 con el id de la venta existente. `people` es requerido; `waiter_id` = usuario que abre, salvo que la caja indique otro.
   - **Mostrador:** sin mesa; `customer_name` opcional.
2. **Agregar ítem** (solo en `open`). Variante activa de producto activo. Los modificadores tienen que pertenecer a grupos asignados al producto y respetar `min_select`/`max_select` de cada grupo (los grupos con `min_select` > 0 son obligatorios). El ítem entra `pending`.
3. **Borrar ítem pendiente.** Cualquiera que cargue ventas; registra el evento `item_deleted` con el detalle del ítem.
4. **Confirmar tanda.** Todos los `pending` pasan a `confirmed` con `batch` = máximo + 1 y se descuenta stock. Sin pendientes devuelve 409.
5. **Pedir cuenta.** `open` → `billing`, solo si no hay pendientes y hay al menos un ítem confirmado. **Reabrir:** `billing` → `open`.
6. **Cobrar.**
   - Se acepta en `billing`. En mostrador también en `open`: si hay pendientes, primero se confirman en la misma transacción.
   - `amount` > 0 y ≤ saldo (`total − paid_total`).
   - En efectivo se puede enviar `tendered` ≥ `amount`; `change` = `tendered − amount`.
   - Si `paid_total` alcanza el `total`, la venta se **cierra** en la misma transacción.
   - Con `client_request_id` repetido devuelve el resultado del pago original sin crear otro.
7. **Cerrar** (automático al completar el pago). Pasa a `closed`, registra `closed_by` y genera la proyección. Una venta con total 0 (todo descontado) se cierra con la acción explícita `POST /sales/<id>/close`, permitida si el saldo es 0.

### Anulaciones (permiso `Anular`, motivo obligatorio)

- **Ítem confirmado** en una venta `open`/`billing`: pasa a `cancelled`, devuelve stock, anula los descuentos de ese ítem y recalcula. Si el nuevo total queda por debajo de `paid_total`, devuelve 409 (primero hay que anular un pago).
- **Pago:** en una venta `billing`/`closed`. Si estaba `closed`, vuelve a `billing` y se retira la proyección.
- **Venta:** solo sin pagos activos. Pasa a `cancelled`, anula los ítems y descuentos activos y devuelve el stock de los confirmados.

### Descuentos

- Solo en ventas `open`/`billing`. Los descuentos de ítem solo se aplican a ítems **confirmados** (un pendiente se puede borrar sin dejar descuentos huérfanos).
- **Plantilla no restringida:** permitida para quien carga ventas (`POS` o `Camarero`).
- **Plantilla restringida o descuento libre:** requiere `Descuentos`. El descuento libre exige motivo.
- **Cálculo:**
  - **Porcentaje de ítem:** sobre su `line_total`.
  - **Porcentaje de venta:** sobre el subtotal menos los descuentos de ítems.
  - **Monto:** su valor, con tope en la base.
  - Redondeo a 2 decimales con `ROUND_HALF_UP`.
- **Topes:** un ítem o una venta nunca quedan negativos (el excedente se recorta). Si el nuevo total queda por debajo de `paid_total`, devuelve 409.
- Puede haber varios descuentos activos por venta y por ítem.

### Totales (`pricing.py`, funciones puras)

- `subtotal` = Σ `line_total` de los ítems no anulados (pendientes incluidos, para mostrar el total en curso).
- `discount_total` = Σ `amount` de los descuentos activos.
- `total` = `subtotal` − `discount_total`.
- `paid_total` = Σ `amount` de los pagos activos.

### Mover de mesa

Solo ventas de salón `open`/`billing`, hacia una mesa activa sin ventas abiertas. Registra el evento con origen y destino.

### Dividir la cuenta

- **Entrada:** `[{item_id, quantity}]` de ítems **confirmados** de una venta `open`/`billing` sin pagos activos.
- **Resultado:** se crea una venta nueva (misma mesa, mismo mozo, `people` = 1, `split_from_id`, en `billing`) y se pasan los ítems.
- **Partir un renglón:** si se pide menos que la cantidad del ítem, el ítem original reduce su cantidad y se crea uno nuevo en la venta destino con la cantidad pedida y una copia de sus modificadores.
- **Descuentos:** los de los ítems movidos van con ellos. Si se parte un renglón con descuento, el descuento se reparte proporcionalmente.
- **Venta de origen:** sus descuentos de venta quedan en el origen y se recalculan sobre la nueva base.
- **Venta vacía:** si la de origen queda sin ítems activos, se cancela automáticamente (con motivo "Dividida").
- **Stock:** no se mueve stock, porque ya se descontó al confirmar.

### Stock

- **Al confirmar:** se descuenta, por cada ítem, la variante (producto sin receta con `track_stock`) o la receta × cantidad, más `supply_quantity × quantity` de cada modificador con insumo.
- **Al anular un ítem confirmado:** se devuelve lo mismo. Los insumos de los modificadores salen de las copias guardadas en el ítem; la receta del producto es la vigente al momento de anular (no se copia la receta en cada venta).
- **Sin bloqueo:** `stock_service` gana el modo `allow_negative=True` (lo usa el POS); el modo actual que valida sigue siendo el default.
- **Concurrencia:** las filas de variantes e insumos se bloquean con `with_for_update()`, ordenadas por id.

### Proyección a `sales`

- **Al cerrar** se crea la fila:
  - `source='galia'`, `external_id=NULL`, `creacion` = `opened_at`, `cerrada` = `closed_at` (ambos en UTC, igual que el sync de Fudo), `fecha` = `closed_at.date()` (mismo criterio que `fudo_sync`, para que los reportes traten igual ambas fuentes), `estado='Cerrada'`.
  - `cliente` = `customer_name`, `mesa` = nombre o número de la mesa, `sala` = nombre del salón, `personas`, `camarero` = nombre del empleado del mozo (o su email).
  - `medio_pago` = el nombre del único medio usado, o `'Mixto'`.
  - `total`, `fiscal=False`, `tipo_venta` = `'Local'` (salón) o `'Mostrador'`, `comentario`, `origen='Galia POS'`, `id_origen` = `pos_sales.id`.
  - Se guarda el id de esa fila en `pos_sales.sale_id`.
- **Al reabrir** (anular un pago de una venta cerrada) o anular la venta: se borra la fila proyectada y `sale_id` = NULL.

### Auditoría

Toda acción de escritura registra un `pos_sale_events` en la misma transacción:

| Grupo | Eventos |
|---|---|
| Venta | `opened`, `cancelled`, `closed` |
| Ítems | `item_added`, `item_deleted`, `item_cancelled` |
| Tandas y cuenta | `batch_confirmed`, `bill_requested`, `reopened` |
| Descuentos | `discount_added`, `discount_cancelled` |
| Pagos | `payment_added`, `payment_cancelled` |
| Mesa | `moved`, `split_out`, `split_in` |

El `payload` lleva lo necesario para reconstruir qué pasó (ítem, cantidades, montos, motivo).

## Permisos

Módulos nuevos en el catálogo, otorgados a `admin` por el seed:

| Módulo | Habilita |
|---|---|
| `POS` | Caja: plano, todas las ventas, mostrador, cobrar, configuración de salones y mesas |
| `Camarero` | Abrir ventas de salón, cargar y confirmar ítems, pedir cuenta, mover, dividir, aplicar plantillas no restringidas |
| `Cobrar` | Registrar pagos (para quien no tiene `POS`) |
| `Anular` | Anular ítems confirmados, pagos y ventas |
| `Descuentos` | Descuentos libres y plantillas restringidas |

`module_required` acepta varios módulos (`module_required('POS', 'Camarero')` = cualquiera de los dos) y marca `_access_control = 'module:POS|Camarero'`. Los permisos que dependen del contenido (si la plantilla es restringida) se validan en el servicio.

La configuración de modificadores usa el módulo `Products`. La de salones y mesas usa `POS`. Los medios de pago y las plantillas de descuento son solo para admin.

## API (`/api/v1/pos`)

| Método y ruta | Permiso | Descripción |
|---|---|---|
| `GET /floor?salon_id=` | POS o Camarero | Mesas del salón con su venta activa (id, número, estado, total, mozo, personas, apertura) |
| `GET /sales?status=&type=` | POS o Camarero | Ventas (por defecto `open` y `billing`) |
| `POST /sales` | POS o Camarero (mostrador: POS) | Abrir |
| `GET /sales/<id>` | POS o Camarero | Venta completa con ítems, modificadores, descuentos y pagos |
| `POST /sales/<id>/items` | POS o Camarero | Agregar ítem `{product_variant_id, quantity, modifier_option_ids, note}` |
| `DELETE /sales/<id>/items/<item_id>` | POS o Camarero | Borrar ítem pendiente |
| `POST /sales/<id>/confirm` | POS o Camarero | Confirmar tanda |
| `POST /sales/<id>/items/<item_id>/cancel` | Anular | `{reason}` |
| `POST /sales/<id>/request-bill`, `/reopen` | POS o Camarero | Pedir cuenta / reabrir |
| `POST /sales/<id>/discounts` | POS o Camarero (+ Descuentos según el caso) | `{item_id?, template_id?, kind?, value?, reason?}` |
| `POST /discounts/<id>/cancel` | igual que para crearlo | Anula el descuento |
| `POST /sales/<id>/payments` | POS o Cobrar | `{payment_method_id, amount, tendered?, client_request_id?}` |
| `POST /payments/<id>/cancel` | Anular | `{reason}` |
| `POST /sales/<id>/close` | POS o Cobrar | Cerrar una venta con saldo 0 |
| `POST /sales/<id>/move` | POS o Camarero | `{table_id}` |
| `POST /sales/<id>/split` | POS o Camarero | `{items: [{item_id, quantity}]}` |
| `POST /sales/<id>/cancel` | Anular | `{reason}` |
| `GET /sales/<id>/events` | POS | Auditoría de la venta |
| CRUD `/config/salons`, `/config/tables` | POS | Salones y mesas (baja lógica) |
| CRUD `/config/modifier-groups` (con opciones), `PUT /config/products/<id>/modifier-groups` | Products | Modificadores y su asignación |
| CRUD `/config/payment-methods`, `/config/discount-templates` | admin | Medios de pago y plantillas |
| `GET /catalog` | POS o Camarero | Productos activos con variantes, precios y grupos de modificadores, en una sola respuesta |

Cada acción sobre una venta devuelve la venta completa recalculada. El frontend nunca calcula totales.

## Estructura del código

- `backend/app/models/pos/`: un archivo por agregado (`floor.py`, `modifiers.py`, `sale.py`, `payments.py`, `discounts.py`, `events.py`) y `__init__.py`.
- `backend/app/services/pos/`:
  - `sale_service.py`: abrir, ítems, tandas, cuenta, mover, dividir, anular la venta.
  - `pricing.py`: funciones puras de totales y descuentos.
  - `discount_service.py`.
  - `payment_service.py`: cobrar, anular pagos, cerrar.
  - `stock_hooks.py`: descuento y devolución.
  - `projection.py`.
  - `audit.py`.
  - `errors.py`: `PosError(status, message)`.
- `backend/app/routes/pos_sales.py`, `pos_config.py`, `pos_floor.py`. Las rutas son delgadas: validan la entrada, llaman al servicio y traducen `PosError` a JSON.
- `backend/app/services/stock_service.py`: modo `allow_negative` y funciones de devolución.

## Concurrencia y errores

- Cada acción sobre una venta abre una transacción y toma la venta con `SELECT … FOR UPDATE`. Abrir en una mesa bloquea la fila de la mesa para que no haya dos aperturas simultáneas.
- Errores de negocio: `PosError` → 409 (estado inválido o conflicto) o 400 (datos inválidos), con mensaje en castellano. 404 si no existe. Errores inesperados: 500 con mensaje genérico y `logger.exception`.
- Idempotencia de pagos con `client_request_id`. Con un id repetido de otra venta devuelve 409.
- Numeración: `UNIQUE(business_date, number)` en `pos_sales`. Si dos ventas se abren en el mismo instante y chocan, la segunda recibe 409 ("probá de nuevo"); la UI puede reintentar sola.

## Migración

Una migración `b1a4_add_pos_sales_engine` después de `b1a3_add_site_config`:
- Crea las tablas de configuración y de venta.
- Agrega `sales.source` (server default `'fudo'`).
- Inserta los módulos `POS`, `Camarero`, `Cobrar`, `Anular` y `Descuentos`, con permisos de `admin` (`employee` sin otorgar).
- Inserta los medios de pago iniciales: Efectivo (cash), Débito (card), Crédito (card), Transferencia (transfer) y MercadoPago (other).

Downgrade completo.

## Tests

- **`pricing`:** unitarios sin base de datos (modificadores, descuentos de ítem y de venta, topes, redondeo, división proporcional).
- **Servicios:**
  - ciclo de salón y de mostrador;
  - validación de modificadores (mínimos y máximos, grupo no asignado);
  - tandas y stock, incluido el negativo y modificadores con insumo;
  - borrado de pendientes auditado;
  - anulación de ítem con devolución de stock;
  - anulación de pago con reapertura y retiro de la proyección;
  - anulación de venta;
  - mover;
  - dividir, partiendo un renglón con descuento;
  - cobros parciales con vuelto y cierre automático;
  - idempotencia;
  - correlativo diario;
  - proyección en `sales`;
  - eventos de auditoría.
- **API:** permisos por módulo (Camarero sin Cobrar → 403 al cobrar; plantilla restringida sin Descuentos → 403; Anular), 409 y 400 con mensajes, y el test de cobertura de rutas.
- **Integración (PostgreSQL en Docker, marcados y salteados si no hay base):** dos aperturas simultáneas de la misma mesa y dos pagos concurrentes que excederían el saldo.
- **Línea base:** sin fallas nuevas respecto de `docs/superpowers/plans/2026-10-08-pos-base-test-baseline.txt`.

## Fuera de alcance

- UI (ciclos 1b y 1c).
- Impresión y comanda, estados de cocina por ítem.
- Caja y arqueo, facturación, propinas, delivery, unir mesas, MercadoPago integrado.
- Reportes nuevos por producto (los datos quedan disponibles).
