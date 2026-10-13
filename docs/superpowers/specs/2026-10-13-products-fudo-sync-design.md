# Sincronización de Productos con Fudo — Diseño

Fecha: 2026-10-13 · Rama: `feature/products-fudo-sync` (sale de `origin/main`; head de migraciones `b2a0_add_cash_registers`)

## Objetivo

Durante la transición hacia el POS nativo, **Fudo es la fuente de verdad** del catálogo. El módulo de Productos
(`products`, `product_categories`, `product_variants`, usado por el POS) hoy no tiene vínculo con Fudo; la carta
digital sí (`fudo_products` + `menu_item_variants.fudo_product_id`). Este cambio hace que Productos se cree y
actualice desde Fudo (nombre, categoría, precio, activo), igual que la carta. Al hacer el corte con Fudo
(sub-proyecto 6 del POS) la sincronización se apaga.

### Decisiones del usuario

- Fudo manda durante la transición (no es importación única ni escritura hacia Fudo).
- Mapeo 1 a 1 por defecto (cada producto de Fudo → un Producto con una variante vinculada), con la posibilidad de
  agrupar a mano varios productos de Fudo como variantes de un mismo Producto.
- Los campos que vienen de Fudo quedan bloqueados en la UI y en el backend.
- No hay productos manuales relevantes: no se vincula nada automáticamente por nombre (salvo categorías, ver abajo).
- Enfoque A: la sync de productos se cuelga de la sync de la carta y lee su caché; no llama otra vez a Fudo.

### Fuera de alcance

- Empujar cambios de Galia hacia Fudo.
- Vincular por nombre productos existentes.
- Que la carta se apoye sobre Productos en lugar de `fudo_products` (queda para el corte, sub-proyecto 6).

## Modelo de datos

Migración `b2b0_products_fudo_link` (`down_revision = 'b2a0_add_cash_registers'`):

| Tabla | Columna | Tipo | Notas |
|---|---|---|---|
| `product_categories` | `fudo_category_id` | String(20), unique, nullable | `'__none__'` para "Sin categoría" |
| `product_categories` | `fudo_status` | String(20), nullable | `None` \| `'missing'` |
| `product_variants` | `fudo_product_id` | String(20), unique, nullable | FK lógica a `fudo_products.fudo_id` (sin FK real: la carta borra filas de la caché) |
| `product_variants` | `fudo_status` | String(20), nullable | `'ok'` \| `'inactive'` \| `'missing'` \| `None` (no vinculada) |

`products` no cambia. Un Producto está **vinculado** si alguna de sus variantes tiene `fudo_product_id`.

`to_dict()`:
- `ProductCategory`: agrega `fudo_category_id`, `fudo_status`.
- `ProductVariant`: agrega `fudo_product_id`, `fudo_status`.
- `Product`: agrega `fudo_linked` (bool) y `fudo_locked_fields` (lista de campos bloqueados, ver API). Se calculan
  con una consulta a las variantes; el listado los calcula en lote para no hacer N+1 adicionales.

## Servicio de sincronización

`backend/app/services/product_sync_service.py`:

```python
def sync_products_from_cache(raw_categories) -> dict
```

- `raw_categories`: la lista de categorías de Fudo que ya descargó la carta (formato JSON:API de Fudo). Puede venir
  vacía si Fudo no devolvió categorías; en ese caso no se marcan categorías como `missing`.
- Lee todos los `FudoProduct` de la caché (ya actualizada por la carta en la misma transacción).
- No hace `commit`: lo hace quien lo llama.

`menu_sync_service.sync_fudo_products(client)` lo invoca al final, antes de su `commit`, y suma las estadísticas al
resultado bajo la clave `catalog` (la clave `products` ya existe: es el conteo de productos de Fudo) (`{categories_created, products_created, variants_updated, alerts}`). La
protección actual se mantiene: si Fudo no devuelve productos se lanza `ValueError` y no se toca nada.

### Pasos

1. **Categorías.** Upsert por `fudo_category_id`:
   - Nueva: si existe una `ProductCategory` sin vincular con el mismo nombre (comparación exacta tras `strip`,
     sin distinguir mayúsculas), se adopta asignándole el `fudo_category_id`. Si no, se crea. Si el nombre choca
     con una categoría vinculada a otro id de Fudo, se crea con el sufijo ` (Fudo)` (y `" (Fudo 2)"`, etc. si
     vuelve a chocar). El nombre se trunca a 100.
   - Existente: se actualiza el nombre (con la misma regla de choque), `is_active=True`, `fudo_status=None`.
   - Vinculada que no vino de Fudo (solo si `raw_categories` no está vacía; nunca `'__none__'`):
     `is_active=False`, `fudo_status='missing'`.
   - Productos sin categoría en Fudo van a "Sin categoría" (`fudo_category_id='__none__'`), creada a demanda.
   - Productos cuya categoría de Fudo no está entre las conocidas (Fudo no devolvió categorías): si el Producto ya
     existe no se mueve; si es nuevo va a "Sin categoría".
2. **Variantes vinculadas.** Para cada `ProductVariant` con `fudo_product_id`:
   - En la caché y activo en Fudo: `name` = nombre de Fudo (truncado a 100), `price` = precio de Fudo,
     `is_active=True`, `fudo_status='ok'`. Cuenta en `variants_updated` si cambió precio o nombre.
   - En la caché e inactivo en Fudo: `is_active=False`, `fudo_status='inactive'`.
   - Ausente de la caché: `is_active=False`, `fudo_status='missing'`. Nunca se borra (el POS la referencia).
   - `alerts` cuenta las variantes con estado distinto de `'ok'`.
3. **Productos vinculados.**
   - Si tiene exactamente una variante vinculada: `name` = nombre de Fudo (truncado a 200).
   - Si tiene varias: el nombre lo define Galia y no se toca.
   - Categoría: la del producto de Fudo de la primera variante vinculada (menor `id`) que esté en la caché.
   - `is_active` = alguna variante (vinculada o manual) activa.
   - Nunca se tocan descripción, imagen, receta, stock, `track_stock`, `has_recipe`, modificadores, ni color,
     ícono o descripción de la categoría.
4. **Productos nuevos.** Cada `FudoProduct` activo cuyo `fudo_id` no está en ninguna variante: se crea un `Product`
   (`name` = nombre de Fudo, categoría según el paso 1) con una `ProductVariant` (`name` = nombre de Fudo,
   `price` = precio de Fudo, `fudo_product_id`, `fudo_status='ok'`, stock 0). El flag `ignored` de la carta no
   aplica. Los inactivos de Fudo no se crean.
5. Devuelve las estadísticas.

La sync es idempotente: dos ejecuciones seguidas sin cambios en Fudo no modifican nada.

## API

Respuesta común para un campo bloqueado: **409** `{"error": "Este dato se edita en Fudo"}`. Solo se rechaza si el
valor enviado es distinto del actual (así el formulario puede reenviar el objeto completo sin fallar).

### `routes/products.py`

- `PUT /products/<id>`: si el Producto está vinculado, 409 al cambiar `category_id` o `is_active`, y al cambiar
  `name` cuando tiene una sola variante vinculada. `fudo_locked_fields` refleja exactamente estas reglas.
- `DELETE /products/<id>`: 409 si está vinculado.
- `PUT /products/<id>/variants/<vid>`: si la variante está vinculada, 409 al cambiar `name`, `price` o
  `is_active`. `stock_quantity` y `min_stock` siguen editables.
- `DELETE /products/<id>/variants/<vid>`: 409 si está vinculada, salvo que esté `missing` (ya no existe en Fudo): en ese caso se desvincula (`fudo_product_id` y `fudo_status` en null) y queda inactiva, para poder resolver la alerta.
- `POST /products/<id>/variants`: sigue permitido en Productos vinculados (variantes manuales).

Endpoints nuevos (todos `@token_required` + `@module_required('Products')`, salvo el GET que es
`@authenticated_only`):

- `POST /products/sync` → `menu_sync_service.sync_fudo_products(FudoClient())`. 200 con las estadísticas; ante
  error, `rollback` y **502** "Error sincronizando con Fudo. Revisá las credenciales o probá más tarde."
- `GET /products/fudo-candidates` → `{"products": [{fudo_id, name, price, category_name, is_active, product_id,
  product_name}]}` desde la caché; `product_id`/`product_name` es el Producto de Galia donde está vinculado (o null).
- `POST /products/<id>/variants/attach` con `{"fudo_product_id": "..."}`:
  - 400 si falta o no es string; 404 si el Producto o el `fudo_product_id` (en la caché) no existen.
  - 409 si ya está en este Producto.
  - Si existe una variante con ese `fudo_product_id` en otro Producto, se mueve (`product_id` = este). Si el Producto
    de origen queda sin variantes activas, se desactiva (no se borra: puede tener ventas).
  - Si no existe, se crea la variante con los datos de la caché.
  - 200 con el Producto actualizado (mismo formato que `GET /products/<id>`).
- `POST /products/<id>/variants/<vid>/detach`:
  - 404 si no existe; 409 si la variante no está vinculada o si es la única variante del Producto.
  - Crea un Producto nuevo (nombre de Fudo, misma categoría) y mueve la variante allí. 201 con el Producto nuevo.

### `routes/product_categories.py`

- `PUT`: si la categoría está vinculada, 409 al cambiar `name` o `is_active`; `color`, `icon` y `description`
  editables.
- `DELETE`: 409 si está vinculada.

## Frontend

- `services/productsService.js`: `syncFudo()`, `getFudoCandidates()`, `attachFudoVariant(productId, fudoProductId)`,
  `detachVariant(productId, variantId)`.
- `pages/Products.jsx`:
  - Botón "Sincronizar con Fudo" (solo con permiso `Products`), con estado de carga y toast resumen
    ("N precios actualizados · N productos nuevos · N alertas").
  - Insignia "Fudo" en Productos vinculados y alerta ámbar si alguna variante tiene `fudo_status` `missing` o
    `inactive`.
  - Filtro rápido "Con alertas de Fudo": `GET /products` acepta `fudo_alerts=true` y devuelve solo Productos con
    alguna variante `missing` o `inactive` (incluye inactivos, porque una variante en alerta suele dejar al
    Producto inactivo).
- `pages/ProductDetail.jsx`:
  - Aviso arriba si está vinculado: "Nombre, categoría, precios y estado se editan en Fudo".
  - Inputs de los campos en `fudo_locked_fields` en `disabled`, con ícono de candado y `title` explicativo.
  - Variantes vinculadas: nombre y precio en solo lectura, insignia de estado (ok / inactiva en Fudo / ya no existe
    en Fudo); stock y mínimo editables; sin botón de borrar; botón "Separar" si el Producto tiene más de una variante.
  - Acción "Agregar variante desde Fudo": abre `FudoProductPicker` con los candidatos; los que ya están en otro
    Producto se pueden elegir con la leyenda "se moverá desde «X»" y piden confirmación; los de este Producto quedan
    deshabilitados.
- `components/menu/FudoProductPicker.jsx`: nuevas props opcionales `isDisabled(p)` (reemplaza la regla de
  "ya en la carta"), `describe(p)` (leyenda por producto o null) y `emptyLabel` (por defecto el texto actual). Sin
  esas props la carta no cambia de comportamiento.
- `pages/ProductCategories.jsx`: insignia "Fudo"; nombre y activo bloqueados en las vinculadas.

## Errores

- La sync de productos corre en la misma transacción que la de la carta: cualquier excepción revierte las dos.
- `POST /menu/sync` (permiso `Menu`) y `POST /products/sync` (permiso `Products`) ejecutan la misma sync completa.
  Es aceptable: solo copia datos de Fudo.

## Tests

Backend (pytest, reutilizando `tests/menu_fakes.py`):

- `tests/test_product_sync.py`: creación desde cero; actualización de precio y nombre; inactivo; missing; categoría
  missing; categorías vacías no marcan missing; adopción de categoría con el mismo nombre; choque de nombre con
  sufijo "(Fudo)"; Producto agrupado mantiene su nombre; nunca toca stock, receta, imagen ni descripción;
  idempotencia; la sync de la carta incluye las estadísticas de productos.
- `tests/test_products_fudo_lock.py`: 409 en cada campo bloqueado de Producto, variante y categoría; los campos
  libres siguen editables; reenviar el mismo valor no falla; `fudo_locked_fields`.
- `tests/test_products_attach.py`: attach que mueve, attach que crea, desactivación del Producto de origen, attach
  al mismo Producto (409), ids inexistentes (404), detach y sus 409; `POST /products/sync` con 200 y 502.
- `tests/test_menu_tasks.py`: el cron cubre los dos módulos.

Frontend (vitest, entorno node sin testing-library, que no se agrega): utilidades puras en `utils/fudoLock.js`
(campos bloqueados, estado de variante, resumen de sync, leyenda del selector). El comportamiento de las pantallas se
verifica a mano en el preview del navegador.

## Puesta en marcha

- Sin cambios en `render.yaml`: el cron `galia-menu-sync` ya corre `app.tasks.menu_tasks`.
- Probar la migración en Postgres antes de deployar: upgrade, downgrade, upgrade.
- La primera sync en producción crea todo el catálogo; si hay productos manuales de prueba, desactivarlos antes.
