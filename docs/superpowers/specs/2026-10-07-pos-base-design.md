# POS Base (sub-proyecto 0) — Diseño

**Fecha:** 2026-10-07
**Rama:** `feature/pos-base` (desde `main` @ `d31feec`)
**Rama fuente:** `origin/release/products-menu-suppliers` (147 commits, nunca desplegada)

## Contexto

Galia va a reemplazar a Fudo como sistema POS (opción A: Galia es la fuente de verdad).
El trabajo se divide en sub-proyectos, cada uno con su propio spec → plan → implementación:

| # | Sub-proyecto | Depende de |
|---|---|---|
| **0** | **Base y rama** (este documento) | — |
| 1 | Núcleo de venta: modelo `Sale`/`SaleItem` unificado, estados de item, modificadores, cancelación, descuentos, tipos de venta, medios de pago, propinas; porte de la UI POS/Camarero | 0 |
| 2 | Caja: turnos, apertura/cierre, movimientos, arqueo | 1 |
| 3 | Cocina e impresión: cocinas, ruteo, agente ESC/POS, KDS, tiempo real | 1 |
| 4 | Facturación electrónica ARCA | 1, 2 |
| 5 | Cobros integrados MercadoPago (Point/QR) | 1, 2 |
| 6 | Corte con Fudo: migración de catálogo/historial, apagar sync, carta digital sobre catálogo Galia | 1–4 |

La rama `release/products-menu-suppliers` contiene, mezclados, el POS, proveedores, productos/insumos,
check-in biométrico, permisos y branding, más archivos basura commiteados. Como nunca se desplegó,
sus modelos y migraciones se pueden reescribir sin compatibilidad hacia atrás.

## Objetivo

Llevar a `main`, limpios y testeados, los módulos que no son POS y que el POS necesita como base:
**permisos, proveedores, productos e insumos, branding**. Nada del POS ni del biométrico.

## Enfoque

Rama nueva desde `main`; cada módulo se trae con `git checkout origin/release/products-menu-suppliers -- <paths>`,
se adapta y se commitea por separado. Las migraciones se reescriben. La rama vieja queda como
referencia y se preserva con el tag `archive/pos-v1`.

## Alcance

### Se porta (en este orden)

| # | Módulo | Backend | Frontend |
|---|---|---|---|
| 1 | Permisos | `models/module.py`, `role_permission.py`, `user_permission.py`; `utils/permissions.py`; `module_required` en `utils/decorators.py`; `routes/permissions.py` | `components/configuration/PermissionMatrix.jsx`, `pages/Permissions.jsx`, `components/RoleProtectedRoute.jsx`, `userModules` en `context/AuthContext.jsx` |
| 2 | Proveedores | `models/supplier.py`, `supplier_id` en `models/expense.py`, validación en `routes/expenses.py`, `routes/suppliers.py` | `pages/Suppliers.jsx`, `pages/SupplierDetail.jsx`, `services/suppliersService.js` |
| 3 | Productos e insumos | `models/product_category.py`, `product.py`, `product_variant.py`, `product_recipe_item.py`, cambios en `supply.py`; `routes/product_categories.py`, `products.py`, `supplies.py`; `services/stock_service.py` | `pages/Products.jsx`, `ProductDetail.jsx`, `ProductCategories.jsx`, `Supplies.jsx`, `Stock.jsx`; `services/productsService.js`, `productCategoriesService.js`, `suppliesService.js` |
| 4 | Branding | `models/site_config.py`, `routes/config.py`, `utils/s3_utils.py`, `utils/storage.py`, `utils/file_upload.py` | `pages/admin/BrandingConfig.jsx`, `services/configService.js`, `constants/colors.js`, cambios de `index.css` |

Tests portados: `test_suppliers.py`, `test_products.py`, `test_product_categories.py`, `test_config.py`.
`stock_service.deduct_stock_for_sale` se porta con su lógica (receta → insumos) y tests propios,
pero ninguna venta lo invoca todavía (eso llega en el sub-proyecto 1).

### No se porta

- **POS** (va al sub-proyecto 1, reescrito): modelos `Sale` (campos nuevos), `SaleItem`, `Order`/`OrderItem`,
  `Mesa`, `Salon`, `Payment`, `PrinterDevice`, `NotificationPreference`; rutas `orders`, `salons`,
  `configuration` y cambios en `sales.py`/`notifications.py`; componentes `pos/`, `camarero/`,
  `configuration/{Mesas,Salones,PrinterDevices}Manager.jsx`, `notifications/`; layouts `PosLayout`,
  `CamareroLayout`; páginas `Pos.jsx`, `Camarero.jsx`, `POSConfiguration.jsx`; servicios
  `ordersService`, `salonsService`, `salesService` (cambios), `salePrinting`, `configurationService`,
  `notificationService`; `context/NotificationContext.jsx`; `test_sales_products.py`, `test_salons.py`.
  `test_sales_products.py` cubre descuento de stock vía venta: su parte de stock se reescribe como test
  directo de `stock_service`.
- **Check-in biométrico** completo: `biometric_session.py`, `location_boundary.py`, columnas biométricas
  de `work_block.py`, `routes/biometric.py`, `components/biometric/`, `pages/BiometricCheckIn.jsx`,
  `services/biometricService.js`, `seed_biometric_locations.py`, `setup_biometric.sh`,
  `BIOMETRIC_README.md`, `docs/BIOMETRIC_CHECKIN_TESTING.md`, dependencias `qrcode`, `Pillow`
  (no se usa en otro lado), `@vladmandic/face-api`, `jsqr`.
- **Basura:** `.playwright-mcp/`, `*.png` sueltos en la raíz, `backend/frontend/public/uploads/`,
  `TASK_9_SUMMARY.md`, `TASK_10_SUMMARY.md`, `FINAL_DELIVERABLE.md`, `IMPLEMENTATION_REPORT.md`,
  `PRINTER_TESTING_GUIDE.md`, `query`, el archivo con nombre roto `C:UsersonofrDesktop…supply.py`,
  `frontend/test_image.txt`, `backend/simple_test.py`, `test_endpoint_http.py`,
  `test_modules_endpoint.py`, `verify_and_create_modules.py`, `verify_user_passwords.py`,
  `reset_admin_password.py`, `.superpowers/brainstorm/`, `.claude/settings.local.json`.
- **Docs del POS** (specs/planes de mayo 2026): quedan en la rama archivada como referencia del sub-proyecto 1.

## Migraciones

Se descartan las 13 migraciones de la rama vieja (dos raíces con `down_revision = None`, dos merges,
`site_config` dependiente del biométrico). Se escriben 4 nuevas, en cadena lineal desde el head de `main`
(`merge_heads_march8`):

1. `add_permissions_system` — tablas `modules`, `role_permissions`, `user_permissions` + **seed** del
   catálogo de módulos y permisos por rol como data migration (idempotente: inserta solo si no existe).
2. `add_suppliers` — tabla `suppliers`; columna `expenses.supplier_id` (FK nullable, indexada).
3. `add_products_and_supplies` — `product_categories`, `products`, `product_variants`,
   `product_recipe_items` y cambios de `supplies`.
4. `add_site_config` — tabla `site_config`.

Cada una con `downgrade` funcional.

**Conflicto conocido:** `feature/carta-digital` agrega `add_menu_tables` también colgando de
`merge_heads_march8`. La rama que se mergee segunda reencadena su primera migración al head de la otra
(cambiando `down_revision`); no se crean merge migrations.

## Permisos

### Regla

- Todo endpoint de negocio usa `@token_required` + `@module_required('<Módulo>')`.
- `@admin_required` queda sólo para administración del sistema: `permissions`, `fudo_sync`, `config` (branding).
- Endpoints de autoservicio del empleado (`employee_schedule`, la parte propia de `absence_requests`,
  `time_tracking` y `payroll`) usan `MySchedule` / `MyPayroll`.
- Sin decorador de módulo: `auth`, `notifications` (lectura propia), health.
- `check_module_access` mantiene la prioridad: admin siempre → override por usuario → permiso por rol → denegado.

### Catálogo de módulos y mapeo

| Módulo | Rutas |
|---|---|
| `Dashboard` | página `/dashboard` del frontend (sin blueprint propio; consume endpoints de `Reports`) |
| `Employees` | `employees`, `job_positions`, `employee_documents`, `social_security` |
| `Schedules` | `schedules`, `shifts`, `schedule_summary`, `store_hours`, `holidays`, `vacation_periods`, `coverage`, gestión de `absence_requests` y `time_tracking` |
| `Payroll` | `payroll` (gestión) |
| `Reports` | `reports` (incluye Día/Hora y GAO), `ml_dashboard`, `ml_predictions` |
| `Expenses` | `expenses`, `csv_import` |
| `Sales` | `sales` (historial e importación actual) |
| `Suppliers` | `suppliers` |
| `Products` | `products`, `product_categories` |
| `Stock` | `supplies`, página de stock |
| `MyPayroll` | recibos propios |
| `MySchedule` | horario, ausencias y fichadas propias |

`POS` y `Configuration` (mesas/salones/impresoras) se agregan en el sub-proyecto 1.

### Seed por rol

- `admin`: todos los módulos.
- `employee`: `MyPayroll`, `MySchedule`.

Esto reproduce exactamente el comportamiento actual: nadie gana ni pierde acceso al mergear.

### Test de cobertura

Test parametrizado que recorre `app.url_map` y verifica que cada view function esté envuelta en
`module_required` o `admin_required` (marcado vía atributo en el wrapper), salvo una whitelist explícita
(`auth.*`, `static`, health, notificaciones propias). Falla si aparece un endpoint nuevo sin proteger.

## Frontend

- `App.jsx` y `Sidebar.jsx` se editan sobre la versión de `main` (no se copian de la rama vieja):
  se agregan rutas e ítems de Proveedores, Productos, Categorías, Insumos, Stock, Permisos y Branding.
  No entran `/pos`, `/camarero`, `/pos-config`, `/biometric`.
- El Sidebar muestra ítems según `userModules` (de `GET /api/v1/permissions/modules/my-modules`)
  en lugar de `is_admin`. Las rutas se envuelven en `RoleProtectedRoute moduleName="…"`.
- `package.json` sin `@vladmandic/face-api` ni `jsqr`.
- Se eliminan `print`/`console.log` de depuración agregados en la rama vieja (por ejemplo en `/auth/me`).

## Verificación

1. `pytest` backend completo en verde: tests de `main` + portados + `stock_service` + cobertura de permisos.
2. `npm run build` y `eslint` sin errores.
3. `flask db upgrade` desde base vacía hasta head, y `flask db downgrade` hasta `merge_heads_march8`.
4. Prueba manual en navegador:
   - admin: ve todos los módulos; crea proveedor, categoría, producto con receta; ajusta stock; cambia logo.
   - employee: ve sólo Mi Nómina y Mi Horario; los endpoints nuevos responden 403.

## Entrega

- Tag `archive/pos-v1` sobre `origin/release/products-menu-suppliers`, pusheado.
- PR `feature/pos-base → main` con commits por módulo (permisos → proveedores → productos/insumos → branding).

## Fuera de alcance

POS y modelo de venta unificado, caja, cocina/impresión, facturación, MercadoPago, migración de la carta
digital al catálogo de Galia y apagado del sync con Fudo (sub-proyectos 1–6).
