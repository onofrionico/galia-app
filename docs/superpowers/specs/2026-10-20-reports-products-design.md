# Reportes: ventas por producto y categoría

Fecha: 2026-10-20. El usuario pidió saltear las preguntas; las decisiones de abajo son de Claude.

## Por qué

Reportes solo ve el total de cada venta (`sales`). No se puede saber qué se vende, qué categoría
pesa más ni qué productos casi no rotan, que es el reporte más usado en Fudo/Toast y la base para
food cost y menu engineering (puntos 3 y 4 de la revisión de reportes).

Hoy las ventas reales están en Fudo (el POS nativo todavía no reemplazó a Fudo), así que el
reporte tiene que funcionar con datos de Fudo ahora y con los del POS después del corte.

## Qué se construye

1. **Tabla `sale_items`**: los ítems vendidos de cada fila de `sales`, con la misma forma para
   las dos fuentes. Columnas: `sale_id` (FK a `sales`, borrado en cascada), `external_id`
   (id del ítem en Fudo, único, nulo para el POS), `product_variant_id` (nullable),
   `product_name`, `variant_name` (nullable), `category_name` (nullable), `quantity`,
   `unit_price`, `total`, `unit_cost` (nullable; Fudo lo informa y sirve para food cost).
   Nombres y categoría se guardan como estaban al vender (no dependen del catálogo actual).
   Solo se guardan ítems no cancelados.
2. **Sync de Fudo**: `GET /sales` pide `include=items,items.product,items.product.productCategory,waiter,table,table.room`
   con `fields[...]` explícitos (en `/expenses` vimos que sin `fields` no vienen atributos).
   Por cada venta se reemplazan sus ítems. Una venta ya existente sin ítems los recibe aunque
   no se pida "actualizar existentes", así re-sincronizar un período rellena el historial.
   `total = price × quantity` (price de Fudo se asume unitario — verificar con
   `scripts/inspect_fudo_sales.py`). El vínculo con el catálogo es por
   `ProductVariant.fudo_product_id`.
3. **Arreglo de la sync de ventas**: el parser leía atributos que no existen (`status`, `type`,
   `userName`, `cashRegisterName`, `comments`, `fiscalReceipt`). Pasa a leer `saleState`,
   `saleType` (EAT-IN/TAKEAWAY/DELIVERY), `comment`, mozo desde `waiter`, mesa y salón desde
   `table`/`table.room` en `included`.
4. **POS**: `projection.project` copia los ítems no cancelados de la venta (`line_total`
   incluye modificadores; categoría desde el producto). `unproject` los borra por cascada.
5. **Endpoint `GET /reports/products?start_date&end_date`** (módulo Reports):
   - `summary`: unidades, facturación por ítems, productos distintos, y **cobertura**:
     ventas del período con ítems / total y facturación por ítems / total de `sales`. Sirve de
     control: muestra cuánto del período todavía no tiene detalle y si los montos cierran.
   - `by_category`: unidades, facturación y % por categoría.
   - `by_product`: producto + variante, categoría, unidades, facturación, precio promedio,
     % de facturación, clase ABC (A hasta 80 % acumulado, B hasta 95 %, C el resto) y
     variación de facturación contra el período anterior de igual largo.
6. **Pantalla**: pestaña "Productos" en Reportes, con el mismo selector de período: tarjetas
   (unidades, productos, cobertura), tabla de categorías con barra de participación y tabla de
   productos ordenable con buscador y badge ABC. Aviso cuando la cobertura es baja.

## No incluye

- Descuentos de la venta repartidos por producto (se reporta venta bruta por ítem).
- Subítems de Fudo (combos/agregados con precio propio): se ven como diferencia en la cobertura.
- Food cost y menu engineering (usan `unit_cost`, pero son el punto 4).
- Backfill automático: el historial se completa re-sincronizando ventas desde la pantalla de sync.

## A verificar con datos reales

`price` unitario vs. total de línea, y nombres de atributos/relaciones de Fudo, con
`backend/scripts/inspect_fudo_sales.py` antes de la primera sync en producción.
