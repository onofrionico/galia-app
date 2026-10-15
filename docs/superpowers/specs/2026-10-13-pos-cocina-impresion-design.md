# Cocina e impresión (sub-proyecto 3) — Diseño

**Fecha:** 2026-10-13
**Rama:** `feature/pos-cocina-impresion` (desde `main` en `78960e1`, con los sub-proyectos 1 y 2 y la sincronización de productos con Fudo)
**Antecede:**
- `docs/superpowers/specs/2026-10-09-pos-sales-engine-design.md` (1a)
- `docs/superpowers/specs/2026-10-10-pos-caja-design.md` (1b)
- `docs/superpowers/specs/2026-10-10-pos-camarero-design.md` (1c)
- `docs/superpowers/specs/2026-10-13-pos-caja-arqueo-design.md` (2)
- `docs/superpowers/specs/2026-10-13-products-fudo-sync-design.md` (catálogo sincronizado con Fudo)

## Contexto

El POS ya toma pedidos por tandas: al confirmar, cada ítem guarda su número de tanda (`pos_sale_items.batch`). Falta que esos pedidos lleguen a cocina y barra, y poder imprimir la precuenta y el ticket de la venta.

El local tiene impresoras térmicas de comandas. Hoy no hay pantallas de cocina, pero el diseño debe permitir sumarlas después.

El backend corre en Render (en la nube): no puede hablar directo con una impresora del local. La impresión la hace una PC del local con QZ Tray, un programa que expone las impresoras a una página web por `localhost`.

## Decisiones de producto

- **Hardware:** impresoras térmicas de comandas, extensible a pantallas de cocina (KDS) más adelante.
- **Estaciones:** una impresora por estación (por ejemplo, Cocina y Barra) más la impresora de caja para precuenta y ticket. Cada categoría de producto se asigna a una estación; una tanda se divide en una comanda por estación.
- **Conexión:** mixta. Hay impresoras de red (IP, puerto 9100) y USB (instaladas en Windows).
- **Cuándo se imprime:**
  - comanda automática al confirmar cada tanda, una por estación;
  - comanda de anulación al anular un ítem ya enviado;
  - precuenta con botón (también ofrecido al pedir la cuenta);
  - ticket no fiscal opcional al cobrar;
  - reimpresión de cualquiera desde el historial de la venta.
- **Fallas:**
  - los trabajos quedan en cola en el backend y se reintentan solos;
  - la caja muestra un aviso visible con "Reintentar" y "Marcar como impresa";
  - cada trabajo tiene estado.
- **Cómo se imprime:** una página de Galia abierta en una PC del local (`/pos/impresion`) con QZ Tray. Una sola PC de impresión (la de caja) atiende todas las impresoras de red y su USB. Una USB enchufada a otra PC necesita QZ Tray y su propia página en esa PC.

## Enfoque

Cola de trabajos de impresión en el backend, con el contenido como documento estructurado (JSON), no como bytes de impresora. La página de impresión toma los trabajos de sus impresoras, los convierte a ESC/POS y los imprime con QZ Tray (TCP a IP:9100 para las de red, nombre de Windows para las USB). Después reporta el resultado.

El mismo documento y las estaciones sirven después para una pantalla de cocina.

Se descartaron:
- **Agente propio en Python (pull):** más robusto, pero hay que escribir, empaquetar e instalar un programa.
- **WebSocket (push):** Render con gunicorn no está preparado; demasiada infraestructura para ganar unos segundos.

## Modelo de datos

Migración `b3a0_add_print_stations`, con `down_revision = 'b2b0_products_fudo_link'`.

### `print_stations`

`id`, `name` (String(60), único: "Cocina", "Barra"), `position` (Integer, por defecto 0), `is_active` (Boolean, por defecto true).

### `printers`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | PK | |
| `name` | String(60) | único |
| `connection` | String(10) | `network` o `usb` |
| `host` | String(100) | obligatorio si es `network` |
| `port` | Integer | por defecto 9100 |
| `os_name` | String(120) | nombre de la impresora en Windows; obligatorio si es `usb` |
| `paper_width` | Integer | 58 u 80 |
| `print_point` | String(60) | punto de impresión que la atiende, por ejemplo "Caja" |
| `station_id` | FK `print_stations` | nulo |
| `is_cashier` | Boolean | imprime precuenta y ticket |
| `is_active` | Boolean | |

Reglas de validación:
- Una impresora con `station_id` no puede ser `is_cashier`.
- Hay como máximo una impresora de caja activa (validado en el servicio).
- Una estación tiene como máximo una impresora activa.

### `product_categories.station_id`

FK `print_stations`, nulo. Nulo significa sin comanda. Es un campo propio de Galia: la sincronización con Fudo solo bloquea `name` e `is_active` y no lo toca.

### `print_jobs`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | PK | |
| `kind` | String(10) | `order`, `void`, `bill`, `receipt`, `test` |
| `printer_id` | FK `printers` | índice |
| `sale_id` | FK `pos_sales` | nulo (los `test` no tienen venta) |
| `station_id` | FK `print_stations` | nulo |
| `batch` | Integer | nulo; tanda de la comanda |
| `document` | JSON | ver "Documento" |
| `status` | String(10) | `pending`, `printing`, `printed`, `failed`; índice compuesto (`printer_id`, `status`, `id`) |
| `attempts` | Integer | por defecto 0 |
| `error` | String(255) | último error |
| `claimed_by` | String(60) | punto de impresión que lo tomó |
| `claimed_at`, `printed_at`, `failed_at` | DateTime | |
| `reprint_of` | FK `print_jobs` | nulo |
| `created_by` | FK `users` | |
| `created_at` | DateTime | |

### `print_points`

Latido de cada punto de impresión: `name` (PK, String(60)) y `last_seen_at` (DateTime).

## Documento

JSON con:
- `title`: "COCINA", "ANULACIÓN · BARRA", "PRECUENTA", "TICKET", "PRUEBA";
- `header`: líneas cortas como mesa o "Mostrador #n", mozo, personas, tanda, fecha y hora, y "REIMPRESIÓN" si corresponde;
- `lines`: renglones, cada uno con `qty`, `text`, `amount` (opcional), `details` (modificadores y nota como sub-renglones) y `strike` (true en anulaciones);
- `totals`: `[{label, amount}]` (subtotal, descuentos, total, pagos, vuelto);
- `footer`: líneas, por ejemplo "No válido como factura".

Los montos van en el documento ya calculados por el backend. El frontend no calcula nada.

## Reglas

### Comandas

- **Al confirmar:** dentro de `sale_service.confirm_pending` (cubre la confirmación desde la caja, desde el celular y la confirmación automática del cobro de mostrador), en la misma transacción, después de confirmar:
  - se agrupan los ítems confirmados de la tanda por estación de la categoría de su producto (`item → variant → product → category.station_id`);
  - por cada estación activa con impresora activa se crea un `print_job` `order` con un documento que lleva:
    - el título con el nombre de la estación en mayúsculas;
    - el encabezado: mesa (`label`) o "Mostrador #n", mozo, "Tanda n" y hora en Argentina;
    - un renglón por ítem: cantidad, producto, variante (si no es la única), modificadores y nota.
  - Ítems sin estación, o de una estación sin impresora activa, no generan trabajo.
- **Al anular un ítem confirmado** (`cancel_item`) y al anular una venta con ítems confirmados (`cancel_sale_rows`): un trabajo `void` por estación afectada. Título "ANULACIÓN · <ESTACIÓN>", los ítems tachados y el motivo.
  - Borrar un ítem pendiente no genera nada.
  - Dividir o mover una venta tampoco genera comanda: cocina ya tiene los ítems.
- **Mover de mesa:** no imprime nada.

### Precuenta y ticket

- **`POST /sales/<id>/print/bill`** (venta `open` o `billing` con ítems confirmados): trabajo `bill` a la impresora de caja.
  - Documento: mesa o mostrador, personas, mozo; ítems activos con importe, descuentos, subtotal y total; pie "No válido como factura".
- **`POST /sales/<id>/print/receipt`** (venta `closed`): trabajo `receipt` con lo mismo más los pagos activos (medio, monto y vuelto) y el pie.
- **Sin impresora de caja activa:** 409 "No hay impresora de caja configurada".

### Reimpresión

`POST /print/jobs/<id>/reprint` crea una copia del trabajo (mismo `kind`, impresora actual de la estación o de caja, documento con "REIMPRESIÓN" agregado al encabezado), con `reprint_of`.

### Cola

- **`POST /print/claim {print_point}`:**
  - registra el latido;
  - devuelve hasta 10 trabajos `pending` de las impresoras activas con ese `print_point`, en orden de `id`, y los pasa a `printing` con `claimed_by` y `claimed_at`;
  - usa `SELECT … FOR UPDATE SKIP LOCKED` en PostgreSQL (en SQLite, sin bloqueo) para que dos pestañas no tomen lo mismo;
  - cada trabajo devuelto incluye la conexión de su impresora (`connection`, `host`, `port`, `os_name`, `paper_width`).
- **`POST /print/jobs/<id>/done`:** pasa a `printed` con `printed_at`.
- **`POST /print/jobs/<id>/failed {error}`:** suma un intento, guarda el error y `failed_at`, y pasa a `failed`.
- **Recuperación** (se ejecuta al comienzo de cada `claim`):
  - `printing` con `claimed_at` de hace más de 60 s vuelve a `pending`;
  - `failed` con menos de 5 intentos y `failed_at` de hace más de 15 s vuelve a `pending`.
- **`POST /print/jobs/<id>/retry`:** vuelve a `pending` y reinicia los intentos.
- **`POST /print/jobs/<id>/mark-printed`:** pasa a `printed` a mano, con `claimed_by` = "manual".
- **`GET /print/status`:**
  - trabajos con problemas: `failed`, o `pending`/`printing` creados hace más de 30 s;
  - puntos de impresión con su último latido y si están caídos (más de 30 s sin señal);
  - cantidad de pendientes.
- **`GET /sales/<id>/print-jobs`:** trabajos de una venta, para el historial.

### Firma de QZ Tray

- **`GET /print/qz-certificate`:** devuelve el texto del certificado de la variable de entorno `QZ_CERTIFICATE`, o 404 si no está.
- **`POST /print/qz-sign {request}`:** firma `request` con la clave privada de `QZ_PRIVATE_KEY` (RSA, SHA-512, base64), o 404 si no está.
- Sin certificado, QZ Tray imprime igual, pero pide confirmación en cada trabajo.

### Configuración

CRUD admin en `/pos/config/print-stations` y `/pos/config/printers` (bajas lógicas), con las validaciones de `printers`. `PUT /api/v1/product-categories/<id>` acepta `station_id` (nulo o una estación activa).

## API

Blueprint `pos_print` en `/api/v1/pos`. Las rutas son delgadas y la lógica va en `services/pos/print_service.py` (cola, comandas, documentos) y `print_documents.py` (armado de documentos). Los errores van con `PosError`, como en el resto del POS.

| Ruta | Permiso |
|---|---|
| `POST /sales/<id>/print/bill`, `/print/receipt`, `POST /print/jobs/<id>/reprint`, `GET /sales/<id>/print-jobs` | `POS` o `Camarero` |
| `POST /print/claim`, `/print/jobs/<id>/done`, `/failed`, `/retry`, `/mark-printed`, `GET /print/status`, `GET /print/qz-certificate`, `POST /print/qz-sign`, `POST /print/printers/<id>/test` | `POS` |
| `/config/print-stations`, `/config/printers` | admin |

`POST /print/printers/<id>/test` crea un trabajo `test` con un documento de prueba (nombre de la impresora, ancho, línea con acentos y ñ, fecha).

## Interfaz

### Configuración

- **Ajustes del POS** (admin), solapas nuevas:
  - "Estaciones": nombre, orden, activa;
  - "Impresoras": nombre, conexión, IP y puerto o nombre en Windows, ancho, punto de impresión, estación o "impresora de caja", activa.
- **Productos → Categorías:** columna "Estación" con un selector (estaciones activas o "Sin comanda").

### POS (`/pos` y celular)

- **Indicador "Impresión"** en la barra superior del POS:
  - en rojo si `GET /print/status` reporta trabajos con problemas o un punto de impresión caído;
  - consulta cada 15 s;
  - al tocarlo abre un panel con los trabajos con problemas (venta, estación, tipo, antigüedad, error), cada uno con "Reintentar" y "Marcar como impresa", y el estado de cada punto de impresión.
- **Panel de venta:**
  - "Precuenta" en "Más";
  - después de "Pedir cuenta", un aviso con "Imprimir precuenta";
  - el resumen "Venta cerrada" suma "Imprimir ticket";
  - la pestaña Historial (o una sección "Impresiones") lista los trabajos de la venta con estado y "Reimprimir".
- **Celular:** las mismas acciones de la venta (los componentes son compartidos con el 1b). Sin indicador de impresión.

### Página de impresión (`/pos/impresion`, permiso `POS`)

- Pantalla propia, sin barra de salones.
- **Punto de impresión:** se elige en un selector con los `print_point` configurados, y queda guardado en `localStorage`.
- **Impresoras:** muestra las que atiende, con su estado.
- **Conexión con QZ Tray** (librería `qz-tray`): configura la firma con `GET /print/qz-certificate` y `POST /print/qz-sign`. Si QZ no está abierto, muestra "QZ Tray no está abierto", un botón "Reintentar" y el enlace a la guía.
- **Bucle:** cada 2 s, con `setInterval` (funciona con la pestaña oculta):
  - llama a `claim`;
  - por cada trabajo arma el ESC/POS (`escpos.js`) y lo imprime con QZ: `{host, port}` para las de red, `os_name` para las USB, datos `raw` con codificación CP858;
  - reporta `done` o `failed` con el mensaje de error.
- **Log y alertas:** log del día con los últimos 50 trabajos (hora, impresora, tipo, resultado) y un sonido corto cuando un trabajo falla.
- **"Imprimir prueba"** por impresora.
- **Modo simulación** (casilla): no usa QZ Tray. Muestra el texto de cada trabajo como saldría impreso y lo marca `done`. Sirve para probar sin impresoras.
- **Bloqueo de pantalla:** se mantiene la pantalla encendida con Wake Lock si está disponible.

### ESC/POS (`frontend/src/pos/print/escpos.js`)

Funciones puras:
- `renderText(document, width)` devuelve líneas de texto de 32 o 48 columnas. La usan la simulación y los tests.
- `renderEscPos(document, width)` devuelve un string con comandos:
  - inicialización y página de códigos CP858 (`ESC t 19`);
  - título en doble tamaño;
  - negrita en el encabezado;
  - monto alineado a la derecha;
  - corte parcial (`GS V 1`).

## Guía de instalación (`docs/pos/impresion-qz.md`)

1. Instalar QZ Tray en la PC de impresión.
2. Generar el par de claves con `openssl` (comando incluido) y cargar `QZ_CERTIFICATE` y `QZ_PRIVATE_KEY` en Render.
3. Copiar el certificado como override de QZ Tray en esa PC, para imprimir sin confirmación.
4. Dar de alta estaciones e impresoras en Ajustes del POS y asignar estaciones a las categorías.
5. Abrir `/pos/impresion`, elegir el punto de impresión y dejarla como pestaña fija de inicio de Chrome.
6. Probar cada impresora con "Imprimir prueba".

## Estructura del código

### Backend

- `backend/app/models/pos/printing.py`: `PrintStation`, `Printer`, `PrintJob`, `PrintPoint`.
- `backend/app/models/product_category.py`: `station_id`.
- `backend/app/services/pos/print_documents.py`: documentos de comanda, anulación, precuenta, ticket y prueba.
- `backend/app/services/pos/print_service.py`:
  - `jobs_for_batch(sale, items, user)`, `jobs_for_void(sale, items, user)`;
  - `print_bill`, `print_receipt`, `reprint`, `test_print`;
  - `claim`, `mark_done`, `mark_failed`, `retry`, `mark_printed`, `status`;
  - `sign_qz`.
- `backend/app/services/pos/sale_service.py`: llamadas a `jobs_for_batch` en `confirm_pending` y a `jobs_for_void` en `cancel_item` y `cancel_sale_rows`.
- `backend/app/routes/pos_print.py` (blueprint), `backend/app/routes/pos_config.py` (CRUD de estaciones e impresoras), `backend/app/routes/product_categories.py` (`station_id`).
- `backend/migrations/versions/b3a0_add_print_stations.py`.
- Dependencia `cryptography` en `requirements.txt` para la firma, salvo que ya esté.

### Frontend

- `frontend/src/pos/print/`: `escpos.js` (+ test), `printStatus.js` (+ test: regla del indicador), `qz.js` (conexión, firma, impresión), `PrintPage.jsx`, `PrintStatusBadge.jsx`, `PrintJobsList.jsx`.
- `frontend/src/pos/api/posApi.js`: `posPrintApi`.
- `frontend/src/pos/sale/*`: botones de precuenta, ticket y reimpresión.
- `frontend/src/pos/layout/PosTopBar.jsx`: indicador.
- `frontend/src/pages/admin/PosSettings.jsx`: solapas de estaciones e impresoras.
- `frontend/src/pages/ProductCategories.jsx`: columna de estación.
- `frontend/src/App.jsx`: ruta `/pos/impresion`.
- Dependencia nueva: `qz-tray` (npm).

## Pruebas y verificación

### Backend (pytest, TDD)

- **Comandas:**
  - una tanda con ítems de dos estaciones genera dos `order`, cada uno solo con sus ítems, con modificadores y nota;
  - una categoría sin estación no genera nada;
  - una estación sin impresora activa no genera nada;
  - la confirmación desde la ruta del celular y el cobro de mostrador también generan comanda.
- **Anulaciones:**
  - anular un ítem confirmado genera un `void` en su estación;
  - anular una venta genera un `void` por estación;
  - borrar un pendiente no genera nada.
- **Precuenta y ticket:**
  - documento con totales y pagos;
  - estado de la venta inválido da 409;
  - sin impresora de caja da 409.
- **Reimpresión:** copia el trabajo con `reprint_of` y la marca.
- **Cola:**
  - `claim` filtra por punto de impresión y solo toma impresoras activas, en orden, y los pasa a `printing`;
  - `done` y `failed`;
  - recuperación de `printing` vencidos y reintento de `failed` hasta 5;
  - `retry` y `mark-printed`;
  - latido y estado.
- **Concurrencia** (PostgreSQL, se saltea sin `POS_PG_TEST_URL`): dos `claim` simultáneos no reciben el mismo trabajo.
- **Configuración:**
  - validaciones de impresoras (conexión, una de caja, una por estación);
  - `station_id` en categorías;
  - la sincronización con Fudo no pisa `station_id`.
- **Firma QZ:** sin variables de entorno da 404; con un par generado en el test, la firma verifica contra el certificado.
- **Generales:**
  - permisos;
  - test de cobertura de rutas;
  - cadena de migraciones (`b3a0` después de `b2b0`);
  - sin fallas nuevas respecto de la línea base.

### Frontend (Vitest)

- `escpos`:
  - ancho de 32 y 48 columnas;
  - corte de líneas largas;
  - monto alineado a la derecha;
  - acentos y ñ en CP858;
  - corte de papel;
  - las cinco plantillas.
- `printStatus`: regla del indicador.
- `npm test` y `npm run build` OK.

### Verificación manual

En el preview sobre SQLite, con la página de impresión en modo simulación:

1. Configurar Cocina y Barra, la impresora de caja y las categorías.
2. Confirmar una tanda mixta: aparece una comanda de cada estación, cada una con solo sus ítems.
3. Anular un ítem: anulación en su estación.
4. Precuenta y ticket en caja.
5. Reimprimir con la marca.
6. Cerrar la página de impresión y confirmar una tanda: el indicador se pone rojo y el panel muestra la cola. Reabrir la página: se imprime solo.
7. "Marcar como impresa" y "Reintentar".

Con impresoras reales, la prueba se hace en el local siguiendo la guía.

## Fuera de alcance

- Pantalla de cocina (KDS): queda preparada por las estaciones, el documento JSON y los estados de los trabajos.
- Factura o ticket fiscal (sub-proyecto 4, ARCA).
- Ticket de cierre de caja "Z".
- Apertura del cajón de dinero.
- Logo e imágenes en el ticket.
- Agente de impresión propio sin QZ Tray.
