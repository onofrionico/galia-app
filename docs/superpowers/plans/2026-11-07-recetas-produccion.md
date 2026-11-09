# Recetas de producción — plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sección de Recetas (vista de cocina + editor + costo) que reemplaza a la composición plana de productos (`product_recipe_items`) y gobierna el descuento de stock.

**Architecture:** Tres tablas nuevas (`recipes`, `recipe_ingredients`, `recipe_steps`) y un factor por variante (`product_variants.recipe_units`). Un servicio puro expande una receta a "insumos por unidad de rendimiento" (recursivo sobre bases, con conversión de unidades) y lo usan tanto `stock_service` como el cálculo de costo. Blueprint nuevo `/api/v1/recipes` con tres módulos de permiso. Frontend React: lista, vista de cocina mobile-first, editor, y el panel de receta en `ProductDetail`. La carga inicial es un JSON curado a mano + script idempotente con modo de prueba.

**Tech Stack:** Flask, SQLAlchemy, Alembic, pytest (backend `venv`), React + Vite + Tailwind, vitest.

**Spec:** `docs/superpowers/specs/2026-11-06-recetas-produccion-design.md`

## Global Constraints

- Tests backend: `cd backend && venv/Scripts/python.exe -m pytest <archivo> -q`. Frontend: `cd frontend && npm test`.
- Migraciones nuevas encadenan sobre la cabeza actual `b6e0_schedule_is_public`: `b7a0_add_recipes` y luego `b7a1_drop_product_recipe_items`. `tests/test_migration_chain.py::test_single_head` debe seguir pasando; agregar un test de encadenamiento por cada una, como los existentes.
- Módulos de permiso (nombre / display_name): `Recipes` / "Ver recetas", `RecipeCosts` / "Ver costo de recetas", `RecipesAdmin` / "Administrar recetas". Categoría `Operations`, ruta `/recipes`. Rol `admin` granted, rol `employee` **no** granted. Mismo patrón que el módulo `Conciliar` en `b5b0_add_mercadopago.py` (insert idempotente, downgrade borra permisos y módulo).
- Sin el módulo `RecipeCosts` el backend **no incluye** ninguna clave de costo en ninguna respuesta (recetas ni productos).
- Precio de insumo = último `SupplyPrice` (por `recorded_at` desc, `id` desc), expresado **por la unidad del insumo** (`supplies.unit`).
- Stock: se mantiene la cuantización a 0,001 y la simetría descuento/devolución de `stock_service`.
- Nunca inventar datos en la carga inicial: lo que la planilla no dice va a `pending_notes` o queda con cantidad `null`.
- Todo texto visible en español rioplatense, como el resto de la app.
- Cada endpoint nuevo lleva decorador de permiso explícito (`module_required` / `authenticated_only`); `tests/test_route_access_coverage.py` debe pasar.

## Review Focus

1. Base usada con una unidad distinta a su rendimiento (bizcocho rinde "1 unidad", se usa "500 g") → ingrediente no convertible: costo incompleto y no descuenta, sin romper la receta padre. Test en Task 2.
2. Ciclo indirecto (A usa B, B usa A) al guardar → 400 con mensaje claro. Test en Task 4.
3. Desactivar una base que otra receta activa usa, o una receta con stock activo → 409. Test en Task 4.
4. Empleado con `Recipes` pero sin `RecipeCosts` → ninguna clave `cost*` en lista, detalle ni producto. Test en Task 4.
5. Venta de un producto cuya receta tiene un ingrediente `quantity=null` → la venta pasa, los demás insumos se descuentan y la devolución restituye lo mismo. Test en Task 3.

---

### Task 1: Conversión de unidades

**Files:**
- Create: `backend/app/services/units.py`
- Test: `backend/tests/test_units.py`

**Interfaces:**
- Produces: `normalize_unit(unit: str | None) -> str | None` (devuelve una unidad canónica `'g' | 'kg' | 'ml' | 'l' | 'unidad'` o `None` si no se reconoce) y `convert(quantity: Decimal, from_unit: str | None, to_unit: str | None) -> Decimal | None` (`None` si no son de la misma familia o alguna no se reconoce).

- [ ] **Step 1: Tests**

```python
@pytest.mark.parametrize('raw,expected', [
    ('g', 'g'), ('gr', 'g'), ('Gramos', 'g'), ('KG', 'kg'), ('kilo', 'kg'),
    ('ml', 'ml'), ('cc', 'ml'), ('L', 'l'), ('lt', 'l'), ('litro', 'l'),
    ('u', 'unidad'), ('unid', 'unidad'), ('Unidades', 'unidad'),
    ('cucharada', None), ('pizca', None), ('', None), (None, None),
])
def test_normalize_unit(raw, expected): assert normalize_unit(raw) == expected

def test_convert_mass(): assert convert(Decimal('250'), 'g', 'kg') == Decimal('0.25')
def test_convert_volume(): assert convert(Decimal('1.5'), 'l', 'cc') == Decimal('1500')
def test_convert_same_unit(): assert convert(Decimal('3'), 'unid', 'unidad') == Decimal('3')
def test_convert_cross_family_is_none(): assert convert(Decimal('1'), 'g', 'ml') is None
def test_convert_unknown_is_none(): assert convert(Decimal('2'), 'cucharada', 'g') is None
```

- [ ] **Step 2:** Correr, ver que falla (módulo inexistente).
- [ ] **Step 3:** Implementar en `units.py` con una tabla de alias → (canónica, familia, factor a base: g, ml, unidad). Comparar sin tildes, en minúsculas, sin espacios ni punto final.
- [ ] **Step 4:** Correr, pasa.
- [ ] **Step 5:** Commit `feat(recetas): conversión de unidades`.

---

### Task 2: Modelos, migración b7a0 y expansión de recetas

**Files:**
- Create: `backend/app/models/recipe.py` (`Recipe`, `RecipeIngredient`, `RecipeStep`)
- Modify: `backend/app/models/__init__.py`, `backend/app/models/product_variant.py` (columna `recipe_units`), `backend/app/models/product.py` (relación `recipe`)
- Create: `backend/migrations/versions/b7a0_add_recipes.py`
- Create: `backend/app/services/recipe_service.py`
- Test: `backend/tests/test_recipe_service.py`, `backend/tests/test_recipe_migration.py`, `backend/tests/test_migration_chain.py`

**Interfaces:**
- Produces (modelos):
  - `Recipe`: `id`, `name` String(150) unique, `product_id` FK products **unique** nullable, `yield_quantity` Numeric(10,3) nullable, `yield_unit` String(30) nullable, `total_time_minutes` Integer nullable, `advance_notes` Text (ej. "1 día de freezer antes de hornear"), `notes` Text, `pending_notes` Text ("a completar", visible como aviso), `is_active` Boolean default True, `updated_by` FK users nullable, `created_at`, `updated_at`. Relaciones `ingredients` y `steps` ordenadas por `position`, cascade delete-orphan; `product` (backref `Product.recipe`, uselist=False).
  - `RecipeIngredient`: `id`, `recipe_id`, `position` Integer, `supply_id` FK nullable, `sub_recipe_id` FK recipes nullable (CheckConstraint: exactamente uno de los dos), `quantity` Numeric(12,4) **nullable** (null = a completar / a ojo), `unit` String(30) nullable, `note` String(200) nullable ("pizca", "a ojo").
  - `RecipeStep`: `id`, `recipe_id`, `position`, `title` String(120), `instruction` Text, `temperature_c` Integer nullable, `time_min` Integer nullable, `time_max` Integer nullable, `doneness` Text nullable, `tip` Text nullable.
  - `ProductVariant.recipe_units` Numeric(10,3) not null default 1 (server_default '1').
- Produces (servicio): `expand_per_yield_unit(recipe: Recipe) -> Expansion` donde `Expansion` es un dataclass con `supplies: dict[int, Decimal]` (cantidad en la unidad del insumo por 1 unidad de rendimiento) e `issues: list[str]` (mensajes "Manteca: unidad 'cucharada' no convertible a kg", "Leche: cantidad a completar", "Bizcocho: sin rendimiento"). Una receta sin `yield_quantity` (o ≤ 0) devuelve `supplies={}` y un issue. Sub-receta: cantidad del ingrediente convertida a `yield_unit` de la base, multiplicada por la expansión de la base. Protección de ciclos con un set de visitados (levanta `ValueError('Ciclo de recetas: ...')`).
- Produces: `RECIPE_MODULES = ('Recipes', 'RecipeCosts', 'RecipesAdmin')` en `recipe_service.py`.

- [ ] **Step 1: Tests de expansión** (`test_recipe_service.py`, fixture `app` como en `test_stock_service.py`)

```python
def test_batch_divided_by_yield():           # chipa: 1000 g mandioca (insumo en kg), rinde 20 → 0.05 kg
def test_sub_recipe_expands_through_base():  # torta usa 1 "unidad" de bizcocho (rinde 1 unidad, 400 g harina) → 0.4 kg harina por torta
def test_sub_recipe_in_grams_of_base_in_grams()  # base rinde 1200 g, se usan 600 g → mitad de cada insumo
def test_base_unit_mismatch_is_issue():      # base rinde "1 unidad", se usa "500 g" → supplies sin esos insumos, issue con el nombre de la base
def test_null_quantity_is_issue_not_error(): # quantity None → issue "cantidad a completar", el resto se expande
def test_missing_yield_is_issue():           # yield None → supplies == {}, 1 issue
def test_cycle_raises():                     # A→B→A → ValueError
```

- [ ] **Step 2:** Correr, falla.
- [ ] **Step 3:** Modelos + `expand_per_yield_unit`.
- [ ] **Step 4:** Correr, pasa.
- [ ] **Step 5: Migración `b7a0_add_recipes`** (down_revision `b6e0_schedule_is_public`): crea las tres tablas, agrega `recipe_units`, inserta los tres módulos (patrón `Conciliar`), y copia la composición actual con una función de módulo `copy_compositions(bind)`: por cada producto con filas en `product_recipe_items` crea una `Recipe` con `name` = nombre del producto (si choca, sufijo " (producto #id)"), `product_id` = producto, `yield_quantity=1`, `yield_unit='unidad'`, `pending_notes='Migrada de la composición anterior: faltan pasos.'`, e ingredientes con la **misma cantidad** y `unit = supplies.unit` (no la `unit` de la fila vieja: así la conversión es identidad y el descuento no cambia). `product_recipe_items` **no** se borra todavía. Downgrade: borra módulos, columna y tablas.
- [ ] **Step 6: Test** `test_recipe_migration.py::test_copy_compositions_keeps_quantities`: crear producto con dos `ProductRecipeItem` (unidad de fila 'g' distinta a insumo 'kg'), importar el módulo de migración con `importlib`, correr `copy_compositions(db.session.connection())`, verificar receta vinculada, rinde 1, ingredientes con cantidad idéntica y `unit == supply.unit`, y que `expand_per_yield_unit` devuelve exactamente las cantidades viejas. Y `test_copy_compositions_is_idempotent` (correr dos veces no duplica: saltea productos que ya tienen receta).
- [ ] **Step 7:** Agregar `test_recipes_follows_schedule_is_public` en `test_migration_chain.py`; correr `test_migration_chain.py`, `test_recipe_*.py`.
- [ ] **Step 8:** Commit `feat(recetas): modelos, migración y expansión de recetas`.

---

### Task 3: El stock usa la receta; se retira `product_recipe_items`

**Files:**
- Modify: `backend/app/services/stock_service.py` (`stock_requirements`)
- Modify: `backend/app/routes/products.py` (quitar `GET/PUT /<id>/recipe`; `has_recipe` deja de aceptarse en create/update — se ignora; `to_dict` del detalle agrega `recipe: {id, name} | None`)
- Modify: `backend/app/services/product_fudo_info.py` (usa `product.recipe`)
- Delete: `backend/app/models/product_recipe_item.py`; quitar de `models/__init__.py` y la relación en `Product`
- Create: `backend/migrations/versions/b7a1_drop_product_recipe_items.py` (down_revision `b7a0_add_recipes`; downgrade recrea la tabla y la repuebla desde recetas vinculadas con rinde 1)
- Modify tests/helpers: `tests/pos_helpers.py`, `tests/test_stock_moves.py`, `tests/test_stock_service.py`, `tests/test_products.py`, `tests/test_products_fudo_lock.py`, `tests/test_product_sync.py` → crear `Recipe` + `RecipeIngredient` (rinde 1, unidad del insumo) en lugar de `ProductRecipeItem`; borrar tests de los endpoints `/recipe` eliminados.
- Test: `backend/tests/test_stock_service.py`, `backend/tests/test_migration_chain.py`

**Interfaces:**
- Consumes: `expand_per_yield_unit` (Task 2).
- Produces: comportamiento — producto con `has_recipe=True` y `recipe` vinculada descuenta `expansion.supplies[s] × variant.recipe_units × cantidad`. Sin receta vinculada o con issues, descuenta lo que sí se pudo expandir; nunca levanta por issues. Producto con `has_recipe=True` sin receta: no descuenta insumos.

- [ ] **Step 1: Tests nuevos** en `test_stock_service.py`:

```python
def test_recipe_batch_with_yield_deducts_per_unit():    # rinde 20, 1000 g mandioca (insumo kg, stock 5) → vender 2 descuenta 0.1
def test_variant_recipe_units_multiplies():             # torta rinde 12 porciones; variante Entera recipe_units=12 descuenta 12× la Porción
def test_incomplete_ingredient_does_not_block_sale():   # ingrediente quantity None + otro válido → venta OK, sólo el válido baja; devolución (move_stock sign=1) lo restituye
def test_linked_but_inactive_recipe_does_not_deduct():  # has_recipe False, track_stock False, receta vinculada → nada
```

- [ ] **Step 2:** Correr, fallan.
- [ ] **Step 3:** Cambiar `stock_requirements`; migrar helpers y tests existentes; borrar modelo y endpoints.
- [ ] **Step 4:** Migración `b7a1` + test de encadenamiento.
- [ ] **Step 5:** Correr la suite completa del backend: `venv/Scripts/python.exe -m pytest -q`. Esperado: todo verde salvo tests que ya fallan en `main` (correr la suite en `main` para comparar y listar esos casos en el commit).
- [ ] **Step 6:** Commit `feat(recetas): el stock se descuenta desde la receta`.

---

### Task 4: Costo y API de recetas

**Files:**
- Modify: `backend/app/services/recipe_service.py` (costo, validación y guardado)
- Create: `backend/app/routes/recipes.py`; registrar en `backend/app/__init__.py`
- Modify: `backend/app/routes/products.py` (detalle: `recipe_cost` sólo con `RecipeCosts`)
- Test: `backend/tests/test_recipe_cost.py`, `backend/tests/test_recipes_api.py`

**Interfaces:**
- Consumes: `expand_per_yield_unit`, `convert`, `check_module_access(user, name)`.
- Produces (servicio):
  - `recipe_cost(recipe) -> dict`: `{'batch_cost': Decimal|None, 'unit_cost': Decimal|None, 'complete': bool, 'issues': [str], 'lines': [{'ingredient_id', 'cost': Decimal|None, 'issue': str|None}]}`. Línea de insumo = cantidad convertida a `supply.unit` × último precio; sin precio → issue "Sin precio cargado". Línea de base = cantidad convertida a `yield_unit` de la base × `unit_cost` de la base. `batch_cost` = suma de líneas con costo; `unit_cost = batch_cost / yield_quantity` (None si no hay rendimiento). `complete` = sin issues.
  - `save_recipe(recipe: Recipe | None, payload: dict, user) -> Recipe` — valida y reemplaza ingredientes y pasos completos (como el PUT viejo); levanta `RecipeError(message, status)`.
- Produces (API, prefijo `/api/v1/recipes`):

| Método y ruta | Módulo | Notas |
|---|---|---|
| `GET ''` | `Recipes` | `?q=`, `?bases=1` (sin producto), sólo activas. Ítem: `id, name, product: {id,name}|null, yield_quantity, yield_unit, total_time_minutes, has_pending, is_base` (+ `unit_cost, cost_complete` con `RecipeCosts`) |
| `GET '/<id>'` | `Recipes` | receta completa: ingredientes con `supply: {id,name,unit}` o `sub_recipe: {id,name}`, pasos, `pending_notes`, `updated_at`, `updated_by_name`, `used_in: [{id,name}]` (+ `cost` = `recipe_cost` con `RecipeCosts`) |
| `POST ''` | `RecipesAdmin` | crea, 201 |
| `PUT '/<id>'` | `RecipesAdmin` | reemplaza todo; 400 si ciclo, insumo/base inexistente o inactiva, cantidad ≤ 0, nombre duplicado; 409 si quita el rendimiento con stock activo |
| `DELETE '/<id>'` | `RecipesAdmin` | `is_active=False`; 409 si es base de otra receta activa o su producto tiene `has_recipe=True` |
| `PUT '/<id>/product'` | `RecipesAdmin` | body `{product_id: int|null, stock_active: bool, variant_units: {variant_id: number}}`. 409 si el producto ya tiene otra receta; 400 si `stock_active` sin rendimiento o con `track_stock=True` en el producto. Setea `product.has_recipe = stock_active` y `recipe_units` de cada variante (> 0). |

  Toda respuesta pasa por un serializador `serialize_recipe(recipe, include_cost: bool)`; `include_cost = check_module_access(user, 'RecipeCosts')`.

- [ ] **Step 1: Tests de costo** (`test_recipe_cost.py`):

```python
def test_cost_uses_latest_price_and_converts():  # 250 g manteca, precio 8000/kg (último de dos) → línea 2000
def test_unit_cost_divides_by_yield():           # batch 3000, rinde 20 → unit_cost 150
def test_base_cost_flows_into_parent():          # base rinde 1000 g con batch 5000 (unit_cost 5/g); padre usa 300 g → línea 1500
def test_missing_price_is_incomplete():          # complete False, issue con el nombre del insumo
```

- [ ] **Step 2: Tests de API** (`test_recipes_api.py`, usuarios con `UserPermission` como en `pos_helpers.py`):

```python
def test_employee_without_recipes_module_gets_403()
def test_viewer_sees_recipe_without_any_cost_keys()   # recorre el JSON (lista, detalle y GET /products/<id>) y afirma que ninguna clave contiene 'cost'
def test_cost_viewer_gets_cost()
def test_viewer_cannot_edit()                          # PUT con sólo Recipes → 403
def test_indirect_cycle_rejected()                     # 400
def test_delete_base_in_use_conflicts()                # 409
def test_link_and_activate_sets_has_recipe_and_units()
def test_activate_without_yield_rejected()             # 400
def test_link_product_with_other_recipe_conflicts()    # 409
```

- [ ] **Step 3:** Correr, fallan.
- [ ] **Step 4:** Implementar servicio y blueprint.
- [ ] **Step 5:** Correr estos tests + `test_route_access_coverage.py` + `test_products.py`; pasan.
- [ ] **Step 6:** Commit `feat(recetas): costo y API de recetas`.

---

### Task 5: Frontend — lista y vista de cocina

**Files:**
- Create: `frontend/src/services/recipesService.js` (`list({q, bases})`, `get(id)`, `create(data)`, `update(id, data)`, `remove(id)`, `linkProduct(id, data)`)
- Create: `frontend/src/pages/Recipes.jsx`, `frontend/src/pages/RecipeView.jsx`
- Create: `frontend/src/components/recipes/format.js` + `format.test.js`
- Modify: `frontend/src/App.jsx` (rutas `/recipes`, `/recipes/:id` con `RoleProtectedRoute moduleName="Recipes"`), `frontend/src/components/layout/Sidebar.jsx` (ítem "Recetas", ícono `BookOpen`, `module: 'Recipes'`, en la sección `productos` después de "Productos")

**Interfaces:**
- Consumes: API de Task 4.
- Produces: `formatStepTime(min, max) -> string` ("12 min", "10–12 min", "1 h 15 min", "" si ambos null), `formatQuantity(quantity, unit, note) -> string` ("250 g", "2 unidades", "pizca", "a completar" si quantity null y sin note), `formatYield(quantity, unit)`.

- [ ] **Step 1:** Tests vitest de `format.js` con esos ejemplos exactos.
- [ ] **Step 2:** Correr `npm test`, falla; implementar; pasa.
- [ ] **Step 3: `Recipes.jsx`**: buscador, filtro "Todas / Productos / Bases", tarjetas grandes (nombre, rinde, tiempo, insignia "A completar" si `has_pending`, costo por unidad si viene en la respuesta). Botón "Nueva receta" sólo si `hasModuleAccess('RecipesAdmin')`.
- [ ] **Step 4: `RecipeView.jsx`** (mobile-first, `max-w-2xl`, base `text-lg`): encabezado (nombre, rinde, tiempo total, `advance_notes` en un aviso destacado, `pending_notes` en aviso ámbar); ingredientes en lista con cantidad a la izquierda en negrita, las bases como enlace a `/recipes/<id>`; pasos numerados, un bloque por paso: título, instrucción, y chips para temperatura ("180 °C"), tiempo, punto (ícono ojo) y consejo (ícono alerta). Bloque de costo sólo si `recipe.cost` existe. Botón "Editar" sólo con `RecipesAdmin`. Nada para escribir.
- [ ] **Step 5:** Verificar en el navegador con el dev server: lista y una receta a 375 px y 768 px de ancho, sin scroll horizontal; con un usuario sin `RecipeCosts` no aparece costo.
- [ ] **Step 6:** Commit `feat(recetas): lista y vista de cocina`.

---

### Task 6: Frontend — editor y panel en el producto

**Files:**
- Create: `frontend/src/pages/RecipeEditor.jsx` (rutas `/recipes/new` y `/recipes/:id/edit`, `moduleName="RecipesAdmin"`)
- Create: `frontend/src/components/recipes/IngredientRow.jsx`, `StepEditor.jsx`, `ProductLinkPanel.jsx`
- Modify: `frontend/src/pages/ProductDetail.jsx` (reemplaza el bloque de receta y el checkbox `has_recipe` por `ProductLinkPanel` en sólo lectura + enlace), `frontend/src/services/productsService.js` (quitar `getRecipe/saveRecipe`), `frontend/src/pages/Products.jsx` y `Stock.jsx` (siguen usando `has_recipe` del listado; sin cambios salvo que se rompan)

**Interfaces:**
- Consumes: `recipesService`, `GET /supplies`, `GET /recipes?bases=1`, `GET /products` (para vincular).

- [ ] **Step 1: Editor**: datos generales (nombre, rinde cantidad + unidad, tiempo total, preparación previa, notas, "a completar"); ingredientes con buscador combinado insumos + bases, cantidad (vacía permitida), unidad (por defecto la del insumo o el rendimiento de la base), nota; pasos con agregar/quitar/subir/bajar y los campos título, indicación, temperatura, tiempo mín/máx, punto, consejo. Guardar = un solo `PUT`; errores 400/409 del backend se muestran tal cual arriba del formulario.
- [ ] **Step 2: Panel de producto** (`ProductLinkPanel`) dentro del editor: elegir producto, "Usar esta receta para el stock" (deshabilitado si el producto tiene `track_stock` o no hay rendimiento, con el motivo), y por variante "unidades de la tanda que usa" (default 1).
- [ ] **Step 3: `ProductDetail`**: muestra receta vinculada (nombre, rinde, si gobierna stock, costo por unidad si viene) con enlace "Ver receta"; sin receta: texto "Sin receta" y, con `RecipesAdmin`, enlace "Crear receta".
- [ ] **Step 4:** Verificar en navegador: crear una base y una receta que la use, vincular a un producto, activar stock, ver el producto; probar el error de ciclo.
- [ ] **Step 5:** `npm run build` sin errores. Commit `feat(recetas): editor y vínculo con productos`.

---

### Task 7: Carga inicial del recetario

**Files:**
- Create: `backend/scripts/data/recetario_galia.json`
- Create: `backend/scripts/import_recetario.py`
- Create: `docs/recetas-carga-inicial.md`
- Test: `backend/tests/test_import_recetario.py`

**Interfaces:**
- JSON: `{"recipes": [ {name, product_name|null, is_base, yield_quantity|null, yield_unit|null, total_time_minutes|null, advance_notes, notes, pending_notes, ingredients: [{supply_name | sub_recipe_name, quantity|null, unit, note}], steps: [{title, instruction, temperature_c, time_min, time_max, doneness, tip}]} ], "doubts": [str]}`.
- Script: `python scripts/import_recetario.py [--apply]` (sin `--apply` = prueba: no escribe, imprime el informe). Produce `run_import(data: dict, apply: bool) -> Report` con `created_recipes, skipped_existing, linked, unlinked_reasons, created_supplies, unmatched_products`.

- [ ] **Step 1: Transcribir la planilla** al JSON. Fuente: cada hoja por CSV en `https://docs.google.com/spreadsheets/d/1grtlaZxzwFb3Fmy2WSiLqE7bJyvwU7s1L59bKSWAS30/gviz/tq?tqx=out:csv&sheet=<hoja>` (hojas: Cookies, Chipa, Muffins, crumble, Galletitas de Nuez, scones, Banoffee, Matilda, Souffle de nuez, Torta Galia). Reglas: pasos en el formato de "Galletitas de Nuez", separando temperatura/tiempo/punto en sus campos **sólo si la planilla los dice**; lo que falta va a `pending_notes`; las dudas del spec (yema vs 2 huevos, ganache de Matilda, 6,5 cookies, queso en el crumble, polvo de hornear 10 vs 12 g) van a `doubts` y se cargan tal cual; cookies y muffins: una receta por variedad; bases como recetas `is_base` sólo donde la planilla las trae idénticas — si difieren, cada receta conserva su versión y la diferencia va a `doubts`.
- [ ] **Step 2: Tests** del importador (`test_import_recetario.py`) con un JSON chico:

```python
def test_dry_run_writes_nothing()
def test_matches_supply_ignoring_case_and_accents()   # "azucar rubia" ↔ "Azúcar Rubia"
def test_creates_missing_supply_without_price()
def test_links_product_without_recipe_but_does_not_activate_stock()  # has_recipe sigue False
def test_does_not_overwrite_product_that_already_has_recipe()        # queda sin vincular, en unlinked_reasons
def test_rerun_skips_existing_recipe_by_name()
def test_sub_recipes_created_before_parents()
```

- [ ] **Step 3:** Correr, falla; implementar `run_import`; pasa.
- [ ] **Step 4:** Correr el script en prueba contra la base local con datos de ejemplo y verificar el informe.
- [ ] **Step 5:** Escribir `docs/recetas-carga-inicial.md`: lista de "a completar" por receta, dudas para pastelería, bases extraídas, y cómo correr el script en producción (primero sin `--apply`, revisar, después con `--apply`).
- [ ] **Step 6:** Commit `feat(recetas): carga inicial del recetario`.
