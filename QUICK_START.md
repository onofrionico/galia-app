# 🚀 Guía Rápida - Módulo de Empleados

## ✅ Estado Actual

**Backend**: ✅ Corriendo en http://localhost:5000
**Frontend**: ✅ Corriendo en http://localhost:5173

## 🔑 Credenciales de Acceso

```
Email: admin@cafeteria.com
Password: admin123
```

## 📊 Datos de Prueba Creados

Se han creado 4 puestos de trabajo:

1. **Barista** (Por Hora) - $2,500/hora
2. **Cajero/a** (Por Hora) - $2,300/hora
3. **Encargado/a** (Full Time) - $500,000/mes
4. **Ayudante de Cocina** (Part Time) - $250,000/mes

## 🧪 Flujo de Prueba Recomendado

### 1. Acceder a la Aplicación
- Abre http://localhost:5173
- Inicia sesión con las credenciales de admin

### 2. Ver Puestos de Trabajo
- Navega a "Puestos de Trabajo" (si está en el menú) o accede directamente a http://localhost:5173/job-positions
- Verifica que se muestran los 4 puestos creados
- Prueba editar un puesto
- Prueba crear un nuevo puesto

### 3. Crear un Empleado
- Navega a "Empleados" o accede a http://localhost:5173/employees
- Click en "Nuevo Empleado"
- Completa el formulario con datos de prueba:

**Información Personal:**
- Nombre: Juan
- Apellido: Pérez
- DNI: 12345678
- CUIL: 20-12345678-7 (el dígito verificador debe ser correcto)
- Fecha de Nacimiento: 01/01/1990 (debe tener +18 años)
- Email: juan.perez@example.com
- Teléfono: +54 9 11 1234-5678
- Dirección: Av. Corrientes 1234, CABA

**Información Laboral:**
- Tipo de Relación: Relación de Dependencia
- Puesto: Barista
- Fecha de Ingreso: (fecha actual)
- Contraseña Temporal: empleado123

**Contacto de Emergencia:**
- Nombre: María Pérez
- Teléfono: +54 9 11 9876-5432
- Relación: Hermana

### 4. Probar Validaciones

Intenta crear un empleado con datos inválidos para verificar las validaciones:

- **DNI inválido**: 123 → Debe mostrar error
- **CUIL inválido**: 20-12345678-0 → Debe mostrar error (dígito verificador incorrecto)
- **Menor de edad**: Fecha de nacimiento reciente → Debe mostrar error
- **Email inválido**: test@test → Debe mostrar error

### 5. Buscar y Filtrar Empleados

Una vez creados algunos empleados:
- Busca por nombre
- Busca por DNI
- Filtra por estado
- Filtra por puesto
- Filtra por rango de fechas de ingreso

### 6. Ver Detalle de Empleado

- Click en un empleado de la lista
- Verifica que muestra toda la información
- Verifica que muestra el historial de puestos

### 7. Editar Empleado

- Desde el detalle, click en "Editar"
- Modifica algunos campos
- Guarda los cambios
- Verifica que se actualizaron correctamente

### 8. Cambiar Puesto de Empleado

- Edita un empleado
- Cambia su puesto a otro diferente
- Guarda
- Verifica en el detalle que el historial de puestos se actualizó

### 9. Desactivar Empleado

- Desde el detalle de un empleado
- Click en "Desactivar"
- Confirma la acción
- Verifica que el empleado aparece como "Inactivo"
- Verifica que no puede iniciar sesión con sus credenciales

## 🐛 Verificaciones Importantes

### ✅ Validación de CUIL
El CUIL debe tener el formato XX-XXXXXXXX-X y el dígito verificador debe ser correcto.

**Ejemplos de CUILs válidos:**
- DNI 12345678 → CUIL: 20-12345678-7
- DNI 23456789 → CUIL: 20-23456789-4
- DNI 34567890 → CUIL: 20-34567890-0

**Calculadora online**: Puedes usar https://www.cuil.org.ar/ para generar CUILs válidos

### ✅ Edad Mínima
La fecha de nacimiento debe resultar en una edad de al menos 18 años.

### ✅ Email Único
No se pueden crear dos empleados con el mismo email.

### ✅ Historial de Puestos
Cada vez que cambias el puesto de un empleado, se crea un registro en el historial.

### ✅ Permisos
- **Admin**: Puede crear, editar, ver y desactivar empleados
- **Empleado**: Solo puede ver su propia información

## 🔧 Comandos Útiles

### Reiniciar Backend
```bash
cd backend
source venv/bin/activate
python run.py
```

### Reiniciar Frontend
```bash
cd frontend
npm run dev
```

### Ver Logs del Backend
Los logs se muestran en la terminal donde ejecutaste `python run.py`

### Ver Logs del Frontend
Abre la consola del navegador (F12) y ve a la pestaña "Console"

### Recrear Datos de Prueba
```bash
cd backend
source venv/bin/activate
python init_test_data.py
```

## 📝 Notas

- Los empleados creados automáticamente obtienen una cuenta de usuario
- La contraseña temporal debe ser cambiada en el primer acceso (funcionalidad pendiente)
- Al desactivar un empleado, se eliminan sus turnos futuros
- Los empleados desactivados no pueden acceder al sistema
- El historial de puestos se mantiene incluso si se desactiva el empleado

## 🎯 Próximos Pasos Sugeridos

1. Probar crear varios empleados con diferentes puestos
2. Verificar que las búsquedas y filtros funcionan correctamente
3. Probar el cambio de estado de empleados
4. Verificar que los permisos funcionan correctamente
5. Probar la edición de puestos de trabajo

## 🆘 Problemas Comunes

### Error: "Could not determine join condition"
✅ **Solucionado**: Se especificó `foreign_keys` en la relación User.employee

### Error: "CUIL inválido"
Verifica que el dígito verificador sea correcto usando la calculadora online

### No se muestran los empleados
Verifica que el backend esté corriendo y que no haya errores en la consola

### Error 401 al hacer login
Verifica que las credenciales sean correctas: admin@cafeteria.com / admin123

## ✨ Características Implementadas

- ✅ CRUD completo de empleados
- ✅ CRUD completo de puestos de trabajo
- ✅ Validación de DNI argentino (7-8 dígitos)
- ✅ Validación de CUIL con dígito verificador
- ✅ Validación de edad mínima 18 años
- ✅ Email único en el sistema
- ✅ Búsqueda en tiempo real
- ✅ Filtros avanzados (estado, puesto, fechas)
- ✅ Paginación
- ✅ Historial de puestos
- ✅ Desactivación lógica (no física)
- ✅ Permisos por rol
- ✅ UI responsive con TailwindCSS
- ✅ Validaciones en frontend y backend

¡Todo listo para probar! 🎉
