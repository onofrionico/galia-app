# Carta: categorías desde Fudo y grupos de presentación — Diseño

**Fecha:** 2026-10-08
**Estado:** Aprobado en brainstorming, pendiente de revisión del spec
**Base:** extiende `2026-10-07-carta-digital-design.md` (ya mergeado en `main`, PR #3)

## Objetivo

1. Que las categorías de la carta sean las de Fudo (consistencia con la caja) y que cada ítem tome su categoría automáticamente.
2. Que la carta se arme sola a partir de los productos de Fudo (ítems nuevos se crean ocultos para revisar).
3. Agregar **grupos**: una capa puramente de presentación para organizar las categorías en secciones de la carta pública. No forman parte de la gestión de productos.

## Decisiones tomadas

| Tema | Decisión |
|---|---|
| Origen de las categorías | Fudo. Se crean/renombran sólo desde Fudo; en galia-app se edita orden, visibilidad, nota, grupo y "mostrar título". |
| Categoría de un ítem | Automática: la de Fudo del primer precio vinculado. Si en Fudo cambia, el ítem se mueve en la próxima sync. |
| Ítems a partir de productos Fudo | Creación automática **oculta** de un ítem por producto activo no vinculado ni ignorado. |
| Varios precios en un ítem | "Unir con otro ítem" (los precios del absorbido pasan al destino; el absorbido se borra). |
| Ignorar | Borra el ítem y marca el producto Fudo como ignorado: la sync no lo vuelve a crear. |
| Grupos | Dos niveles en la carta pública: barra sticky por grupo; categorías como subtítulos dentro del grupo. |
| Título de categoría | Opcional por categoría (`show_title`, default true). |
| Seed del PDF | Se elimina (`seed_menu.py`, `data/menu_seed.json`, su test). |

## 1. Modelo de datos

Migración Alembic nueva `carta_grupos_fudo` (down_revision = `add_menu_tables`; si al implementar `main` tiene otro head, encadenar desde ese).

- **MenuGroup** (nuevo): `id, name (String 100), slug (unique), sort_order, created_at, updated_at`.
- **MenuCategory**:
  - `+ fudo_category_id` String(20), unique, nullable (null = categoría heredada creada a mano antes de este cambio).
  - `+ group_id` FK → menu_groups.id, nullable, `ondelete SET NULL`.
  - `+ show_title` Boolean, not null, default true.
  - `+ fudo_status` String(20), nullable: `'missing'` cuando la categoría desapareció de Fudo.
  - `name` pasa a ser escrito por la sync para categorías con `fudo_category_id`.
  - `sort_order` ahora es el orden **dentro de su grupo**.
- **FudoProduct**: `+ fudo_category_id` String(20), nullable.
- **MenuItem**: `+ reviewed_at` DateTime nullable (null = ítem creado por la sync que nadie revisó todavía; se setea al editar o hacer visible el ítem). `category_id` lo escribe la sync o el backend.

## 2. Sincronización (`menu_sync_service.sync_fudo_products`)

Orden dentro de una sola transacción (mismo guardado de "Fudo no devolvió productos" de hoy):

1. **Categorías**: para cada categoría de Fudo, upsert de `MenuCategory` por `fudo_category_id`:
   - nueva → `name` de Fudo, `slug` único, `group_id = None`, `is_visible = True`, `show_title = True`, `sort_order` = al final de "sin grupo";
   - existente → actualiza `name` (y slug si cambia el nombre), `fudo_status = None`;
   - categorías con `fudo_category_id` que ya no vienen de Fudo → `is_visible = False`, `fudo_status = 'missing'` (no se borran: pueden tener ítems).
2. **Productos**: upsert de `FudoProduct` como hoy, guardando también `fudo_category_id`.
3. **Variantes vinculadas**: precios y `fudo_status` como hoy.
4. **Recategorización**: para cada ítem con al menos una variante vinculada a un producto existente, `category_id` = categoría de Fudo del producto de su **primera** variante vinculada (por `sort_order`). Si cambia, el ítem va al final de la nueva categoría.
5. **Ítems nuevos**: por cada `FudoProduct` activo, no ignorado y no vinculado a ninguna variante → crear `MenuItem(name = nombre Fudo, is_visible = False, category = la de Fudo)` con una variante vinculada (`label = None`, precio Fudo, `fudo_status = 'ok'`). Productos sin categoría en Fudo van a una categoría especial "Sin categoría" (creada por la sync con `fudo_category_id = '__none__'`).

Devuelve `{products, price_changes, alerts, categories_created, items_created}`.

Efecto en el cron: los ítems y categorías nuevos se crean ocultos/al final; `has_unpublished_changes` no los cuenta mientras estén ocultos (no cambian el snapshot), así que el auto-publish por cambio de precio sigue funcionando.

## 3. API admin (cambios en `/api/v1/menu`)

- `GET /` agrega `groups: [{id, name, slug, sort_order}]`; cada categoría agrega `fudo_category_id, group_id, show_title, fudo_status`.
- Categorías:
  - `POST /categories` → **se elimina** (las categorías vienen de Fudo).
  - `PUT /categories/<id>` acepta sólo `description, is_visible, show_title, group_id` (int o null). `name` se rechaza (400) si la categoría tiene `fudo_category_id`.
  - `DELETE /categories/<id>` sólo permitido para categorías heredadas (sin `fudo_category_id`) y vacías.
  - `PUT /categories/reorder` pasa a recibir `{group_id: int|null, ids: [...]}` y exige el set exacto de categorías de ese grupo.
- Grupos (nuevos): `POST /groups {name}`, `PUT /groups/<id> {name}`, `DELETE /groups/<id>` (categorías quedan sin grupo), `PUT /groups/reorder {ids}` (set exacto).
- Ítems:
  - `POST /items` sólo para ítems **sin** productos Fudo (todo precio manual): exige `category_id` de una categoría existente.
  - `PUT /items/<id>`: `category_id` sólo se acepta si el ítem no tiene variantes vinculadas; si las tiene, la categoría se recalcula desde Fudo al guardar.
  - `POST /items/<id>/merge {source_item_id}` (nuevo): mueve las variantes del origen al final del destino, recalcula categoría, borra el origen (su imagen se limpia al publicar si queda huérfana). Error si son el mismo ítem.
  - `POST /items/<id>/ignore` (nuevo): marca como ignorados los `FudoProduct` de sus variantes vinculadas y borra el ítem.
- Bandeja: `GET /inbox` pasa a devolver `{new_items: [ítems ocultos creados por la sync y nunca editados], alerts: [...variantes con alerta..., ...categorías con fudo_status 'missing'...]}`. "Nuevos" = ítems con `reviewed_at IS NULL`.
- `GET /fudo-products?unassigned=true` y `POST /fudo-products/<id>/ignore` se eliminan (ya no hay productos sin asignar).

## 4. Snapshot `menu.json` v2

```json
{
  "version": 2,
  "published_at": "...",
  "settings": {...},
  "tags": [...],
  "groups": [
    {
      "slug": "desayuno-y-merienda",
      "name": "Desayuno y merienda",
      "categories": [
        {"slug": "cafeteria", "name": "Cafetería", "show_title": true, "description": "...", "items": [ ...igual que v1... ]}
      ]
    }
  ]
}
```

- Grupos ordenados por `sort_order`; categorías por `sort_order` dentro del grupo.
- Categorías sin grupo → grupo final `{"slug": "otros", "name": "Otros"}`.
- Si no existe ningún `MenuGroup`, un único grupo `{"slug": "carta", "name": null}` con todas las categorías (la carta se ve como hoy, sin título de grupo).
- Se omiten categorías ocultas o sin ítems visibles, y grupos que quedan vacíos.
- El hash para "cambios sin publicar" usa la misma regla actual (claves de imagen, no URLs).

## 5. Panel admin

- Pestañas: **Carta · Grupos · Configuración**.
- **Carta**: lista agrupada por grupo (encabezados de grupo no editables acá) y "Sin grupo" al final. Cada categoría muestra: nombre con badge "de Fudo" (o "manual" para heredadas), selector de grupo, ↑↓ dentro del grupo, ojo (visible), ✎ (nota, `show_title`), badge de alerta si `fudo_status = 'missing'`. Se quita "+ Categoría".
- **Grupos**: lista con ↑↓, renombrar, borrar, "+ Grupo".
- **Ítem (modal)**: sin campo "Categoría" si tiene precios vinculados (muestra "Categoría: X (de Fudo)"); botones nuevos "Unir con otro ítem" (abre un selector con buscador de los demás ítems; el ítem abierto es el **origen** y se une al elegido) e "Ignorar". El selector de categoría sólo aparece en ítems 100% manuales.
- **Bandeja `/menu/inbox` → "Nuevos y alertas"**: nuevos ítems ocultos (acciones: Editar, Mostrar, Unir con…, Ignorar) y alertas (variantes y categorías).
- Aviso en `/menu` si existen categorías heredadas (sin `fudo_category_id`): "Hay N categorías creadas a mano: mové sus ítems o borralas".

## 6. Carta pública (`menu-site/`)

- `loadMenu` acepta v1 y v2; v1 se convierte a v2 en `normalizeMenu` como un único grupo sin título.
- Barra sticky: chips por **grupo**; scrollspy sobre secciones de grupo.
- Sección de grupo: título grande (si `name` no es null); dentro, cada categoría con subtítulo si `show_title`, y su `description` si tiene texto (aunque `show_title` sea false).
- `filterMenu` filtra en dos niveles y oculta categorías y grupos vacíos.

## 7. Limpieza

- Eliminar `backend/seed_menu.py`, `backend/data/menu_seed.json`, `backend/tests/test_seed_menu.py`.
- `menu-site/public/menu.sample.json` se regenera en formato v2 a mano (datos de ejemplo con 2 grupos, una categoría con `show_title: false`).

## 8. Testing

- Backend:
  - sync: crea categorías, actualiza nombres, marca `missing`, crea ítems ocultos, no recrea ignorados, recategoriza, "Sin categoría", no publica ítems ocultos.
  - grupos: CRUD, reorder (set exacto), borrar deja categorías sin grupo.
  - categorías: no se puede renombrar una de Fudo; reorder por grupo; `show_title`.
  - ítems: merge (variantes, categoría, origen borrado), ignore, `POST /items` sólo manual, `category_id` ignorado en ítems vinculados.
  - snapshot v2: orden, "Otros", sin grupos, grupos vacíos omitidos, `show_title`.
  - migración: upgrade/downgrade en schema temporal de Postgres (como en el feature anterior).
- menu-site: `normalizeMenu` v1→v2, `filterMenu` anidado, `activeSection` sobre grupos.

## Riesgos

- Producción puede tener categorías/ítems creados a mano: la migración no los toca; el aviso del panel guía la limpieza.
- La primera sync en producción creará cientos de ítems ocultos de golpe (uno por producto Fudo). Es esperado; la bandeja los lista para revisar.
- Contrato v2: se deploya primero `menu-site` (que acepta v1 y v2) y después el backend; si se deployan juntos, la carta online sigue leyendo el último v1 publicado hasta la próxima publicación.
