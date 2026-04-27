# Diseño — Módulo de Proveedores

**Fecha:** 2026-04-27
**Contexto:** Sub-proyecto 1 de la hoja de ruta de migración desde Fudo POS hacia Galia. El objetivo final es reemplazar Fudo completamente; este módulo es el primero porque tiene valor independiente (historial analítico de compras por proveedor) y es la base para módulos futuros como Inventario.

## Objetivo

Centralizar la gestión de proveedores en Galia, permitiendo:
1. Mantener un directorio de proveedores con datos de contacto
2. Vincular gastos existentes (y futuros) a proveedores específicos
3. Consultar historial analítico de compras por proveedor (totales, tendencias, desglose por categoría)

No incluye órdenes de compra ni gestión de entregas — eso pertenece al módulo de Inventario.

---

## Modelo de datos

### Nueva tabla: `suppliers`

| Campo | Tipo | Notas |
|---|---|---|
| `id` | Integer PK | |
| `name` | String(200) NOT NULL | Nombre del proveedor |
| `cuit` | String(20) nullable | CUIT/RUT |
| `email` | String(200) nullable | |
| `phone` | String(50) nullable | |
| `address` | Text nullable | |
| `notes` | Text nullable | Notas internas |
| `is_active` | Boolean default true | |
| `created_at` | DateTime | |
| `updated_at` | DateTime | |

### Cambio en tabla `expenses`

Agregar columna `supplier_id` como FK opcional a `suppliers`. El campo `proveedor` (string libre) se mantiene para:
- Gastos importados de Fudo/CSV sin proveedor vinculado
- Compatibilidad con datos históricos

**Regla de display:** si `supplier_id` está presente, tiene prioridad sobre el string `proveedor`. Si no, se muestra el string.

### Migración de datos existentes

Al crear un proveedor, el sistema ejecuta una búsqueda por coincidencia exacta de nombre (case-insensitive) contra el campo `proveedor` en `expenses` y propone vincular los gastos encontrados. El usuario confirma o descarta la vinculación.

---

## Backend

**Archivos nuevos:**
- `backend/app/models/supplier.py` — modelo SQLAlchemy `Supplier`
- `backend/app/routes/suppliers.py` — blueprint con endpoints CRUD + historial
- `backend/migrations/versions/XXXX_add_suppliers.py` — Alembic migration

**Endpoints:**
```
GET    /api/v1/suppliers              Lista con stats rápidas (total gastado, última compra)
POST   /api/v1/suppliers              Crear proveedor
GET    /api/v1/suppliers/<id>         Detalle + historial de gastos
PUT    /api/v1/suppliers/<id>         Editar proveedor
DELETE /api/v1/suppliers/<id>         Desactivar (soft delete vía is_active=false)
GET    /api/v1/suppliers/<id>/expenses  Historial paginado con filtros de fecha
POST   /api/v1/suppliers/<id>/link-expenses  Vincular gastos por nombre
```

**Cambios en módulos existentes:**
- `backend/app/routes/expenses.py` — agregar `supplier_id` al formulario de creación/edición
- `backend/app/routes/fudo_sync.py` — al sincronizar gastos, intentar vincular por nombre exacto automáticamente

---

## Frontend

**Archivos nuevos:**
- `frontend/src/pages/Suppliers.jsx` — lista de proveedores
- `frontend/src/pages/SupplierDetail.jsx` — detalle con tabs: Datos de contacto | Historial de compras
- `frontend/src/services/suppliersService.js` — cliente API

**Componentes del detalle del proveedor:**
- Tab "Contacto": formulario editable con nombre, CUIT, email, teléfono, dirección, notas
- Tab "Historial": tabla de gastos vinculados con filtro por rango de fechas, subtotales por categoría, métricas (total período, promedio mensual)
- Panel "Vincular gastos": aparece al crear un proveedor nuevo si hay gastos con nombre coincidente; también accesible desde el detalle

**Cambios en módulos existentes:**
- Formulario de gastos: campo "Proveedor" pasa de texto libre a autocomplete con opción de crear nuevo proveedor inline
- Sidebar admin: nueva entrada "Proveedores" bajo una sección "Compras"

---

## Métricas analíticas por proveedor

Calculadas en el backend sobre los gastos vinculados:
- Total gastado en período seleccionado
- Promedio mensual (últimos 12 meses)
- Desglose por categoría de gasto
- Último gasto registrado

No se requieren tablas adicionales — todo se calcula con queries sobre `expenses`.

---

## Hoja de ruta general (contexto)

Este es el Sub-proyecto 1 de 7:

| # | Módulo | Estado |
|---|---|---|
| 1 | **Proveedores** | Este spec |
| 2 | Productos / Menú | Pendiente |
| 3 | Clientes | Pendiente |
| 4 | Cajas + Medios de pago | Pendiente |
| 5 | POS (órdenes, mesas, delivery) | Pendiente |
| 6 | Documentos fiscales | Pendiente |
| 7 | Inventario / Stock | Pendiente |
