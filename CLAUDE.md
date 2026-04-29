# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Galia is a web-based café management system built with a Flask/Python backend and React frontend. It handles scheduling, payroll, sales tracking, expense management, financial reporting, and integrations with Fudo POS.

## Architecture

### Monolithic Structure
- **Backend**: Flask API (Python 3.11) with SQLAlchemy ORM, runs on port 5001
- **Frontend**: React 18 with Vite, runs on port 5173
- **Database**: PostgreSQL 15 with Alembic migrations
- **API**: RESTful endpoints under `/api/v1/`

### Backend Structure (`backend/app/`)
- **models/**: SQLAlchemy ORM models (27 models covering entities like Employee, Schedule, Payroll, Expense, Sale, etc.)
- **routes/**: API blueprints organized by feature (auth, schedules, sales, expenses, reports, payroll, employees, etc.)
- **services/**: Business logic layer (separate from routes, e.g., payroll calculations, report generation)
- **utils/**: Helper functions and utilities
- **ml/**: Machine learning prediction models
- **tasks/**: Background tasks (not currently in routes)
- **extensions.py**: Flask extension initialization (db, login_manager, bcrypt, migrate)
- **config.py**: Environment-based configuration (development, production, testing)

### Frontend Structure (`frontend/src/`)
- **pages/**: Full-page components (Dashboard, Payroll, Schedules, Employees, Reports, etc.)
- **components/**: Reusable UI components organized by feature (common, expenses, schedules, timeTracking, layout, notifications, etc.)
- **services/**: API client functions using axios
- **context/**: React Context for shared state
- **utils/**: Helper functions and formatting utilities

### Database
- PostgreSQL 15 as primary datastore
- Migrations use Flask-Migrate/Alembic located in `backend/migrations/`
- Multiple initialization scripts in backend root for setup and data migration

## Key Commands

### Backend

**Setup and run locally:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
export FLASK_ENV=development  # or set in .env
python run.py  # Starts on port 5001
```

**Database migrations:**
```bash
cd backend
flask db init           # Initialize migration directory (first time only)
flask db migrate -m "description"  # Create new migration
flask db upgrade        # Apply migrations
flask db downgrade      # Revert last migration
```

**Tests:**
```bash
cd backend
pytest                  # Run all tests
pytest tests/test_payroll_deletion.py  # Run specific test file
pytest tests/ -v        # Verbose output
```

**Build for production:**
```bash
bash build.sh  # Runs pip install, migrations, and initialization scripts
```

### Frontend

**Setup and run locally:**
```bash
cd frontend
npm install
npm run dev  # Starts on port 5173, proxies /api to localhost:5001
```

**Lint and build:**
```bash
cd frontend
npm run lint   # ESLint check
npm run build  # Production build to dist/
npm run preview  # Preview production build
```

## Important Modules and Features

### Core Features
- **Authentication** (`auth.py` route): Flask-Login with bcrypt, session-based
- **Schedules** (`schedules.py` route): Work schedule grids with shift management
- **Payroll** (`payroll.py` route): Automated salary calculations based on hours, multipliers, and extraordinary amounts
- **Sales** (`sales.py` route): Transaction recording and tracking
- **Expenses** (`expenses.py` route): Expense tracking with category management
- **Reports** (`reports.py` route): Sales, expense, payroll, and financial balance reports
- **Employees** (`employees.py` route): Employee management and job position tracking

### Advanced Features
- **Fudo Integration** (`fudo_sync.py`): Syncs sales and expenses from Fudo POS with automatic API token renewal
- **Time Tracking** (`time_tracking.py` route): Employee hour tracking
- **Payroll Claims** (`payroll_claim.py` model): Dispute tracking for payroll items
- **Social Security Documents** (`social_security_documents.py` route): Document uploads and management
- **Vacation Periods** (`vacation_periods.py` route): Vacation request and management
- **ML Predictions** (`ml_predictions.py` route): ML-based sales and staffing predictions
- **Notifications** (`notifications.py` route): System notification alerts

### Configuration
- **Environment variables**: Stored in `.env` file (copy from `.env.example`)
- **Database URL**: `DATABASE_URL` environment variable (defaults to local PostgreSQL)
- **CORS origins**: `CORS_ORIGINS` comma-separated list of allowed origins
- **Secret key**: `SECRET_KEY` for session management

## Testing

Tests use pytest framework in `backend/tests/`:
- **test_permissions.py**: Role-based access control
- **test_schedule_management.py**: Schedule CRUD operations
- **test_payroll_deletion.py**: Payroll deletion and cascading effects
- **test_sales_date_filter.py**: Sales filtering and aggregation
- **test_social_security_documents.py**: Document upload workflows
- **test_timezone_fix.py**: Timezone handling
- **test_format_utils.py**: Number and currency formatting
- **test_employee_documents.py**: Employee document management

Run tests with `pytest` in the backend directory.

## Development Workflow

1. **Backend changes**: Modify models, routes, or services in `backend/app/`
2. **Database schema changes**: Create migration with `flask db migrate`, review SQL, run `flask db upgrade`
3. **Frontend changes**: Modify components, pages, or services in `frontend/src/`
4. **Testing**: Run `pytest` in backend before committing
5. **Building**: Frontend has development server with hot reload; backend requires manual restart

## Common Development Tasks

### Adding a new API endpoint
1. Create/update model in `backend/app/models/`
2. Create/update route in `backend/app/routes/` as a Flask blueprint
3. Register blueprint in `backend/app/__init__.py`
4. Create frontend service in `frontend/src/services/` for API calls
5. Create/update React pages or components to consume the service

### Adding a database field
1. Update SQLAlchemy model in `backend/app/models/`
2. Create migration: `flask db migrate -m "Add field_name to table_name"`
3. Review generated migration SQL
4. Apply migration: `flask db upgrade`
5. Test with pytest

### Running a single backend test
```bash
pytest tests/test_payroll_deletion.py::test_function_name -v
```

## Ports and URLs

- **Frontend dev**: http://localhost:5173
- **Backend API**: http://localhost:5001
- **API base path**: http://localhost:5001/api/v1
- **Vite proxy**: Requests to `/api/*` on port 5173 are proxied to port 5001

## Docker (Optional)

A Docker setup is available:
```bash
docker-compose up -d  # Starts both backend and frontend
```

See `docker-compose.yml` for service definitions. Frontend Dockerfile uses multi-stage build; backend uses Python 3.11 with gunicorn.

## Key Notes

- **CORS**: Configured in `backend/app/config.py` and controlled by `CORS_ORIGINS` env var
- **Session management**: 7-day default session lifetime, cookie-based authentication
- **Database URL format**: Must use `postgresql://` scheme (code auto-converts legacy `postgres://`)
- **API versioning**: All endpoints use `/api/v1/` prefix
- **Timezone handling**: App handles timezone conversions (see test_timezone_fix.py)
- **Fudo integration**: Requires `FUDO_API_KEY` and `FUDO_API_SECRET` environment variables
