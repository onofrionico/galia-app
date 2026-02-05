# Arquitectura Técnica: Sistema de Gestión para Cafetería

**Created**: 2026-02-04  
**Type**: Aplicación Web Monolítica

## Visión General

Aplicación web monolítica con arquitectura simple y fácilmente deployable. Prioriza simplicidad, mantenibilidad y bajo costo operativo.

## Stack Tecnológico

### Backend

**Framework**: **Flask** (Python)
- Simple y ligero
- Excelente para aplicaciones monolíticas
- Amplia documentación y comunidad
- Fácil de aprender y mantener

**Base de Datos**: **PostgreSQL**
- Robusta y confiable
- Excelente para datos transaccionales
- Soporte nativo para backups
- Gratuita y open source

**ORM**: **SQLAlchemy**
- Integración perfecta con Flask
- Migraciones con Alembic
- Queries type-safe

**Autenticación**: **Flask-Login + Flask-Bcrypt**
- Manejo de sesiones simple
- Encriptación de contraseñas
- Protección CSRF integrada

### Frontend

**Framework**: **React** con **Vite**
- Componentes reutilizables
- Excelente experiencia de desarrollo
- Build rápido con Vite

**UI Framework**: **shadcn/ui** + **TailwindCSS**
- Componentes modernos y accesibles
- Diseño responsive por defecto
- Fácil personalización

**Iconos**: **Lucide React**
- Iconos modernos y consistentes
- Ligero y tree-shakeable

**State Management**: **React Context API** + **React Query**
- Context para estado de autenticación
- React Query para cache y sincronización de datos del servidor
- Sin complejidad innecesaria de Redux

**Routing**: **React Router v6**
- Routing declarativo
- Protección de rutas por rol

**Gráficos**: **Recharts**
- Gráficos responsive
- Fácil integración con React
- Suficiente para reportes y dashboards

### Estructura del Proyecto Monolítico

```
sdd-galia-app/
├── backend/
│   ├── app/
│   │   ├── __init__.py           # Inicialización de Flask app
│   │   ├── config.py             # Configuración (dev, prod)
│   │   ├── models/               # Modelos SQLAlchemy
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── employee.py
│   │   │   ├── schedule.py
│   │   │   ├── shift.py
│   │   │   ├── sale.py
│   │   │   ├── expense.py
│   │   │   └── ...
│   │   ├── routes/               # Endpoints API REST
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── schedules.py
│   │   │   ├── sales.py
│   │   │   ├── expenses.py
│   │   │   ├── reports.py
│   │   │   └── ...
│   │   ├── services/             # Lógica de negocio
│   │   │   ├── __init__.py
│   │   │   ├── schedule_service.py
│   │   │   ├── payroll_service.py
│   │   │   ├── report_service.py
│   │   │   └── ...
│   │   ├── utils/                # Utilidades
│   │   │   ├── decorators.py     # @admin_required, etc.
│   │   │   ├── validators.py
│   │   │   └── helpers.py
│   │   └── extensions.py         # db, login_manager, etc.
│   ├── migrations/               # Alembic migrations
│   ├── tests/                    # Tests unitarios
│   ├── requirements.txt          # Dependencias Python
│   └── run.py                    # Entry point
│
├── frontend/
│   ├── src/
│   │   ├── components/           # Componentes React
│   │   │   ├── ui/              # shadcn/ui components
│   │   │   ├── layout/
│   │   │   │   ├── Navbar.jsx
│   │   │   │   ├── Sidebar.jsx
│   │   │   │   └── Layout.jsx
│   │   │   ├── schedules/
│   │   │   │   ├── ScheduleGrid.jsx
│   │   │   │   ├── ShiftForm.jsx
│   │   │   │   └── ...
│   │   │   ├── sales/
│   │   │   ├── reports/
│   │   │   └── ...
│   │   ├── pages/                # Páginas/Vistas
│   │   │   ├── Login.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Schedules.jsx
│   │   │   ├── Sales.jsx
│   │   │   ├── Expenses.jsx
│   │   │   ├── Reports.jsx
│   │   │   └── ...
│   │   ├── hooks/                # Custom hooks
│   │   │   ├── useAuth.js
│   │   │   ├── useSchedules.js
│   │   │   └── ...
│   │   ├── services/             # API client
│   │   │   ├── api.js           # Axios config
│   │   │   ├── authService.js
│   │   │   ├── scheduleService.js
│   │   │   └── ...
│   │   ├── context/              # React Context
│   │   │   └── AuthContext.jsx
│   │   ├── utils/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── docs/                         # Documentación
├── specs/                        # Especificaciones
├── .env.example                  # Variables de entorno ejemplo
├── docker-compose.yml            # Para desarrollo local
├── Dockerfile                    # Para deployment
└── README.md
```

## Arquitectura de Capas

```
┌─────────────────────────────────────────┐
│         Frontend (React + Vite)         │
│  - Componentes UI                       │
│  - State Management (Context + Query)   │
│  - Routing                              │
└─────────────────┬───────────────────────┘
                  │ HTTP/REST API
┌─────────────────▼───────────────────────┐
│         Backend (Flask)                 │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │   Routes (API Endpoints)          │ │
│  │   - /api/auth/*                   │ │
│  │   - /api/schedules/*              │ │
│  │   - /api/sales/*                  │ │
│  │   - /api/reports/*                │ │
│  └──────────────┬────────────────────┘ │
│                 │                       │
│  ┌──────────────▼────────────────────┐ │
│  │   Services (Business Logic)      │ │
│  │   - ScheduleService              │ │
│  │   - PayrollService               │ │
│  │   - ReportService                │ │
│  └──────────────┬────────────────────┘ │
│                 │                       │
│  ┌──────────────▼────────────────────┐ │
│  │   Models (SQLAlchemy ORM)        │ │
│  │   - User, Employee, Schedule     │ │
│  │   - Sale, Expense, Report        │ │
│  └──────────────┬────────────────────┘ │
└─────────────────┼───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         PostgreSQL Database             │
└─────────────────────────────────────────┘
```

## API REST Design

### Convenciones
- **Base URL**: `/api/v1`
- **Formato**: JSON
- **Autenticación**: Session-based (Flask-Login)
- **Status Codes**: Estándar HTTP

### Endpoints Principales

#### Autenticación
```
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
GET    /api/v1/auth/me
```

#### Grillas Horarias
```
GET    /api/v1/schedules              # Listar grillas
POST   /api/v1/schedules              # Crear grilla
GET    /api/v1/schedules/:id          # Detalle grilla
PUT    /api/v1/schedules/:id          # Actualizar grilla
DELETE /api/v1/schedules/:id          # Eliminar grilla
GET    /api/v1/schedules/:id/shifts   # Turnos de una grilla
POST   /api/v1/schedules/:id/shifts   # Agregar turno
PUT    /api/v1/shifts/:id             # Actualizar turno
DELETE /api/v1/shifts/:id             # Eliminar turno
```

#### Empleados
```
GET    /api/v1/employees              # Listar empleados
POST   /api/v1/employees              # Crear empleado
GET    /api/v1/employees/:id          # Detalle empleado
PUT    /api/v1/employees/:id          # Actualizar empleado
GET    /api/v1/employees/:id/schedule # Horario del empleado
GET    /api/v1/employees/:id/hours    # Horas trabajadas por período
```

#### Ventas
```
GET    /api/v1/sales                  # Listar ventas
POST   /api/v1/sales                  # Registrar venta
GET    /api/v1/sales/:id              # Detalle venta
GET    /api/v1/sales/summary          # Resumen por período
```

#### Gastos
```
GET    /api/v1/expenses               # Listar gastos
POST   /api/v1/expenses               # Registrar gasto
GET    /api/v1/expenses/:id           # Detalle gasto
PUT    /api/v1/expenses/:id           # Actualizar gasto
DELETE /api/v1/expenses/:id           # Eliminar gasto
```

#### Reportes
```
GET    /api/v1/reports/sales          # Reporte de ventas
GET    /api/v1/reports/expenses       # Reporte de gastos
GET    /api/v1/reports/balance        # Balance financiero
GET    /api/v1/reports/payroll        # Reporte de sueldos
POST   /api/v1/reports/export         # Exportar reporte (PDF/Excel)
```

## Modelo de Datos

### Diagrama ER Simplificado

```mermaid
erDiagram
    USER ||--o| EMPLOYEE : "puede ser"
    EMPLOYEE ||--o{ SHIFT : "tiene asignados"
    SCHEDULE ||--|{ SHIFT : "contiene"
    EMPLOYEE ||--o{ SALE : "registra"
    SALE ||--o{ SALE_ITEM : "contiene"
    EXPENSE }o--|| EXPENSE_CATEGORY : "pertenece a"
    EMPLOYEE ||--o{ PAYROLL : "recibe"
    SUPPLY ||--o{ SUPPLY_PRICE : "tiene histórico"
    
    USER {
        int id PK
        string email UK
        string password_hash
        string role
        boolean is_active
        datetime created_at
    }
    
    EMPLOYEE {
        int id PK
        int user_id FK
        string full_name
        decimal hourly_rate
        date hire_date
    }
    
    SCHEDULE {
        int id PK
        date start_date
        date end_date
        string status
        int created_by FK
        datetime created_at
    }
    
    SHIFT {
        int id PK
        int schedule_id FK
        int employee_id FK
        date shift_date
        time start_time
        time end_time
        decimal hours
    }
    
    SALE {
        int id PK
        decimal amount
        string payment_method
        int employee_id FK
        datetime created_at
    }
    
    SALE_ITEM {
        int id PK
        int sale_id FK
        string description
        int quantity
        decimal unit_price
        decimal subtotal
    }
    
    EXPENSE {
        int id PK
        decimal amount
        date expense_date
        int category_id FK
        string description
        string supplier
        int created_by FK
    }
    
    EXPENSE_CATEGORY {
        int id PK
        string name
        string description
    }
    
    PAYROLL {
        int id PK
        int employee_id FK
        int month
        int year
        decimal hours_worked
        decimal hourly_rate
        decimal gross_salary
        datetime generated_at
    }
    
    SUPPLY {
        int id PK
        string name
        string unit
    }
    
    SUPPLY_PRICE {
        int id PK
        int supply_id FK
        decimal price
        date recorded_at
        string supplier
    }
```

## Seguridad

### Autenticación y Autorización
- **Session-based authentication** con Flask-Login
- Contraseñas hasheadas con bcrypt (cost factor 12)
- CSRF protection habilitado
- Decoradores para protección de rutas: `@login_required`, `@admin_required`

### Validación
- Validación de inputs en backend con Flask-WTF o Marshmallow
- Sanitización de datos antes de queries
- Validación de tipos y rangos

### Base de Datos
- SQLAlchemy ORM previene SQL injection
- Prepared statements por defecto
- Índices en columnas frecuentemente consultadas

### Headers de Seguridad
```python
# Flask-Talisman para headers de seguridad
- Content-Security-Policy
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Strict-Transport-Security (HTTPS)
```

## Deployment

### Opción 1: Render.com (Recomendado - Más Simple)

**Ventajas**:
- Free tier generoso
- Deploy automático desde Git
- PostgreSQL incluido
- SSL automático
- Zero configuration

**Pasos**:
1. Conectar repositorio GitHub
2. Configurar como "Web Service"
3. Build command: `pip install -r requirements.txt && cd frontend && npm install && npm run build`
4. Start command: `gunicorn run:app`
5. Agregar PostgreSQL database
6. Configurar variables de entorno

**Costo**: $0 (free tier) o $7/mes (starter)

### Opción 2: Railway.app

**Ventajas**:
- Muy fácil de usar
- Deploy desde GitHub
- PostgreSQL incluido
- Buen free tier

**Costo**: $5/mes de crédito gratis, luego pay-as-you-go

### Opción 3: DigitalOcean App Platform

**Ventajas**:
- Infraestructura robusta
- Escalable
- Buen soporte

**Costo**: Desde $5/mes

### Opción 4: Docker + VPS (Más control)

**Para producción con Docker**:

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Frontend build
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm ci

COPY frontend ./frontend
RUN cd frontend && npm run build

# Copy backend
COPY backend ./backend

# Serve frontend desde Flask
ENV FLASK_APP=backend/run.py
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "backend.run:app"]
```

```yaml
# docker-compose.yml (para desarrollo)
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: galia_db
      POSTGRES_USER: galia_user
      POSTGRES_PASSWORD: dev_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: .
    ports:
      - "5000:5000"
    environment:
      DATABASE_URL: postgresql://galia_user:dev_password@db:5432/galia_db
      FLASK_ENV: development
    depends_on:
      - db
    volumes:
      - ./backend:/app/backend
      - ./frontend:/app/frontend

volumes:
  postgres_data:
```

## Variables de Entorno

```bash
# .env.example

# Flask
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=your-secret-key-here-change-in-production

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/galia_db

# Session
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# CORS (si frontend está en dominio diferente)
CORS_ORIGINS=https://yourdomain.com

# Backup
BACKUP_ENABLED=True
BACKUP_SCHEDULE=0 2 * * *  # Daily at 2 AM
```

## Performance y Escalabilidad

### Caching
- **Flask-Caching** para cachear reportes pesados
- Cache de queries frecuentes (lista de empleados, categorías)
- TTL configurable por tipo de dato

### Optimizaciones de Base de Datos
```sql
-- Índices recomendados
CREATE INDEX idx_shifts_employee_date ON shifts(employee_id, shift_date);
CREATE INDEX idx_sales_date ON sales(created_at);
CREATE INDEX idx_expenses_date ON expenses(expense_date);
CREATE INDEX idx_sales_employee ON sales(employee_id);
```

### Paginación
- Todas las listas con paginación (20-50 items por página)
- Cursor-based pagination para mejor performance

### Límites Esperados (Monolito Simple)
- **Usuarios concurrentes**: 50-100
- **Ventas por día**: 500-1000
- **Empleados**: hasta 50
- **Reportes**: generación en < 3 segundos

## Backups

### Estrategia
1. **Automáticos diarios** (PostgreSQL pg_dump)
2. **Retención**: 30 días
3. **Storage**: S3 compatible (DigitalOcean Spaces, AWS S3)
4. **Restauración**: Script automatizado

### Script de Backup
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backup_$DATE.sql"

pg_dump $DATABASE_URL > $BACKUP_FILE
gzip $BACKUP_FILE

# Upload to S3
aws s3 cp $BACKUP_FILE.gz s3://your-bucket/backups/

# Keep only last 30 days
find . -name "backup_*.sql.gz" -mtime +30 -delete
```

## Monitoreo

### Logs
- **Flask logging** configurado
- Logs estructurados (JSON)
- Niveles: ERROR, WARNING, INFO

### Métricas Básicas
- Uptime monitoring (UptimeRobot - gratis)
- Error tracking (Sentry - free tier)
- Performance: tiempos de respuesta de endpoints críticos

## Testing

### Backend
```python
# pytest + pytest-flask
- Unit tests para services
- Integration tests para endpoints
- Fixtures para datos de prueba
```

### Frontend
```javascript
// Vitest + React Testing Library
- Component tests
- Integration tests para flujos críticos
```

### Coverage Target
- Backend: > 70%
- Frontend: > 60%

## Migración y Mantenimiento

### Migraciones de Base de Datos
```bash
# Alembic
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Versionado
- Semantic versioning (v1.0.0)
- Tags en Git para releases
- CHANGELOG.md actualizado

## Roadmap de Implementación

### Fase 1: MVP (4-6 semanas)
1. Setup proyecto y estructura
2. Autenticación y usuarios
3. Gestión de grilla horaria (P1)
4. Consulta de horario empleados (P1)
5. Registro de ventas (P1)
6. Deploy inicial

### Fase 2: Core Features (3-4 semanas)
7. Liquidación de sueldos (P2)
8. Gestión de gastos (P2)
9. Reportes básicos de ventas (P2)

### Fase 3: Analytics (2-3 semanas)
10. Balance financiero (P3)
11. Seguimiento de precios de insumos (P3)
12. Reportes avanzados y exportación

## Consideraciones Futuras

### Cuando escalar (si es necesario)
- **Microservicios**: Si algún módulo necesita escalar independientemente
- **Cache distribuido**: Redis para múltiples instancias
- **CDN**: Para assets estáticos
- **Load balancer**: Para múltiples instancias del backend

### Pero por ahora...
**El monolito es suficiente y recomendado** para:
- Negocio de tamaño pequeño-mediano
- < 100 usuarios concurrentes
- Simplicidad de mantenimiento
- Costos bajos de operación
