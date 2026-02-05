# Datos de Prueba - Galia Cafetería

Este documento describe los datos de prueba disponibles para la aplicación de gestión de cafetería.

## ⚠️ IMPORTANTE

**Este script es SOLO para desarrollo y pruebas locales.**

- Los datos de prueba NO son parte de las migraciones de Alembic
- Se cargan mediante un script independiente (`seed_test_data.py`)
- El script verifica automáticamente si ya existen datos antes de insertarlos
- Si detecta que ya existe el usuario `admin@galia.com`, te preguntará si deseas recargar
- **NO ejecutar en producción** - solo para desarrollo local

## 🚀 Cómo Cargar los Datos de Prueba

### Opción 1: Usando el script de carga (Recomendado)
```bash
cd backend
python load_test_data.py
```

### Opción 2: Usando el script de seed directamente
```bash
cd backend
python seed_test_data.py
```

## 👥 Usuarios y Credenciales

### Administrador
- **Email:** `admin@galia.com`
- **Password:** `admin123`
- **Rol:** Admin
- **Nombre:** Administrador Galia

### Empleados
Todos los empleados tienen la contraseña: `empleado123`

1. **Juan Pérez**
   - Email: `juan.perez@galia.com`
   - Tarifa: $1,800/hora
   - Fecha de contratación: 15/03/2024

2. **María García**
   - Email: `maria.garcia@galia.com`
   - Tarifa: $1,900/hora
   - Fecha de contratación: 01/02/2024

3. **Carlos Rodríguez**
   - Email: `carlos.rodriguez@galia.com`
   - Tarifa: $1,750/hora
   - Fecha de contratación: 10/04/2024

4. **Ana Martínez**
   - Email: `ana.martinez@galia.com`
   - Tarifa: $2,000/hora
   - Fecha de contratación: 20/01/2024

5. **Pedro López**
   - Email: `pedro.lopez@galia.com`
   - Tarifa: $1,850/hora
   - Fecha de contratación: 05/05/2024

## 📊 Datos Incluidos

### Horarios y Turnos
- **4 horarios semanales** (últimas 4 semanas)
- **~140 turnos** distribuidos entre todos los empleados
- Turnos de mañana (7:00-15:00 / 8:00-16:00)
- Turnos de tarde (15:00-23:00 / 16:00-22:00)
- Turnos de fin de semana (9:00-17:00)

### Ventas
- **~200 ventas** de los últimos 30 días
- 5-10 ventas por día
- Métodos de pago: efectivo, tarjeta débito, tarjeta crédito, transferencia
- Productos incluidos:
  - Café expreso ($800)
  - Café con leche ($1,000)
  - Cappuccino ($1,200)
  - Medialunas ($1,500)
  - Tostado ($2,000)
  - Sandwich de miga ($1,800)
  - Jugo natural ($1,300)
  - Agua mineral ($600)

### Gastos
- **~30 gastos** de los últimos 30 días
- Categorías:
  - Alimentos (cada 3 días)
  - Servicios (cada 10 días)
  - Limpieza (cada 7 días)
  - Mantenimiento
  - Equipamiento
  - Marketing

### Suministros
- **8 suministros** activos:
  - Café en grano (kg)
  - Leche (litros)
  - Azúcar (kg)
  - Vasos descartables (unidades)
  - Servilletas (paquetes)
  - Pan (kg)
  - Medialunas (docenas)
  - Facturas (docenas)

- **Precios históricos** de los últimos 30 días para seguimiento de costos

### Nóminas
- **5 nóminas** del mes anterior
- Calculadas basadas en horas trabajadas y tarifa por hora
- Aproximadamente 160-180 horas por empleado

### Notificaciones
- **4 notificaciones** de ejemplo:
  - Nuevos horarios publicados
  - Turnos modificados
  - Turnos asignados

### Logs de Cambios
- **Registro de cambios** en horarios
- Historial de modificaciones de turnos

## 🧪 Casos de Prueba Cubiertos

### Gestión de Empleados
✅ Ver lista de empleados  
✅ Ver detalles de empleado individual  
✅ Empleados con diferentes tarifas horarias  
✅ Empleados con diferentes fechas de contratación  

### Gestión de Horarios
✅ Horarios en estado "draft" y "published"  
✅ Múltiples turnos por día  
✅ Turnos de diferentes duraciones  
✅ Distribución de empleados en turnos  
✅ Horarios de fin de semana  

### Ventas
✅ Ventas con múltiples items  
✅ Diferentes métodos de pago  
✅ Ventas distribuidas a lo largo del día  
✅ Ventas asignadas a diferentes empleados  
✅ Histórico de 30 días  

### Gastos
✅ Gastos en diferentes categorías  
✅ Gastos recurrentes (servicios, limpieza)  
✅ Gastos con y sin proveedor  
✅ Histórico de 30 días  

### Suministros
✅ Seguimiento de precios históricos  
✅ Diferentes unidades de medida  
✅ Múltiples proveedores  
✅ Tendencias de precios  

### Nóminas
✅ Cálculo de salarios  
✅ Diferentes horas trabajadas por empleado  
✅ Histórico mensual  

### Notificaciones
✅ Notificaciones leídas y no leídas  
✅ Diferentes tipos de notificaciones  
✅ Notificaciones relacionadas con horarios y turnos  

## 🔄 Resetear los Datos

Para eliminar todos los datos de prueba y volver a empezar:

```bash
cd backend
flask db downgrade -1
flask db upgrade
```

Esto ejecutará el método `downgrade()` de la migración que eliminará todos los datos de prueba.

## 📝 Notas Importantes

1. **Los datos son relativos**: Las fechas se generan relativamente a la fecha actual, por lo que siempre tendrás datos "recientes".

2. **Contraseñas hasheadas**: Todas las contraseñas están correctamente hasheadas usando bcrypt.

3. **Relaciones intactas**: Todos los datos respetan las foreign keys y relaciones entre tablas.

4. **Datos realistas**: Los montos, horarios y cantidades son realistas para una cafetería.

5. **ML System**: Si tienes el sistema de ML activado, estos datos pueden ser usados para entrenar modelos de predicción.

## 🎯 Próximos Pasos

Después de cargar los datos de prueba, puedes:

1. Iniciar sesión con cualquiera de las credenciales
2. Explorar el dashboard con datos reales
3. Probar la creación de nuevos horarios
4. Registrar nuevas ventas
5. Generar reportes con datos históricos
6. Probar las notificaciones
7. Verificar el cálculo de nóminas

## ⚠️ Advertencias

- **No usar en producción**: Estos datos son solo para desarrollo y pruebas
- **Contraseñas débiles**: Las contraseñas son simples para facilitar las pruebas
- **Datos ficticios**: Todos los nombres y datos son ficticios
