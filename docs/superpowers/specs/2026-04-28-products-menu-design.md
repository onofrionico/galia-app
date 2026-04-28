# Sub-proyecto 2: Productos / Menú — Spec de diseño

**Fecha:** 2026-04-28  
**Branch objetivo:** `feature/products-menu`  
**Parte de:** Hoja de ruta migración Fudo → Galia

---

## Objetivo

Reemplazar la gestión de menú y registro de ventas que hoy vive en Fudo POS. Galia pasará a ser el sistema de caja, con un catálogo de productos propio, variantes, gestión de mesas por salón y control de stock híbrido.

---

## Decisiones de diseño

| Tema | Decisión |
|---|---|
| Scope | Catálogo + ítems de venta + stock híbrido |
| Ventas | Galia reemplaza a Fudo para el registro de ventas nuevas |
| Categorías | Configurables desde la UI (CRUD) |
| Variantes | Sí, cada variante tiene su propio precio |
| Stock | Híbrido: cantidad directa en variante (simple) o receta de insumos (elaborado) |
| UI de caja | Plano de mesas por salón + POS táctil al abrir una mesa |
| Salones | Múltiples salones, cada uno con layout físico posicional |
| Implementación | Por capas: datos → catálogo → POS/ventas → stock |

---

## Modelo de datos

### Entidades nuevas

#### `ProductCategory`
```
id, name, description, color, icon, is_active, created_at, updated_at
```
Categorías configurables del menú (ej: Cafés, Panadería, Bebidas frías).

#### `Product`
```
id, name, description, category_id (FK → ProductCategory)
image_url, has_recipe (bool), is_active, created_at, updated_at
```
`has_recipe` determina el modo de stock: `false` → descuenta `stock_quantity` de la variante; `true` → descuenta insumos según receta.

#### `ProductVariant`
```
id, product_id (FK → Product), name (ej: "Chico", "Mediano", "Grande")
price, stock_quantity, min_stock, is_active, created_at, updated_at
```
Un producto sin variantes de tamaño igual tiene al menos una variante (precio único). `stock_quantity` y `min_stock` solo aplican cuando `product.has_recipe = false`; para productos con receta, el stock disponible se deriva de los insumos, y estos campos no se usan.

#### `ProductRecipeItem`
```
id, product_id (FK → Product), supply_id (FK → Supply)
quantity (decimal), unit (string)
```
Lista de insumos y cantidades para elaborar el producto. Solo aplica cuando `product.has_recipe = true`.

#### `Salon`
```
id, name, description, is_active, created_at, updated_at
```
Espacio físico diferenciado (ej: Salón Principal, Terraza, Salón VIP).

#### `Mesa`
```
id, salon_id (FK → Salon), number (int), name (string, opcional)
capacity (int), pos_x (float), pos_y (float), width (float), height (float)
status: 'libre' | 'ocupada' | 'reservada'
is_active, created_at, updated_at
```
`pos_x / pos_y / width / height` guardan la posición y tamaño en el plano del salón como valores porcentuales (0–100) relativos al contenedor, para que el layout sea responsive. Son actualizados desde el modo "Editar plano" del POS.

#### `SaleItem`
```
id, sale_id (FK → Sale), product_variant_id (FK → ProductVariant)
quantity (int), unit_price (decimal, snapshot al momento de venta), subtotal (decimal)
```
`unit_price` es un snapshot del precio al momento de la venta para que los reportes históricos no cambien si el precio del producto se actualiza después.

### Entidades existentes modificadas

#### `Sale` (extensión)
Campos nuevos:
- `source: 'fudo' | 'galia'` — distingue ventas históricas de Fudo de las registradas en Galia
- `mesa_id (FK → Mesa, nullable)` — mesa asociada a la venta

#### `Supply` (extensión)
Campos nuevos:
- `stock_quantity (decimal)` — cantidad actual en stock
- `min_stock (decimal)` — alerta cuando el stock baja de este valor

### Relaciones
```
ProductCategory 1:N Product
Product         1:N ProductVariant
Product         1:N ProductRecipeItem → Supply
Salon           1:N Mesa
Sale            1:N SaleItem → ProductVariant
Sale            N:1 Mesa
```

### Lógica de stock al registrar venta
Al guardar una `Sale` con items:
- Para cada `SaleItem`:
  - Si `product.has_recipe = false` → `ProductVariant.stock_quantity -= sale_item.quantity`
  - Si `product.has_recipe = true` → para cada `ProductRecipeItem` del producto: `Supply.stock_quantity -= recipe_item.quantity * sale_item.quantity`

---

## API endpoints

### Blueprint `product_categories` — `/api/v1/product-categories`
```
GET    /                    Lista de categorías activas
POST   /                    Crear categoría
PUT    /:id                 Editar categoría
DELETE /:id                 Desactivar categoría (soft delete)
```

### Blueprint `products` — `/api/v1/products`
```
GET    /                    Lista con filtros: category_id, search, is_active (paginada)
POST   /                    Crear producto
GET    /:id                 Detalle de producto
PUT    /:id                 Editar producto
DELETE /:id                 Desactivar producto (soft delete)

GET    /:id/variants        Lista de variantes del producto
POST   /:id/variants        Crear variante
PUT    /:id/variants/:vid   Editar variante
DELETE /:id/variants/:vid   Desactivar variante

GET    /:id/recipe          Receta del producto (si has_recipe)
PUT    /:id/recipe          Reemplazar receta completa (array de items)

GET    /low-stock           Variantes y/o insumos por debajo de min_stock
PUT    /:id/variants/:vid/stock   Ajuste manual de stock
```

### Blueprint `salons` — `/api/v1/salons`
```
GET    /                    Lista de salones activos
POST   /                    Crear salón
PUT    /:id                 Editar salón
DELETE /:id                 Desactivar salón

GET    /:id/mesas           Mesas del salón (incluye pos_x/y/width/height)
POST   /:id/mesas           Crear mesa en el salón
PUT    /:id/mesas/:mid      Editar mesa (incluye actualizar posición en el plano)
DELETE /:id/mesas/:mid      Desactivar mesa
```

### Blueprint `sales` — extendido
```
POST   /                    Crear venta (acepta items: [{variant_id, quantity}], mesa_id)
GET    /:id                 Detalle de venta (incluye sale_items con producto/variante)
GET    /daily-summary       Stats del día: total, cantidad, top productos (para el POS)
GET    /top-products        Ranking de productos más vendidos (filtro fecha)
```

---

## Frontend

### Nuevo grupo en Sidebar: "Menú"
- 🛒 **Caja** → `/pos`
- 🍽️ **Productos** → `/products`
- 🏷️ **Categorías** → `/product-categories`
- 📦 **Stock** → `/stock`

### Páginas nuevas

#### `/pos` — Caja
Vista principal del salón con tabs por salón. Cada tab muestra el plano físico del salón con las mesas posicionadas (libre / ocupada / reservada). 
- Click en **mesa libre** → abre modal POS para esa mesa
- Click en **mesa ocupada** → abre drawer lateral con la comanda activa (ítems + total + botones cobrar/agregar ítem/cerrar mesa)
- Click en **mesa reservada** → muestra info de la reserva
- Barra inferior: resumen del día (total vendido, cantidad de ventas, alertas de stock bajo)
- Botón **"⚙️ Editar plano"**: activa modo drag-and-drop para reposicionar/redimensionar mesas, agregar o desactivar. Guarda `pos_x/pos_y/width/height` vía `PUT /api/v1/salons/:id/mesas/:mid`

#### Modal POS (desde mesa libre)
- Tabs de categorías de productos en la parte superior
- Grilla de botones de productos (color por categoría) con precio
- Al tocar un producto con múltiples variantes → selector de tamaño
- Comanda lateral: lista de ítems, total acumulado, selector de medio de pago
- Botón **COBRAR** → registra la venta, descuenta stock, marca mesa como libre

#### `/products` — Lista de productos
Tabla con filtro por categoría. Columnas: nombre, categoría, variantes (chips con precio), estado. Acciones: crear, editar, desactivar. Links a `/products/:id`.

#### `/products/:id` — Detalle de producto
Tabs:
- **Info**: nombre, descripción, categoría, imagen, toggle `has_recipe`
- **Variantes**: tabla editable (nombre + precio + stock_quantity + min_stock por fila)
- **Receta** (visible si `has_recipe`): tabla de insumos con selector de `Supply` y cantidad/unidad
- **Historial**: ventas recientes que incluyen este producto

#### `/product-categories` — Categorías
CRUD simple. Sigue el patrón de `ExpenseCategories`. Campos: nombre, descripción, color (color picker), ícono (selector de emoji).

#### `/stock` — Inventario
Vista unificada:
- Sección "Stock directo": variantes de productos donde `product.has_recipe = false`, con `stock_quantity` / `min_stock`. Resalta en rojo las que estén bajo mínimo.
- Sección "Insumos": `Supply` con `stock_quantity` / `min_stock`. Mismo tratamiento visual.
- Ajuste manual inline: input de cantidad editable por fila.

### Servicios JS nuevos/modificados
- `productsService.js` — CRUD + variantes + receta + stock
- `productCategoriesService.js` — CRUD de categorías
- `salonsService.js` — CRUD de salones + mesas + layout
- `salesService.js` — extendido con `createSale(items, mesaId)`, `getDailySummary()`, `getTopProducts()`

---

## Implementación por capas

| Capa | Contenido |
|---|---|
| 1. Datos | Modelos SQLAlchemy + migraciones + todos los endpoints CRUD |
| 2. Catálogo | UI de productos, variantes, categorías, recetas |
| 3. POS + Ventas | Salones, mesas, plano físico, POS táctil, registro de ventas con ítems |
| 4. Stock | Vista de inventario, alertas de mínimo, ajuste manual |

Cada capa es desplegable y testeable de forma independiente antes de avanzar a la siguiente.

---

## Testing

- Tests unitarios de la lógica de descuento de stock (simple y por receta)
- Tests de endpoints: CRUD products, variants, salons, mesas, sale con items
- Verificar que `unit_price` en `SaleItem` es snapshot y no referencia mutable
- Verificar que ventas Fudo históricas (`source='fudo'`) no son afectadas por los nuevos endpoints
