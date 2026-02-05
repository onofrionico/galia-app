# Guía de Configuración - Módulo de Gestión de Empleados

## ✅ Implementación Completada

Se ha implementado completamente el módulo de gestión de empleados con las siguientes características:

### Backend
- ✅ Modelos de base de datos (Employee, JobPosition, EmployeeJobHistory)
- ✅ Validaciones de DNI/CUIL argentino con dígito verificador
- ✅ Validación de edad mínima 18 años
- ✅ Endpoints REST API completos (CRUD)
- ✅ Migración de base de datos
- ✅ Permisos diferenciados (admin vs empleado)
- ✅ Eliminación automática de turnos al desactivar empleado

### Frontend
- ✅ Lista de empleados con búsqueda y filtros
- ✅ Formulario de creación/edición con validaciones
- ✅ Vista de detalle con historial de puestos
- ✅ Gestión de puestos de trabajo
- ✅ Utilidades de validación (DNI/CUIL)
- ✅ Rutas configuradas en React Router

## 📋 Pasos para Completar la Configuración

### 1. Aplicar la Migración de Base de Datos

```bash
cd backend

# Activar entorno virtual (si usas uno)
source venv/bin/activate  # En Linux/Mac
# o
venv\Scripts\activate  # En Windows

# Aplicar la migración
flask db upgrade

# Verificar que las tablas se crearon correctamente
flask shell
>>> from app.extensions import db
>>> db.engine.table_names()
```

**Nota**: La migración realizará los siguientes cambios:
- Creará la tabla `job_positions`
- Creará la tabla `employee_job_history`
- Agregará nuevos campos a la tabla `employees` existente
- Migrará datos existentes (dividirá `full_name` en `first_name` y `last_name`)

### 2. Crear Puestos de Trabajo Iniciales

Antes de crear empleados, necesitas crear al menos un puesto de trabajo. Puedes hacerlo de dos formas:

#### Opción A: Desde el Frontend
1. Inicia el servidor backend y frontend
2. Accede a `/job-positions`
3. Crea los puestos necesarios (ej: Barista, Cajero, Encargado)

#### Opción B: Desde Python Shell
```python
from app import create_app
from app.extensions import db
from app.models.job_position import JobPosition

app = create_app()
with app.app_context():
    # Crear puesto por hora
    barista = JobPosition(
        name='Barista',
        description='Preparación de cafés y bebidas',
        contract_type='por_hora',
        hourly_rate=2500.00,
        overtime_rate_multiplier=1.5,
        weekend_rate_multiplier=1.25,
        holiday_rate_multiplier=2.0,
        is_active=True
    )
    
    # Crear puesto full-time
    encargado = JobPosition(
        name='Encargado',
        description='Gestión general del local',
        contract_type='full_time',
        base_salary=500000.00,
        standard_hours_per_week=40,
        standard_hours_per_month=160,
        overtime_rate_multiplier=1.5,
        weekend_rate_multiplier=1.25,
        holiday_rate_multiplier=2.0,
        is_active=True
    )
    
    db.session.add(barista)
    db.session.add(encargado)
    db.session.commit()
    
    print("Puestos creados exitosamente")
```

### 3. Actualizar Empleados Existentes (Si los hay)

Si ya tienes empleados en la base de datos, necesitarás actualizar sus datos:

```python
from app import create_app
from app.extensions import db
from app.models.employee import Employee
from app.models.employee_job_history import EmployeeJobHistory
from datetime import date

app = create_app()
with app.app_context():
    employees = Employee.query.all()
    
    for emp in employees:
        # Asignar datos faltantes (ajusta según tus necesidades)
        if not emp.dni:
            emp.dni = '12345678'  # Reemplazar con DNI real
        if not emp.cuil:
            emp.cuil = '20-12345678-9'  # Reemplazar con CUIL real
        if not emp.birth_date:
            emp.birth_date = date(1990, 1, 1)  # Reemplazar con fecha real
        if not emp.phone:
            emp.phone = '+54 9 11 1234-5678'
        if not emp.address:
            emp.address = 'Dirección a completar'
        if not emp.employment_relationship:
            emp.employment_relationship = 'dependencia'
        if not emp.emergency_contact_name:
            emp.emergency_contact_name = 'Contacto a completar'
        if not emp.emergency_contact_phone:
            emp.emergency_contact_phone = '+54 9 11 0000-0000'
        if not emp.emergency_contact_relationship:
            emp.emergency_contact_relationship = 'Familiar'
        if not emp.status:
            emp.status = 'activo'
        
        # Asignar a un puesto (ajusta el ID según corresponda)
        if not emp.current_job_position_id:
            emp.current_job_position_id = 1  # ID del puesto
            
            # Crear registro en historial
            history = EmployeeJobHistory(
                employee_id=emp.id,
                job_position_id=1,
                start_date=emp.hire_date or date.today(),
                notes='Migración inicial'
            )
            db.session.add(history)
    
    db.session.commit()
    print(f"Actualizados {len(employees)} empleados")
```

### 4. Iniciar los Servidores

#### Backend
```bash
cd backend
source venv/bin/activate  # Si usas entorno virtual
python run.py
```

#### Frontend
```bash
cd frontend
npm install  # Si es la primera vez
npm run dev
```

### 5. Probar el Módulo

#### Flujo de Prueba Completo:

1. **Gestión de Puestos**
   - Acceder a `/job-positions`
   - Crear un puesto "Por Hora" (ej: Barista)
   - Crear un puesto "Full Time" (ej: Encargado)
   - Editar un puesto y cambiar multiplicadores
   - Verificar que no se puede desactivar un puesto con empleados asignados

2. **Crear Empleado**
   - Acceder a `/employees`
   - Click en "Nuevo Empleado"
   - Completar todos los campos requeridos
   - Probar validaciones:
     - DNI con menos de 7 dígitos → Error
     - CUIL con dígito verificador incorrecto → Error
     - Fecha de nacimiento menor a 18 años → Error
     - Email inválido → Error
   - Crear empleado con datos válidos
   - Verificar que se crea automáticamente el usuario
   - Verificar que aparece en el historial de puestos

3. **Búsqueda y Filtros**
   - Buscar por nombre → Debe filtrar
   - Buscar por DNI → Debe filtrar
   - Buscar por email → Debe filtrar
   - Filtrar por estado → Debe mostrar solo ese estado
   - Filtrar por puesto → Debe mostrar solo ese puesto
   - Filtrar por rango de fechas → Debe filtrar correctamente
   - Limpiar filtros → Debe mostrar todos

4. **Ver Detalle**
   - Click en un empleado
   - Verificar que muestra toda la información
   - Verificar que muestra el historial de puestos
   - Verificar badges de estado y tipo de contrato

5. **Editar Empleado**
   - Como admin: Editar todos los campos
   - Cambiar puesto → Verificar que se actualiza el historial
   - Cambiar estado a "vacaciones" → Debe actualizar
   - Como empleado: Solo editar datos personales permitidos

6. **Desactivar Empleado**
   - Crear turnos futuros para un empleado
   - Desactivar el empleado
   - Verificar que los turnos futuros se eliminaron
   - Verificar que el usuario no puede acceder al sistema
   - Verificar que el empleado aparece como "Inactivo"

7. **Permisos**
   - Login como empleado regular
   - Verificar que solo ve su propia información en `/employees`
   - Verificar que puede editar sus datos personales
   - Verificar que NO puede crear/desactivar empleados
   - Verificar que NO puede acceder a `/job-positions`

## 🔧 Solución de Problemas

### Error: "No module named flask"
```bash
pip install -r requirements.txt
```

### Error: "Table already exists"
Si la migración falla porque las tablas ya existen:
```bash
flask db stamp head
flask db migrate -m "Fix migration"
flask db upgrade
```

### Error: "CUIL inválido" al crear empleado
Verifica que el CUIL tenga el formato correcto: XX-XXXXXXXX-X
El dígito verificador debe ser correcto según el algoritmo módulo 11.

Ejemplo de CUIL válido para DNI 12345678:
- Calcular: 2*5 + 0*4 + 1*3 + 2*2 + 3*7 + 4*6 + 5*5 + 6*4 + 7*3 + 8*2 = 158
- 158 % 11 = 4
- 11 - 4 = 7
- CUIL: 20-12345678-7

### Error: "Employee must be at least 18 years old"
Verifica que la fecha de nacimiento sea al menos 18 años antes de hoy.

### Los filtros no funcionan
Verifica que el backend esté corriendo y que la URL del API esté configurada correctamente en `.env`:
```
VITE_API_URL=http://localhost:5000
```

## 📊 Estructura de Datos

### Employee
- Información personal: nombre, DNI, CUIL, fecha nacimiento, contacto
- Información laboral: puesto, tipo relación, fecha ingreso, estado
- Contacto emergencia: nombre, teléfono, relación
- Foto de perfil (opcional)

### JobPosition
- Nombre y descripción
- Tipo de contrato: por_hora, part_time, full_time
- Salario base o tarifa horaria
- Horas estándar (para part_time/full_time)
- Multiplicadores: horas extras, fin de semana, feriados

### EmployeeJobHistory
- Empleado
- Puesto
- Fecha inicio y fin
- Notas

## 🎯 Próximas Mejoras Sugeridas

1. **Upload de Foto de Perfil**: Implementar endpoint para subir imágenes
2. **Exportar a Excel**: Agregar botón para exportar lista de empleados
3. **Notificaciones**: Enviar email al crear empleado con credenciales
4. **Dashboard de Empleados**: Estadísticas de empleados por puesto, estado, etc.
5. **Gestión de Permisos Granular**: Roles intermedios (supervisor, etc.)
6. **Historial de Cambios**: Auditoría completa de modificaciones
7. **Integración con Nómina**: Calcular sueldos automáticamente
8. **Reportes**: Generar reportes de empleados en PDF

## 📝 Notas Importantes

- **Seguridad**: Las contraseñas se hashean con bcrypt
- **Validaciones**: Se validan tanto en frontend como backend
- **Eliminación**: Los empleados NO se eliminan físicamente, solo se desactivan
- **Turnos**: Al desactivar un empleado, se eliminan TODOS sus turnos futuros
- **Historial**: Se mantiene registro completo de cambios de puesto
- **Permisos**: Solo el rol "admin" puede gestionar empleados y puestos

## 🆘 Soporte

Si encuentras algún problema, verifica:
1. Logs del backend en la consola
2. Logs del frontend en la consola del navegador (F12)
3. Respuestas de la API en la pestaña Network
4. Estado de la base de datos con `flask shell`
