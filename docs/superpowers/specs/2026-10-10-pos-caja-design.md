# POS de caja web (sub-proyecto 1b) — Diseño

**Fecha:** 2026-10-10
**Rama:** `feature/pos-caja` (desde `feature/pos-sales`)
**Antecede:** `docs/superpowers/specs/2026-10-09-pos-sales-engine-design.md` (1a: modelo, reglas y API `/api/v1/pos`)

## Contexto

El sub-proyecto 1 ("núcleo de venta") se divide en tres ciclos: 1a motor de venta (backend), **1b POS de caja (web)** y 1c Camarero (celular). Este documento cubre el 1b: la interfaz de caja sobre la API del 1a, la configuración y los pocos agregados de backend que la UI necesita.

El frontend depende de toda la API del 1a. El spec y el plan se escriben ahora; la implementación empieza cuando el 1a esté terminado, haciendo merge de `feature/pos-sales` en `feature/pos-caja`.

## Decisiones de producto

- **Dispositivo:** táctil primero (tablet o pantalla táctil), pero cómodo con mouse y teclado: la búsqueda de productos se usa escribiendo y Enter agrega.
- **Marco:** pantalla completa propia en `/pos`, fuera del layout de Galia, con barra superior (salones, Mostrador, Configuración, usuario, salida a Galia).
- **Plano:** mesas en sus posiciones reales (`pos_x`, `pos_y`, `width`, `height` del 1a), con colores por estado: libre (gris), abierta (ámbar), cuenta pedida (rojo). En configuración se arrastran y redimensionan.
- **Panel de venta:** panel lateral sobre el plano; el plano queda visible. Los productos se agregan desde un modal con buscador.
- **Variantes:** una tarjeta por producto; la variante se elige en el paso de detalle junto con los modificadores. Si el producto tiene una sola variante activa no se pregunta.
- **Mostrador:** conviven las ventas que se cobran en el momento y las que quedan abiertas a nombre del cliente.
- **Varias cuentas por mesa:** al dividir, la mesa muestra un contador ("4 · 2 cuentas") y el panel una pestaña por cuenta.
- **Mozo:** por defecto el usuario que abre la venta. Desde la caja se puede elegir otro y reasignarlo después (solo `POS`, auditado). Desde el celular (1c) siempre es quien abre.
- **Motivos de anulación:** catálogo administrable en la base; se guarda el texto y el id del motivo elegido.
- **Actualización en vivo:** polling por cambios sobre `pos_sale_events`, pensado para la caja y 10 mozos. Sin WebSockets.

## Enfoque

Todo el POS vive en `frontend/src/pos/`. El estado del servidor (plano, ventas, catálogo) lo maneja React Query, ya presente en el proyecto. Cada acción es una mutation que escribe en la caché la venta completa devuelta por el backend. El estado de pantalla (salón, venta seleccionada) vive en la URL, así que recargar no pierde nada. Los hooks y el cliente de API quedan listos para que el 1c los reutilice.

Se descartaron:
- **Store global (Zustand):** dependencia nueva y dos fuentes de verdad para algo que la URL y el estado local resuelven.
- **Página única con `useState`, como las páginas actuales:** con polling, mutations y modales anidados se vuelve difícil de mantener.

## Rutas y permisos de la UI

### POS (fuera del `Layout` de Galia, con `PosLayout`)

| Ruta | Permiso | Contenido |
|---|---|---|
| `/pos` | `POS` o `Camarero` | Redirige al primer salón activo (por `position`) |
| `/pos/salon/:salonId?sale=<id>` | `POS` o `Camarero` | Plano y panel lateral; `sale` es la venta seleccionada |
| `/pos/mostrador?sale=<id>` | `POS` | Tablero de ventas de mostrador y el mismo panel |
| `/pos/config` | `POS` | Salones y editor del plano |

Sin salones activos, `/pos` muestra un estado vacío con un enlace a `/pos/config` (o un aviso, si el usuario no tiene `POS`).

### Galia (dentro del `Layout`)

| Ruta / lugar | Permiso | Contenido |
|---|---|---|
| `/products/modifiers` | `Products` | Grupos de modificadores con sus opciones (nombre, recargo, insumo y cantidad, orden, activo) |
| Sección "Modificadores" en `ProductDetail` | `Products` | Asignar grupos al producto y ordenarlos (`PUT /config/products/<id>/modifier-groups`) |
| `/admin/pos-settings` | admin | Solapas: medios de pago, plantillas de descuento, motivos de anulación |
| Sidebar: "Abrir POS" | `POS` o `Camarero` | Enlace a `/pos` |

Los módulos `POS`, `Camarero`, `Cobrar`, `Anular` y `Descuentos` ya aparecen en la pantalla de Permisos porque vienen del catálogo (1a).

### Qué ve cada permiso dentro del POS

- **`POS`:** todo: salones, Mostrador, Configuración, elegir y reasignar mozo, Historial, cobrar.
- **`Camarero` sin `POS`:** plano y sus operaciones de salón (abrir, cargar, confirmar, pedir cuenta, mover, dividir, plantillas no restringidas). No ve Mostrador, Configuración, Historial ni el selector de mozo.
- **`Cobrar`:** muestra "Cobrar" a quien no tiene `POS`.
- **`Anular`:** muestra "Anular" en ítems confirmados, pagos y venta.
- **`Descuentos`:** muestra plantillas restringidas y descuento libre.

Las acciones sin permiso no se muestran. El backend valida igual; un 403 inesperado muestra "No tenés permiso para…".

## Pantallas

### Barra superior (`PosTopBar`)

Solapas por salón activo, "Mostrador" (solo `POS`), "Configuración" (solo `POS`), nombre del usuario y "Salir a Galia" (vuelve a `/dashboard`).

### Plano (`FloorPlan`, `TableTile`)

- Lienzo con las mesas en coordenadas del 1a, escalado para entrar en el ancho disponible (las coordenadas se guardan en una grilla lógica fija y se escalan al dibujar).
- Cada mesa muestra número o nombre y, si está ocupada, total, mozo y tiempo abierta. Con más de una venta, el contador de cuentas.
- Color por estado: libre; abierta (alguna venta `open`); cuenta pedida (todas sus ventas en `billing`).
- **Modo "elegir mesa destino"** (para mover): se resaltan las mesas libres, las demás se atenúan; tocar una libre confirma, Esc o "Cancelar" sale.
- Tocar una mesa libre abre `OpenTableModal`; tocar una ocupada selecciona su venta (`?sale=`).

### Tablero de mostrador (`CounterPage`)

Tarjetas de ventas de mostrador `open`/`billing` (número del día, cliente, total, antigüedad) y un botón "Nueva venta" que crea la venta (nombre de cliente opcional) y abre el panel con el modal de productos.

### Panel de venta (`SalePanel`)

- **Encabezado:** mesa o "Mostrador #n", personas, mozo (con "Cambiar" para `POS`), hora de apertura, estado. Pestañas por cuenta si la mesa tiene varias ventas.
- **Pestañas del panel:** "Ticket" e "Historial" (solo `POS`; línea de tiempo de `GET /sales/<id>/events`: quién, qué, cuándo, motivo).
- **Ticket:** ítems agrupados por tanda; los pendientes aparte y resaltados. Cada ítem muestra cantidad, nombre y variante, modificadores, nota, importe y sus descuentos. Abajo: subtotal, descuentos, total, pagado y saldo.
- **Menú del ítem** (al tocarlo, dentro de `TicketItem`):
  - Pendiente: "Borrar".
  - Confirmado: "Descuento al ítem", "Anular" (con `Anular`).
  - Descuento aplicado: "Quitar descuento".
- **Pie** (`SaleFooter`): "Agregar productos", "Confirmar tanda (n)" (resaltado con pendientes), "Descuento", "Cuenta" / "Reabrir", "Cobrar", y un menú "⋯" con "Mover", "Dividir", "Anular venta" y, con saldo 0, "Cerrar".
- "Cuenta" o "Cobrar" con pendientes confirman primero la tanda y lo avisan.

### Abrir mesa (`OpenTableModal`)

Personas (por defecto 2, con botones − y +) y, solo para `POS`, el mozo (por defecto quien abre; lista de `GET /pos/waiters`). Al aceptar abre la venta, la selecciona y abre `AddProductsModal`.

### Agregar productos (`AddProductsModal`)

- **Paso 1, lista:** foco en la búsqueda; chips de categorías; grilla de tarjetas de producto con precio (el de la variante si es única, "desde $x" si hay varias). Enter agrega el primer resultado. Un toque agrega una unidad sin modificadores si el producto no los necesita y tiene una sola variante; si no, va al paso 2. El modal queda abierto y el pie muestra lo agregado ("3 agregados: 2 Latte, 1 Medialuna") y "Listo".
- **Paso 2, detalle** (también con el botón "⋯" de la tarjeta, para agregar nota o cantidad): variante, grupos de modificadores con su mínimo y máximo (los obligatorios bloquean "Agregar" hasta cumplirse), nota, cantidad y el importe del renglón. "Agregar" vuelve al paso 1.
- El catálogo sale de `GET /catalog` (una vez por sesión). Cada agregado llama a `POST /sales/<id>/items`.

### Cobro (`PaymentModal`)

- Izquierda: total, pagos registrados (con "✕" para anular, con `Anular`, motivo obligatorio) y saldo. Medios de pago activos como botones.
- Derecha: monto a aplicar (por defecto el saldo); en efectivo, "Recibido" con botones rápidos ("Justo" y redondeos hacia arriba) y el vuelto; teclado numérico táctil (el teclado físico también funciona).
- "Registrar pago" envía el pago. Si el saldo llega a 0 la venta se cierra: el modal muestra "Venta cerrada" con el vuelto y, al cerrarlo, el panel se deselecciona.
- Con saldo pendiente el modal sigue abierto para el siguiente pago.

### Descuento (`DiscountModal`)

Mismo modal para venta o ítem (según desde dónde se abra): plantillas activas del alcance correspondiente como botones (las restringidas solo con `Descuentos`) y, con `Descuentos`, "Libre": porcentaje o monto, valor y motivo obligatorio.

### Dividir (`SplitModal`)

Ítems confirmados con un selector de cantidad (0 a la cantidad del ítem, de a 1; si la cantidad no es entera, permite el resto). "Crear cuenta aparte" llama a `POST /sales/<id>/split` y selecciona la venta nueva. Deshabilitado si la venta tiene pagos activos, con el motivo.

### Anulación (`CancelReasonModal`)

Motivos activos del catálogo como botones, más un campo de texto libre. Con motivo elegido el texto es opcional (se agrega como detalle); sin motivo elegido el texto es obligatorio. Se usa para ítems confirmados, pagos y ventas.

### Configuración del plano (`/pos/config`: `SalonList`, `FloorEditor`)

- Lista de salones: crear, renombrar, ordenar, desactivar (el backend rechaza si tiene ventas activas).
- Editor: lienzo con grilla; agregar mesa (número, nombre, capacidad, forma rectangular por tamaño); arrastrar para mover y desde la esquina para redimensionar, con pointer events (sirve para mouse y táctil), ajustando a la grilla. Los cambios se guardan al soltar (`PUT /config/tables/<id>`). Desactivar mesa desde su ficha.

## Flujo de datos y sincronización

### Queries

| Clave | Se pide | Se invalida |
|---|---|---|
| `['pos','floor',salonId]` | Al entrar al salón | Cambios de ventas de esas mesas; respaldo cada 60 s; mutations de mesa |
| `['pos','sale',id]` | Venta seleccionada | Cambios de esa venta (y se reemplaza con la respuesta de cada mutation) |
| `['pos','sales',{type:'counter'}]` | Tablero de mostrador | Cambios de ventas de mostrador |
| `['pos','catalog']` | Una vez por sesión (`staleTime` 5 min) | Botón "Recargar carta" |
| `['pos','events',id]` | Pestaña Historial | Cambios de esa venta |
| `['pos','waiters']`, `['pos','cancel-reasons']`, `['pos','payment-methods']`, `['pos','discount-templates']` | Al usarlos | `staleTime` 5 min |

Los medios de pago y las plantillas activas se leen de `GET /payment-methods` (`POS`, `Camarero` o `Cobrar`) y `GET /discount-templates` (`POS` o `Camarero`), ya definidos en el 1a. El plano usa la lista `salons` que devuelve `GET /floor` para las solapas de la barra superior.

### Polling por cambios (`usePosChanges`)

- Corre en `PosLayout`, solo con la pestaña visible.
- Cada 3 s llama a `GET /pos/changes?since=<último id>`.
- Por cada venta en la respuesta invalida su `sale` y sus `events`; si hay ventas de salón, el plano (`floor`, solo se vuelve a pedir el que está en pantalla) y, si hay de mostrador, el tablero.
- El primer llamado (sin `since`) solo obtiene el último id.
- Con `reset: true` o tras un error de red, invalida todo `['pos']`.
- La lógica de "respuesta → claves a invalidar" es una función pura testeada.

### Mutations (`useSaleActions`)

- Cada acción escribe la venta devuelta en `['pos','sale',id]` e invalida el plano o el tablero correspondiente.
- Sin actualizaciones optimistas: el frontend nunca muestra montos que no calculó el backend. Las únicas cuentas locales son vistas previas: el vuelto mientras se tipea "Recibido", el importe del renglón antes de agregarlo y la suma de las cuentas de una mesa en el plano.
- Mientras una mutation corre, los botones de esa venta se deshabilitan.

### Idempotencia de pagos

`PaymentModal` genera un `client_request_id` con `crypto.randomUUID()` al preparar cada pago y lo reutiliza si el envío falla y se reintenta. Se renueva después de un pago exitoso.

### Errores

- **409/400:** aviso con el mensaje del backend y refresco de la venta. Si abrir una mesa devuelve 409 con el id de la venta existente, se selecciona esa venta en lugar de mostrar error.
- **403:** "No tenés permiso para…".
- **Red o 500:** aviso genérico con "Reintentar".
- Los avisos son un componente de toasts propio del POS (no hay librería de toasts en el proyecto).

## Agregados al backend

Una migración `b1b1_add_pos_cash_ui_support` después de `b1a4_add_pos_sales_engine`. Rutas delgadas, lógica en servicios, errores con `PosError`, como en el 1a.

### Motivos de anulación

- **`cancel_reasons`**: `id`, `name` (único), `position`, `is_active`, timestamps.
- **`cancel_reason_id`** → `cancel_reasons` (nullable) en `pos_sale_items`, `pos_payments` y `pos_sales`.
- Las anulaciones de ítem, pago y venta aceptan `{reason_id?, reason?}`:
  - Con `reason_id` (motivo activo): `cancel_reason` = nombre del motivo, más `" — " + reason` si viene texto.
  - Sin `reason_id`: `reason` obligatorio (400 si falta).
  - `reason_id` inexistente o inactivo: 400.
  - El `payload` del evento incluye `reason_id` y el texto final.
- **API:** CRUD `/config/cancel-reasons` (admin, baja lógica) y `GET /cancel-reasons` (solo activos, `POS`, `Camarero` o `Anular`).
- **Datos iniciales:** "Error de carga", "Cliente se arrepintió", "Invitación de la casa", "Producto agotado".

### Cambios para el polling

`GET /changes?since=<id>` (`POS` o `Camarero`):
- Sin `since`: `{last_event_id, sales: []}`.
- Con `since`: eventos con `id > since`, hasta 500. Devuelve `last_event_id` y las ventas distintas afectadas con `{id, table_id, salon_id, sale_type, status}`.
- Si hay más de 500: `{last_event_id, reset: true}`.
- Usa la PK de `pos_sale_events`; no agrega tablas ni índices.

### Mozos

- **`GET /waiters`** (`POS`): usuarios activos con módulo `Camarero` o `POS` (o admin), con `id` y nombre para mostrar (nombre del empleado o email).
- **`POST /sales/<id>/waiter {waiter_id}`** (`POS`): venta `open`/`billing`; el usuario debe cumplir el mismo criterio (400 si no). Registra `waiter_changed` con el anterior y el nuevo. Devuelve la venta completa.
- **`POST /sales`** valida `waiter_id` con el mismo criterio cuando viene.

### Infraestructura

- Compresión de respuestas con `flask-compress` (nueva dependencia en `backend/requirements.txt`).
- `render.yaml`: gunicorn con `--worker-class gthread --threads 4`.

## Estructura del código

### Frontend (`frontend/src/pos/`)

- `api/posApi.js`: un método por endpoint de `/api/v1/pos`, sobre el `api` de axios existente.
- `hooks/`: `keys.js`, `usePosQueries.js` (`useFloor`, `useSale`, `useCounterSales`, `useCatalog`, `useSaleEvents` y `useLookup` para mozos, motivos, medios y plantillas), `useSaleMutation.js`, `usePosChanges.js`, `usePosPermissions.js`, `useConfigMutation.js`, `useElementWidth.js`, `useNow.js`.
- `layout/`: `PosLayout.jsx`, `PosTopBar.jsx`, `PosRoute.jsx` (guardia de permisos), `PosHome.jsx`.
- `ui/`: `Modal.jsx`, `Toasts.jsx`, `buttons.js`, `Chip.jsx`, `StatusBadge.jsx`, `CenteredMessage.jsx`.
- `floor/`: `FloorPlan.jsx`, `TableTile.jsx`, `SalonPage.jsx`.
- `counter/`: `CounterPage.jsx`.
- `sale/`: `SalePanel.jsx`, `SaleHeader.jsx`, `Ticket.jsx`, `TicketItem.jsx`, `SaleFooter.jsx`, `SaleHistory.jsx`.
- `modals/`: `AddProductsModal.jsx` (con `ProductDetailStep.jsx`), `PaymentModal.jsx`, `DiscountModal.jsx`, `SplitModal.jsx`, `CancelReasonModal.jsx`, `OpenTableModal.jsx`, `WaiterModal.jsx`, `NewCounterSaleModal.jsx`, `NumericKeypad.jsx`.
- `config/`: `PosConfigPage.jsx`, `SalonList.jsx`, `FloorEditor.jsx`, `TableForm.jsx`.
- `utils/`: `money.js` (formato ARS), `errors.js` (mensaje de error de axios a texto), `changes.js` (respuesta de `/changes` a claves de invalidación), `change.js` (vista previa del vuelto y montos rápidos), `keypad.js`, `ids.js`, `time.js`, `permissions.js` (acciones permitidas según módulos, estado y rol), `floor.js` (estado de mesa y geometría del plano), `catalog.js`, `modifiers.js`, `quantity.js`, `events.js`.
- Páginas de Galia: `pages/ModifierGroups.jsx`, sección en `pages/ProductDetail.jsx`, `pages/admin/PosSettings.jsx`; rutas en `App.jsx` y entradas en `Sidebar.jsx`.

Los componentes usan la paleta Galia de Tailwind ya existente. Tamaños táctiles: objetivos de al menos 44 px.

### Backend

- `backend/app/models/pos/cancel_reasons.py` y columnas nuevas en los modelos de venta.
- `backend/app/services/pos/cancel_reasons.py` (resolver `reason_id`/`reason` a texto), `changes_service.py`, y la reasignación de mozo en `sale_service.py`.
- Rutas en `pos_config.py` (CRUD de motivos) y `pos_sales.py` / `pos_floor.py` (`/changes`, `/waiters`, `/cancel-reasons`, `/sales/<id>/waiter`).

## Pruebas y verificación

### Backend (pytest, TDD)

- Motivos: CRUD solo admin; anular ítem, pago y venta con `reason_id` (copia el nombre), con texto, con ambos, sin ninguno (400), con motivo inactivo (400).
- `/changes`: sin `since`, con eventos de varias ventas (sin duplicados), tope con `reset`, permisos.
- Mozos: listado filtrado por módulo; reasignar con evento `waiter_changed`; mozo sin permiso (400); venta cerrada (409); `Camarero` sin `POS` (403); `POST /sales` con `waiter_id` inválido (400).
- Compresión: una respuesta grande con `Accept-Encoding: gzip` vuelve comprimida.
- Test de cobertura de rutas actualizado.
- Sin fallas nuevas respecto de la línea base de tests.

### Frontend

- **Vitest** como dependencia de desarrollo, sin Testing Library, para la lógica pura de `utils/` (todos los archivos salvo `errors.js`).
- `npm run lint` sin errores nuevos respecto de la línea base y `npm run build` OK.

### Verificación manual

En el preview del navegador, con el backend sobre Postgres en Docker (base nueva, no la local en revisión ajena), en cada tarea de UI y al final:

1. Crear un salón y acomodar mesas en el editor.
2. Abrir una mesa (eligiendo mozo), cargar productos con variante, modificadores y nota, confirmar la tanda.
3. Descuento de ítem y de venta; pedir la cuenta.
4. Dividir la cuenta y cobrar en partes, con vuelto.
5. Mover de mesa y reasignar mozo.
6. Anular un ítem confirmado con un motivo del catálogo; ver el Historial.
7. Venta de mostrador cobrada en el momento y otra que queda abierta.
8. Dos pestañas (caja y un usuario `Camarero`): un cambio en una aparece en la otra en unos 3 s.
9. Anchos de 1024 px y 1920 px.

## Fuera de alcance

- Vista móvil del camarero (1c).
- Comanda, precuenta e impresión (3).
- Caja y arqueo (2).
- Reportes de anulaciones (los datos quedan guardados).
- WebSockets.
