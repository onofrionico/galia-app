# MercadoPago integrado (sub-proyecto 5) — diseño

**Estado:** aprobado en conversación el 2026-10-15. Rama `feature/pos-mercadopago` (sale de `main` en `d44ca14`).

## Contexto y objetivo

Galia ya es el POS del café (sub-proyectos 0–4 en producción: ventas, caja, Camarero, cocina e impresión, facturación ARCA).

**Cómo es hoy con MercadoPago:**
- MercadoPago es un medio de pago que la caja carga a mano ("MercadoPago", marcado "lo factura otro sistema").
- El café tiene **un Point Smart**, y los mozos lo **llevan a la mesa** para cobrar.

**Objetivos:**
1. **Cobro integrado con el Point:** desde la caja o desde el celular del mozo (Camarero, con "Cobrar"), Galia manda el monto al Point. El mozo cobra en la mesa y el pago se registra solo en la venta.
2. **Conciliación:** comparar todo lo que entra a la cuenta de MercadoPago con los pagos de MercadoPago cargados en Galia, y resolver las diferencias desde Galia.

**Criterios de éxito:**
- Un cobro aprobado en el Point queda registrado **una sola vez** en la venta correcta, sin tipear nada, aunque el aviso de MercadoPago llegue tarde, dos veces o no llegue.
- Anular un pago del Point permite devolver el dinero en MercadoPago desde Galia, y nunca anula en Galia una devolución que MercadoPago rechazó.
- Para cada día, la conciliación muestra qué coincide, qué está solo en MercadoPago y qué está solo en Galia, y deja todo resuelto con nota y autor.

## Decisiones

| Tema | Decisión |
|---|---|
| Alcance | Cobro integrado con Point Smart y conciliación. |
| Terminales | Una (Point Smart) en modo PDV. El modelo admite elegir otra terminal en la configuración. |
| Desde dónde se cobra | Caja y Camarero (POS o "Cobrar"). |
| Monto | Saldo por defecto, editable (pagos parciales). |
| API | **API de Órdenes** de MercadoPago (`POST /v1/orders`, `type: "point"`), con webhook firmado y consulta de respaldo. |
| Conciliación | Todos los movimientos de la cuenta (búsqueda de pagos) contra los pagos de medios marcados "Es de MercadoPago". Se resuelve desde Galia: asociar, crear pago, "no es una venta" o "revisado". |
| Devolución | Al anular, se elige "Devolver también en MercadoPago" (reembolso total por API) o "Solo anular en Galia". |
| Permisos | Cobrar: POS o "Cobrar". Devolver: "Anular". Conciliación: módulo nuevo **"Conciliar"**. Configuración: admin. |
| Cliente HTTP | Propio con `requests` (sin SDK), como el de ARCA. |

## Arquitectura

```
Caja / Camarero ──POST /mp/sales/<id>/point──▶ point_service ──▶ mp_client ──REST──▶ api.mercadopago.com
      ▲   └──GET /mp/point-orders/<id> (cada 3 s)──▶ refresh ──┘                           │
      │                                                                                     │ webhook firmado
      └── venta cerrada ◀── payment_service.add_payment ◀── apply_order (idempotente) ◀────┘
Conciliación ──▶ reconciliation_service ──▶ mp_client.search_payments ──▶ mp_movements / mp_reconciliations
```

**Paquete nuevo `backend/app/services/mercadopago/`:**
- `client.py`: `MpClient(access_token)` sobre `requests`, con errores tipados (`MpUnavailable`, `MpRejected(status, message, cause)`) y timeouts de 5 s para la conexión y 20 s para la respuesta. Expone:
  - terminales: `list_terminals()`, `set_pdv_mode(terminal_id)`;
  - órdenes: `create_order(...)`, `get_order(id)`, `cancel_order(id)`;
  - pagos: `get_payment(id)`, `search_payments(begin, end, offset)`, `refund(payment_id, idempotency_key)`;
  - cuenta: `me()`.
- `fake.py`: `FakeMercadoPago` (mismos métodos, en memoria). Solo se activa con `MP_FAKE=1` **y** base SQLite.
- `settings.py`: configuración, cifrado de los tokens (Fernet derivada de `SECRET_KEY`, igual que la clave de ARCA, con `info=b'galia-mp-token'`), `get_client()` y `missing()`.
- `point_service.py`: crear, refrescar, aplicar y cancelar órdenes de Point.
- `webhook.py`: verificación de firma y despacho.
- `refund_service.py`: devolución al anular un pago.
- `reconciliation_service.py`: traer movimientos, cruces, sugerencias y resoluciones.

## Datos

Migración `b5b0_add_mercadopago` (`down_revision = 'b5a0_expenses_fudo_link'`, reencadenada al mergear el PR #19).

### `mp_settings` (una sola fila, `id = 1`)

- `environment` (`test` | `production`, por defecto `test`).
- `test_access_token` y `prod_access_token`: texto cifrado.
- `terminal_id` (string): la terminal en uso.
- `webhook_secret`: texto cifrado.
- `point_payment_method_id`: FK a `payment_methods`, el medio "MercadoPago Point".
- `user_id`: id de la cuenta de MercadoPago, de `me()`, para mostrar.
- `updated_at`.

### `payment_methods.is_mercadopago`

- Boolean, no nulo, por defecto `false`.
- La migración lo pone en `true` para los medios cuyo nombre contiene "mercado" (sin importar mayúsculas).
- Se edita en Ajustes del POS → Medios de pago.

### `mp_point_orders`

- **Venta y monto:** `sale_id` (FK), `amount` (Numeric).
- **Identificación en MercadoPago:**
  - `terminal_id`;
  - `mp_order_id` (único, nulo hasta que MercadoPago responde);
  - `external_reference` (`galia-venta-<sale_id>-<id>`);
  - `idempotency_key` (UUID, único).
- **Estado:**
  - `status` (`creating`, `created`, `processing`, `approved`, `failed`, `canceled`, `expired`);
  - `status_detail`, el motivo de MercadoPago (por ejemplo, rechazada);
  - `error`: texto para la caja.
- **Resultado:** `mp_payment_id`, `payment_id` (FK a `pos_payments`, el pago de Galia creado).
- **Auditoría:** `created_by`, `created_at`, `updated_at`, `last_checked_at`.
- **Índices:** en `sale_id`, y un índice único parcial en `terminal_id` donde `status IN ('creating', 'created', 'processing')`: **un cobro activo por terminal**.

### `pos_payments.mp_payment_id`

- String, nulo; índice no único (una devolución parcial futura puede repetirlo).
- Lo completan los pagos del Point y los que se crean o asocian desde la conciliación.

### `mp_movements`

- **Identificación:** `mp_payment_id` (único), `date_created` (UTC), `business_date` (fecha Argentina).
- **Importes:**
  - `amount`: lo cobrado, Numeric;
  - `refunded_amount`, Numeric;
  - `net_amount`: lo que llega a la cuenta, si viene;
  - `currency`.
- **Detalle del movimiento:**
  - `status` (`approved`, `refunded`, `charged_back`, `cancelled`, `rejected`, …), `status_detail`;
  - `channel`: de dónde vino (`point`, `qr`, `link`, `transfer`, `other`), derivado de `point_of_interaction.type` y `payment_type_id`;
  - `payment_type`, `payment_method`;
  - `description`, `external_reference`, `payer_label` (texto corto, sin datos sensibles);
  - `raw`: JSON con los campos usados, nunca datos de tarjeta.
- **Control:** `fetched_at`.

### `mp_reconciliations`

- `mp_movement_id` (FK, nulo) y `payment_id` (FK a `pos_payments`, nulo).
- `kind`:
  - `matched_auto`: por id;
  - `matched_manual`: asociado a mano;
  - `payment_created`: se creó el pago desde la conciliación;
  - `not_a_sale`: el movimiento no es una venta;
  - `reviewed`: pago de Galia sin movimiento, revisado.
- `note`, `created_by`, `created_at`.
- **Restricciones:** un movimiento tiene como máximo una resolución, y un pago también (índices únicos parciales en cada FK no nula).

### Módulo de permisos `Conciliar`

Se crea con un insert idempotente en la migración, como los demás módulos.

## Cobro con Point

### Crear (`point_service.start(user, sale_id, amount)`)

1. **Permiso:** POS o "Cobrar".
2. **Configuración:** completa (token del entorno, terminal y medio Point); si no, "Falta configurar MercadoPago: <qué>".
3. **Venta:** `load_sale` con lock.
   - Tiene que estar `billing`, o ser de mostrador y estar `open`. Una mesa abierta pide antes la cuenta, igual que `pay` en el frontend.
   - `0 < amount ≤ balance`.
4. **Inserción `creating`:** se inserta la orden en estado `creating` con `idempotency_key` y se confirma la transacción. El índice único parcial rechaza un segundo cobro activo en la terminal: 409 "El Point está cobrando <lugar> ($X): esperá o cancelalo".
5. **Pedido a MercadoPago:** `client.create_order(...)` con:
   - `type: "point"`, `external_reference`;
   - `transactions.payments: [{amount}]`;
   - `config.point.terminal_id`, `print_on_terminal: "no_ticket"`;
   - y el header `X-Idempotency-Key`.
6. **Respuesta:**
   - **Correcta:** `mp_order_id` y estado `created`, y se confirma.
   - **`MpUnavailable`:** se reintenta **una vez con la misma clave de idempotencia**; si vuelve a fallar, `failed` con "MercadoPago no responde". La clave hace seguro el reintento.
   - **`MpRejected`:** `failed` con el motivo, por ejemplo "La terminal no está en modo PDV".

### Aplicar el resultado (`point_service.apply(order_id)`, idempotente)

Lo usan el webhook y el refresco:

1. Bloquea la fila de `mp_point_orders` (`FOR UPDATE`). Si ya está en estado final, no hace nada.
2. Consulta `client.get_order(mp_order_id)` y traduce el estado:
   - `processed` con pago `approved`: **approved**;
   - `at_terminal`: `processing`;
   - `canceled`: `canceled`;
   - `expired`: `expired`;
   - `failed`, o pago `rejected`: `failed` con `status_detail`.
   La tabla de traducción vive en `client.py` y la cubren los tests.
3. **Si queda approved:**
   - toma `mp_payment_id` y el monto del pago;
   - crea el pago con `payment_service.add_payment(...)`: medio "MercadoPago Point", el **monto aprobado** y `client_request_id = 'mp-order-<id>'`. Ese `client_request_id` único es la segunda red contra duplicados;
   - guarda `mp_payment_id` en el pago y `payment_id` en la orden.
   - Si la venta ya no admite el pago (anulada o con saldo menor), el pago se registra igual hasta el saldo disponible. Si queda excedente, se marca la orden con `error` "Cobrado de más: $X, revisalo en Conciliación" y se audita. **El dinero cobrado nunca se pierde de vista.**
4. Confirma la transacción.

### Refrescar (`GET /mp/point-orders/<id>`)

Devuelve la orden. Si no está en estado final y `last_checked_at` tiene más de 5 s, llama a `apply` (consulta de respaldo). El frontend pregunta cada 3 s mientras muestra la espera.

### Cancelar (`POST /mp/point-orders/<id>/cancel`)

- Solo en `created`. Llama a `client.cancel_order`.
- Si MercadoPago responde que ya está en proceso, 409 "El cobro ya se está procesando en el Point: esperá el resultado", y se refresca.
- **Expiración local:** si una orden sigue `created` 10 minutos después de creada, el refresco la cancela en MercadoPago y la marca `expired`.

### Webhook (`POST /api/v1/mercadopago/webhook`, sin login)

1. **Firma:** verifica el header `x-signature` (`ts` y `v1`). Calcula un HMAC-SHA256 con el secreto sobre el *manifest* `id:<data.id>;request-id:<x-request-id>;ts:<ts>;`, según la documentación de MercadoPago. Si la firma no es válida: 401 y log.
2. **Despacho:** si el evento es de órdenes, busca `mp_point_orders` por `mp_order_id` y llama a `apply`. Cualquier otro evento responde 200 sin hacer nada.
3. **Respuesta:** siempre 200 rápido. Los errores internos van al log, y el refresco lo resuelve después.

## Devolución al anular

En `POST /pos/payments/<id>/cancel` se agrega el campo `refund_mp` (bool). Solo se tiene en cuenta si el pago tiene `mp_payment_id`.

- **`refund_mp=true`:**
  1. `refund_service.refund(payment)` llama a `client.refund(mp_payment_id, idempotency_key = 'refund-<payment_id>')`, **antes** de anular en Galia.
  2. **Si MercadoPago la acepta**, se anula como siempre (`payment_service.cancel_payment`) y se audita `mp_refund_id`.
  3. **Si la rechaza**, 409 "MercadoPago rechazó la devolución: <motivo>", y no se anula nada.
  4. **Si no responde**, 409 "MercadoPago no responde: no se anuló el pago".
- **`refund_mp=false`:** se anula como hoy.

**Frontend:** el modal de motivo de anulación del pago muestra, si el pago tiene `mp_payment_id`, las opciones "Devolver también en MercadoPago" (marcada) y "Solo anular en Galia".

## Conciliación

### Traer el día (`reconciliation_service.fetch(day)`)

- Pagina `search_payments` entre las 00:00 y las 23:59:59 de Argentina, en UTC, con `sort=date_created`.
- Hace upsert en `mp_movements` por `mp_payment_id`.
- Devolver o volver a traer el día actualiza estados y montos devueltos sin duplicar.
- Trae como máximo 1.000 movimientos por día. Si hay más, avisa.

### Cruces del día (`reconciliation_service.day(day)`)

**Movimientos:** los del día con `status` `approved`, `refunded`, `charged_back` o `partially_refunded`. Los `rejected` y `cancelled` se muestran aparte, plegados, porque no movieron dinero.

**Pagos de Galia:** los pagos del día con medio `is_mercadopago`, activos o anulados. Un pago anulado con movimiento devuelto también es una coincidencia.

**Coincidencias:**
- **automática:** el pago tiene un `mp_payment_id` igual al del movimiento;
- **manual:** hay una resolución `matched_manual` o `payment_created`.

**Tres listas:**
- **Coinciden.** Cada fila muestra diferencias de monto si las hay (por ejemplo, una devolución parcial hecha afuera).
- **Solo en MercadoPago.** Cada fila trae **sugerencias**: pagos de Galia sin cruzar, con el mismo monto y una diferencia de hora de ±15 min.
- **Solo en Galia.**

Los totales se muestran por lista y por canal.

**Estado del día:** "conciliado" si no quedan elementos sin resolver.

### Resoluciones

Cada resolución lleva nota opcional y registra quién y cuándo.

- **Asociar:** el movimiento se cruza con un pago de Galia sin cruzar. Se guarda `matched_manual` y se completa `mp_payment_id` en el pago.
- **Crear pago:** se crea el pago en una venta elegida (ventas del día, cerradas o en cobro) con el medio "es de MercadoPago" elegido y el monto del movimiento, por `payment_service.add_payment` con `client_request_id = 'mp-mov-<id>'`. Queda la resolución `payment_created`. Si la venta está cerrada, el pago se rechaza por la regla actual ("supera el saldo"): en ese caso se usa "Asociar" o "No es una venta".
- **No es una venta:** `not_a_sale`, con nota obligatoria.
- **Revisado** (pago de Galia sin movimiento): `reviewed`, con nota obligatoria.
- **Deshacer:** borra la resolución. Un pago creado desde la conciliación se anula aparte, con el flujo normal.

## API (prefijo `/api/v1`)

| Método y ruta | Permiso | Qué hace |
|---|---|---|
| `POST /mp/sales/<id>/point` `{amount}` | POS o Cobrar | Crea el cobro en el Point |
| `GET /mp/point-orders/<id>` | POS o Cobrar | Estado (con refresco de respaldo) |
| `POST /mp/point-orders/<id>/cancel` | POS o Cobrar | Cancela el cobro en curso |
| `GET /mp/sales/<id>/point-orders` | POS o Cobrar | Cobros de Point de la venta (para "Cobro pendiente") |
| `POST /mercadopago/webhook` | público, con firma | Avisos de MercadoPago |
| `POST /pos/payments/<id>/cancel` `{…, refund_mp}` | Anular | Anula, con devolución opcional |
| `POST /mp/reconciliation/<day>/fetch` | Conciliar | Trae los movimientos del día |
| `GET /mp/reconciliation/<day>` | Conciliar | Cruces, sugerencias y totales |
| `GET /mp/reconciliation?from&to` | Conciliar | Resumen por día (estado y diferencias) |
| `POST /mp/reconciliation/resolutions` `{kind, movement_id?, payment_id?, sale_id?, payment_method_id?, note}` | Conciliar | Resolver |
| `DELETE /mp/reconciliation/resolutions/<id>` | Conciliar | Deshacer |
| `GET` / `PUT /mp/settings` | admin | Configuración, sin tokens |
| `PUT /mp/settings/token` `{environment, access_token}` | admin | Guarda el token cifrado y verifica con `me()` |
| `GET /mp/settings/terminals` | admin | Terminales de la cuenta |
| `POST /mp/settings/terminals/<id>/pdv` | admin | Pasa la terminal a modo PDV |
| `POST /mp/settings/test` | admin | Prueba la conexión y la terminal |

**Venta:** `sale_to_dict` suma `point_order: {id, status, amount} | null`, con el cobro de Point activo si lo hay, para el aviso "Cobro en Point pendiente".

**Pago:** `payment_to_dict` suma `mp_payment_id`.

## Interfaz

### Ajustes → MercadoPago (admin)

Tarjetas con estado:
- **Entorno:** prueba o producción.
- **Token:** pegar el access token de la integración y guardarlo; Galia verifica y muestra la cuenta.
- **Terminal:** buscar las terminales, elegir una y, si hace falta, "Pasar a modo PDV".
- **Webhook:** la URL para copiar y el campo para la clave secreta.
- **Medio de pago del Point:** se elige o se crea "MercadoPago Point".
- **Probar conexión.**

### Modal de cobro (caja y Camarero)

Si el medio elegido es el del Point:
1. El botón principal pasa a **"Enviar al Point"**.
2. Al enviarlo, la vista de espera muestra el monto, "Esperando el cobro en el Point…", el tiempo transcurrido y **Cancelar**.
3. **Resultado:**
   - aprobado: sigue el flujo normal (venta cerrada, vuelto 0);
   - rechazado, expirado o cancelado: el mensaje, con **Reintentar** y **Elegir otro medio**.

**Si se cierra el modal** durante la espera, la venta muestra el aviso **"Cobro en Point pendiente · $X"**, con **Ver** (reabre la espera) y **Cancelar**.

### Anular pago

Si el pago tiene `mp_payment_id`, el modal de motivo suma las opciones de devolución.

### Finanzas → Conciliación MercadoPago (Conciliar)

- **Calendario del mes** con el estado de cada día: conciliado, con N diferencias o sin traer.
- **Al abrir un día:**
  - el botón **Traer de MercadoPago**;
  - las tres listas con totales, la acción de cada fila y las sugerencias;
  - los movimientos rechazados, plegados.

### Ajustes del POS → Medios de pago

Columna nueva **"Es de MercadoPago"**.

## Errores (mensajes)

| Situación | Mensaje |
|---|---|
| Configuración incompleta | "Falta configurar MercadoPago: <qué falta>" |
| MercadoPago no responde | "MercadoPago no responde, probá de nuevo" |
| Terminal no disponible o fuera de modo PDV | "El Point no está listo para recibir cobros: revisá que esté prendido y en modo PDV" |
| Terminal ocupada | "El Point está cobrando <lugar> ($X): esperá o cancelalo" |
| Monto inválido | "El monto tiene que ser mayor a 0 y no superar el saldo ($X)" |
| Rechazo del pago | "El pago fue rechazado en el Point: <motivo legible>" |
| Cancelación tardía | "El cobro ya se está procesando en el Point: esperá el resultado" |
| Devolución rechazada | "MercadoPago rechazó la devolución: <motivo>" |

## Pruebas

- **`client.py`:** traducción de estados, armado de pedidos con idempotencia y errores tipados. Usa respuestas grabadas, sin red.
- **`FakeMercadoPago`:**
  - el ciclo completo (crear, procesar, aprobar, rechazar, expirar, cancelar);
  - reintento con la misma clave de idempotencia;
  - un cobro por terminal y monto mayor al saldo.
- **Idempotencia:**
  - webhook duplicado, y webhook más refresco: un solo pago;
  - aprobado con un monto distinto del pedido;
  - aprobado sobre una venta anulada (excedente marcado).
- **Webhook:** firma válida, firma inválida (401) y evento desconocido (200).
- **Devolución:** aceptada (anula), rechazada (no anula), "solo Galia", e idempotencia de la clave.
- **Conciliación:**
  - traer y volver a traer sin duplicar;
  - cruce automático por id y sugerencias por monto y hora;
  - las cuatro resoluciones y deshacer;
  - el estado del día y los totales;
  - los rechazados aparte.
- **Permisos:** por endpoint, incluido "Conciliar".
- **PostgreSQL** (con `POS_PG_TEST_URL`): webhook y refresco aplican la misma orden aprobada en paralelo, y queda un solo pago.
- **Entorno de prueba de MercadoPago (opcional):** un test marcado que corre solo con `MP_TEST_TOKEN` y `MP_TEST_TERMINAL`. Crea y cancela una orden real de prueba.
- **Frontend (Vitest):** la lógica pura del estado del cobro (transiciones y mensajes) y el resumen de la conciliación.
- **Verificación manual:** preview SQLite con `MP_FAKE=1`, más una pantalla de debug solo con el fake ("Simular en el Point: aprobar / rechazar") para recorrer el flujo en la caja y en Camarero. Después, una prueba real en el entorno de prueba de MercadoPago con el Point del local.

## Fuera de alcance

- QR dinámico en la caja.
- Links de pago y pago desde la mesa por el cliente.
- Varias terminales a la vez.
- Propinas.
- Devoluciones parciales.
- Conciliación de comisiones, retenciones y liquidaciones (`net_amount` se guarda, pero no se concilia).
- Transferencias que la búsqueda de pagos no devuelva: si en el entorno real no aparecen, se agrega en otro ciclo con los reportes de movimientos de la cuenta.
