# Galia - Sistema de Gestión para Cafetería

Sistema web monolítico para la gestión integral de una cafetería con servicio a la mesa.

## Características Principales

- 📅 **Gestión de Grillas Horarias**: Planificación y asignación de turnos del personal
- 💰 **Liquidación de Sueldos**: Cálculo automático basado en horas trabajadas
- 🛒 **Registro de Ventas**: Control de ingresos y transacciones
- 💸 **Gestión de Gastos**: Seguimiento de egresos por categoría
- 📊 **Reportes y Análisis**: Reportes comparativos semanales, mensuales y trimestrales
- 📈 **Balance Financiero**: Análisis de rentabilidad del negocio

## Stack Tecnológico

### Backend
- **Flask** (Python 3.11)
- **PostgreSQL** 15
- **SQLAlchemy** ORM
- **Flask-Login** para autenticación

### Frontend
- **React** 18
- **Vite** como build tool
- **TailwindCSS** para estilos
- **React Router** para navegación
- **React Query** para manejo de estado del servidor
- **Lucide React** para iconos

## Requisitos Previos

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Docker y Docker Compose (opcional)

## Instalación y Configuración

### Opción 1: Con Docker (Recomendado)

1. Clonar el repositorio:
```bash
git clone <repository-url>
cd sdd-galia-app
```

2. Copiar el archivo de variables de entorno:
```bash
cp .env.example .env
```

3. Levantar los servicios con Docker Compose:
```bash
docker-compose up -d
```

4. Acceder a la aplicación:
- Frontend: http://localhost:5173
- Backend API: http://localhost:5000

### Opción 2: Instalación Local

#### Backend

1. Crear y activar entorno virtual:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno:
```bash
cp ../.env.example ../.env
# Editar .env con tus configuraciones
```

4. Crear la base de datos PostgreSQL:
```bash
createdb galia_db
```

5. Inicializar migraciones:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

6. Ejecutar el servidor:
```bash
python run.py
```

#### Frontend

1. Instalar dependencias:
```bash
cd frontend
npm install
```

2. Ejecutar el servidor de desarrollo:
```bash
npm run dev
```

3. Acceder a http://localhost:5173

## Estructura del Proyecto

```
sdd-galia-app/
├── backend/                    # Backend Flask
│   ├── app/
│   │   ├── models/            # Modelos SQLAlchemy
│   │   ├── routes/            # Endpoints API REST
│   │   ├── services/          # Lógica de negocio
│   │   └── utils/             # Utilidades
│   ├── migrations/            # Migraciones de DB
│   └── requirements.txt       # Dependencias Python
│
├── frontend/                   # Frontend React
│   ├── src/
│   │   ├── components/        # Componentes React
│   │   ├── pages/             # Páginas/Vistas
│   │   ├── services/          # API client
│   │   └── context/           # React Context
│   └── package.json           # Dependencias Node
│
├── specs/                      # Especificaciones
├── docs/                       # Documentación
├── docker-compose.yml          # Docker Compose config
└── README.md
```

## API Endpoints

### Autenticación
- `POST /api/v1/auth/login` - Iniciar sesión
- `POST /api/v1/auth/logout` - Cerrar sesión
- `GET /api/v1/auth/me` - Usuario actual

### Grillas Horarias
- `GET /api/v1/schedules` - Listar grillas
- `POST /api/v1/schedules` - Crear grilla
- `GET /api/v1/schedules/:id` - Detalle de grilla
- `PUT /api/v1/schedules/:id` - Actualizar grilla
- `DELETE /api/v1/schedules/:id` - Eliminar grilla

### Ventas
- `GET /api/v1/sales` - Listar ventas
- `POST /api/v1/sales` - Registrar venta
- `GET /api/v1/sales/:id` - Detalle de venta

### Gastos
- `GET /api/v1/expenses` - Listar gastos
- `POST /api/v1/expenses` - Registrar gasto
- `GET /api/v1/expenses/categories` - Categorías de gastos

### Reportes
- `GET /api/v1/reports/sales` - Reporte de ventas
- `GET /api/v1/reports/expenses` - Reporte de gastos
- `GET /api/v1/reports/balance` - Balance financiero
- `GET /api/v1/reports/payroll` - Reporte de sueldos

## Desarrollo

### Ejecutar Tests

Backend:
```bash
cd backend
pytest
```

Frontend:
```bash
cd frontend
npm test
```

### Migraciones de Base de Datos

Crear nueva migración:
```bash
flask db migrate -m "Descripción del cambio"
```

Aplicar migraciones:
```bash
flask db upgrade
```

Revertir migración:
```bash
flask db downgrade
```

## Deployment

Ver la documentación completa de deployment en `specs/technical-architecture.md`.

### Opciones recomendadas:
1. **Render.com** (más simple, free tier disponible)
2. **Railway.app** (fácil de usar)
3. **DigitalOcean App Platform** (escalable)
4. **Docker en VPS** (más control)

## Roles de Usuario

### Administrador/Gerente
- Acceso completo a todas las funcionalidades
- Gestión de grillas horarias
- Liquidación de sueldos
- Gestión de gastos
- Visualización de reportes y balances
- Gestión de empleados

### Empleado
- Consulta de horarios asignados
- Registro de ventas
- Visualización de información personal

## Contribuir

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto es privado y propietario.

## Soporte

Para preguntas o problemas, contactar al equipo de desarrollo.

## Roadmap

### Fase 1: MVP (4-6 semanas)
- [x] Setup inicial del proyecto
- [ ] Autenticación y gestión de usuarios
- [ ] Gestión de grilla horaria
- [ ] Consulta de horario para empleados
- [ ] Registro de ventas
- [ ] Deploy inicial

### Fase 2: Core Features (3-4 semanas)
- [ ] Liquidación de sueldos
- [ ] Gestión de gastos
- [ ] Reportes básicos de ventas

### Fase 3: Analytics (2-3 semanas)
- [ ] Balance financiero
- [ ] Seguimiento de precios de insumos
- [ ] Reportes avanzados y exportación
