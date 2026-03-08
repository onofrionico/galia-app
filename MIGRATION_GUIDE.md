# Guía de Migración: Sistema de Categorías Normalizado

## Resumen de Cambios

Se ha migrado el sistema de categorías de gastos desde un modelo duplicado (campo `categoria` como texto libre + tabla `expense_categories`) a un sistema completamente normalizado usando únicamente la tabla `expense_categories` con relación `category_id`.

## Cambios Implementados

### 1. Base de Datos

**Migración creada:** `migrate_to_normalized_categories.py`

Esta migración:
- ✅ Crea categorías en `expense_categories` desde valores únicos del campo `categoria`
- ✅ Clasifica automáticamente como 'directo' o 'indirecto' usando keywords
- ✅ Mapea todos los gastos existentes a `category_id`
- ✅ Crea categoría por defecto "Sin categoría" para gastos sin clasificar
- ✅ Elimina las columnas legacy `categoria` y `subcategoria`
- ✅ Hace `category_id` NOT NULL

### 2. Backend

**Archivos modificados:**

#### `app/models/expense.py`
- ✅ Actualizado `to_dict()` para remover `categoria` y `subcategoria`
- ✅ Actualizado `from_csv_row()` para mapear CSV `Categoría` → `category_id`
- ✅ Creación automática de categorías al importar CSV

#### `app/routes/expenses.py`
- ✅ Filtro por `category_id` en lugar de `categoria`
- ✅ Endpoint `/filters` retorna categorías normalizadas con `{id, name, expense_type}`
- ✅ Validación de `category_id` en creación y actualización
- ✅ Estadísticas agrupadas por `ExpenseCategory` con `expense_type`
- ✅ Export CSV incluye `category_name` y `expense_type`

#### `app/routes/reports.py`
- ✅ `get_expenses_metrics()` usa `expense_type` de la categoría
- ✅ `expenses_report()` filtra por `category_id` y agrupa por categoría normalizada
- ✅ Eliminados keywords hardcodeados para clasificar directo/indirecto

### 3. Frontend

**Archivo modificado:** `frontend/src/pages/Expenses.jsx`

- ✅ Filtros usan `category_id` en lugar de `categoria`
- ✅ Formulario usa dropdown de categorías con validación requerida
- ✅ Tabla muestra `category_name` y badge de tipo (D/I)
- ✅ Modal de detalles muestra categoría normalizada con tipo
- ✅ Eliminadas referencias a `categoria` y `subcategoria`

## Instrucciones de Ejecución

### Paso 1: Backup de la Base de Datos

```bash
# Crear backup antes de migrar
pg_dump -U postgres galia_db > backup_pre_migration_$(date +%Y%m%d).sql
```

### Paso 2: Ejecutar la Migración

```bash
cd backend
flask db upgrade
```

### Paso 3: Verificar la Migración

```bash
# Verificar que todas las categorías se crearon
flask shell
>>> from app.models.expense import ExpenseCategory, Expense
>>> ExpenseCategory.query.count()  # Debe mostrar cantidad de categorías únicas
>>> Expense.query.filter(Expense.category_id.is_(None)).count()  # Debe ser 0
>>> exit()
```

### Paso 4: Reiniciar Servicios

```bash
# Backend
cd backend
flask run

# Frontend (en otra terminal)
cd frontend
npm run dev
```

## Verificación Post-Migración

### Checklist de Verificación

- [ ] Todas las categorías únicas están en `expense_categories`
- [ ] Todos los gastos tienen `category_id` asignado
- [ ] Las columnas `categoria` y `subcategoria` fueron eliminadas
- [ ] Los filtros en el frontend funcionan correctamente
- [ ] El formulario de creación requiere categoría
- [ ] Los reportes clasifican correctamente directo/indirecto
- [ ] La importación CSV sigue funcionando
- [ ] La exportación CSV incluye categoría normalizada

### Queries de Verificación

```sql
-- Verificar categorías creadas
SELECT id, name, expense_type, is_active FROM expense_categories ORDER BY name;

-- Verificar distribución de gastos por categoría
SELECT 
    ec.name, 
    ec.expense_type,
    COUNT(e.id) as total_gastos,
    SUM(e.importe) as total_importe
FROM expenses e
JOIN expense_categories ec ON e.category_id = ec.id
WHERE e.cancelado = false
GROUP BY ec.id, ec.name, ec.expense_type
ORDER BY total_importe DESC;

-- Verificar que no hay gastos sin categoría
SELECT COUNT(*) FROM expenses WHERE category_id IS NULL;
```

## Rollback (Si es necesario)

Si necesitas revertir la migración:

```bash
cd backend
flask db downgrade
```

**NOTA:** El downgrade recreará las columnas `categoria` y `subcategoria` y las poblará desde `category_id`, pero se perderá la información de `subcategoria` original.

## Beneficios de la Migración

1. **Datos normalizados:** Una sola fuente de verdad para categorías
2. **Clasificación consistente:** Tipo directo/indirecto definido en la categoría
3. **Mejor integridad:** Foreign key constraints y validaciones
4. **UI mejorada:** Dropdowns en lugar de texto libre
5. **Reportes precisos:** Sin depender de keywords hardcodeados
6. **Mantenibilidad:** Más fácil agregar/modificar categorías

## Gestión de Categorías

Para agregar nuevas categorías después de la migración, puedes:

1. **Vía importación CSV:** Las categorías nuevas se crean automáticamente
2. **Vía código:** Crear endpoint de administración de categorías (recomendado para futuro)
3. **Vía SQL directo:**

```sql
INSERT INTO expense_categories (name, expense_type, is_active, created_at)
VALUES ('Nueva Categoría', 'indirecto', true, CURRENT_TIMESTAMP);
```

## Soporte

Si encuentras algún problema durante la migración, verifica:
- Logs del backend para errores de migración
- Console del navegador para errores del frontend
- Que la versión de la migración sea la correcta en `alembic_version`
