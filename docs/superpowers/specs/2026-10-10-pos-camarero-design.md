# Camarero en el celular (sub-proyecto 1c) — Diseño

**Fecha:** 2026-10-10
**Rama:** `feature/pos-camarero` (desde `feature/pos-caja`)
**Antecede:**
- `docs/superpowers/specs/2026-10-09-pos-sales-engine-design.md` (1a: modelo, reglas y API `/api/v1/pos`, ya en `main`)
- `docs/superpowers/specs/2026-10-10-pos-caja-design.md` (1b: POS de caja web)

## Contexto

El sub-proyecto 1 ("núcleo de venta") se divide en tres ciclos: 1a motor de venta (backend), 1b POS de caja (web) y **1c Camarero (celular)**. Este documento cubre el 1c: la interfaz móvil con la que los mozos toman pedidos en el salón.

El 1c se apoya en lo que construye el 1b:
- **Frontend:** el cliente de API, los hooks de React Query, el polling por cambios y las utilidades de `frontend/src/pos/`.
- **Backend:** `GET /changes`, los motivos de anulación y el listado de mozos.

La implementación empieza cuando el 1b esté mergeado.

## Decisiones de producto

- **Formato:** ruta móvil `/camarero` dentro del frontend de Galia, instalable como PWA. Sin app nativa ni tiendas.
- **Dispositivos:** cada mozo usa su celular personal y entra con su usuario de Galia. Sin PIN ni cambio rápido de usuario.
- **Mesas:** dos vistas, Lista (tarjetas) y Plano (posiciones reales con zoom), con un selector que se recuerda por dispositivo y un filtro "Mías / Todas".
- **Mesas ajenas:** cualquier mozo opera cualquier mesa de salón, como permite el 1a. La tarjeta muestra de quién es y toda acción queda auditada con su usuario.
- **Acciones:** las mismas que el 1b da a `Camarero` sin `POS`:
  - abrir mesa, cargar con variante, modificadores y nota, y confirmar la tanda;
  - pedir la cuenta y reabrir;
  - mover y dividir;
  - descuentos con plantillas no restringidas.

  Los permisos agregan acciones:
  - `Cobrar`: cobrar;
  - `Anular`: anular ítems confirmados, pagos y ventas;
  - `Descuentos`: plantillas restringidas y descuento libre.
- **Mozo de la venta:** siempre quien abre la mesa desde el celular.
- **Conexión:** funciona solo con conexión. Sin red se avisa y se bloquean las acciones. No hay cola offline.

## Enfoque

Árbol de rutas propio en `frontend/src/camarero/`, con componentes pensados para el teléfono, sobre la base compartida del 1b:
- `pos/api`, `pos/hooks`: `useFloor`, `useSale`, `useCatalog`, `usePosChanges`, `useSaleActions`, `usePosPermissions` y `usePosLookups`.
- `pos/utils`: `money`, `errors`, `changes`, `change` y `permissions`.

La lógica de negocio, los permisos y la sincronización existen una sola vez. El 1c solo agrega presentación y lo propio del celular: conectividad, PWA, gestos y preferencias por dispositivo.

Se descartaron:
- **Componentes del 1b responsive:** atan el diseño de caja al del teléfono y llenan los componentes de condicionales por tamaño.
- **App Vite aparte:** doble build y deploy, y código compartido entre proyectos, para unos 10 mozos.

## Rutas, entrada y sesión

### Rutas (fuera del `Layout` de Galia, con `CamareroLayout`)

| Ruta | Permiso | Contenido |
|---|---|---|
| `/camarero?salon=<id>` | `Camarero` o `POS` | Mesas del salón: solapas, selector Plano/Lista, filtro Mías/Todas |
| `/camarero/venta/:saleId` | `Camarero` o `POS` | La venta en pantalla completa |

- El salón, la vista y el filtro se guardan en `localStorage` por dispositivo (`useDevicePrefs`). Si la URL trae `?salon=`, gana la URL.
- Sin salón en la URL ni guardado (o si el guardado ya no está activo), se usa el primer salón activo.
- Sin salones activos, se muestra un aviso: "No hay salones configurados. Pedile a la caja que los cree."
- Las acciones secundarias son hojas inferiores dentro de la ruta. Al abrir una hoja se agrega una entrada al historial, así el "atrás" del teléfono la cierra antes de salir de la venta.

### Entrada

- **Después del login:** un usuario con `Camarero`, sin `POS` y que no es admin va a `/camarero`. Los demás siguen yendo a `/dashboard`. Si el login venía de una ruta protegida (por ejemplo, la sesión expiró estando en `/camarero/venta/12`), vuelve a esa ruta.
- **Sidebar:** entrada "Camarero" para `Camarero` o `POS`, junto a "Abrir POS" del 1b.
- **`/pos` en pantallas de menos de 768 px:** `PosLayout` muestra un aviso descartable, "¿Estás en el celular? Abrí la vista Camarero", con enlace a `/camarero`. El descarte se recuerda en `localStorage`.

### PWA

- `vite-plugin-pwa` (dependencia de desarrollo) con manifest:
  - `name: "Galia Camarero"`, `short_name: "Camarero"`;
  - `start_url: "/camarero"`, `scope: "/"`, `display: "standalone"`;
  - colores de la paleta Galia;
  - íconos de 192 y 512 px (y uno *maskable*) en `frontend/public/`, generados a partir del logo de Galia.
- El service worker (Workbox, `generateSW`) precachea solo los archivos estáticos del build. Las llamadas a la API no se cachean: `navigateFallbackDenylist` incluye `/api`, y en producción el backend vive en otro origen.
- Actualizaciones con `registerType: 'prompt'`: `UpdateBanner` muestra "Hay una versión nueva — Actualizar" y recarga al tocarlo.
- El manifest es único para todo el frontend. En escritorio no cambia nada visible.

### Sesión

Login actual de Galia con el token guardado. Con el token vencido (401), el flujo actual lleva al login. Después del login se vuelve a la ruta de origen (ver Entrada).

## Pantallas

### Mesas (`TablesScreen`)

- **Barra superior:**
  - solapas de salón con desplazamiento horizontal, que salen de la lista `salons` de `GET /floor`;
  - selector Plano/Lista;
  - filtro "Mías / Todas";
  - menú con el usuario, "Salir a Galia" (`/dashboard`, solo si tiene otros módulos) y "Cerrar sesión".
- **Lista (`TableList`, `TableCard`):** grilla de 2 columnas (3 desde 600 px). Cada tarjeta muestra:
  - número o nombre de la mesa;
  - color por estado, igual que en el 1b: libre (gris), abierta (ámbar, alguna venta `open`), cuenta pedida (rojo, todas en `billing`);
  - si está ocupada: total, mozo ("Vos" si es el usuario actual) y minutos desde la apertura;
  - "n cuentas" si hay más de una venta;
  - un punto indicador si alguna venta tiene `pending_count > 0`.
- **Filtro "Mías":** muestra las mesas donde alguna venta tiene `waiter.id` igual al usuario, más las libres. "Todas" muestra todas.
- **Plano (`FloorView`):**
  - mesas en sus coordenadas del 1a, escaladas al ancho de pantalla (`floorScale`);
  - zoom con pellizco y botones +/− (de 1× a 3×), desplazamiento con arrastre (`usePinchZoom`, pointer events);
  - solo lectura;
  - el filtro "Mías" atenúa las mesas ajenas en lugar de ocultarlas.
- **Al tocar una mesa:**
  - **Libre:** `OpenTableSheet`, con personas (stepper, por defecto 2, mínimo 1) y "Abrir y cargar". Llama a `POST /sales` (salón, mesa, personas; sin `waiter_id`), navega a la venta y abre `AddProductsSheet`.
    - Si la apertura devuelve 409 con la venta existente, se navega a esa venta.
  - **Con una venta:** navega a `/camarero/venta/:id`.
  - **Con varias ventas:** `PickSaleSheet`, con una fila por cuenta (número, total, estado).

### Venta (`SaleScreen`)

- **Encabezado fijo:** "← Mesas" (vuelve a `/camarero` con el salón de la venta), mesa y salón, personas, mozo, estado. Si la mesa tiene varias ventas activas, chips para cambiar de cuenta.
- **Ticket (`MobileTicket`):**
  - primero los pendientes, bajo "Sin enviar" y resaltados;
  - después los confirmados, agrupados por tanda;
  - cada ítem muestra cantidad, nombre y variante, modificadores, nota, importe y sus descuentos;
  - los anulados se ven tachados y con el motivo.
- **Totales:** subtotal, descuentos, total, pagado y saldo.
- **Al tocar un ítem:** `ItemActionsSheet`, con las acciones que permite `pos/utils/permissions`:
  - pendiente: "Borrar";
  - confirmado: "Descuento al ítem", "Anular" (con `Anular`);
  - con descuento: "Quitar descuento".
- **Barra inferior fija (`SaleBottomBar`):**
  - "+ Agregar" (grande);
  - "Enviar (n)", resaltado si hay pendientes (confirma la tanda);
  - "Cuenta" o "Reabrir";
  - "Cobrar", solo si `permissions` lo permite;
  - "⋯", con "Descuento a la venta", "Mover", "Dividir", "Anular venta" (con `Anular`) y "Cerrar" (con saldo 0).

  "Cuenta" o "Cobrar" con pendientes confirman primero la tanda y lo avisan, como en el 1b.
- **Si la venta se cierra** (desde el celular o desde otro dispositivo): pantalla breve "Venta cerrada" (con el vuelto si lo hubo) y un botón "Volver a mesas".
- **Si la venta se anula o se mueve desde otro dispositivo:** se refresca y se muestra el estado nuevo.

### Hojas inferiores (`sheets/`)

- **`BottomSheet`:**
  - base común: fondo oscurecido, cierre deslizando hacia abajo, con el botón ✕ o con "atrás";
  - mueve el foco al abrir y lo devuelve al cerrar;
  - altura según el contenido, o casi completa con `size="full"`;
  - respeta `env(safe-area-inset-bottom)`.
- **`AddProductsSheet`** (pantalla casi completa):
  - búsqueda arriba, chips de categoría y lista de productos de una columna con precio ("desde $x" si hay varias variantes);
  - un toque agrega una unidad si el producto tiene una sola variante activa y ningún grupo de modificadores obligatorio. Si no, abre `ProductDetailSheet`;
  - un toque largo, o el botón "⋯" de la fila, abre siempre el detalle;
  - el pie muestra el resumen ("3 agregados: 2 Latte, 1 Medialuna") y "Listo".
  - El catálogo sale de `GET /catalog`; cada agregado llama a `POST /sales/<id>/items`.
- **`ProductDetailSheet`:** variante, grupos de modificadores con mínimo y máximo (los obligatorios bloquean "Agregar"), nota, cantidad con stepper e importe del renglón. Usa las mismas reglas que el `ProductDetailStep` del 1b.
- **`PaymentSheet`:**
  - medios de pago activos como botones grandes;
  - monto (por defecto el saldo);
  - en efectivo, "Recibido" con botones rápidos (`change.js` del 1b) y vuelto;
  - los campos usan `inputmode="decimal"`;
  - pagos registrados con "✕" para anular (con `Anular`, motivo obligatorio);
  - genera un `client_request_id` por pago y lo reutiliza en los reintentos;
  - con saldo 0, la venta se cierra (ver Venta).
- **`DiscountSheet`:** venta o ítem; plantillas activas del alcance (las restringidas solo con `Descuentos`) y, con `Descuentos`, "Libre": porcentaje o monto, valor y motivo obligatorio.
- **`SplitSheet`:** ítems confirmados con stepper de cantidad, con las mismas reglas que el `SplitModal` del 1b. Deshabilitado si la venta tiene pagos activos, con el motivo. "Crear cuenta aparte" navega a la venta nueva.
- **`MoveSheet`:** mesas libres del salón actual, con solapas para cambiar de salón (`GET /floor?salon_id=`). Tocar una mesa la mueve y vuelve a la venta.
- **`CancelReasonSheet`:** motivos activos del catálogo (1b) como botones más texto libre, con las mismas reglas que `CancelReasonModal`.
- **`PickSaleSheet`:** elegir la cuenta de una mesa con varias ventas.

### Detalles táctiles

- Objetivos táctiles de al menos 48 px.
- Área segura del iPhone en la barra superior e inferior.
- `useWakeLock` pide `navigator.wakeLock.request('screen')` con la app visible y lo renueva al volver al frente. Si el navegador no lo soporta, no hace nada.
- Mientras corre una mutation, los botones de la venta se deshabilitan, como en el 1b.

## Flujo de datos y conexión

### Datos

- **Queries del 1b sin cambios:**
  - `['pos','floor',salonId]`, `['pos','sale',id]`, `['pos','catalog']`;
  - `['pos','payment-methods']`, `['pos','discount-templates']`, `['pos','cancel-reasons']`.
- **Mutations:** `useSaleActions` del 1b. Cada una escribe en caché la venta devuelta. Sin actualizaciones optimistas.
- **Polling:** `usePosChanges` del 1b, montado en `CamareroLayout`. Cada 3 s con la página visible, en pausa con la página oculta. Al volver a visible pide `/changes` de inmediato.

### Conectividad (`useConnectivity`)

- Combina `navigator.onLine`, los eventos `online`/`offline` y el resultado de cada llamada a `/changes`.
- **Pasa a "sin conexión":**
  - con `offline`;
  - con dos fallos de red seguidos del polling (sin respuesta HTTP; un 4xx o 5xx no cuenta).
- **Vuelve a "conectado"** con la primera respuesta exitosa.
- **Sin conexión:**
  - banda fija "Sin conexión — reintentando…";
  - todos los botones de acción deshabilitados;
  - la información visible queda, con la marca "desactualizado".
- **Al reconectar:** invalida todo `['pos']` y quita la banda.
- **Mutation que falla por red:**
  - aviso "No se pudo completar, revisá el ticket" y refresco de la venta al reconectar;
  - el cobro reintenta con el mismo `client_request_id`, así que no se duplica.
- La regla de transición (eventos → estado) es una función pura testeada (`connectivityReducer`).

### Errores

Los mismos que el 1b (`pos/utils/errors`, toasts del POS):
- 409/400: mensaje del backend y refresco;
- 403: "No tenés permiso para…";
- red o 500: aviso con "Reintentar".

## Agregados al backend

- **`pending_count` en `GET /floor`:** cada venta del resumen (`sale_to_dict(..., include_items=False)` dentro de `floor`) suma la cantidad de ítems con estado pendiente.
  - Los ítems anulados y los confirmados no cuentan.
  - Se calcula con una consulta agrupada por `sale_id` para todas las ventas del plano, sin una consulta por venta.
  - Resuelve también el pendiente "flags de pendientes en el plano" anotado en el 1a.
- Sin migración. Sin endpoints nuevos: el resto ya existe en el 1a (con `Camarero`, `Cobrar`, `Anular` y `Descuentos`) o lo agrega el 1b.

## Estructura del código

### Frontend (`frontend/src/camarero/`)

- `layout/`: `CamareroLayout.jsx` (polling, banda de conexión, toasts del 1b, Wake Lock), `CamareroRoute.jsx` (guardia `Camarero` o `POS`), `ConnectivityBanner.jsx`, `UpdateBanner.jsx`.
- `tables/`: `TablesScreen.jsx`, `TableList.jsx`, `TableCard.jsx`, `FloorView.jsx`, `OpenTableSheet.jsx`.
- `sale/`: `SaleScreen.jsx`, `MobileTicket.jsx`, `ItemActionsSheet.jsx`, `SaleBottomBar.jsx`, `SaleClosedView.jsx`.
- `sheets/`: `BottomSheet.jsx`, `AddProductsSheet.jsx`, `ProductDetailSheet.jsx`, `PaymentSheet.jsx`, `DiscountSheet.jsx`, `SplitSheet.jsx`, `MoveSheet.jsx`, `CancelReasonSheet.jsx`, `PickSaleSheet.jsx`.
- `hooks/`: `useConnectivity.js`, `useWakeLock.js`, `useDevicePrefs.js`, `usePinchZoom.js`.
- `utils/`:
  - `tableFilters.js`: estado de la tarjeta y filtro Mías/Todas;
  - `floorScale.js`: escala y límites del plano;
  - `connectivity.js`: `connectivityReducer`;
  - `postLogin.js`: ruta de destino después del login según módulos, rol y ruta de origen.

Fuera de `camarero/`:
- `App.jsx` (rutas), `context/AuthContext.jsx` y la página de Login (destino después del login con `postLogin`).
- `components/layout/Sidebar.jsx` (entrada "Camarero").
- `pos/layout/PosLayout.jsx` (aviso para pantallas angostas).
- `vite.config.js` (PWA), `src/main.jsx` (registro del service worker), íconos en `public/`.

Componentes con la paleta Galia de Tailwind.

### Backend

- `backend/app/routes/pos_floor.py`: cálculo de `pending_count` (helper en `services/pos/serializers.py` o en la propia ruta, siguiendo lo que haga el 1b con el plano).

## Pruebas y verificación

### Backend (pytest, TDD)

- `GET /floor` devuelve `pending_count`:
  - con pendientes;
  - sin pendientes (0);
  - con ítems anulados o confirmados (no cuentan);
  - con varias ventas en una mesa.
- La cantidad de consultas de `GET /floor` no crece con la cantidad de ventas (conteo de sentencias con un listener de SQLAlchemy).
- Sin fallas nuevas respecto de la línea base (`backend/scripts/compare_baseline.py`).

### Frontend (Vitest, ya agregado en el 1b)

- `tableFilters`: estados libre, abierta y cuenta pedida; varias cuentas; Mías con y sin ventas propias; libres incluidas.
- `floorScale`: escala según el ancho; límites de zoom y desplazamiento.
- `connectivityReducer`: un fallo no cambia el estado; dos fallos seguidos pasan a sin conexión; 4xx o 5xx no cuentan; `offline` pasa a sin conexión de inmediato; la primera respuesta exitosa reconecta.
- `postLogin`: `Camarero` sin `POS` va a `/camarero`; admin y `POS` van a `/dashboard`; la ruta de origen gana.
- `npm run lint` sin errores nuevos y `npm run build` OK. El build genera `manifest.webmanifest` y el service worker.

### Verificación manual

En el preview del navegador con viewport móvil (375×812), con el backend sobre Postgres en Docker (base nueva):

1. Login como usuario `Camarero` sin `POS` → `/camarero`.
2. Vistas Lista y Plano (zoom y desplazamiento), Mías y Todas, cambio de salón; recargar conserva las preferencias.
3. Abrir una mesa, cargar productos con variante, modificadores y nota, y enviar la tanda.
4. Pedir la cuenta, dividir y mover de mesa.
5. Con `Cobrar`: cobrar en efectivo con vuelto y ver "Venta cerrada". Sin `Cobrar`: no aparece el botón.
6. Con `Anular`: anular un ítem confirmado con un motivo del catálogo.
7. La caja (1b) en otra pestaña ve los cambios del celular en unos 3 s, y al revés.
8. DevTools en modo offline: banda, acciones bloqueadas y recuperación al volver la red.
9. El "atrás" del navegador cierra las hojas antes de salir de la venta.
10. El manifest es válido e instalable (DevTools → Application), y el aviso de versión nueva aparece después de un nuevo build.

## Fuera de alcance

- Modo offline con cola de acciones.
- PIN y dispositivos compartidos.
- Notificaciones push (por ejemplo, "pedido listo"): van con cocina (3).
- Comanda, precuenta e impresión (3).
- Ventas de mostrador desde el celular.
- Editar el plano desde el celular.
