# Camarero en el celular (sub-proyecto 1c) — Diseño

**Fecha:** 2026-10-10 (revisado el 2026-10-12, con el 1b ya en `main`)
**Rama:** `feature/pos-camarero` (desde `main`, que ya incluye el 1a y el 1b)
**Antecede:**
- `docs/superpowers/specs/2026-10-09-pos-sales-engine-design.md` (1a: modelo, reglas y API `/api/v1/pos`)
- `docs/superpowers/specs/2026-10-10-pos-caja-design.md` (1b: POS de caja web, PR #10)

## Contexto

El sub-proyecto 1 ("núcleo de venta") se divide en tres ciclos: 1a motor de venta (backend), 1b POS de caja (web) y **1c Camarero (celular)**. Este documento cubre el 1c: la interfaz móvil con la que los mozos toman pedidos en el salón.

El 1b dejó en `frontend/src/pos/` todo lo que el 1c reutiliza:

- **API y datos:**
  - `api/posApi.js`;
  - `hooks/usePosQueries.js` (`useFloor`, `useSale`, `useCatalog`, `useLookup`);
  - `hooks/useSaleMutation.js` (ejecuta una acción, escribe la venta devuelta en caché, avisa los errores);
  - `hooks/usePosChanges.js` (polling a `/changes`);
  - `hooks/usePosPermissions.js`;
  - `hooks/keys.js`.
- **Reglas:** en `utils/`:
  - `permissions` (`posPermissions`, `saleActions`, `itemActions`);
  - `floor` (`tableStatus`, `tableSummary`, `canvasHeight`);
  - `catalog`, `modifiers`, `change`, `money`, `time`, `errors`, `ids`.
- **Componentes:**
  - `ui/Modal.jsx`, en el que se apoyan todos los modales;
  - `ui/Toasts.jsx`;
  - `ui/buttons.js`;
  - `sale/SalePanel.jsx` con `SaleHeader`, `Ticket`, `TicketItem` y `SaleFooter`;
  - `floor/FloorPlan.jsx` y `TableTile.jsx`;
  - los modales `AddProductsModal` (con `ProductDetailStep`), `PaymentModal`, `DiscountModal`, `SplitModal`, `CancelReasonModal` y `OpenTableModal`.

## Decisiones de producto

- **Formato:** ruta móvil `/camarero` dentro del frontend de Galia, instalable como PWA. Sin app nativa.
- **Dispositivos:** cada mozo usa su celular personal y entra con su usuario de Galia. Sin PIN.
- **Mesas:** dos vistas, Lista (tarjetas) y Plano (posiciones reales con zoom), con un selector que se recuerda por dispositivo y un filtro "Mías / Todas".
- **Mesas ajenas:** cualquier mozo opera cualquier mesa de salón, como permite el 1a. La tarjeta muestra de quién es y toda acción queda auditada con su usuario.
- **Acciones:** las mismas que el 1b le da a `Camarero` sin `POS`, calculadas con `saleActions` / `itemActions`:
  - abrir, cargar y confirmar la tanda;
  - pedir la cuenta y reabrir;
  - mover y dividir;
  - descuentos con plantillas no restringidas.

  Además, `Cobrar` habilita cobrar, `Anular` habilita anular y `Descuentos` habilita las plantillas restringidas y el descuento libre.
- **Mozo de la venta:** al abrir desde el celular, siempre quien abre (sin selector de mozo, aunque el usuario tenga `POS`).
- **Conexión:** funciona solo con conexión. Sin red se avisa y se bloquean las acciones. No hay cola offline.

## Enfoque

Lo propio del 1c vive en `frontend/src/camarero/`: layout móvil, pantalla de mesas, pantalla de venta, conectividad, PWA y preferencias por dispositivo. **La venta y sus acciones reutilizan los componentes del 1b**, con dos cambios chicos y compatibles en `pos/`:

1. **`Modal` con modo hoja inferior.**
   - Un contexto `ModalPresentationContext` (`'dialog'` por defecto, `'sheet'` dentro de `/camarero`) decide cómo se dibuja.
   - En modo hoja, el modal:
     - queda anclado abajo, a todo el ancho, con bordes superiores redondeados;
     - tiene un alto máximo del 92 % de la pantalla y respeta `env(safe-area-inset-bottom)`;
     - se cierra con el botón "atrás" del teléfono.
   - Dos modales consultan el contexto:
     - `PaymentModal` oculta el `NumericKeypad` en pantalla (sus campos ya tienen `inputMode="decimal"`);
     - `AddProductsModal` no enfoca el buscador al abrir, para que el teclado no tape la carta.
2. **`SalePanel` con variante de pantalla completa.**
   - `variant="screen"` dibuja a todo el ancho y alto, en lugar del panel lateral de 400 px.
   - El pie queda fijo con el área segura.
   - El botón de cerrar del encabezado pasa a "← Mesas" (`SaleHeader` recibe `closeLabel`).

Además, `OpenTableModal` recibe `allowWaiterPick` (por defecto `perms.pos`, como hoy). El 1c pasa `false`.

Se descartaron:
- **Reescribir los modales como hojas propias del 1c:** duplica la lógica de cobro, modificadores, descuentos y anulaciones.
- **Componentes del 1b responsive por tamaño de pantalla:** la caja en una tablet angosta cambiaría de comportamiento.
- **App Vite aparte:** doble build y deploy para unos 10 mozos.

## Rutas, entrada y sesión

### Rutas (fuera del `Layout` de Galia, con `CamareroLayout`)

| Ruta | Permiso | Contenido |
|---|---|---|
| `/camarero?salon=<id>` | `Camarero` o `POS` (`perms.canUse`) | Mesas del salón: solapas, selector Plano/Lista, filtro Mías/Todas |
| `/camarero/venta/:saleId?add=1` | `Camarero` o `POS` | La venta en pantalla completa; `add=1` abre "Agregar productos" al entrar |

- La guardia es `PosRoute` del 1b (`require="canUse"`).
- El salón, la vista y el filtro se guardan en `localStorage` por dispositivo (`useDevicePrefs`, con `try/catch`). Si la URL trae `?salon=`, gana la URL.
- Sin salón en la URL ni guardado (o si el guardado ya no está activo), se usa el primero de la lista `salons` de `GET /floor`.
- Sin salones activos: "No hay salones configurados. Pedile a la caja que los cree."

### Entrada

- **Después del login** (`utils/postLogin.js`, función pura):
  - si `ProtectedRoute` guardó una ruta de origen (`location.state.from`), se vuelve ahí;
  - si no, un usuario con `Camarero`, sin `POS` y que no es admin, va a `/camarero`;
  - los demás, a `/dashboard`.
- **Ruta de origen tras un 401:** el interceptor de axios redirige con `window.location` y pierde el estado del router. Antes de redirigir guarda la ruta actual en `sessionStorage` (`postLoginRedirect`, con `try/catch`), y `postLogin` la usa si no hay `state.from`. Se descarta después de usarla.
- **`AuthContext.login`** devuelve `{ user, modules }` para que `Login` calcule el destino sin esperar a que se actualice el estado. Es el único llamador.
- **Interceptor de 403:** hoy redirige a `/dashboard` salvo en `/pos`. Se suma `/camarero` a la excepción, porque una acción sin permiso no debe sacar al mozo de la pantalla.
- **Sidebar:** entrada "Camarero" (`/camarero`) con `anyModule: ['POS', 'Camarero']`, junto a "Abrir POS".
- **`/pos` en pantallas de menos de 768 px:** `PosLayout` muestra un aviso descartable, "¿Estás en el celular? Abrí la vista Camarero", con enlace. El descarte se recuerda en `localStorage`.

### PWA

- Se mantiene `public/site.webmanifest` (lo enlaza `index.html`, con los íconos que ya existen). Se actualiza a:
  - `name: "Galia Camarero"`, `short_name: "Camarero"`;
  - `start_url: "/camarero"`, `scope: "/"`, `display: "standalone"`;
  - `theme_color: "#5C2E46"` (igual que el `<meta name="theme-color">`), `background_color` crema de Galia;
  - los íconos actuales, más el de 512 con `"purpose": "any maskable"`.
- `vite-plugin-pwa` (dependencia de desarrollo) se usa **solo para el service worker**:
  - `manifest: false`, `strategies: 'generateSW'`, `registerType: 'prompt'`;
  - precachea solo los archivos estáticos del build;
  - `navigateFallbackDenylist: [/^\/api/]` y sin `runtimeCaching`, así la API nunca se cachea;
  - `devOptions.enabled: false`.
- **`UpdateBanner`** (con `useRegisterSW` de `virtual:pwa-register/react`): "Hay una versión nueva — Actualizar", que llama a `updateServiceWorker(true)`. Se monta en `CamareroLayout`. El resto de Galia toma la versión nueva al recargar.

### Sesión

El login actual de Galia con el token guardado. Con un 401 se va al login y después se vuelve a la ruta de origen (ver Entrada).

## Pantallas

### Mesas (`TablesScreen`)

- **Barra superior:**
  - solapas de salón con desplazamiento horizontal (de `salons` de `GET /floor`);
  - selector Plano/Lista;
  - filtro "Mías / Todas";
  - menú con el nombre del usuario, "Salir a Galia" (`/dashboard`) y "Cerrar sesión".
- **Lista (`TableList`, `TableCard`):** grilla de 2 columnas (3 desde 600 px). Cada tarjeta muestra:
  - número o nombre de la mesa;
  - color por estado, con `tableStatus` del 1b: libre gris, abierta ámbar, cuenta pedida roja;
  - si está ocupada, con `tableSummary`: total, mozo ("Vos" si es el usuario actual) y tiempo abierta (`elapsedLabel` con `useNow`);
  - "n cuentas" si hay más de una;
  - un punto indicador si alguna venta tiene `pending_count > 0`.
- **Filtro "Mías"** (`utils/tableFilters.js`): las mesas donde alguna venta tiene `waiter.id` igual al usuario, más las libres. "Todas" muestra todas.
- **Plano (`FloorView`):**
  - `FloorPlan` del 1b dentro de un contenedor con zoom;
  - pellizco o botones +/−, de 1× a 3×; desplazamiento con el scroll nativo del contenedor (`usePinchZoom`, pointer events, límites en `utils/zoom.js`);
  - solo lectura;
  - con "Mías", las mesas ajenas se atenúan: `TableTile` recibe `dimmed`.
- **Al tocar una mesa:**
  - **Libre:** `OpenTableModal` (en modo hoja, `allowWaiterPick={false}`). Al abrir navega a `/camarero/venta/:id?add=1`. Si la mesa ya estaba abierta (409), navega a esa venta sin `add`.
  - **Ocupada:** navega a `/camarero/venta/:id` de su primera venta. Las demás cuentas se eligen con las pestañas del panel.

### Venta (`SaleScreen`)

- **`SalePanel` del 1b con `variant="screen"`:**
  - `saleId` sale de la URL; `initialModal = 'add'` si viene `?add=1`, y el parámetro se quita al abrirlo;
  - `siblings`: las ventas activas de la mesa, tomadas de `useFloor(sale.table.salon_id)`;
  - `onSelect(id)` navega a esa venta con `replace`;
  - `onClose` navega a `/camarero?salon=<salón de la venta>`;
  - `onStartMove` abre `MoveSheet`.
- Lo demás es el comportamiento del 1b:
  - ticket con pendientes resaltados y tandas;
  - menú del ítem (borrar, descuento, anular);
  - pie con "Agregar", "Confirmar tanda (n)", "Pedir cuenta" / "Reabrir", "Cobrar" (solo con `Cobrar`) y "Más" (descuento a la venta, mover, dividir, cerrar con saldo 0, anular venta);
  - pedir la cuenta o cobrar con pendientes confirma la tanda primero;
  - el cobro muestra "Venta cerrada" con el vuelto y, al aceptar, vuelve a mesas;
  - anular la venta también vuelve a mesas.
- **Si la venta desaparece o se cierra desde otro dispositivo:** el panel la muestra cerrada o anulada (el pie del 1b ya lo indica) y "← Mesas" vuelve.
- **`MoveSheet`** (`Modal` en modo hoja):
  - solapas de salón y mesas libres del salón como botones grandes (`useFloor(salonId)`, `tableStatus === 'free'`);
  - tocar una mesa llama a `posApi.move` con `useSaleMutation`, avisa "Venta movida a …" y cierra;
  - si no hay mesas libres en el salón: "No hay mesas libres en este salón."

### Detalles táctiles

- Botones del 1b de al menos 44 px. En `/camarero`, las tarjetas y el pie usan 48 px.
- Área segura del iPhone en la barra superior (`env(safe-area-inset-top)`) y en el pie o la hoja (`env(safe-area-inset-bottom)`). `index.html` suma `viewport-fit=cover` al viewport.
- `useWakeLock` pide `navigator.wakeLock.request('screen')` con la página visible y lo renueva al volver al frente. Si no hay soporte o falla, no hace nada.
- Mientras corre una mutation, los botones se deshabilitan, como en el 1b.

## Flujo de datos y conexión

### Datos

Lo del 1b sin cambios:
- queries por `posKeys`;
- acciones con `useSaleMutation`, sin actualizaciones optimistas;
- `usePosChanges` montado en `CamareroLayout`: cada 3 s con la pestaña visible y sin consultar en segundo plano.

El 1c le agrega a `usePosChanges` un parámetro opcional `onResult(ok, error)` para informar el resultado de cada consulta a la conectividad. El 1b no lo pasa y no cambia.

### Conectividad (`useConnectivity`)

- **Estado:** `connectivityReducer(state, event)`, función pura en `utils/connectivity.js`. Eventos: `offline`, `online`, `poll-ok`, `poll-network-error`, `poll-http-error`.
  - `offline` → sin conexión de inmediato;
  - dos `poll-network-error` seguidos (sin respuesta HTTP) → sin conexión;
  - `poll-http-error` (4xx o 5xx) no cuenta como falta de red y reinicia el contador;
  - `poll-ok` → conectado, contador en 0;
  - `online` no reconecta por sí solo: espera el siguiente `poll-ok`.
- **Sin conexión:**
  - `ConnectivityBanner` fijo arriba: "Sin conexión — reintentando…";
  - una capa transparente sobre el contenido bloquea los toques, así ninguna acción sale sin red;
  - la información visible queda.
- **Al reconectar:** `usePosChanges` ya invalida todo `['pos']` tras un fallo (1b). La banda y la capa se quitan.
- **Una mutation que falla por red:** `useSaleMutation` ya muestra el aviso con "Reintentar" y refresca la venta. El cobro reintenta con el mismo `client_request_id`, así que no se duplica.

### Errores

Los del 1b (`errorMessage`, toasts): 409/400 con el mensaje del backend, 403 "No tenés permiso…", red o 500 con "Reintentar".

## Agregados al backend

- **`pending_count` en `GET /floor`:** cada venta del resumen suma la cantidad de ítems pendientes. Los confirmados y los anulados no cuentan.
  - Se calcula con una sola consulta agrupada (`SELECT sale_id, count(*) … WHERE status = 'pending' AND sale_id IN (…) GROUP BY sale_id`) para todas las ventas del plano.
  - Las ventas sin pendientes llevan 0.
- Sin migración. Sin endpoints nuevos.

## Estructura del código

### Frontend

**`frontend/src/camarero/`:**
- `CamareroLayout.jsx`:
  - `ToastProvider`;
  - `ModalPresentationContext` en `'sheet'`;
  - `usePosChanges` con la conectividad;
  - `ConnectivityBanner`;
  - `useWakeLock`;
  - `UpdateBanner`;
  - `<Outlet />`.
- `ConnectivityBanner.jsx`, `UpdateBanner.jsx`.
- `TablesScreen.jsx`, `TablesTopBar.jsx`, `TableList.jsx`, `TableCard.jsx`, `FloorView.jsx`.
- `SaleScreen.jsx`, `MoveSheet.jsx`.
- `hooks/`: `useConnectivity.js`, `useWakeLock.js`, `useDevicePrefs.js`, `usePinchZoom.js`.
- `utils/`:
  - `tableFilters.js`: filtro Mías/Todas, `hasPending`, `isMine`;
  - `zoom.js`: límites y paso de zoom;
  - `connectivity.js`: `connectivityReducer`;
  - `postLogin.js`;
  - con sus `*.test.js`.

**Cambios en `frontend/src/pos/`:**
- `ui/Modal.jsx`: modo hoja más el "atrás" del teléfono.
- `ui/ModalPresentation.js`: contexto y `useModalPresentation`.
- `hooks/useBackToClose.js`.
- `sale/SalePanel.jsx` (`variant`), `sale/SaleHeader.jsx` (`closeLabel`).
- `modals/PaymentModal.jsx` (teclado en pantalla según el modo), `modals/AddProductsModal.jsx` (autofoco según el modo), `modals/OpenTableModal.jsx` (`allowWaiterPick`).
- `floor/TableTile.jsx` (`dimmed`).
- `hooks/usePosChanges.js` (`onResult`).
- `layout/PosLayout.jsx` (aviso para pantallas angostas).

**Fuera de `pos/` y `camarero/`:**
- `App.jsx` (rutas).
- `components/ProtectedRoute.jsx` (`state.from`).
- `context/AuthContext.jsx` (`login` devuelve los módulos).
- `pages/Login.jsx` (destino con `postLogin`).
- `services/api.js` (excepción del 403 y ruta de origen tras un 401).
- `components/layout/Sidebar.jsx`.
- `vite.config.js` (PWA), `src/main.jsx` (nada: el registro lo hace `UpdateBanner`).
- `public/site.webmanifest`, `index.html` (`viewport-fit=cover`).

### `useBackToClose` (el "atrás" cierra la hoja)

- **Al montarse una hoja:** `history.pushState({ ...history.state, posSheet: id }, '')`. Conserva `idx`, `key` y `usr` de React Router, así el router no ve un cambio de ruta.
- **`popstate`:** si la entrada actual ya no es la de esta hoja, llama a `onClose`.
- **Al cerrarse por botón o ✕:** si la entrada actual sigue siendo la de esta hoja, `history.back()` la quita.
- **Hojas apiladas** (cobro y luego anular un pago): cada una tiene su entrada; el "atrás" cierra la de arriba.
- Solo se activa en modo hoja. En la caja no cambia nada.

### Backend

`backend/app/routes/pos_floor.py`: helper `_pending_counts(sale_ids)` y el campo `pending_count` en cada venta de `floor`.

## Pruebas y verificación

### Backend (pytest, TDD)

- `GET /floor` devuelve `pending_count`:
  - con pendientes;
  - en 0 sin pendientes;
  - sin contar confirmados ni anulados;
  - con dos ventas en una mesa, cada una con su cuenta.
- El plano usa una cantidad fija de consultas para `pending_count`, sin importar cuántas ventas haya (conteo de sentencias con un listener `before_cursor_execute`).
- Sin fallas nuevas respecto de la línea base (`backend/scripts/compare_baseline.py`).

### Frontend (Vitest)

- `tableFilters`: Mías con y sin ventas propias; libres incluidas; varias cuentas; `hasPending`.
- `zoom`: límites de 1× a 3× y paso.
- `connectivityReducer`:
  - un fallo de red no cambia el estado; dos seguidos pasan a sin conexión;
  - un 4xx o 5xx no cuenta y reinicia el contador;
  - `offline` pasa a sin conexión de inmediato;
  - `online` no reconecta solo;
  - `poll-ok` reconecta.
- `postLogin`:
  - `Camarero` sin `POS` va a `/camarero`;
  - admin y `POS` van a `/dashboard`;
  - `state.from` gana sobre `sessionStorage`, y este gana sobre el destino por permisos;
  - no se vuelve a `/login`.
- `npm test` y `npm run build` OK. El build genera `sw.js`.
- `npm run lint` no se usa: el proyecto no tiene configuración de ESLint (hallazgo del 1b).

### Verificación manual

En el preview del navegador con viewport móvil (375×812), con el backend local de preview (SQLite, `seed_pos_demo.py` con `POS_DEMO_SEED=1`):

1. Login como usuario `Camarero` sin `POS` → `/camarero`.
2. Lista y Plano (zoom), Mías y Todas, cambio de salón; recargar conserva las preferencias.
3. Abrir una mesa (sin selector de mozo) → se abre "Agregar productos" en hoja inferior; cargar con variante, modificadores y nota; confirmar la tanda.
4. El punto de pendientes aparece en la tarjeta antes de confirmar.
5. Pedir la cuenta, dividir (pestañas de cuentas) y mover de mesa con `MoveSheet`.
6. Con `Cobrar`: cobrar en efectivo con vuelto, sin teclado en pantalla, y ver "Venta cerrada" → vuelve a mesas. Sin `Cobrar`: no aparece el botón.
7. Con `Anular`: anular un ítem confirmado con un motivo del catálogo.
8. El "atrás" del navegador cierra la hoja abierta sin salir de la venta.
9. La caja (`/pos`) en otra pestaña ve los cambios del celular en unos 3 s, y al revés.
10. DevTools en modo offline: banda, toques bloqueados, recuperación al volver la red.
11. La caja en escritorio sigue igual: modales centrados, `Escape` cierra, panel lateral de 400 px.
12. Build de producción con `vite preview`: el manifest es instalable (DevTools → Application) y el aviso de versión nueva aparece después de un segundo build.

## Fuera de alcance

- Modo offline con cola de acciones.
- PIN y dispositivos compartidos.
- Notificaciones push (por ejemplo, "pedido listo"): van con cocina (3).
- Comanda, precuenta e impresión (3).
- Ventas de mostrador desde el celular.
- Editar el plano desde el celular.
