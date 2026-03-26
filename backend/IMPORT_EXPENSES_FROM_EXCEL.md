# Importar Gastos desde Excel de Fudo

## Contexto

La API de Fudo `/expenses` no devuelve los atributos de los gastos (amount, date, description, etc.), solo devuelve IDs y relaciones. Por esta razón, la sincronización automática de gastos desde la API de Fudo no es posible.

**Solución**: Importar gastos desde el archivo Excel que Fudo proporciona.

## Requisitos

```bash
pip install pandas openpyxl
```

## Uso

### 1. Exportar gastos desde Fudo

1. Ingresa a tu cuenta de Fudo
2. Ve a la sección de Gastos
3. Exporta los gastos del período deseado como archivo Excel (.xlsx)

### 2. Ejecutar el script de importación

```bash
cd backend
source venv/bin/activate
python update_expenses_from_excel.py <ruta_al_archivo.xlsx>
```

**Ejemplo**:
```bash
python update_expenses_from_excel.py ../gastos-237595-20260310-1-qs0jhj.xlsx
```

## Funcionamiento

El script:

1. **Lee el archivo Excel** de Fudo
2. **Identifica las columnas** automáticamente (ID, Fecha, Monto, Proveedor, Descripción, etc.)
3. **Actualiza gastos existentes** usando el `external_id` de Fudo (si ya fueron importados previamente)
4. **Crea nuevos gastos** si no existen en la base de datos
5. **Muestra un resumen** al finalizar:
   - Gastos actualizados
   - Gastos creados
   - Errores encontrados

## Estructura esperada del Excel

El script intenta detectar automáticamente las columnas. Busca nombres como:

- **ID**: `ID`, `id`, `expense_id`
- **Fecha**: `Fecha`, `Date`, `fecha`
- **Monto**: `Monto`, `Total`, `Importe`, `Amount`
- **Proveedor**: `Proveedor`, `Provider`
- **Descripción**: `Descripción`, `Description`, `Concepto`

## Notas Importantes

- El script procesa los registros en lotes de 50 para optimizar el rendimiento
- Los gastos se marcan con `creado_por = 'Excel Import'` para identificar su origen
- Si un gasto ya existe (mismo `external_id`), se actualiza con los nuevos datos
- Los montos se convierten automáticamente al formato correcto

## Sincronización de Ventas

La sincronización de **ventas** desde la API de Fudo **sí funciona correctamente** y puede usarse desde el frontend de la aplicación.

Solo los **gastos** requieren importación manual desde Excel debido a las limitaciones de la API de Fudo.

## Soporte

Si tienes problemas con la importación:

1. Verifica que el archivo Excel tenga las columnas esperadas
2. Revisa los mensajes de error del script
3. Contacta al soporte de Fudo si necesitas un formato específico de exportación
