# Especificación del Módulo de Gestión de Empleados

**Fecha de Creación**: 2026-02-05  
**Prioridad**: P1 (Crítico para operación)

## Resumen Ejecutivo

El módulo de gestión de empleados es fundamental para el sistema de cafetería, permitiendo administrar la información laboral del personal, sus contratos, puestos de trabajo, y servir como base para la gestión de grillas horarias y liquidación de sueldos.

## Entidades Principales

### 1. Employee (Empleado)

Representa a cada persona que trabaja en la cafetería.

**Atributos**:
- `id`: Identificador único (UUID)
- `user_id`: Relación con tabla User (1:1)
- `first_name`: Nombre(s) del empleado
- `last_name`: Apellido(s) del empleado
- `dni`: DNI argentino (7-8 dígitos, único)
- `cuil`: CUIL argentino (formato XX-XXXXXXXX-X, único)
- `birth_date`: Fecha de nacimiento
- `phone`: Teléfono de contacto
- `address`: Dirección completa
- `email`: Email (único, heredado de User)
- `profile_photo_url`: URL de foto de perfil (opcional)
- `employment_relationship`: Tipo de relación laboral (ENUM: 'dependencia', 'monotributo')
- `emergency_contact_name`: Nombre de contacto de emergencia
- `emergency_contact_phone`: Teléfono de contacto de emergencia
- `emergency_contact_relationship`: Relación con contacto de emergencia
- `hire_date`: Fecha de ingreso
- `status`: Estado del empleado (ENUM: 'activo', 'inactivo', 'suspendido', 'vacaciones', 'licencia')
- `current_job_position_id`: Relación con JobPosition actual
- `created_at`: Fecha de creación del registro
- `updated_at`: Fecha de última actualización
- `created_by_id`: Usuario que creó el registro
- `updated_by_id`: Usuario que actualizó el registro

**Validaciones**:
- DNI: 7-8 dígitos numéricos, único en el sistema
- CUIL: Formato XX-XXXXXXXX-X, único en el sistema, validación de dígito verificador
- Email: Formato válido, único en el sistema
- Edad mínima: 18 años cumplidos al momento de registro
- Teléfono: Formato argentino válido
- Status: Solo puede ser modificado por rol Gerente

**Reglas de Negocio**:
- Al crear un empleado, automáticamente se crea su usuario en el sistema con rol 'empleado'
- Al desactivar un empleado (status = 'inactivo'), se eliminan todos sus turnos futuros asignados
- No se permite eliminación física, solo lógica (cambio de status)
- Un empleado inactivo no puede tener turnos asignados
- La foto de perfil debe ser validada (formato, tamaño máximo 5MB)
- **IMPORTANTE**: Los empleados inactivos NO deben aparecer en las grillas de selección ni listados por defecto
- La desactivación de empleados debe manejar correctamente todas las relaciones (turnos, nóminas, etc.) sin generar errores

### 2. JobPosition (Puesto de Trabajo)

Representa los diferentes puestos o roles laborales en la cafetería.

**Atributos**:
- `id`: Identificador único (UUID)
- `name`: Nombre del puesto (ej: "Barista", "Cajero", "Encargado")
- `description`: Descripción del puesto
- `contract_type`: Tipo de contrato (ENUM: 'por_hora', 'part_time', 'full_time')
- `base_salary`: Salario base mensual (para part_time y full_time)
- `hourly_rate`: Tarifa por hora (para por_hora)
- `standard_hours_per_week`: Horas estándar semanales (para part_time y full_time)
- `standard_hours_per_month`: Horas estándar mensuales (calculado)
- `overtime_rate_multiplier`: Multiplicador para horas extras (ej: 1.5 para 50% adicional)
- `weekend_rate_multiplier`: Multiplicador para fines de semana (ej: 1.25)
- `holiday_rate_multiplier`: Multiplicador para feriados (ej: 2.0)
- `is_active`: Estado del puesto (boolean)
- `created_at`: Fecha de creación
- `updated_at`: Fecha de actualización
- `created_by_id`: Usuario que creó el puesto

**Validaciones**:
- Nombre único y no vacío
- Si contract_type = 'por_hora', hourly_rate es obligatorio
- Si contract_type = 'part_time' o 'full_time', base_salary y standard_hours son obligatorios
- Multiplicadores deben ser >= 1.0

**Reglas de Negocio**:
- Los puestos son configurables por el Gerente
- Un puesto puede tener múltiples empleados asignados
- No se pueden eliminar puestos con empleados activos asignados
- Al desactivar un puesto, no se desactivan automáticamente los empleados

### 3. EmployeeJobHistory (Historial de Puestos)

Mantiene el historial de cambios de puesto de cada empleado.

**Atributos**:
- `id`: Identificador único (UUID)
- `employee_id`: Relación con Employee
- `job_position_id`: Relación con JobPosition
- `start_date`: Fecha de inicio en el puesto
- `end_date`: Fecha de fin en el puesto (NULL si es el puesto actual)
- `notes`: Notas sobre el cambio
- `created_at`: Fecha de creación del registro
- `created_by_id`: Usuario que registró el cambio

**Reglas de Negocio**:
- Solo puede haber un registro activo (end_date = NULL) por empleado
- Al cambiar de puesto, se cierra el registro anterior (se asigna end_date)
- Se mantiene todo el historial para auditoría

## Funcionalidades

### CRUD de Empleados

#### Crear Empleado (POST /api/employees)
**Permisos**: Solo Gerente

**Request Body**:
```json
{
  "first_name": "Juan",
  "last_name": "Pérez",
  "dni": "12345678",
  "cuil": "20-12345678-9",
  "birth_date": "1995-03-15",
  "phone": "+54 9 11 1234-5678",
  "address": "Av. Corrientes 1234, CABA",
  "email": "juan.perez@example.com",
  "employment_relationship": "dependencia",
  "emergency_contact_name": "María Pérez",
  "emergency_contact_phone": "+54 9 11 8765-4321",
  "emergency_contact_relationship": "Hermana",
  "hire_date": "2026-02-01",
  "job_position_id": "uuid-del-puesto",
  "password": "contraseña-temporal"
}
```

**Proceso**:
1. Validar todos los campos
2. Verificar edad mínima (18 años)
3. Verificar unicidad de DNI, CUIL, email
4. Crear usuario en tabla User con rol 'empleado'
5. Crear registro en Employee
6. Crear registro inicial en EmployeeJobHistory
7. Enviar email de bienvenida con credenciales

**Response**: Empleado creado con status 201

#### Listar Empleados (GET /api/employees)
**Permisos**: Gerente (todos), Empleado (solo su propio registro)

**Query Parameters**:
- `search`: Búsqueda por nombre, DNI, email
- `status`: Filtrar por estado (activo, inactivo, suspendido, vacaciones, licencia)
- `job_position_id`: Filtrar por puesto
- `hire_date_from`: Filtrar por fecha de ingreso desde
- `hire_date_to`: Filtrar por fecha de ingreso hasta
- `page`: Número de página
- `limit`: Cantidad de resultados por página
- **NUEVO**: `include_inactive`: Boolean (default: false) - Por defecto solo muestra empleados activos

**Response**:
```json
{
  "employees": [
    {
      "id": "uuid",
      "first_name": "Juan",
      "last_name": "Pérez",
      "email": "juan.perez@example.com",
      "phone": "+54 9 11 1234-5678",
      "status": "activo",
      "job_position": {
        "id": "uuid",
        "name": "Barista"
      },
      "hire_date": "2026-02-01",
      "profile_photo_url": "url"
    }
  ],
  "total": 25,
  "page": 1,
  "limit": 10
}
```

#### Ver Detalle de Empleado (GET /api/employees/:id)
**Permisos**: Gerente (cualquier empleado), Empleado (solo su propio registro)

**Response**: Todos los datos del empleado + historial de puestos

#### Actualizar Empleado (PUT /api/employees/:id)
**Permisos**: Gerente (todos los campos), Empleado (solo datos personales: phone, address, emergency_contact)

**Request Body**: Campos a actualizar

**Reglas**:
- Si se cambia job_position_id, se actualiza EmployeeJobHistory
- Si se cambia status a 'inactivo', se eliminan turnos futuros
- **MODIFICADO**: El CUIL debe ser editable para corregir errores de carga (con validación de formato y unicidad)
- No se puede cambiar DNI una vez creado (mantener restricción solo en DNI)

#### Desactivar Empleado (PATCH /api/employees/:id/deactivate)
**Permisos**: Solo Gerente

**Proceso**:
1. Cambiar status a 'inactivo'
2. Eliminar todos los turnos futuros asignados
3. Deshabilitar acceso al sistema (user.is_active = false)
4. Registrar en log de auditoría

### CRUD de Puestos de Trabajo

#### Crear Puesto (POST /api/job-positions)
**Permisos**: Solo Gerente

**Request Body**:
```json
{
  "name": "Barista Senior",
  "description": "Encargado de preparación de cafés especiales",
  "contract_type": "full_time",
  "base_salary": 450000,
  "standard_hours_per_week": 40,
  "overtime_rate_multiplier": 1.5,
  "weekend_rate_multiplier": 1.25,
  "holiday_rate_multiplier": 2.0
}
```

#### Listar Puestos (GET /api/job-positions)
**Permisos**: Gerente

**Query Parameters**:
- `is_active`: Filtrar por activos/inactivos
- `contract_type`: Filtrar por tipo de contrato

#### Actualizar Puesto (PUT /api/job-positions/:id)
**Permisos**: Solo Gerente

#### Desactivar Puesto (PATCH /api/job-positions/:id/deactivate)
**Permisos**: Solo Gerente
**Validación**: No puede tener empleados activos asignados

## Validaciones Específicas

### DNI Argentino
- Formato: 7-8 dígitos numéricos
- Rango válido: 1.000.000 - 99.999.999
- Único en el sistema

### CUIL Argentino
- Formato: XX-XXXXXXXX-X (11 dígitos con guiones)
- Primeros 2 dígitos: tipo (20, 23, 24, 27, etc.)
- Siguientes 8 dígitos: DNI
- Último dígito: verificador (calculado con algoritmo módulo 11)
- Único en el sistema

**Algoritmo de validación**:
```
1. Extraer los 10 primeros dígitos (sin el verificador)
2. Multiplicar cada dígito por: [5,4,3,2,7,6,5,4,3,2]
3. Sumar todos los productos
4. Calcular: 11 - (suma % 11)
5. Si resultado = 11, verificador = 0
6. Si resultado = 10, verificador = 9
7. Sino, verificador = resultado
```

### Edad Mínima
- Calcular edad a partir de birth_date
- Debe tener 18 años cumplidos al momento de registro
- Validar en backend y frontend

### Email Único
- Validar formato de email
- Verificar que no exista en tabla User
- Case-insensitive

## Interfaz de Usuario

### Vista de Lista de Empleados

**Componente**: `EmployeeList.jsx`

**Elementos**:
- Header con título "Gestión de Empleados" y botón "Nuevo Empleado"
- Barra de búsqueda (busca en nombre, DNI, email)
- Filtros:
  - Estado (dropdown: Todos, Activo, Inactivo, Suspendido, Vacaciones, Licencia)
  - Puesto (dropdown con lista de puestos)
  - Fecha de ingreso (date range picker)
- Tabla con columnas:
  - Foto (thumbnail)
  - Nombre completo
  - Email
  - Teléfono
  - Puesto
  - Estado (badge con color)
  - Acciones (Ver, Editar, Desactivar)
- Paginación

**Diseño**: Tabla responsive con TailwindCSS, iconos de Lucide

### Vista de Detalle/Edición de Empleado

**Componente**: `EmployeeForm.jsx`

**Secciones**:

1. **Información Personal**
   - Foto de perfil (upload con preview)
   - Nombre y Apellido
   - DNI y CUIL
   - Fecha de nacimiento
   - Email
   - Teléfono
   - Dirección

2. **Información Laboral**
   - Tipo de relación laboral (radio buttons)
   - Puesto actual (dropdown)
   - Fecha de ingreso
   - Estado (dropdown, solo Gerente)

3. **Contacto de Emergencia**
   - Nombre
   - Teléfono
   - Relación

4. **Historial de Puestos** (solo en modo edición)
   - Tabla con: Puesto, Fecha inicio, Fecha fin, Duración

**Validaciones en tiempo real**:
- DNI: 7-8 dígitos
- CUIL: Formato y dígito verificador
- Email: Formato válido
- Edad: >= 18 años
- Teléfono: Formato argentino

**Botones**:
- Guardar
- Cancelar
- Desactivar (solo Gerente, solo en modo edición)

### Vista de Gestión de Puestos

**Componente**: `JobPositionList.jsx`

**Elementos**:
- Header con botón "Nuevo Puesto"
- Lista de puestos con:
  - Nombre
  - Tipo de contrato
  - Salario base / Tarifa horaria
  - Cantidad de empleados asignados
  - Estado
  - Acciones (Editar, Desactivar)

**Componente**: `JobPositionForm.jsx`

**Campos**:
- Nombre del puesto
- Descripción
- Tipo de contrato (radio buttons)
- Campos condicionales según tipo:
  - Por hora: Tarifa horaria
  - Part-time/Full-time: Salario base, Horas semanales
- Multiplicadores (horas extras, fin de semana, feriados)

## Endpoints del Backend

```
POST   /api/employees                    - Crear empleado
GET    /api/employees                    - Listar empleados (con filtros)
GET    /api/employees/:id                - Ver detalle de empleado
PUT    /api/employees/:id                - Actualizar empleado
PATCH  /api/employees/:id/deactivate     - Desactivar empleado
PATCH  /api/employees/:id/change-status  - Cambiar estado
POST   /api/employees/:id/photo          - Subir foto de perfil

POST   /api/job-positions                - Crear puesto
GET    /api/job-positions                - Listar puestos
GET    /api/job-positions/:id            - Ver detalle de puesto
PUT    /api/job-positions/:id            - Actualizar puesto
PATCH  /api/job-positions/:id/deactivate - Desactivar puesto

GET    /api/employees/:id/job-history    - Ver historial de puestos
```

## Modelo de Base de Datos

```sql
-- Tabla de empleados
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    dni VARCHAR(8) UNIQUE NOT NULL,
    cuil VARCHAR(13) UNIQUE NOT NULL,
    birth_date DATE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address TEXT NOT NULL,
    profile_photo_url TEXT,
    employment_relationship VARCHAR(20) NOT NULL CHECK (employment_relationship IN ('dependencia', 'monotributo')),
    emergency_contact_name VARCHAR(100) NOT NULL,
    emergency_contact_phone VARCHAR(20) NOT NULL,
    emergency_contact_relationship VARCHAR(50) NOT NULL,
    hire_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'activo' CHECK (status IN ('activo', 'inactivo', 'suspendido', 'vacaciones', 'licencia')),
    current_job_position_id UUID REFERENCES job_positions(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_id UUID REFERENCES users(id),
    updated_by_id UUID REFERENCES users(id),
    CONSTRAINT age_check CHECK (EXTRACT(YEAR FROM AGE(birth_date)) >= 18)
);

-- Tabla de puestos de trabajo
CREATE TABLE job_positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    contract_type VARCHAR(20) NOT NULL CHECK (contract_type IN ('por_hora', 'part_time', 'full_time')),
    base_salary DECIMAL(10, 2),
    hourly_rate DECIMAL(10, 2),
    standard_hours_per_week INTEGER,
    standard_hours_per_month INTEGER,
    overtime_rate_multiplier DECIMAL(3, 2) DEFAULT 1.5,
    weekend_rate_multiplier DECIMAL(3, 2) DEFAULT 1.0,
    holiday_rate_multiplier DECIMAL(3, 2) DEFAULT 1.0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_id UUID REFERENCES users(id)
);

-- Tabla de historial de puestos
CREATE TABLE employee_job_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    job_position_id UUID NOT NULL REFERENCES job_positions(id),
    start_date DATE NOT NULL,
    end_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_id UUID REFERENCES users(id),
    CONSTRAINT one_active_position_per_employee UNIQUE NULLS NOT DISTINCT (employee_id, end_date)
);

-- Índices
CREATE INDEX idx_employees_dni ON employees(dni);
CREATE INDEX idx_employees_cuil ON employees(cuil);
CREATE INDEX idx_employees_status ON employees(status);
CREATE INDEX idx_employees_user_id ON employees(user_id);
CREATE INDEX idx_employee_job_history_employee ON employee_job_history(employee_id);
CREATE INDEX idx_employee_job_history_active ON employee_job_history(employee_id, end_date) WHERE end_date IS NULL;
```

## Casos de Prueba

### Test 1: Crear empleado válido
- Crear empleado con todos los datos válidos
- Verificar que se crea el usuario asociado
- Verificar que se crea el registro en historial de puestos
- Verificar que el empleado aparece en la lista

### Test 2: Validación de DNI/CUIL
- Intentar crear empleado con DNI duplicado → Error
- Intentar crear empleado con CUIL inválido → Error
- Intentar crear empleado con CUIL duplicado → Error

### Test 3: Validación de edad
- Intentar crear empleado menor de 18 años → Error
- Crear empleado con exactamente 18 años → Success

### Test 4: Desactivar empleado con turnos
- Crear empleado y asignarle turnos futuros
- Desactivar empleado
- Verificar que los turnos fueron eliminados
- Verificar que el usuario no puede acceder al sistema
- **NUEVO**: Verificar que no se generan errores en cascada al desactivar
- **NUEVO**: Verificar que el empleado desactivado no aparece en grillas de selección

### Test 5: Cambiar puesto de empleado
- Cambiar el puesto de un empleado
- Verificar que se cierra el registro anterior en historial
- Verificar que se crea nuevo registro activo

### Test 6: Búsqueda y filtros
- Buscar por nombre → Resultados correctos
- Filtrar por estado → Solo empleados con ese estado
- Filtrar por puesto → Solo empleados de ese puesto

### Test 7: Permisos
- Empleado intenta crear otro empleado → Error 403
- Empleado intenta editar datos de otro empleado → Error 403
- Empleado edita sus propios datos personales → Success
- Gerente edita cualquier empleado → Success

## Criterios de Aceptación

- ✅ Gerente puede crear empleado con todos los datos en menos de 3 minutos
- ✅ Sistema valida correctamente DNI y CUIL argentinos
- ✅ Sistema valida edad mínima de 18 años
- ✅ Al crear empleado, se genera automáticamente su usuario
- ✅ Al desactivar empleado, se eliminan sus turnos futuros
- ✅ Empleado puede ver y editar su información personal
- ✅ Búsqueda encuentra empleados por nombre, DNI o email
- ✅ Filtros funcionan correctamente (estado, puesto, fecha)
- ✅ Historial de puestos se mantiene correctamente
- ✅ Puestos de trabajo son configurables por el Gerente
- ✅ Sistema calcula correctamente tarifas según tipo de contrato
- ✅ Foto de perfil se sube y muestra correctamente
- ✅ No se pueden eliminar empleados, solo desactivar
- ✅ Email es único en el sistema
- ✅ Interfaz es responsive y fácil de usar
- **NUEVO**: ✅ Empleados inactivos no aparecen en grillas de selección por defecto
- **NUEVO**: ✅ La desactivación de empleados funciona sin errores
- **NUEVO**: ✅ El CUIL es editable para correcciones (con validación)

## Próximos Pasos

1. Implementar modelos de base de datos
2. Crear migraciones
3. Implementar endpoints del backend
4. Implementar validaciones
5. Crear componentes del frontend
6. Integrar con sistema de autenticación
7. Pruebas unitarias e integración
8. Documentación de API
