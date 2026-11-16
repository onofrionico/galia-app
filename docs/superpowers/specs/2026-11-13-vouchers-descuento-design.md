# Vouchers de descuento — diseño

Fecha: 2026-11-13 · Estado: pendiente de aprobación

## Intención y por qué

Galia Café regala vouchers impresos como premio en concursos (sorteos de Instagram, etc.) para promocionar el negocio. Cada voucher es un papel físico con un código único. En caja se ingresa el código y se descuenta de la cuenta. Un voucher canjeado no se puede volver a usar, y una fotocopia o una foto del código tampoco sirve: el primer canje gana y los siguientes se rechazan.

## Objetivos

- Crear **tandas** de vouchers (nombre del concurso, cantidad, monto, vencimiento) y generar un código único por voucher.
- Imprimir una tanda en hojas con la marca de Galia, varios vouchers por página, desde el navegador (sin QZ Tray).
- Canjear en el POS con el código: se aplica como un descuento más de la venta, con auditoría.
- Garantizar a nivel de base de datos que un voucher no se canjea dos veces, ni siquiera desde dos cajas a la vez.
- Saber de qué tanda sale cada voucher y cuánto rindió cada concurso (emitidos, canjeados, descuento total otorgado).

## No-objetivos

- Descuentos en porcentaje o producto gratis. Solo monto fijo en esta etapa (decisión del usuario: opción A).
- Escaneo del QR con cámara en caja. El papel lleva el QR, pero en caja se tipea el código; el escaneo queda para después.
- Vouchers digitales, envío por mail o WhatsApp, o vincular un voucher a un cliente de Cafecitos.
- Impedir físicamente la fotocopia. Solo garantizamos que no se pueda canjear dos veces.

## Anti-objetivos

- Que el código sea adivinable o secuencial (alguien podría probar códigos y canjear premios ajenos).
- Que una venta cancelada deje el voucher "quemado" para siempre.
- Que el canje dependa de que el frontend valide: toda regla se valida en el backend.

## Restricciones

- galia-app: backend Flask + SQLAlchemy + Flask-Migrate, frontend React; se despliega solo en Render al mergear a `main`.
- Valores de negocio sin hardcodear: monto, vencimiento, mínimo de consumo y textos de condiciones se configuran en cada tanda.
- Acciones destructivas con rastro: anular un voucher guarda quién, cuándo y por qué. No hay borrado físico.
- Migraciones: cadena actual de `main` termina en `b7c0_production_forecast`; la nueva se cuelga de ahí (hay que re-verificar la cabeza antes de abrir el PR).
- Horarios en hora Argentina (UTC-3). El POS guarda `datetime.utcnow()`.

## Enfoques considerados

1. **Módulo propio de vouchers que genera un descuento del POS** (elegido). Tandas y vouchers en tablas propias. El canje crea un `PosDiscount` enlazado al voucher. Reutiliza el cálculo de totales, la auditoría y las reglas de venta que ya existen.
2. **Un código genérico por concurso, reutilizable.** Más simple, pero no cumple "no se puede reutilizar ni copiar" y no permite saber quién canjeó cada uno. Descartado.
3. **Servicio externo de cupones (Shopify, Stripe, etc.).** Descartado: el usuario prefiere desarrollos propios dentro del repo.

Elegido: 1, aprobado por el usuario en la conversación.

## Diseño

### Datos

- `voucher_batches`: `id`, `name`, `amount` (Numeric 12,2), `min_sale_amount` (nullable), `expires_at` (fecha, vale hasta el fin de ese día en hora Argentina), `terms` (texto de condiciones que se imprime), `quantity`, `created_by`, `created_at`.
- `vouchers`: `id`, `batch_id`, `code` (único), `voided_at`, `voided_by`, `void_reason`, `created_at`.
- `pos_discounts.voucher_id` (FK nullable a `vouchers`), con **índice único parcial** sobre `voucher_id` donde `cancelled_at IS NULL`. Esto es lo que impide dos canjes activos del mismo voucher.
- No se guarda un "estado canjeado" en el voucher: se **deriva** de si existe un `PosDiscount` activo enlazado, y de si la venta está abierta, en cobro o cerrada. Así no hay estados que se desincronicen.

### Estados que ve el usuario

Disponible · En uso (aplicado a una venta todavía abierta o en cobro) · Canjeado (la venta está cerrada) · Vencido · Anulado.

### Código

10 caracteres aleatorios (unos 49 bits), que se muestran como `GAL-XXXXX-XXXXX`. Alfabeto sin caracteres confusos (sin 0/O, 1/I/L). Se genera con `secrets`. En caja se normaliza lo que se tipea (mayúsculas, sin guiones ni espacios). Un código inexistente da el mismo mensaje que uno inválido, sin revelar nada.

### Canje en el POS

Servicio nuevo en el estilo de `discount_service.add_discount`:

1. Bloquea la venta (`load_sale`) y exige estado abierta o en cobro.
2. Busca el voucher por código. Rechaza con mensaje claro si: no existe, está anulado, está vencido, ya está aplicado o canjeado (dice cuándo y en qué venta), o la venta no llega al mínimo de consumo de la tanda.
3. Crea un `PosDiscount` de tipo `amount`, alcance venta, `voucher_id` seteado, motivo "Voucher <nombre de la tanda>".
4. Recalcula con `recalc`. El monto del voucher queda **tapado por lo que resta de la venta**: no hay vuelto ni saldo a favor, y la diferencia se pierde.
5. Registra la auditoría `voucher_redeemed`, ejecuta `close_if_settled` y commitea.

Si dos cajas aplican el mismo código a la vez, el índice único hace fallar a la segunda, y el servicio lo traduce al mensaje "ya está en uso".

Un voucher no se puede aplicar dos veces a la misma venta ni usarse en más de una venta a la vez. Se permiten varios vouchers distintos en una misma venta.

### Cuándo se libera

El voucher vuelve a estar disponible cuando su descuento se anula: porque la cajera lo quita antes de cobrar, o porque se cancela la venta (`cancel_sale_rows` ya anula los descuentos). Si se anula un pago de una venta cerrada, la venta vuelve a "en cobro" y el descuento se puede quitar, con lo que el voucher también se libera. Quitar un descuento de voucher exige un motivo y queda auditado.

### Permisos

- Módulo nuevo `Vouchers`: crear tandas, imprimir, anular y ver el reporte. Al principio solo el admin; después se puede dar a otros usuarios.
- **Canjear** lo puede hacer cualquiera que pueda cobrar en el POS (módulo `Cobrar`), sin necesidad del permiso `Descuentos`: el código es la autorización.
- Los cambios de configuración de una tanda (por ejemplo extender el vencimiento) quedan en un historial con quién y cuándo. Nunca se edita el monto de una tanda ya impresa.

### API (backend)

- `POST /api/v1/vouchers/batches`: crea tanda y genera los códigos en una sola transacción.
- `GET /api/v1/vouchers/batches` y `GET /api/v1/vouchers/batches/<id>`: listado con emitidos, canjeados y descuento total, y detalle con cada código y su estado. El detalle también alimenta la hoja imprimible, por eso no hay una ruta aparte de impresión.
- `PUT /api/v1/vouchers/batches/<id>`: extiende el vencimiento (queda en el historial).
- `POST /api/v1/vouchers/<id>/void`: anula con motivo.
- `POST /api/v1/vouchers/pos-sales/<sale_id>/redeem`: canje por código.

### Frontend

- Página admin "Vouchers": lista de tandas con sus números, formulario de nueva tanda, detalle con la lista de vouchers y sus estados, y botón imprimir.
- Hoja de impresión: ocho vouchers por A4, con logo y colores de Galia, monto, vencimiento, condiciones, código en letra grande y QR con el código. Se imprime con el diálogo del navegador (hay `window.print` y `@media print` ya usados en la app para la grilla de horarios). Para el QR, una librería chica de generación de QR en el cliente.
- En el POS: en el modal de descuento de la venta (`DiscountModal`), un campo "Código de voucher" con botón Canjear, visible para quien tenga permiso de cobrar. Un voucher aplicado se ve en el ticket como cualquier descuento y se puede quitar con motivo.

## Qué le queda al implementador

- Nombre exacto de rutas, módulos y archivos, siguiendo las convenciones de `pos_*` y `Fidelizacion`.
- Alfabeto y largo exactos del código, mientras sea no secuencial y con al menos ~45 bits de entropía.
- Diseño visual fino del voucher impreso (se revisa con una muestra antes de imprimir una tanda real).
- Elección de la librería de QR.

## Decisiones que tomé yo (a revisar)

- Monto fijo configurable por tanda, con mínimo de consumo opcional (por defecto sin mínimo).
- El monto sobrante se pierde si el voucher supera el total de la venta.
- Estado derivado en vez de un campo de estado en el voucher.
- Canje con permiso `Cobrar`, no `Descuentos`.
- Migración nueva `b9a0_vouchers`, colgada de `b7c0_production_forecast`, que crea las tablas, la columna y el módulo `Vouchers`.

## Verificación esperada

- Pruebas del servicio: canje feliz, código inexistente, vencido, anulado, ya canjeado, mínimo no alcanzado, venta cerrada, doble canje simultáneo, liberación al quitar el descuento y al cancelar la venta.
- Pruebas de la migración en una base de test antes de producción (conteos y reversibilidad), según la regla de migraciones del proyecto.
- Prueba del flujo real levantando la app: crear tanda, imprimir, canjear en una venta, intentar canjear de nuevo, cancelar la venta y ver que el voucher vuelve a estar disponible.
