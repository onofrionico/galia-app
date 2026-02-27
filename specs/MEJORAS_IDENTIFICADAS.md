# Mejoras Identificadas - Feedback de Usuario

**Fecha**: 2026-02-27  
**Estado**: Documentado en especificaciones

## Resumen

Este documento consolida todas las observaciones encontradas al utilizar la aplicación y cómo se han incorporado en las especificaciones técnicas del sistema.

---

## 1. Gestión de Empleados

### ✅ Empleados inactivos no deben aparecer en grillas
- **Problema**: Los usuarios que no están activos aparecen en las grillas de selección
- **Solución**: 
  - Agregar parámetro `include_inactive` (default: false) en endpoint de listado
  - Filtrar empleados inactivos por defecto en todas las vistas de selección
  - Solo mostrar empleados inactivos cuando se solicite explícitamente
- **Spec actualizada**: `employee-management-module.md`

### ✅ Error al desactivar empleados
- **Problema**: Se generan errores al intentar desactivar empleados
- **Solución**:
  - Manejar correctamente todas las relaciones en cascada (turnos, nóminas, etc.)
  - Implementar validaciones previas a la desactivación
  - Agregar logs de auditoría para debugging
  - Verificar que no se generan errores en cascada
- **Spec actualizada**: `employee-management-module.md`

### ✅ CUIL debe ser modificable
- **Problema**: El CUIL no puede modificarse después de la creación, impidiendo corregir errores
- **Solución**:
  - Permitir edición del CUIL (mantener restricción solo en DNI)
  - Validar formato y unicidad al modificar
  - Mantener validación de dígito verificador
- **Spec actualizada**: `employee-management-module.md`

---

## 2. Gestión de Grillas Horarias

### ✅ Mostrar horario de trabajo del local
- **Problema**: No se muestra el horario de trabajo del local al armar grillas
- **Solución**:
  - Crear entidad "Horario de Local" con configuración de horarios
  - Mostrar horarios como referencia en la vista de armado de grilla
  - Permitir configuración de horarios por día de la semana
- **Spec actualizada**: `cafeteria-management-app.md`

### ✅ Configurar horarios de trabajo (multi-local)
- **Problema**: No existe configuración de horarios de trabajo
- **Solución**:
  - Implementar módulo de configuración de horarios
  - Soportar múltiples locales con horarios diferentes
  - Atributos: local_id, nombre_local, días_semana, hora_apertura, hora_cierre
- **Spec actualizada**: `cafeteria-management-app.md`

### ✅ Contabilizar sumatoria de horas en tiempo real
- **Problema**: La sumatoria de horas muestra 0 mientras se arma la grilla
- **Solución**:
  - Implementar cálculo en tiempo real de horas totales
  - Actualizar totales al agregar/modificar/eliminar turnos
  - Mostrar totales por empleado y totales generales
- **Spec actualizada**: `cafeteria-management-app.md`

### ✅ Contabilizar costos en tiempo real
- **Problema**: Los costos no se calculan mientras se agregan turnos
- **Solución**:
  - Calcular costos automáticamente al agregar turnos
  - Usar tarifa horaria del puesto del empleado
  - Mostrar costo estimado total de la grilla
- **Spec actualizada**: `cafeteria-management-app.md`

### ✅ Visualizar empleados en vacaciones
- **Problema**: No se puede ver qué empleados están de vacaciones al armar grilla
- **Solución**:
  - Crear entidad "Período de Vacaciones"
  - Mostrar indicador visual de empleados en vacaciones
  - Alertar al intentar asignar turnos a empleados de vacaciones
  - Atributos: empleado_id, fecha_inicio, fecha_fin, estado, notas
- **Spec actualizada**: `cafeteria-management-app.md`

### ✅ Ver/imprimir grilla en formato calendario
- **Problema**: No existe vista de calendario para la grilla
- **Solución**:
  - Implementar vista de calendario visual
  - Permitir exportación/impresión en formato calendario
  - Facilitar visualización de la semana/mes completo
- **Spec actualizada**: `cafeteria-management-app.md`

### ✅ Nombres visibles al hacer scroll horizontal
- **Problema**: Los nombres de empleadas se pierden al scrollear hacia la derecha
- **Solución**:
  - Implementar columna fija para nombres de empleados
  - Usar sticky positioning en CSS
  - Mantener nombres siempre visibles durante scroll horizontal
- **Spec actualizada**: `cafeteria-management-app.md`

---

## 3. Módulo de Nóminas

### ✅ Calcular con precio vigente histórico
- **Problema**: El cálculo de horas usa la tarifa actual, no la vigente cuando se registraron
- **Solución**:
  - Implementar sistema de tarifas históricas
  - Almacenar tarifa vigente al momento del registro de horas
  - Usar tarifa histórica para cálculos de nóminas pasadas
  - **CRÍTICO**: Esto afecta la precisión de los cálculos de sueldos
- **Spec actualizada**: `PAYROLL_MODULE.md`

### ✅ Eliminar nóminas en borrador
- **Problema**: Las nóminas en borrador no pueden eliminarse
- **Solución**:
  - Agregar endpoint DELETE para nóminas
  - Permitir eliminación solo si status = 'draft'
  - Las nóminas validadas permanecen permanentes
  - Agregar botón de eliminar en UI para borradores
- **Spec actualizada**: `PAYROLL_MODULE.md`

---

## 4. Seguridad y Permisos (CRÍTICO)

### 🔴 CRÍTICO: Control de acceso por URL
- **Problema**: Empleados pueden acceder a módulos restringidos mediante URLs directas
- **Impacto**: Vulnerabilidad de seguridad grave
- **Solución**:
  - Implementar middleware de autorización en TODAS las rutas del backend
  - Validar permisos en backend, no solo ocultar en frontend
  - Retornar error 403 (Forbidden) para accesos no autorizados
  - Validar rol de usuario en cada endpoint protegido
  - Implementar guards de ruta en frontend (UX)
  - Implementar validación en backend (seguridad)
- **Módulos afectados**:
  - Dashboard/Reportes
  - Ventas (de otros empleados)
  - Gastos
  - Nóminas
  - Configuración de grillas
  - Gestión de empleados
- **Spec actualizada**: `reports-dashboard-module.md`, `cafeteria-management-app.md`

---

## Prioridades de Implementación

### P0 - CRÍTICO (Seguridad)
1. ✅ Implementar middleware de autorización en backend
2. ✅ Validar permisos en todas las rutas protegidas
3. ✅ Agregar tests de seguridad de acceso por rol

### P1 - Alta (Funcionalidad Core)
1. ✅ Filtrar empleados inactivos en grillas
2. ✅ Fix error al desactivar empleados
3. ✅ Permitir edición de CUIL
4. ✅ Cálculo en tiempo real de horas y costos
5. ✅ Sistema de tarifas históricas para nóminas

### P2 - Media (Mejoras UX)
1. ✅ Configuración de horarios de local
2. ✅ Visualización de vacaciones
3. ✅ Vista de calendario para grillas
4. ✅ Nombres fijos en scroll horizontal
5. ✅ Eliminar nóminas en borrador

---

## Casos de Prueba Agregados

### Seguridad
- Test de acceso no autorizado vía URL directa
- Test de validación de permisos en backend
- Test de error 403 para empleados sin permisos

### Empleados
- Test de filtrado de empleados inactivos
- Test de desactivación sin errores
- Test de edición de CUIL con validación

### Grillas
- Test de cálculo en tiempo real de horas
- Test de cálculo en tiempo real de costos
- Test de alerta de empleados en vacaciones
- Test de exportación a calendario

### Nóminas
- Test de eliminación de nóminas en borrador
- Test de cálculo con tarifa histórica

---

## Criterios de Aceptación Actualizados

### Empleados
- ✅ Empleados inactivos no aparecen en grillas de selección por defecto
- ✅ La desactivación de empleados funciona sin errores
- ✅ El CUIL es editable para correcciones (con validación)

### Grillas
- ✅ Sistema muestra horario del local al armar grilla
- ✅ Sumatoria de horas se actualiza en tiempo real
- ✅ Costos se calculan automáticamente mientras se agregan turnos
- ✅ Empleados en vacaciones son visibles y alertan al asignar
- ✅ Grilla puede exportarse en formato calendario
- ✅ Nombres permanecen visibles al hacer scroll horizontal

### Nóminas
- ✅ Cálculo usa tarifa vigente histórica, no tarifa actual
- ✅ Nóminas en borrador pueden eliminarse

### Seguridad (CRÍTICO)
- ✅ 100% de las rutas protegidas rechazan acceso no autorizado con error 403
- ✅ Empleados no pueden acceder a ningún módulo restringido mediante URLs directas
- ✅ Backend valida permisos en todas las rutas, no solo frontend

---

## Archivos de Especificación Actualizados

1. ✅ `specs/employee-management-module.md`
   - Filtrado de inactivos
   - Fix desactivación
   - CUIL editable

2. ✅ `specs/cafeteria-management-app.md`
   - Horarios de local
   - Cálculos en tiempo real
   - Vacaciones
   - Vista calendario
   - UI fixes
   - Seguridad crítica

3. ✅ `PAYROLL_MODULE.md`
   - Tarifas históricas
   - Eliminación de borradores

4. ✅ `specs/reports-dashboard-module.md`
   - Seguridad de acceso
   - Validación de permisos
   - Tests de seguridad

---

## Próximos Pasos

1. **Implementación de Seguridad (CRÍTICO)**
   - Crear middleware de autorización
   - Aplicar a todas las rutas protegidas
   - Agregar tests de seguridad
   - Validar en frontend y backend

2. **Mejoras de Empleados**
   - Implementar filtro de inactivos
   - Fix lógica de desactivación
   - Permitir edición de CUIL

3. **Mejoras de Grillas**
   - Configuración de horarios de local
   - Cálculos en tiempo real
   - Sistema de vacaciones
   - Vista de calendario
   - Fix UI scroll

4. **Mejoras de Nóminas**
   - Sistema de tarifas históricas
   - Endpoint de eliminación de borradores

5. **Testing**
   - Tests de seguridad
   - Tests de funcionalidad actualizada
   - Tests de regresión

---

## Notas Importantes

- **Seguridad es PRIORIDAD MÁXIMA**: El control de acceso por URL es una vulnerabilidad crítica
- **Tarifas históricas**: Afecta la precisión de cálculos de sueldos pasados
- **Empleados inactivos**: Impacta múltiples módulos (grillas, nóminas, reportes)
- **Cálculos en tiempo real**: Mejora significativa de UX en armado de grillas

---

**Documento generado**: 2026-02-27  
**Versión**: 1.0  
**Estado**: Todas las mejoras documentadas en specs
