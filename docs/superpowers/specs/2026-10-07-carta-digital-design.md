# Carta digital interactiva — Diseño

**Fecha:** 2026-10-07
**Estado:** Aprobado en brainstorming, pendiente de revisión del spec

## Objetivo

Reemplazar la carta actual (PDF de 7 páginas, `Carta_01.pdf` en Drive) por una carta web interactiva, accesible por QR desde las mesas, administrada desde galia-app y con precios sincronizados desde Fudo.

## Decisiones tomadas

| Tema | Decisión |
|---|---|
| Fuente de datos | Todo se administra en galia-app (no Google Sheets) |
| Precios | Se sincronizan desde Fudo; manuales solo si la variante no está vinculada |
| Entrega al público | Snapshot `menu.json` publicado a S3 público; sitio estático lo lee |
| Funcionalidades públicas | Navegación por categorías, buscador, fotos, etiquetas/filtros |
| Fuera de alcance (v1) | "Agotado", multi-idioma, pedidos online, dominio propio |
| Hosting | Render static site `galia-carta` → `galia-carta.onrender.com` |
| Fotos | Subidas desde galia-app, optimizadas a WebP y guardadas en S3 público |

## Arquitectura

```
Fudo ──(sync productos/precios)──▶ galia-app backend ◀── pantalla "Carta" (admin)
                                        │
                                  [Publicar / sync nocturno]
                                        ▼
                    S3 bucket existente, prefijo público menu/: menu.json + images/
                                        ▼
                     menu-site/ (static, Render) ◀── QR en las mesas
```

Tres unidades independientes:

1. **Backend (galia-app)**: modelos de carta, sync con Fudo, endpoints admin, publicador del snapshot.
2. **Admin (frontend/)**: pantallas de gestión de la carta.
3. **Carta pública (menu-site/)**: sitio estático que solo depende del contrato de `menu.json`.

## 1. Modelo de datos (backend)

Nuevo archivo `backend/app/models/menu.py`:

- **MenuCategory**: `id, name, slug (unique), description, sort_order, is_visible, created_at, updated_at`
- **MenuItem**: `id, category_id (FK), name, description, image_key (nullable), sort_order, is_visible, is_featured, created_at, updated_at`
- **MenuItemVariant**: `id, item_id (FK, cascade), label (nullable), fudo_product_id (nullable, unique), price (Numeric 10,2), fudo_status ('ok'|'inactive'|'missing', nullable), sort_order`
- **MenuTag**: `id, name, slug (unique), color`
- **menu_item_tags**: tabla asociativa item ⟷ tag
- **FudoProduct** (caché de la última sync): `fudo_id (PK), name, price, category_name, is_active, ignored (bool), synced_at`
- **MenuSettings**: clave/valor (`footer_text`, `instagram`, `last_published_at`, `last_published_hash`)

Reglas:
- Ítem con un solo precio = una variante con `label` nulo.
- Si `fudo_product_id` está seteado, `price` lo escribe solo la sync (la API admin rechaza cambios de precio en esa variante).
- Migración Alembic en `backend/migrations/versions/`.

## 2. Sincronización con Fudo

- `FudoClient` (`backend/app/utils/fudo_client.py`) suma `get_products(page_number)` / `get_all_products()` y `get_all_product_categories()`, reutilizando `_make_request`. Referencia: OpenAPI en `https://api.fu.do/v1alpha1/openapi.yml` (docs: https://dev.fu.do/api/).
  - `GET /products`: paginado `page[size]` (máx. 500) / `page[number]`; `include=productCategory`; `fields[product]=name,price,active,position,description,imageUrl`. Respuesta JSON:API: `data[].id`, `data[].attributes.{name, price, active, position, description, imageUrl}`, `data[].relationships.productCategory.data.id`.
  - `GET /product-categories`: `data[].id`, `data[].attributes.{name, position}`. Se usa solo para mostrar la categoría de Fudo en la bandeja "Sin asignar" y en el selector de productos.
  - Se piden todos los productos (activos e inactivos) para poder detectar desactivaciones.
- Servicio `backend/app/services/menu_sync_service.py`:
  1. Trae todos los productos y categorías de Fudo y hace upsert en `FudoProduct` (guardando `category_name`).
  2. Para cada variante vinculada: actualiza `price`; `fudo_status = 'inactive'` si el producto está inactivo, `'missing'` si ya no existe, `'ok'` si no.
  3. Nunca crea, borra ni mueve ítems de la carta.
- "Sin asignar" = `FudoProduct` activos, no ignorados, sin variante vinculada.
- Disparadores: botón "Sincronizar Fudo" en admin + job nocturno que sincroniza y, si cambió algún precio, republica.

## 3. Publicación del snapshot

- Servicio `backend/app/services/menu_publish_service.py` arma el JSON con solo categorías e ítems visibles, ordenados, y lo sube a `s3://<AWS_S3_BUCKET_NAME>/menu/menu.json` con `Cache-Control: max-age=60`.
- "Hay cambios sin publicar": se compara el hash del JSON generado contra `last_published_hash`.
- Se reutiliza el **bucket existente** (el de comprobantes). Todo lo de la carta vive bajo el prefijo `menu/`, que es lo único público:
  - Bucket policy con `s3:GetObject` para `Principal: "*"` **solo** sobre `arn:aws:s3:::<bucket>/menu/*`. Los comprobantes y documentos siguen privados.
  - En "Block Public Access" del bucket hay que desactivar *BlockPublicPolicy* y *RestrictPublicBuckets* (para permitir esa policy). *BlockPublicAcls* e *IgnorePublicAcls* quedan activados: no se usan ACLs.
  - CORS del bucket: `GET`/`HEAD` desde `https://galia-carta.onrender.com` y `http://localhost:5174`.
  - El usuario IAM ya tiene `PutObject`/`DeleteObject` sobre `<bucket>/*`; no requiere cambios.
  - Variable nueva: `MENU_PUBLIC_BASE_URL` (ej. `https://<bucket>.s3.<region>.amazonaws.com/menu`). El bucket sale de la config S3 existente.
  - El código de subida de la carta debe forzar el prefijo `menu/` (nunca escribir fuera de él), y los servicios existentes nunca escriben bajo `menu/`.

Contrato `menu.json` (versión 1):

```json
{
  "version": 1,
  "published_at": "2026-10-07T15:00:00Z",
  "settings": { "footer_text": "...", "instagram": "..." },
  "tags": [{ "slug": "sin-tacc", "name": "Sin TACC", "color": "#7FA34A" }],
  "categories": [
    {
      "slug": "cafes",
      "name": "Cafés",
      "description": "Contanos si lo preferís con azúcar, stevia o sin nada",
      "items": [
        {
          "id": 12,
          "name": "Latte Vainilla",
          "description": null,
          "image": "https://.../images/ab12cd.webp",
          "featured": true,
          "tags": ["recomendado"],
          "variants": [{ "label": null, "price": 6900 }]
        }
      ]
    }
  ]
}
```

## 4. Fotos

- Upload desde el modal de ítem → backend redimensiona (máx. 800px de lado) y convierte a WebP con Pillow → sube a `menu/images/<sha256-corto>.webp` con `Cache-Control: max-age=31536000, immutable`.
- Al reemplazar la foto, la anterior se borra al publicar si ya no la referencia ningún ítem.
- Límite: 10 MB por archivo, solo JPG/PNG/WebP (los navegadores de iPhone convierten HEIC a JPEG al subir).

## 5. API admin

Blueprint `backend/app/routes/menu.py`, prefijo `/api/v1/menu`, todo con `token_required` + `admin_required`:

- `GET /` — árbol completo (categorías → ítems → variantes, tags) + estado (sin publicar, cantidad sin asignar/alertas)
- CRUD `categories`, `items`, `tags`; `PUT /categories/reorder`, `PUT /categories/<id>/items/reorder`
- `POST /items/<id>/image` (multipart), `DELETE /items/<id>/image`
- `GET /fudo-products?unassigned=true&q=` ; `POST /fudo-products/<id>/ignore`
- `POST /sync` ; `POST /publish`
- `GET/PUT /settings`

## 6. Admin (frontend/)

Nuevo grupo **Carta** en `Sidebar.jsx`. Servicio `frontend/src/services/menuService.js`.

- **`/menu`** (`pages/Menu.jsx`): categorías colapsables con ítems; botones ↑↓ para reordenar categorías e ítems; toggle de visibilidad; badges de estado Fudo; barra superior con "Sincronizar Fudo", "Publicar", indicador de cambios sin publicar, contador de sin asignar/alertas y link "Ver carta". Pestaña **Configuración** para tags y settings.
- **Modal de ítem** (`components/menu/MenuItemModal.jsx`): nombre, descripción, categoría, tags, foto con preview, lista de variantes con selector de producto Fudo (buscador). Precio de variante vinculada en solo lectura.
- **`/menu/inbox`** (`pages/MenuInbox.jsx`): productos Fudo sin asignar (crear ítem / agregar como variante / ignorar) y variantes con alerta.
- Usable en mobile (tarjetas en lugar de filas, modal a pantalla completa).

## 7. Carta pública (menu-site/)

- React + Vite + Tailwind en `menu-site/`. Env: `VITE_MENU_URL`.
- Render: nuevo servicio static `galia-carta` en `render.yaml`. Agregar el origen a la CORS del bucket.
- Pantalla única, mobile-first:
  - Header con logo (PNG transparente) y flores.
  - Buscador sin tildes/mayúsculas sobre nombre + descripción; oculta categorías vacías.
  - Chips de tags como filtros (AND).
  - Barra de categorías sticky con scrollspy.
  - Ítems con foto (tarjeta) o sin foto (fila compacta); destacados marcados; variantes como `Porción $11.200 · Entera $12.600`.
  - Foto ampliada al tocar.
  - Footer con `footer_text`.
  - Precios en formato `es-AR` (`$6.900`).
- Identidad: fondo crema, bordó en títulos, acentos lima/coral, tipografía condensada gruesa (Google Fonts, a elegir la más cercana al logo).
- Assets de marca (Drive, compartidos con link):
  - Logos transparentes: carpeta "Logos fondo Transp" (`1lr_XXH-jmiKS3EEqYWCfU0PDIvB2ywzs`)
  - Logos fondo blanco: carpeta "Logos Fondo Blanco" (`1VOQiJnakoCXBmCT7YtAduLFp1epvY5H3`)
  - Ilustraciones: carpeta "ILUSTRACIONES" (`1cSEcMuVWjwoTIR4neUK8j1X9C4ncLgXC`)
  - Se eligen y optimizan los necesarios y se guardan en `menu-site/public/`.
- Resiliencia: guarda el último `menu.json` válido en `localStorage`; si falla la carga lo usa; si nunca hubo uno, muestra "Pedile la carta a nuestro equipo".

## 8. Carga inicial

Script `backend/seed_menu.py` con la transcripción de `Carta_01.pdf` (categorías, ítems, descripciones, variantes y precios actuales, sin vincular a Fudo). Después la encargada vincula variantes con productos Fudo desde el admin. El texto del PDF no conserva la relación plato↔precio, así que la transcripción se hace página por página mirando el PDF.

## 9. Testing

- `backend/tests/test_menu_sync.py`: actualización de precios, estados `inactive`/`missing`, sin asignar, ignorados, la sync no crea/borra ítems.
- `backend/tests/test_menu_publish.py`: forma del JSON, filtra ocultos, orden, hash/cambios sin publicar (S3 mockeado).
- `backend/tests/test_menu_routes.py`: permisos admin, rechazo de precio manual en variante vinculada, reordenamiento.
- `menu-site`: tests unitarios de búsqueda (normalización de tildes) y filtros por tag.

## Pendientes / riesgos

- `stock`/`stockControl` de Fudo permitirían más adelante el estado "Agotado" automático (fuera de alcance v1).
- Fudo tiene su propio menú QR (`enableQrMenu`); esta carta lo reemplaza y no lo usa.
- Configurar en la consola AWS la bucket policy del prefijo `menu/`, los ajustes de Block Public Access y la CORS (lo hace el usuario; el plan incluye el JSON exacto).
- Render free/starter: el static site no se duerme; no depende del backend en runtime.
