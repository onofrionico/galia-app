# Corte con Fudo (sub-proyecto 6): diseño

**Fecha:** 2026-10-20
**Rama:** `feature/pos-corte-fudo`, que sale de `main` en `d8bdc4a`, con los sub-proyectos 0 a 5 ya mergeados.

## Para qué

Galia ya reemplaza al POS de Fudo: venta, caja, cocina, facturación y MercadoPago. Este sub-proyecto es el último paso, **apagar Fudo**, y tiene que resolver las dos preocupaciones del dueño:

1. **No perder la historia.** Hoy el dueño usa Fudo para dos cosas: el POS y el **desglose de ventas por producto**, con el que compara meses ("cuánto se vendía por cada producto"). Esa historia tiene que quedar en Galia completa, desde el primer día en Fudo.
2. **Que el equipo se maneje con Galia en el día a día.** La tarea que más le preocupa es **abrir y cerrar la caja**. Hoy el dueño enseña en persona, y el equipo tiene que poder resolver cuando él no está.

## Objetivos

- Importar a Galia **toda la historia de ventas de Fudo**, con el detalle de productos de cada venta.
- Un reporte nuevo, **Ventas por producto**, que compare dos meses en cantidad y monto. Mezcla sin cortes las ventas importadas de Fudo con las del POS de Galia.
- La **carta digital** pasa a armarse con el **catálogo de Galia** y sigue actualizándose sola, como hoy.
- Un **corte ordenado**:
  - unos días de práctica;
  - el día del corte;
  - unos días en paralelo con Fudo como respaldo;
  - apagar las syncs con Fudo.
- Una **guía para el equipo** junto a la caja.

## No objetivos

- Traer de Fudo los pagos detallados, mesas, mozos o clientes de cada venta vieja, más allá de lo que ya guarda el encabezado en `sales`.
- Rehacer los reportes existentes (ventas totales, gastos, sueldos, productividad). Hay un PR aparte en curso (#23, fecha comercial).
- Migrar gastos viejos: ya están en Galia por la sync de gastos (#19, #21, #22).
- Borrar el código de integración con Fudo. Se desactiva, no se elimina, hasta que el corte esté confirmado.

## Anti-objetivos

El trabajo falla, aunque técnicamente funcione, si pasa cualquiera de estas cosas:

- Una venta queda **contada dos veces**: cargada en Fudo y en Galia, o importada dos veces. Eso infla el reporte por producto.
- Una venta de Fudo **se pierde** en la importación sin que nadie se entere.
- Las ventas de práctica **ensucian los números reales**: reportes, caja, facturación, stock o MercadoPago.
- Se pierde algo de lo que el dueño armó a mano en la carta: grupos, orden, fotos, descripciones, visibilidad.
- La carta deja de actualizarse sola después del corte.

## Restricciones y contexto

- **Stack:** Flask + SQLAlchemy 2 + Alembic, y React 18 + React Query.
- **Deploy:** en Render; `build.sh` corre `flask db upgrade`. Hay un cron diario para la carta (`render.yaml`, `0 7 * * *`, `app/tasks/menu_tasks.py`).
- **Migraciones:** la cadena termina hoy en `b5b0_add_mercadopago`. El PR #23 agrega `b5c0` y puede mergearse antes. Hay que encadenar desde la cabeza que exista al implementar y agregar el test en `tests/test_migration_chain.py`.
- **API de Fudo (v1alpha1, JSON:API):**
  - **sin `fields[...]` no devuelve atributos.** Esto se comprobó con los gastos en producción (#22).
  - `GET /sales` acepta `filter[createdAt]`, `filter[saleState]`, `include=items,items.product,payments.paymentMethod,waiter,table` y `fields[sale]`, `fields[item]` y `fields[product]`.
  - Atributos de la venta: `closedAt`, `createdAt`, `total`, `saleType`, `saleState`, `people`, `customerName`, `comment`.
  - Atributos del ítem: `quantity`, `price`, `cost`, `canceled`, `status`, `createdAt` y la relación `product`.
  - `GET /items` no se puede filtrar por fecha, así que se va por las ventas.
  - Las páginas son de hasta 500.
  - Fuente: la OpenAPI de Fudo en `github.com/api-evangelist/fudo`. **Hay que verificarlo contra la API real** antes de importar.
- **La sync de ventas actual** está en `app/routes/fudo_sync.py`, en `parse_fudo_sale` y `_sync_sales_background`:
  - no pide `fields[sale]`;
  - lee atributos que no están en la especificación (`status`, `type`, `cashRegisterName`, `userName`).
  - Probablemente importa encabezados incompletos o vacíos. Hay que verificarlo y corregirlo.
- **Vínculos que ya existen con Fudo:**
  - `ProductVariant.fudo_product_id` (PR #13);
  - `ProductCategory.fudo_category_id`;
  - `MenuItemVariant.fudo_product_id`;
  - `MenuCategory.fudo_category_id`;
  - la tabla `fudo_products`.
  - El producto de Fudo de una venta vieja se cruza con Galia por `ProductVariant.fudo_product_id`.
- **Ventas del POS de Galia:**
  - se proyectan como una fila en `sales` con `source='galia'` (`app/services/pos/projection.py`), y sus ítems están en `pos_sale_items`;
  - hoy `fecha` es la fecha UTC del cierre. El PR #23 introduce la fecha comercial; el reporte usa esa regla si #23 ya está mergeado y, si no, la misma regla de día comercial definida acá.
- **Ventas importadas de Fudo:** tienen `source='fudo'` y `external_id` igual al id de Fudo. La columna es `Integer`, así que hay que confirmar con la inspección que los ids de Fudo son numéricos.
- **Sync de productos:** hoy Fudo es la fuente de verdad del catálogo (`product_sync_service.py`), y el cron diario pisa nombre, categoría, precio y estado en Galia.

## Lo que decidió el dueño

| Tema | Decisión |
|---|---|
| Historia | Toda, desde que empezaron con Fudo, con el detalle por producto. |
| Reporte | Ranking de productos con barras, un mes contra otro (boceto "B"), con un selector de **monto** o **cantidad** y la variación en %. |
| Corte | Unos días en paralelo. **Todo se carga en Galia** y Fudo queda abierto solo por si falla. |
| Carta | Se arma con el catálogo de Galia. Los cambios de precio **se publican solos**, como hoy. La mantiene el dueño. |
| Gastos | Después del corte se cargan en Galia y los carga el dueño. |
| Aprendizaje del equipo | Lo sigue enseñando el dueño en persona, con una guía corta junto a la caja y unos días de práctica antes del corte, con ventas de prueba que no ensucien los números reales. |
| Práctica | **Modo práctica dentro de la Galia real** (no una copia aparte). |
| Monto del reporte | Cantidad × precio, **sin descontar** los descuentos de la venta. |

## Las piezas

### 1. Ventas de Fudo con su detalle

- **Verificar primero:**
  - un script de inspección, como `scripts/inspect_fudo_expenses.py`, que pide una página de ventas con `include` y `fields`;
  - imprime los atributos reales de venta, ítem y producto, sin datos de clientes;
  - el dueño lo corre con las credenciales de producción.
- **Corregir la sync de ventas** para que pida `fields[...]` y lea los atributos que de verdad manda Fudo.
- **Importar los ítems:**
  - cada venta de Fudo guarda sus ítems en una tabla propia: venta, producto de Fudo, nombre del producto, categoría, cantidad, precio, si fue anulado y la variante de Galia vinculada si existe;
  - el nombre y la categoría se guardan **al importar**, para que un producto que después desaparezca de Fudo o de Galia siga apareciendo en los reportes con su nombre.
- **Encabezados existentes** *(decisión mía)*:
  - Fudo es la fuente de verdad de sus propias ventas, así que la importación **actualiza** los encabezados que ya existen con `source='fudo'`: estado, fechas, total y demás;
  - una venta que Fudo da como anulada deja de contar;
  - la corrida informa cuántos encabezados cambiaron y en qué meses cambió el total, para que el dueño sepa que los reportes viejos se corrigieron.
- **Importación de toda la historia:**
  - recorre Fudo **mes por mes** desde la primera venta;
  - es **reanudable**: si se corta, sigue donde quedó;
  - es **idempotente**: correrla dos veces no duplica nada, porque una venta se identifica por su id de Fudo;
  - deja registro de cada corrida, con un resumen y los errores, como la sync de gastos (`fudo_sync_runs`);
  - una venta que falla no frena el resto, y queda listada para revisar.
- **Control de que no se pierde nada:** por cada mes, cuántas ventas y qué total trae Fudo contra cuántas y qué total quedaron en Galia. Se ve en la corrida.

### 2. Reporte "Ventas por producto"

- **Ubicación:** va en Finanzas o Análisis, donde quedan los reportes. Lo ve quien tiene acceso a Reportes.
- **Comparación:** se eligen dos meses (A y B). El ranking ordena los productos de más a menos según el mes B. Cada producto tiene una barra por mes y la variación en %, y arriba se elige si las barras muestran **monto** o **cantidad**.
- **Origen de los datos:**
  - los ítems importados de Fudo (`source='fudo'`) y los del POS de Galia (`pos_sale_items` de ventas cerradas), por fecha comercial;
  - las ventas y los ítems anulados no cuentan;
  - las ventas de práctica nunca cuentan.
- **Monto (decisión del dueño):** cantidad × precio de los ítems, **sin descontar** los descuentos de la venta, como en el desglose de Fudo.
  - En Galia es el total de la línea del ítem, con sus modificadores y sin el descuento por ítem.
  - La inspección confirma si el `price` de un ítem de Fudo es por unidad o por línea.
  - El control mes a mes de la importación compara las ventas por cantidad y por total de los encabezados, no por la suma de ítems, porque esa suma no da el total si hubo descuentos.
- **Producto:**
  - las variantes se suman en el producto, y se pueden desplegar para verlas por separado;
  - un ítem de Fudo con variante vinculada cuenta como ese producto de Galia;
  - un ítem sin vínculo aparece con su nombre de Fudo.
- **Detalle:** al tocar un producto se ve su detalle día por día en los dos meses.

### 3. Carta digital sobre el catálogo de Galia

- **La carta conserva su propia capa de ítems** *(decisión mía, para no perder lo armado a mano)*:
  - el nombre, la descripción, la foto y el orden de cada ítem de la carta siguen siendo los de la carta;
  - del catálogo de Galia salen el **precio** de cada variante, la **categoría** y el **estado** (activo o inactivo);
  - un ítem de la carta puede seguir agrupando variantes de productos distintos de Galia, como hoy con "Unir con otro ítem";
  - un producto nuevo en Galia crea un ítem nuevo, oculto, con el nombre del producto.
- **Paso inicial, una sola vez:**
  - cada `MenuItemVariant` con `fudo_product_id` pasa a apuntar a la `ProductVariant` de Galia con ese mismo `fudo_product_id`;
  - cada `MenuCategory` con `fudo_category_id` pasa a apuntar a la `ProductCategory` de Galia con ese id;
  - se conservan grupos, orden, fotos, descripciones, etiquetas y visibilidad;
  - lo que no tenga vínculo queda marcado para que el dueño lo revise en la bandeja de la carta.
- **Después:**
  - los precios, nombres y categorías salen del catálogo de Galia;
  - un producto nuevo en Galia entra a la carta **oculto**, para revisar, como hoy;
  - un cambio de precio se **publica solo**, como hoy con el cron, ya sea por el cron o al guardar, a criterio del constructor;
  - la carta deja de consultar a Fudo.

### 4. Modo práctica (decisión del dueño: dentro de la Galia real)

- **Qué es:** un interruptor de admin, "Modo práctica". Mientras está prendido, Galia muestra una franja bien visible, "PRÁCTICA: nada de esto cuenta", en el POS, en Camarero y en la caja.
- **Qué queda marcado:** todo lo que se crea con el modo prendido queda marcado como práctica: ventas, ítems, pagos, sesiones y movimientos de caja, y trabajos de impresión.
- **Qué funciona de verdad:** se puede abrir, operar y cerrar la caja con arqueo, cobrar en efectivo y con tarjeta como medio manual, anular, dividir y mover de mesa. Imprime la comanda y el ticket, con un encabezado "PRÁCTICA" *(decisión mía: sirve para practicar con la cocina)*.
- **Qué no funciona, a propósito** *(decisiones mías)*:
  - no se factura: el botón no aparece, y el backend lo rechaza;
  - no se cobra con el Point: es un cobro real;
  - no se mueve stock;
  - no se proyecta en `sales`;
  - no aparece en reportes, en el historial de Cajas, en la conciliación ni en el reporte por producto.
- **Cómo se protege:** cada camino que toca números reales verifica la marca, del lado del backend; el frontend solo oculta.
  - **Cubrir:** proyección, stock, facturación, MercadoPago, reportes, historial de caja y conciliación.
  - Cada uno con su test.
- **Limpieza:** "Borrar práctica" (admin) elimina todo lo marcado.
  - Solo se puede con el modo apagado y sin cajas de práctica abiertas.
- **Dónde no se puede usar:**
  - El modo no se puede prender si hay una caja real abierta, y no se puede apagar con una caja de práctica abierta.
  - Se usa **antes del corte**, cuando todavía no hay operación real en Galia.

### 5. El corte

1. **Práctica:** unos días con el modo práctica antes del corte.
2. **Día del corte:**
   - desde ese día todo se carga en Galia (ventas, caja, gastos), **también los precios y productos**;
   - Fudo queda abierto como respaldo;
   - *(decisión mía)* hay **dos interruptores**:
     - **"Catálogo en Galia"**, que se activa el día del corte: apaga la sync de productos de Fudo, para que el cron no pise lo que se edita en Galia, y pasa la carta al catálogo de Galia;
     - **"Fudo apagado"**, que se activa al final (paso 4).
   - En el período en paralelo, los precios de Fudo quedan desactualizados: solo sirven como respaldo.
3. **Período en paralelo:**
   - si algo falla y se carga en Fudo, la importación lo trae;
   - el riesgo de duplicar sigue existiendo si una misma venta se carga en los dos sistemas. La guía lo indica: si se carga en Fudo, no se carga en Galia;
   - en este período la importación sigue funcionando, para traer lo que se cargó en Fudo.
4. **Apagar Fudo:**
   - una última importación;
   - el interruptor "Fudo apagado" desactiva las syncs de gastos y ventas que quedaban y los botones "Sincronizar con Fudo";
   - la historia queda en Galia.
   - Es reversible mientras el código siga existiendo.

### 6. Guía para el equipo

`docs/pos/guia-caja.md`, pensada para imprimir y tener junto a la caja, con pantallas reales de Galia. Cubre:

- abrir la caja;
- cerrar la caja y el arqueo;
- qué hacer si el arqueo no cierra;
- cobrar con efectivo, tarjeta y el Point;
- anular un pago;
- qué hacer si Galia falla y hay que pasar a Fudo, sin cargar la misma venta dos veces.

## A criterio del constructor

- La estructura exacta de las tablas nuevas y los nombres.
- Dónde exactamente va el reporte en el menú.
- Si la carta publica por cron o al guardar el precio, siempre que no haga falta publicar a mano.
- Cómo se ve el control mes a mes de la importación.
- El orden de las tareas, con la verificación contra la API real **antes** de la importación completa.
