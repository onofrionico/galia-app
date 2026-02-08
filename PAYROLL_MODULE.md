# Módulo de Nómina de Sueldos

## Descripción General

El módulo de nómina permite a los administradores gestionar los sueldos mensuales de los empleados basándose en las horas trabajadas registradas por cada empleado (no las horas de la grilla programada).

## Características Principales

### 1. Cálculo de Sueldos
- **Cálculo automático** basado en horas trabajadas registradas por el empleado
- **Comparación** entre horas trabajadas vs horas programadas en la grilla
- **Visualización de diferencias** (positivas o negativas)
- **Tarifa horaria** obtenida del puesto de trabajo del empleado

### 2. Gestión de Nóminas
- **Generación de nóminas** por empleado y período (mes/año)
- **Estados de nómina**: Borrador y Validado
- **Validación de nóminas** para bloquear modificaciones
- **Observaciones** personalizadas por nómina
- **Recálculo** de horas y sueldos antes de validar

### 3. Edición de Bloques de Trabajo
- **Visualización detallada** de todos los bloques de trabajo del mes
- **Edición de horarios** de entrada y salida
- **Eliminación de bloques** incorrectos
- **Comparación lado a lado** entre horas trabajadas y horas grilla

### 4. Resúmenes y Reportes
- **Resumen mensual**: Total de sueldos, horas y empleados
- **Histórico**: Comparación de los últimos 6 meses
- **Filtros**: Por año, mes, empleado y estado
- **Indicadores**: Empleados validados vs pendientes

### 5. Generación de Comprobantes PDF
- **Generación automática** de comprobantes de nómina
- **Formato profesional** con datos del empleado y empresa
- **Descarga directa** desde la interfaz
- **Almacenamiento** de PDFs generados

## Estructura del Backend

### Modelo de Datos (`payroll.py`)
```python
- employee_id: ID del empleado
- month: Mes de la nómina (1-12)
- year: Año de la nómina
- hours_worked: Horas trabajadas registradas
- scheduled_hours: Horas programadas en grilla
- hourly_rate: Tarifa por hora
- gross_salary: Sueldo bruto calculado
- status: Estado (draft/validated)
- validated_at: Fecha de validación
- validated_by: Usuario que validó
- pdf_generated: Si se generó el PDF
- pdf_path: Ruta del PDF generado
- notes: Observaciones
```

### Endpoints API

#### Cálculo y Generación
- `GET /api/v1/payroll/calculate/{employee_id}/{year}/{month}` - Calcular nómina
- `POST /api/v1/payroll/generate` - Generar nueva nómina

#### Consultas
- `GET /api/v1/payroll/` - Listar nóminas (con filtros)
- `GET /api/v1/payroll/{id}` - Detalle de nómina
- `GET /api/v1/payroll/{id}/work-blocks` - Bloques de trabajo

#### Modificaciones
- `PUT /api/v1/payroll/{id}` - Actualizar nómina
- `POST /api/v1/payroll/{id}/validate` - Validar nómina
- `PUT /api/v1/payroll/work-blocks/{block_id}` - Editar bloque
- `DELETE /api/v1/payroll/work-blocks/{block_id}` - Eliminar bloque

#### Resúmenes
- `GET /api/v1/payroll/summary/{year}/{month}` - Resumen mensual
- `GET /api/v1/payroll/summary/historical` - Histórico

#### PDF
- `POST /api/v1/payroll/{id}/generate-pdf` - Generar PDF
- `GET /api/v1/payroll/{id}/pdf` - Descargar PDF

## Estructura del Frontend

### Componentes

#### `Payroll.jsx` - Vista Principal
- Lista de nóminas del período seleccionado
- Tarjetas de resumen (total sueldos, horas, empleados)
- Filtros por año, mes, empleado y estado
- Tabla histórica de los últimos 6 meses
- Modal para generar nueva nómina
- Responsive para mobile y desktop

#### `PayrollDetail.jsx` - Detalle de Nómina
- Información completa del empleado y nómina
- Tarjetas con métricas (horas trabajadas, grilla, diferencia, sueldo)
- Comparación lado a lado de horas trabajadas vs grilla
- Edición de observaciones
- Gestión de bloques de trabajo (editar/eliminar)
- Validación de nómina
- Generación y descarga de PDF
- Recálculo de horas y sueldo

### Servicio (`payrollService.js`)
Maneja todas las comunicaciones con la API del backend.

## Flujo de Trabajo

### 1. Generar Nueva Nómina
1. Ir a **Sueldos** en el menú lateral
2. Hacer clic en **Nueva Nómina**
3. Seleccionar empleado, año y mes
4. Hacer clic en **Calcular** para ver el resultado
5. Revisar horas trabajadas, grilla y diferencia
6. Agregar observaciones (opcional)
7. Hacer clic en **Generar Nómina**

### 2. Revisar y Editar Nómina
1. En la lista de nóminas, hacer clic en **Ver Detalle**
2. Revisar las métricas principales
3. Comparar horas trabajadas vs horas grilla
4. Si es necesario, editar bloques de trabajo:
   - Hacer clic en el ícono de editar
   - Modificar horarios de entrada/salida
   - Guardar cambios
5. Eliminar bloques incorrectos si es necesario
6. Agregar o editar observaciones
7. Si se modificaron bloques, hacer clic en **Recalcular**

### 3. Validar Nómina
1. Revisar que todos los datos sean correctos
2. Hacer clic en **Validar Nómina**
3. Confirmar la validación
4. Una vez validada, la nómina no se puede modificar

### 4. Generar Comprobante PDF
1. En el detalle de la nómina, hacer clic en **Generar PDF**
2. El PDF se descargará automáticamente
3. El PDF incluye:
   - Datos de la empresa
   - Período de liquidación
   - Datos del empleado (nombre, DNI, CUIL, puesto)
   - Detalle de horas y tarifa
   - Sueldo bruto total
   - Observaciones (si las hay)

### 5. Consultar Histórico
1. En la vista principal de Sueldos
2. Revisar la tabla "Histórico de Sueldos"
3. Comparar totales de diferentes meses
4. Usar filtros para análisis específicos

## Permisos y Seguridad

- **Solo administradores** pueden acceder al módulo de sueldos
- Todas las operaciones requieren autenticación JWT
- Las nóminas validadas no pueden modificarse
- Los PDFs se almacenan de forma segura en el servidor

## Migración de Base de Datos

Para aplicar los cambios en la base de datos:

```bash
cd backend
flask db upgrade
```

Esto agregará las nuevas columnas al modelo `payrolls`:
- scheduled_hours
- status
- validated_at
- validated_by
- pdf_generated
- pdf_path
- notes
- updated_at

## Dependencias

### Backend
- `reportlab==4.0.7` - Generación de PDFs (ya incluido en requirements.txt)

### Frontend
- `lucide-react` - Iconos (ya incluido)
- React Router - Navegación (ya incluido)

## Notas Importantes

1. **Horas Trabajadas**: Se calculan desde los registros de `TimeTracking` y `WorkBlock`
2. **Horas Grilla**: Se calculan desde los `Shift` programados
3. **Diferencia**: Puede ser positiva (trabajó más) o negativa (trabajó menos)
4. **Tarifa Horaria**: Se obtiene del `JobPosition` del empleado
5. **Validación**: Una vez validada, la nómina queda bloqueada para edición
6. **PDFs**: Se almacenan en `backend/payroll_pdfs/`

## Próximas Mejoras Sugeridas

- Agregar deducciones y bonificaciones
- Cálculo de horas extras con multiplicador
- Exportación masiva de PDFs
- Envío automático de comprobantes por email
- Integración con sistemas contables
- Reportes de costos laborales
- Proyecciones de sueldos futuros
