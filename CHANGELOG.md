# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

## [1.1.0] - 2026-03-08

### Security
- **🔒 CRÍTICO - Validación de permisos en backend**: Implementado decorador `@admin_required` en todos los endpoints administrativos
- **Protección de endpoints de ventas**: Empleados ya no pueden acceder a `/api/v1/sales` mediante URLs directas
- **Protección de endpoints de reportes**: Acceso a reportes restringido solo a administradores
- **Protección de endpoints de gastos**: Gestión de gastos requiere permisos de administrador
- **Protección de endpoints de nóminas**: Acceso a nóminas de todos los empleados restringido a administradores
- **Logging de seguridad**: Todos los intentos de acceso no autorizado se registran con detalles (usuario, IP, endpoint, timestamp)
- **Manejo de errores 403 en frontend**: Interceptor de API muestra notificaciones visuales cuando un usuario intenta acceder a recursos no autorizados
- **Tests de permisos**: 27 tests automatizados para verificar la correcta aplicación de permisos en todos los módulos

### Added
- **Formato de montos argentino**: Todos los montos monetarios ahora se muestran en formato argentino (punto como separador de miles, coma como separador decimal)
  - Utilidad backend `format_money_ar()` en `backend/app/utils/format_utils.py` para formatear montos
  - Utilidad backend `parse_money_ar()` para parsear strings en formato argentino
  - Componente React `MoneyFormat.jsx` para mostrar montos formateados
  - Componente React `MoneyInput.jsx` para inputs de montos con formato argentino
  - Utilidades JavaScript `formatMoney()`, `parseMoney()` y `formatMoneyWithCurrency()` en `frontend/src/utils/moneyFormat.js`
  - Actualización de componentes Payroll, Sales y Expenses para usar el nuevo formato
  - Tests automatizados para backend (pytest) y frontend (Jest) con cobertura completa
  - Ejemplos: 1234.56 se muestra como "1.234,56", 1000000 como "1.000.000,00"
- **Eliminación de nóminas en borrador**: Los administradores pueden eliminar nóminas que están en estado "borrador"
  - Endpoint DELETE `/api/v1/payroll/<id>` con validación de estado
  - Solo permite eliminar nóminas con status = "draft"
  - Botón de eliminación visible únicamente para nóminas en borrador
  - Diálogo de confirmación antes de eliminar
  - Tests automatizados para validar permisos y restricciones de eliminación
- **Sistema de gestión de documentos de cargas sociales**: Los administradores pueden cargar y gestionar comprobantes de cargas sociales para empleados
  - Nuevo modelo `SocialSecurityDocument` con soporte para múltiples tipos de documentos (cargas sociales, aportes, obra social, ART, otros)
  - Almacenamiento seguro en S3 con encriptación AES256
  - Validación de archivos PDF con límite de 10MB
  - Componente `SocialSecurityUpload` integrado en el perfil de empleado
  - Endpoints REST para upload, download, listado y eliminación de documentos
  - Filtros por tipo de documento, año y mes
  - Permisos: solo administradores pueden subir/eliminar, empleados pueden ver sus propios documentos
- **Detalle de cobertura diaria en grillas**: Nueva funcionalidad para visualizar empleados asignados por día
  - Nuevo endpoint `/api/v1/schedules/coverage` que retorna detalle completo de empleados por fecha
  - Componente `DayCoverageDetail.jsx` con modal interactivo para ver asignaciones del día
  - Click en cualquier día del calendario de cobertura muestra detalle de empleados asignados
  - Visualización de nombre, puesto y horario de cada empleado
  - Opción de asignación rápida de turnos desde el modal de detalle
  - Cálculo automático de horas totales programadas por día
- **Gestión de horarios mejorada**: Los turnos en curso ahora aparecen primero en la lista de turnos del empleado
- **Indicador visual de turnos activos**: Los turnos que están en curso se muestran con un borde verde y badge "En curso"
- **Confirmación de eliminación de grillas**: Agregado diálogo de confirmación al eliminar grillas horarias
- **Utilidades de zona horaria**: Nuevo módulo `timezone_utils.py` con funciones para manejo de zona horaria Argentina (UTC-3)
- **Componente de notificación de acceso denegado**: Nuevo componente `ForbiddenNotification.jsx` que muestra alertas visuales cuando se deniega el acceso
- **Tests de zona horaria**: 20+ tests automatizados para verificar el correcto manejo de la zona horaria en fichajes

### Changed
- **Ordenamiento de turnos**: Los turnos en curso tienen prioridad sobre los turnos futuros en la vista del empleado
- **Restricción de eliminación**: Solo las grillas en estado "borrador" pueden ser eliminadas, las publicadas están protegidas
- **Decorador @admin_required mejorado**: Ahora incluye logging detallado con información de seguridad (usuario, rol, IP, método HTTP, timestamp)

### Fixed
- **🔒 CRÍTICO - Zona horaria en fichajes**: Los registros de entrada/salida ahora se guardan en hora Argentina (UTC-3) en lugar de UTC
- **Cálculo de horas trabajadas**: Corregido el cálculo de horas trabajadas que se veía afectado por el desfase de 3 horas
- **Desactivación de empleados**: Corregido error `AttributeError` al desactivar empleados. El modelo `Shift` usa `shift_date` en lugar de `date` como nombre de columna.

## [1.0.0] - Versión actual en producción

### Added
- Sistema inicial de gestión de empleados
- Módulo de control de asistencia y fichajes
- Sistema de gestión de nóminas
- Módulo de solicitudes de ausencias
- Dashboard de reportes
- Sistema de gestión de horarios y turnos
- Autenticación y autorización con JWT
- Sistema de gestión de días festivos
