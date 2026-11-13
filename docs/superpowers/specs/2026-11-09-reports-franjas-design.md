# Reportes: qué se vende en cada turno, para planificar la producción

Fecha: 2026-11-09 · Estado: borrador para revisión

## Para qué

La noche anterior, quien cierra Galia Café decide cuánto laminar (medialunas y demás laminados que se hornean a diario), qué *mealprep* preparar y qué sacar del freezer para descongelar. Hoy eso se decide a ojo. El reporte responde una pregunta concreta: **"mañana, ¿cuántas unidades de cada producto se van a vender, y en qué turno?"**, a partir de lo que se vendió en días comparables.

Éxito: el equipo abre la pestaña la noche anterior, ve el día siguiente ya elegido y, sin hacer cuentas, sabe cuántas unidades de cada producto preparar para Desayuno, Almuerzo y Merienda.

## Objetivos

1. **Turnos configurables en Galia.** Hoy no existen en Galia ni se pueden traer de Fudo: la API de Fudo no tiene un endpoint de turnos, solo un filtro `shiftId` en `/sales`. Se cargan con nombre, hora de inicio y hora de fin, y se editan desde la app sin tocar código (regla del proyecto: nada de valores de negocio hardcodeados). Los valores iniciales los definió el usuario:
   - Desayuno 08:00–12:00
   - Almuerzo 12:00–16:00
   - Merienda 16:00–20:00
2. **Pronóstico del día elegido** (por defecto, mañana en hora Argentina). Por cada producto muestra las unidades esperadas en total y por turno.
3. **Consumo promedio diario** de cada producto y cómo varía según el día de la semana (de lunes a domingo), para entender el ritmo de la semana y no solo el de mañana.
4. **Todos los productos** (lo pidió el usuario) que se vendieron al menos una vez en los días comparables *(decisión mía: los que dan 0 no aparecen)*, agrupados por categoría y ordenados de más a menos vendido dentro de cada una.
5. **Combos y productos armados abiertos en sus componentes** (lo pidió el usuario). Un "Combo Clásico (infusión + 2 medialunas)" suma 2 a Medialuna; una "Medialuna con jamón y queso" suma 1 a Medialuna. Sin esto, el reporte cuenta menos laminados de los que hay que hornear: en producción hay 1018 ítems de combos.
6. **Número limpio** (lo pidió el usuario): sin margen de seguridad ni redondeo para arriba. El equipo redondea. Se muestra con un decimal cuando hace falta (por ejemplo, 23,5).

## No objetivos

- No baja a insumos ni a recetas: abre un producto en otros productos (combo → medialunas), pero no convierte productos en masa ni kilos: "24 medialunas", no "1,2 kg de masa". Eso vendrá con recetas, que hoy no tienen todos los vínculos ni los precios.
- No hace pronósticos con modelos estadísticos ni ML. Es un promedio de días comparables, fácil de explicar y de verificar.
- No es una alerta ni una notificación: se consulta a mano.
- No reemplaza la pestaña "Análisis por tiempo" (horas y días en pesos), que sigue como está.

## Lo que haría fallar esto aunque funcione

- Que mezcle días distintos: un feriado contado como lunes normal, o un sábado promediado con martes, infla o achica todo el pronóstico.
- Que el número no se pueda explicar. Al lado del esperado tiene que verse de qué días sale.
- Que la lista sea ilegible por tener todos los productos: hace falta agrupar y poder buscar o filtrar.

## Cómo se calcula (decisiones)

**Fuente de datos.** `sales` + `sale_items`, solo ventas `estado = 'Cerrada'`, de Fudo y del POS de Galia por igual. Unidades = suma de `sale_items.quantity`. El producto se identifica igual que en el reporte de productos existente (`_product_rows` en `backend/app/routes/reports.py`: nombre de producto + variante + categoría). *(Decisión mía: hoy ningún ítem de Fudo trae variante, así que en la práctica es por producto; las variantes del POS, como Unidad o Docena, quedan en filas separadas porque no son la misma cantidad de piezas.)* Los ítems de Fudo ya tienen precios corregidos (#34), pero acá solo importan las cantidades.

**Día.** Es la fecha comercial `Sale.fecha` (Argentina, corte a las 6 AM, `business_date()`).

**Turno de una venta.** Se toma la hora local (UTC−3) de `Sale.cerrada`, o de `Sale.creacion` si no hay cierre: es la misma conversión que usa `get_sales_by_hour`. La venta cae en el turno cuyo intervalo `[inicio, fin)` contiene esa hora. Si no cae en ninguno (antes de las 8 o después de las 20), suma al total del día en una columna **"Fuera de turno"**. *(Decisión mía: la hora de cierre es lo que hay en los datos de Fudo y se acerca al momento del consumo.)*

**Días comparables para el día elegido D.** *(Decisión mía, el usuario no la objetó.)*
- **D es un día normal:** los últimos **4** días con el mismo día de la semana anteriores a D que no sean feriado.
- **D es feriado** (está en la tabla `holidays` con `type` `national` o `local`; los `special_event` no cuentan como feriado. Hoy en producción todos son `national`): los feriados de los últimos 12 meses anteriores a D con ventas, más los últimos 4 domingos que no sean feriado. Según el usuario, un feriado "es distinto a todo pero muy parecido a un domingo"; así arranca pareciéndose a un domingo y se ajusta a medida que pasan feriados.
- Se cuentan solo los días en que el local vendió algo: un día cerrado no entra como cero. Si un producto no se vendió en un día comparable en que el local sí abrió, ese día cuenta como **0** para ese producto.
- La cantidad de semanas (4) y la ventana de feriados (12 meses) son configurables, igual que los turnos. No quedan fijas en el código. *(Los 12 meses son decisión mía, para que feriados viejos no pesen más que la demanda actual.)*

**Esperado** de un producto y turno = suma de unidades de ese producto en ese turno en los días comparables ÷ cantidad de días comparables.

**Promedio por día de la semana.** Para cada producto, el promedio de unidades de cada día de la semana sobre las últimas N semanas, sin feriados, más una fila de feriados.

**Transparencia.** La respuesta incluye la lista de días comparables usados, y la pantalla la muestra (por ejemplo, "Basado en: sáb 1/11, sáb 25/10, sáb 18/10, sáb 11/10").

## Componentes de un producto

- **No existe hoy.** Las recetas (`recipes`, `recipe_ingredients`) vinculan un producto con insumos y sub-recetas, no con otros productos. Hace falta una tabla nueva, por ejemplo `product_components`: producto (el combo), producto componente y cantidad por unidad vendida. Va sobre el catálogo (`products`) y no sobre nombres de texto: hoy 30 508 de los 30 582 `sale_items` en producción están vinculados a una variante del catálogo (`product_variant_id` → producto). Los no vinculados se cuentan tal como se vendieron.
- **La carga la hace el equipo desde la app.** Se edita en la ficha del producto o en una pantalla propia (elige el builder), con quién y cuándo. Arranca vacía: la migración no inventa composiciones. Componentes genéricos, como "infusión" en el Combo Clásico, simplemente no se cargan.
- **Un solo nivel** *(decisión mía)*: un componente no se vuelve a abrir. Se valida que un producto no sea componente de sí mismo.
- **En el reporte** *(decisión mía)*: el componente muestra el total (directo + desde combos), con el desglose a la vista (por ejemplo, "Medialuna: 40 = 22 sueltas + 18 en combos"). El combo sigue apareciendo como fila propia, porque también se arma. La apertura respeta el turno y el día de la venta del combo.
- **Permiso:** el mismo que edita productos del catálogo.

## Dónde vive

- **Turnos:** tabla nueva (por ejemplo, `sales_shifts` o `day_parts`; el nombre lo decide el builder, pero no puede chocar con `shifts`, que son los turnos de empleados) con nombre, hora de inicio, hora de fin, orden y activo. La migración la crea con los tres turnos iniciales y es idempotente (no duplica si ya existen). No toca tablas existentes, así que no hace falta backup. El ABM va en la pantalla de configuración que ya existe, junto a "Horarios del local" (`/store-hours`, módulo Schedules) o como sección de Reportes; elige el builder. Los cambios quedan registrados con quién y cuándo (`updated_by`, `updated_at`). Un turno se desactiva, no se borra.
- **Cantidad de semanas comparables:** en la misma configuración (un valor, por defecto 4).
- **Backend:** endpoint nuevo en `backend/app/routes/reports.py`, por ejemplo `GET /api/v1/reports/production-forecast?date=YYYY-MM-DD`, con `@module_required('Reports')`, el mismo permiso que el resto de Reportes.
- **Frontend:** una pestaña nueva en `frontend/src/pages/Reports.jsx`, al lado de Dashboard, Análisis por tiempo y Productos, en un componente propio como `ProductsTab.jsx` (por ejemplo, `ProductionTab.jsx`). Tiene un selector de día (por defecto mañana) y una tabla agrupada por categoría con las columnas: Producto · Total esperado · una columna por turno activo · Fuera de turno (solo si hay algo). Se puede buscar por nombre. Al costado o en otra vista, el promedio diario por día de la semana.

## Casos borde

- **Pocos datos** (por ejemplo, un producto nuevo o los primeros feriados): se calcula con los días que haya y se muestra cuántos fueron.
- **Ningún día comparable con ventas:** mensaje claro en lugar de una tabla de ceros.
- **Turnos solapados o con huecos:** se valida al guardar (inicio < fin, sin solapamiento entre activos). Los huecos son válidos y caen en "Fuera de turno".
- **Ventas sin detalle de ítems** (hay algunas viejas de Fudo): no aportan unidades. Se informa la cobertura igual que en el reporte de productos.

## Lo que queda para el builder

- El nombre de la tabla y de la pestaña, y dónde va el ABM de turnos.
- El diseño visual de la tabla y de la vista por día de la semana, respetando el estilo actual de Reportes.
- Si la consulta se hace en SQL agregado o en Python sobre el detalle. El volumen es chico (unos 30 000 ítems por año).
- Tests: cálculo de días comparables (normal, feriado, día sin ventas), asignación de turno incluyendo los bordes (12:00 cae en Almuerzo) y "fuera de turno", y producto ausente contado como 0.
- Verificación real antes de dar por terminado: levantar local con una copia de datos y comparar a mano un producto (por ejemplo, Medialuna) de un sábado contra la consulta en la base.
