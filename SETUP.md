# Guía de Setup Inicial

Esta guía te ayudará a configurar el proyecto desde cero.

## Paso 1: Verificar Requisitos

Asegúrate de tener instalado:

```bash
# Verificar Python
python --version  # Debe ser 3.11 o superior

# Verificar Node.js
node --version    # Debe ser 20 o superior

# Verificar PostgreSQL
psql --version    # Debe ser 15 o superior

# Verificar Docker (opcional)
docker --version
docker-compose --version
```

## Paso 2: Configurar Base de Datos

### Opción A: PostgreSQL Local

1. Crear usuario y base de datos:
```bash
# Conectarse a PostgreSQL
psql postgres

# Crear usuario
CREATE USER galia_user WITH PASSWORD 'dev_password';

# Crear base de datos
CREATE DATABASE galia_db OWNER galia_user;

# Dar permisos
GRANT ALL PRIVILEGES ON DATABASE galia_db TO galia_user;

# Salir
\q
```

### Opción B: Docker PostgreSQL

```bash
docker run -d \
  --name galia-postgres \
  -e POSTGRES_DB=galia_db \
  -e POSTGRES_USER=galia_user \
  -e POSTGRES_PASSWORD=dev_password \
  -p 5432:5432 \
  postgres:15-alpine
```

## Paso 3: Configurar Backend

```bash
# Navegar a la carpeta backend
cd backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En macOS/Linux:
source venv/bin/activate
# En Windows:
# venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Volver a la raíz del proyecto
cd ..

# Copiar archivo de variables de entorno
cp .env.example .env

# Editar .env con tus configuraciones si es necesario
# nano .env  # o usa tu editor preferido
```

## Paso 4: Inicializar Base de Datos

```bash
# Asegúrate de estar en la raíz del proyecto con el venv activado

# Inicializar migraciones
cd backend
export FLASK_APP=run.py  # En Windows: set FLASK_APP=run.py
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
cd ..
```

## Paso 5: Crear Usuario Administrador Inicial

Puedes crear un script o usar la shell de Flask:

```bash
cd backend
flask shell
```

Luego en la shell de Python:
```python
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.employee import Employee
from datetime import date

app = create_app()
with app.app_context():
    # Crear usuario admin
    admin = User(
        email='admin@galia.com',
        role='admin',
        is_active=True
    )
    admin.set_password('admin123')  # CAMBIAR EN PRODUCCIÓN
    db.session.add(admin)
    db.session.commit()
    
    # Crear empleado asociado
    employee = Employee(
        user_id=admin.id,
        full_name='Administrador',
        hourly_rate=0,
        hire_date=date.today()
    )
    db.session.add(employee)
    db.session.commit()
    
    print(f"Usuario admin creado: {admin.email}")
    exit()
```

## Paso 6: Configurar Frontend

```bash
# Navegar a la carpeta frontend
cd frontend

# Instalar dependencias
npm install

# Volver a la raíz
cd ..
```

## Paso 7: Ejecutar la Aplicación

### Opción A: Ejecución Manual

Necesitarás 2 terminales:

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # Activar venv si no está activo
python run.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Opción B: Con Docker Compose

```bash
# Desde la raíz del proyecto
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down
```

## Paso 8: Verificar Instalación

1. Abrir navegador en http://localhost:5173
2. Deberías ver la página de login
3. Ingresar con las credenciales del admin creado:
   - Email: `admin@galia.com`
   - Password: `admin123`

4. Verificar que puedes acceder al dashboard

## Paso 9: Crear Datos de Prueba (Opcional)

Puedes crear un script para poblar la base de datos con datos de prueba:

```bash
cd backend
flask shell
```

```python
from app import create_app
from app.extensions import db
from app.models import *
from datetime import date, time, datetime, timedelta

app = create_app()
with app.app_context():
    # Crear categorías de gastos
    categories = [
        ExpenseCategory(name='Insumos', description='Café, leche, etc.'),
        ExpenseCategory(name='Servicios', description='Luz, agua, internet'),
        ExpenseCategory(name='Mantenimiento', description='Reparaciones'),
        ExpenseCategory(name='Personal', description='Sueldos y cargas'),
        ExpenseCategory(name='Otros', description='Gastos varios'),
    ]
    for cat in categories:
        db.session.add(cat)
    
    # Crear empleados de prueba
    emp_user = User(email='empleado@galia.com', role='employee', is_active=True)
    emp_user.set_password('empleado123')
    db.session.add(emp_user)
    db.session.commit()
    
    employee = Employee(
        user_id=emp_user.id,
        full_name='Juan Pérez',
        hourly_rate=2500,
        hire_date=date(2024, 1, 1)
    )
    db.session.add(employee)
    
    db.session.commit()
    print("Datos de prueba creados exitosamente")
    exit()
```

## Solución de Problemas Comunes

### Error: "No module named 'app'"
- Asegúrate de estar en la carpeta `backend` cuando ejecutas Flask
- Verifica que el entorno virtual esté activado

### Error: "Connection refused" en PostgreSQL
- Verifica que PostgreSQL esté corriendo: `pg_isready`
- Verifica las credenciales en `.env`
- Verifica el puerto (por defecto 5432)

### Error: "CORS policy" en el navegador
- Verifica que `CORS_ORIGINS` en `.env` incluya `http://localhost:5173`
- Reinicia el backend después de cambiar `.env`

### Frontend no carga
- Verifica que el backend esté corriendo en puerto 5000
- Verifica la configuración del proxy en `vite.config.js`
- Limpia cache: `rm -rf node_modules package-lock.json && npm install`

### Migraciones fallan
- Elimina la carpeta `migrations` y vuelve a inicializar
- Verifica que la base de datos esté vacía
- Verifica permisos del usuario en PostgreSQL

## Próximos Pasos

Una vez que la aplicación esté corriendo:

1. Familiarízate con la estructura del código
2. Lee las especificaciones en `specs/`
3. Revisa el roadmap en `README.md`
4. Comienza a implementar las funcionalidades según las prioridades

## Recursos Adicionales

- [Documentación de Flask](https://flask.palletsprojects.com/)
- [Documentación de React](https://react.dev/)
- [Documentación de SQLAlchemy](https://docs.sqlalchemy.org/)
- [Documentación de TailwindCSS](https://tailwindcss.com/)
