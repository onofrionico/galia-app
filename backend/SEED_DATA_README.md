# Datos de Prueba - Seed Data

Este script genera datos de prueba para desarrollo local del módulo de proveedores y productos.

## Contenido Generado

### 📦 Proveedores (5)
- **Distribuidora La Abundancia** - Proveedor general de insumos
- **Café Premium S.A.** - Especialista en café y té
- **Lácteos del Sur** - Productos lácteos
- **Pastelería Artesanal** - Panadería y facturas
- **Insumos Gastronómicos** - Descartables y varios

### 🏷️ Productos Maestros (4)
Productos vinculados entre proveedores para comparación de precios:
- Café en Grano
- Leche Entera
- Azúcar
- Medialunas

### 📋 Productos (~18)
Productos distribuidos entre los 5 proveedores:
- Café, té, yerba mate
- Leche, crema, dulce de leche
- Azúcar, edulcorante
- Medialunas, croissants, facturas
- Servilletas, vasos descartables

### 🛒 Compras (35-50)
- 5-10 compras por proveedor
- Distribuidas en los últimos 90 días
- Cada compra con 2-5 productos aleatorios
- Cantidades y totales realistas

## Cómo Ejecutar

### Opción 1: Desde el directorio backend

```bash
cd backend
source venv/bin/activate
python seed_data.py
```

### Opción 2: Desde la raíz del proyecto

```bash
cd backend
source venv/bin/activate
python seed_data.py
```

## Características

✅ **Idempotente**: Puede ejecutarse múltiples veces sin duplicar datos
- Verifica si los datos ya existen antes de crearlos
- Usa identificadores únicos (tax_id, SKU) para evitar duplicados

✅ **Datos Realistas**:
- Nombres y datos de contacto argentinos
- Precios en pesos argentinos
- Fechas distribuidas en los últimos 3 meses
- Relaciones correctas entre entidades

✅ **Historial de Precios**:
- Cada producto tiene su precio inicial registrado
- Fechas de hace 90 días para simular historial

✅ **Productos Maestros**:
- Algunos productos están vinculados a maestros
- Permite comparación de precios entre proveedores

## Verificación

Después de ejecutar el script, puedes verificar los datos:

```bash
# Conectarse a PostgreSQL
psql -U tu_usuario -d galia_db

# Verificar datos
SELECT COUNT(*) FROM suppliers;
SELECT COUNT(*) FROM products;
SELECT COUNT(*) FROM product_masters;
SELECT COUNT(*) FROM purchases;
SELECT COUNT(*) FROM purchase_items;
```

## Limpieza de Datos

Si necesitas limpiar los datos de prueba:

```sql
-- CUIDADO: Esto eliminará TODOS los datos
TRUNCATE TABLE purchase_items CASCADE;
TRUNCATE TABLE purchases CASCADE;
TRUNCATE TABLE price_history CASCADE;
TRUNCATE TABLE products CASCADE;
TRUNCATE TABLE product_masters CASCADE;
TRUNCATE TABLE suppliers CASCADE;
```

## Notas

- El script respeta las relaciones de clave foránea
- Las compras tienen items con cantidades y precios realistas
- Los totales se calculan automáticamente
- Todos los productos tienen estado 'active'
- Todas las compras tienen estado 'completed'
