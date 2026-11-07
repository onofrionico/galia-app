# Recetas de producción — diseño

Fecha: 2026-11-06

## Intención

Hoy las recetas de pastelería viven en una planilla de Google ("Recetario Galia",
10 recetas). Dicen *cuánto* lleva cada cosa, pero casi nunca *cómo* se hace: el orden,
las temperaturas, los tiempos de horno, cómo darse cuenta de que algo está listo. Eso
queda en la cabeza de cada pastelera.

Queremos una sección de **Recetas** en Galia pensada para quien produce: la pastelera
la abre en el celular o en una tablet de cocina y tiene todo lo necesario para hacer el
producto sin preguntarle a nadie. La receta "Galletitas de Nuez" de la planilla es el
modelo del nivel de detalle buscado: pasos con título, punto de cocción, qué es normal
y qué hacer si algo sale mal.

Dos motivos más:

1. **Unificar recetas y composición de productos.** La receta pasa a ser la única fuente
   de la composición de un producto. La misma ficha que lee la cocina es la que usa
   Galia para el costo y el descuento de stock. Así el costo es más preciso.
2. **Estandarizar la producción a largo plazo.** Con los procesos escritos de forma
   uniforme aparecen las coincidencias: bases compartidas (el bizcocho de chocolate de
   Torta Galia y Matilda, la masa de las cookies), temperaturas que podrían unificarse,
   medidas "a ojo" que hay que fijar.

## Estado actual (relevado en el código)

- `products` tiene `has_recipe` y una lista plana `product_recipe_items`
  (`product_id`, `supply_id`, `quantity`, `unit`). No hay sub-recetas, rendimiento ni
  pasos.
- La receta se edita en `ProductDetail.jsx` vía `PUT /products/<id>/recipe`, protegido
  por el módulo `Products`.
- `stock_service.stock_requirements` descuenta insumos al vender: por cada unidad
  vendida de un producto con receta descuenta `quantity` de cada insumo. **El campo
  `unit` de la receta se ignora**: la cantidad se interpreta en la unidad del insumo.
- **Hoy no existe ningún cálculo de costo de receta** (ni en backend ni en frontend).
  Los insumos tienen historial de precios en `supply_prices`.
- Los permisos son por módulo (`modules`, `role_permissions`, `user_permissions`); el
  rol `admin` tiene acceso a todo. Los módulos se siembran en migraciones
  (ver `b1a0_add_permissions_system.py`).

## Objetivos

1. Una **receta** con:
   - nombre, producto vinculado (opcional: las bases no se venden),
   - **rendimiento** (cantidad + unidad: "20 unidades", "1 torta", "1200 g"),
   - tiempo total aproximado y una nota de "requiere preparación previa" (ej. "las
     cookies necesitan 1 día de freezer antes de hornear"),
   - **ingredientes**: cada uno es un insumo existente **o otra receta (base)**, con
     cantidad y unidad,
   - **pasos** ordenados, cada uno con: título corto, indicación, y opcionalmente
     temperatura (°C), tiempo (minutos o rango), punto ("apenas dorado en los bordes")
     y consejo/qué hacer si sale mal,
   - notas generales.
2. **Vista de cocina** (mobile first, celular y tablet): se lee de arriba hacia abajo —
   encabezado (nombre, rendimiento, tiempo, preparación previa), ingredientes con
   cantidades exactas, pasos numerados uno por bloque con letra grande y los datos de
   temperatura/tiempo/punto destacados. Una base dentro de los ingredientes se toca y
   abre su propia receta. Nada que haya que escribir; botones grandes.
3. **Editor de recetas** para quien tenga el permiso "Administrar recetas": alta,
   edición, reordenar pasos, ingredientes con buscador de insumos y de recetas base.
4. **Costo**: costo de la tanda y costo por unidad de rendimiento, calculado con el
   último precio de cada insumo y el costo por unidad de las bases. Se muestra en el
   editor y en el detalle del producto. Si falta un precio o una unidad no se puede
   convertir, el costo se marca **incompleto** y se dice qué ingrediente falla.
5. **La receta reemplaza a la composición actual**: el descuento de stock por venta
   usa la receta del producto, dividida por el rendimiento y expandiendo las bases.
6. **Tres permisos nuevos** (tres módulos en el sistema de permisos existente):
   - **"Ver recetas"**: abre la sección y la vista de cocina. Se le da a quien produce.
   - **"Ver costo de recetas"**: muestra los costos (de tanda, por unidad, por
     ingrediente) en las recetas y en el detalle del producto. Sin este permiso el
     backend no envía los costos en la respuesta; no alcanza con ocultarlos en la
     pantalla.
   - **"Administrar recetas"**: alta, edición y baja de recetas, y vincular una receta
     a un producto.
   Ninguno se otorga por defecto a ningún rol: al inicio solo los tiene el admin
   (que tiene acceso a todo), y después se asignan por usuario. Quien edita aplica el
   cambio en el momento, sin aprobación.
7. **Carga inicial** de las 10 recetas de la planilla (ver más abajo).

## No objetivos (por ahora)

- Escalar cantidades (hacer el doble o la mitad). Se produce la tanda que dice la receta.
- Planificación u órdenes de producción, registro de lo producido.
- Mover el descuento de stock al momento de producir: sigue siendo al vender.
- Flujo de aprobación de cambios.
- Fotos o videos por paso, temporizadores, marcar pasos como hechos.
- Historial de versiones de la receta (alcanza con "modificada por / cuándo").

## Anti-objetivos (sería un fracaso aunque funcione)

- **Romper el stock o la composición de los productos que ya tienen receta.** Después
  de la migración, cada producto existente debe descontar exactamente lo mismo que hoy.
- **Inventar datos** en la carga inicial: lo que la planilla no dice queda marcado
  "a completar", nunca se rellena con un valor plausible.
- Una vista de cocina que obligue a escribir, a hacer zoom o a navegar mucho con las
  manos ocupadas.
- Tener dos listas que mantener (receta para la cocina y composición para el costo).

## Decisiones tomadas

- Recetas y composición de productos son la misma cosa (decidido por el usuario).
- Se cargan como se hacen en la cocina (por tanda) con su rendimiento; el costo y el
  descuento por unidad salen de dividir por el rendimiento.
- Las bases compartidas son recetas propias sin producto vinculado, usables como
  ingrediente de otras recetas. Sin ciclos (una receta no puede contenerse a sí misma
  directa ni indirectamente).
- Tres permisos separados: ver recetas, ver costos, administrar; solo admin al inicio
  (decidido por el usuario).
- El precio de un insumo (`supply_prices.price`) es por la unidad del insumo
  (kilo, litro, unidad), no por bulto (confirmado por el usuario). No hace falta un
  campo de tamaño de bulto.
- La pastelera solo lee; no hay aprobación (decidido por el usuario).
- Sin escalado por ahora (decidido por el usuario).
- La carga inicial la hace Claude desde la planilla; después la cocinera las corrige
  en la sección (decidido por el usuario).

## Decisiones de diseño tomadas por Claude (revisar)

- **Receta por producto, factor por variante.** La receta se vincula al producto (una
  receta por producto, como hoy). Cada variante tiene un factor "unidades de
  rendimiento que consume", por defecto 1. Ej.: Torta Galia rinde "12 porciones";
  la variante "Entera" consume 12 y la variante "Porción" consume 1. Descuento y
  costo por variante = (receta ÷ rendimiento) × factor.
- **Vincular no cambia el stock hasta que se activa.** El producto mantiene su
  `has_recipe`, que pasa a significar "la receta gobierna stock y costo". Vincular una
  receta no activa `has_recipe` sola; se activa a mano desde el producto (con el
  permiso de administrar recetas). Así la carga inicial no cambia el descuento de
  stock de ningún producto en producción.
- **Composición existente.** Cada producto que hoy tiene `has_recipe` y composición se
  migra a una receta propia con rendimiento 1 unidad, sin pasos, con las mismas
  cantidades en la unidad del insumo: el descuento sigue idéntico. Si la planilla tiene
  una receta para ese mismo producto, **no la pisa**: la receta de la planilla se carga
  sin vincular y queda listada para que alguien decida cuál vale.
- **Productos con `track_stock`** (stock de producto terminado) no cambian: la
  receta se puede vincular para la cocina y el costo, pero no se activa para stock.
- **Ingredientes incompletos.** Con `has_recipe` activo, un ingrediente con unidad no
  convertible o "a completar" no descuenta stock (y se marca el costo como
  incompleto); no bloquea la venta.
- **Editor viejo de composición.** El bloque de receta de `ProductDetail.jsx` deja de
  editar: muestra la receta vinculada (y su costo, con permiso) con un enlace al
  editor de recetas. `PUT /products/<id>/recipe` se elimina o pasa a exigir
  "Administrar recetas".
- **Cómo se hace la carga inicial.** La planilla se puede leer por enlace: cada hoja
  se baja como CSV con
  `https://docs.google.com/spreadsheets/d/<id>/gviz/tq?tqx=out:csv&sheet=<hoja>`.
  Se arma un script idempotente que vincula por nombre contra los
  insumos y productos de producción, con un modo de prueba que solo informa qué
  vincularía y qué crearía. El usuario lo corre en producción después de revisar ese
  informe.

## Carga inicial desde la planilla

Fuente: Google Sheet "Recetario Galia"
(`1grtlaZxzwFb3Fmy2WSiLqE7bJyvwU7s1L59bKSWAS30`), hojas: Cookies (5 variedades),
Chipa, Muffins (3 variedades), crumble, Galletitas de Nuez, scones, Banoffee, Matilda,
Souffle de nuez, Torta Galia. "Hoja 7" está vacía.

- Pasar cada receta al formato de pasos de "Galletitas de Nuez" (título, indicación,
  temperatura, tiempo, punto, consejo), usando solo lo que dice la planilla.
- Lo que falta queda marcado **"a completar"** de forma visible en la receta (ej.
  horno y tiempo de los scones, rendimiento de Torta Galia, Matilda y Crumble, la
  leche "a ojo" de los scones).
- Los posibles errores se cargan **tal cual** y se listan para que los confirme
  pastelería:
  - Galletitas de Nuez: ingredientes dicen "2 huevos", el paso 4 dice "la yema".
  - Matilda: ganache con 500 g de chocolate y 600 g de crema (Torta Galia: 200/250).
  - Cookies: "con esta proporción salen 6,5 cookies".
  - Crumble: "Agregar queso por encima" como último paso.
- Bases a extraer como recetas propias: bizcocho de chocolate (Torta Galia / Matilda;
  difieren en polvo de hornear 10 g vs 12 g y manteca), almíbar de cacao, ganache,
  masa de cookies, premezcla de muffins. Si dos recetas difieren en una cantidad, **no
  se unifican a la fuerza**: se carga cada una como está y la diferencia va a la lista
  de dudas.
- Cada receta se vincula al producto de Galia que corresponda; las que no tengan un
  producto claro quedan sin vincular y se listan.
- Los ingredientes se vinculan a insumos existentes; si un insumo no existe se crea
  sin precio (el costo queda incompleto hasta que se cargue).
- Resultado entregable: un documento `docs/recetas-carga-inicial.md` con la lista de
  "a completar", dudas, recetas sin producto e insumos creados.

## Restricciones

- Backend Flask + SQLAlchemy + Alembic, frontend React (Vite + Tailwind), como el
  resto de Galia. Migraciones encadenadas con el esquema de nombres actual
  (`bXXX_...`) sobre la cabeza vigente de `main`.
- El catálogo de productos se sincroniza desde Fudo (`product_fudo_info`,
  `cutover.catalog_in_galia()`); la receta es dato propio de Galia y no se toca en la
  sync.
- `stock_requirements` se usa en ventas y devoluciones (POS); el cambio debe mantener
  la simetría descuento/devolución y el cuantizado a 0,001.

## Lo que queda a criterio de quien construye

- Modelo de datos exacto (tablas de recetas, ingredientes, pasos) y si
  `product_recipe_items` se reemplaza o se migra a la tabla nueva.
- Conversión de unidades: como mínimo g↔kg y ml↔l, y unidad↔unidad. Unidades no
  convertibles (cucharada, pizca, "a ojo") se aceptan pero dejan el costo y el
  descuento de ese ingrediente marcados como incompletos.
- Ubicación en el menú y rutas del frontend.
- Cómo se ejecuta la carga inicial en producción (script idempotente o migración de
  datos).
