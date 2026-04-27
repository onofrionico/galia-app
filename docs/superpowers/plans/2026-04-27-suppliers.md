# Suppliers (Proveedores) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar un módulo de Proveedores que permita crear un directorio de proveedores, vincularlos a gastos existentes y futuros, y consultar el historial analítico de compras por proveedor.

**Architecture:** Nueva tabla `suppliers` con FK opcional `supplier_id` en `expenses`. El campo `proveedor` (string) se mantiene para compatibilidad con datos históricos y sincronización Fudo. El backend expone endpoints CRUD + historial; el frontend agrega una sección "Compras" en el sidebar con lista y detalle de proveedores.

**Tech Stack:** Flask/SQLAlchemy (backend), Alembic (migrations), pytest (tests), React 18 + Vite (frontend), axios via `api.js` (HTTP client).

---

## File Structure

### New files
- `backend/app/models/supplier.py` — modelo Supplier
- `backend/app/routes/suppliers.py` — blueprint CRUD + historial + link-expenses
- `backend/tests/test_suppliers.py` — tests de API y modelo
- `frontend/src/services/suppliersService.js` — cliente API
- `frontend/src/pages/Suppliers.jsx` — lista de proveedores
- `frontend/src/pages/SupplierDetail.jsx` — detalle con tabs (contacto + historial)

### Modified files
- `backend/app/models/expense.py` — agregar `supplier_id` FK + actualizar `to_dict()`
- `backend/app/models/__init__.py` — importar `Supplier`
- `backend/app/__init__.py` — registrar blueprint `suppliers`
- `backend/app/routes/expenses.py` — aceptar `supplier_id` en create/update
- `backend/app/routes/fudo_sync.py` — auto-vincular proveedor al sincronizar
- `frontend/src/App.jsx` — agregar rutas `/suppliers` y `/suppliers/:id`
- `frontend/src/components/layout/Sidebar.jsx` — agregar grupo "Compras"

---

## Task 1: Supplier model

**Files:**
- Create: `backend/app/models/supplier.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Crear el modelo**

Crear `backend/app/models/supplier.py` con este contenido:

```python
from datetime import datetime
from app.extensions import db


class Supplier(db.Model):
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    cuit = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    address = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    expenses = db.relationship('Expense', backref='supplier', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'cuit': self.cuit,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'notes': self.notes,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
```

- [ ] **Step 2: Registrar en `__init__.py`**

En `backend/app/models/__init__.py`, agregar al inicio:

```python
from app.models.supplier import Supplier
```

Y agregar `'Supplier'` al final de `__all__`.

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/supplier.py backend/app/models/__init__.py
git commit -m "feat: add Supplier model"
```

---

## Task 2: Migración — tabla suppliers + supplier_id en expenses

**Files:**
- Modify: `backend/app/models/expense.py`
- Generate: `backend/migrations/versions/XXXX_add_suppliers.py` (vía Alembic)

- [ ] **Step 1: Agregar supplier_id al modelo Expense**

En `backend/app/models/expense.py`, agregar después de `category_id`:

```python
supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
```

En el método `to_dict()`, agregar al dict retornado:

```python
'supplier_id': self.supplier_id,
'supplier_name': self.supplier.name if self.supplier else None,
```

- [ ] **Step 2: Crear la migración**

```bash
cd backend
flask db migrate -m "add suppliers table and supplier_id to expenses"
```

Revisar el archivo generado en `backend/migrations/versions/`. Debe contener:
- `op.create_table('suppliers', ...)` con todas las columnas del modelo
- `op.add_column('expenses', sa.Column('supplier_id', sa.Integer(), sa.ForeignKey('suppliers.id'), nullable=True))`

- [ ] **Step 3: Aplicar la migración**

```bash
flask db upgrade
```

Expected: `Running upgrade ... -> XXXX, add suppliers table and supplier_id to expenses`

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/expense.py backend/migrations/
git commit -m "feat: add supplier_id FK to expenses and create suppliers table migration"
```

---

## Task 3: Suppliers blueprint — CRUD

**Files:**
- Create: `backend/app/routes/suppliers.py`
- Modify: `backend/app/__init__.py`
- Create: `backend/tests/test_suppliers.py`

- [ ] **Step 1: Escribir los tests (primero)**

Crear `backend/tests/test_suppliers.py`:

```python
import pytest
import json
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.supplier import Supplier


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_user(app):
    with app.app_context():
        user = User(email='admin@test.com', role='admin', is_active=True)
        user.set_password('admin123')
        db.session.add(user)
        db.session.commit()
        return user


def get_token(client, email='admin@test.com', password='admin123'):
    response = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    return json.loads(response.data).get('access_token')


class TestSuppliersCRUD:
    def test_list_empty(self, client, admin_user):
        token = get_token(client)
        r = client.get('/api/v1/suppliers', headers={'Authorization': f'Bearer {token}'})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['suppliers'] == []
        assert data['total'] == 0

    def test_create_supplier(self, client, admin_user):
        token = get_token(client)
        payload = {'name': 'Distribuidora García', 'cuit': '20-12345678-9', 'email': 'garcia@test.com'}
        r = client.post('/api/v1/suppliers', json=payload, headers={'Authorization': f'Bearer {token}'})
        assert r.status_code == 201
        data = json.loads(r.data)
        assert data['name'] == 'Distribuidora García'
        assert data['cuit'] == '20-12345678-9'
        assert data['is_active'] is True

    def test_create_supplier_missing_name(self, client, admin_user):
        token = get_token(client)
        r = client.post('/api/v1/suppliers', json={'cuit': '20-111-1'}, headers={'Authorization': f'Bearer {token}'})
        assert r.status_code == 400

    def test_get_supplier(self, client, admin_user, app):
        with app.app_context():
            s = Supplier(name='Proveedor Test')
            db.session.add(s)
            db.session.commit()
            supplier_id = s.id
        token = get_token(client)
        r = client.get(f'/api/v1/suppliers/{supplier_id}', headers={'Authorization': f'Bearer {token}'})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['name'] == 'Proveedor Test'

    def test_update_supplier(self, client, admin_user, app):
        with app.app_context():
            s = Supplier(name='Viejo Nombre')
            db.session.add(s)
            db.session.commit()
            supplier_id = s.id
        token = get_token(client)
        r = client.put(f'/api/v1/suppliers/{supplier_id}', json={'name': 'Nuevo Nombre'}, headers={'Authorization': f'Bearer {token}'})
        assert r.status_code == 200
        assert json.loads(r.data)['name'] == 'Nuevo Nombre'

    def test_deactivate_supplier(self, client, admin_user, app):
        with app.app_context():
            s = Supplier(name='Para Desactivar')
            db.session.add(s)
            db.session.commit()
            supplier_id = s.id
        token = get_token(client)
        r = client.delete(f'/api/v1/suppliers/{supplier_id}', headers={'Authorization': f'Bearer {token}'})
        assert r.status_code == 200
        with app.app_context():
            assert Supplier.query.get(supplier_id).is_active is False

    def test_list_excludes_inactive_by_default(self, client, admin_user, app):
        with app.app_context():
            db.session.add(Supplier(name='Activo', is_active=True))
            db.session.add(Supplier(name='Inactivo', is_active=False))
            db.session.commit()
        token = get_token(client)
        r = client.get('/api/v1/suppliers', headers={'Authorization': f'Bearer {token}'})
        data = json.loads(r.data)
        assert data['total'] == 1
        assert data['suppliers'][0]['name'] == 'Activo'
```

- [ ] **Step 2: Verificar que los tests fallan (blueprint no existe aún)**

```bash
cd backend
pytest tests/test_suppliers.py -v
```

Expected: errores de `404` o `AssertionError` (rutas no registradas).

- [ ] **Step 3: Crear el blueprint CRUD**

Crear `backend/app/routes/suppliers.py`:

```python
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.supplier import Supplier
from app.models.expense import Expense
from app.utils.jwt_utils import token_required
from app.utils.decorators import admin_required
from sqlalchemy import func
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

bp = Blueprint('suppliers', __name__, url_prefix='/api/v1/suppliers')


@bp.route('', methods=['GET'])
@token_required
@admin_required
def list_suppliers(current_user):
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    search = request.args.get('search', '').strip()

    query = Supplier.query
    if not include_inactive:
        query = query.filter(Supplier.is_active == True)
    if search:
        query = query.filter(Supplier.name.ilike(f'%{search}%'))

    suppliers = query.order_by(Supplier.name).all()

    result = []
    for s in suppliers:
        d = s.to_dict()
        total_30d = db.session.query(func.sum(Expense.importe)).filter(
            Expense.supplier_id == s.id,
            Expense.cancelado == False,
            Expense.fecha >= date.today().replace(day=1)
        ).scalar() or 0
        last_expense = db.session.query(func.max(Expense.fecha)).filter(
            Expense.supplier_id == s.id
        ).scalar()
        d['total_mes_actual'] = float(total_30d)
        d['ultima_compra'] = last_expense.isoformat() if last_expense else None
        result.append(d)

    return jsonify({'suppliers': result, 'total': len(result)}), 200


@bp.route('', methods=['POST'])
@token_required
@admin_required
def create_supplier(current_user):
    data = request.get_json() or {}
    if not data.get('name', '').strip():
        return jsonify({'error': 'El nombre del proveedor es requerido'}), 400

    supplier = Supplier(
        name=data['name'].strip(),
        cuit=data.get('cuit', '').strip() or None,
        email=data.get('email', '').strip() or None,
        phone=data.get('phone', '').strip() or None,
        address=data.get('address', '').strip() or None,
        notes=data.get('notes', '').strip() or None,
    )
    db.session.add(supplier)
    db.session.commit()
    return jsonify(supplier.to_dict()), 201


@bp.route('/<int:supplier_id>', methods=['GET'])
@token_required
@admin_required
def get_supplier(current_user, supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    return jsonify(supplier.to_dict()), 200


@bp.route('/<int:supplier_id>', methods=['PUT'])
@token_required
@admin_required
def update_supplier(current_user, supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    data = request.get_json() or {}

    if 'name' in data:
        if not data['name'].strip():
            return jsonify({'error': 'El nombre no puede estar vacío'}), 400
        supplier.name = data['name'].strip()
    for field in ('cuit', 'email', 'phone', 'address', 'notes'):
        if field in data:
            setattr(supplier, field, data[field].strip() or None)
    if 'is_active' in data:
        supplier.is_active = bool(data['is_active'])

    supplier.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(supplier.to_dict()), 200


@bp.route('/<int:supplier_id>', methods=['DELETE'])
@token_required
@admin_required
def deactivate_supplier(current_user, supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    supplier.is_active = False
    supplier.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'Proveedor desactivado correctamente'}), 200
```

- [ ] **Step 4: Registrar blueprint en `backend/app/__init__.py`**

En la línea que importa todos los blueprints (línea 46), agregar `suppliers` al import:

```python
from app.routes import auth, schedules, sales, expenses, reports, employees, shifts, schedule_summary, notifications, coverage, ml_predictions, ml_dashboard, employee_schedule, job_positions, time_tracking, payroll, csv_import, holidays, store_hours, vacation_periods, absence_requests, social_security, employee_documents, fudo_sync, suppliers
```

Después del último `app.register_blueprint(fudo_sync.bp)`, agregar:

```python
app.register_blueprint(suppliers.bp)
```

- [ ] **Step 5: Correr tests CRUD**

```bash
cd backend
pytest tests/test_suppliers.py::TestSuppliersCRUD -v
```

Expected: todos los tests pasan (7 tests, todos PASSED).

- [ ] **Step 6: Commit**

```bash
git add backend/app/routes/suppliers.py backend/app/__init__.py backend/tests/test_suppliers.py
git commit -m "feat: add suppliers CRUD endpoints"
```

---

## Task 4: Suppliers — historial de gastos + link-expenses

**Files:**
- Modify: `backend/app/routes/suppliers.py`
- Modify: `backend/tests/test_suppliers.py`

- [ ] **Step 1: Agregar tests de historial y link-expenses**

Agregar a `backend/tests/test_suppliers.py` al final:

```python
class TestSupplierExpenses:
    def test_get_expenses_empty(self, client, admin_user, app):
        with app.app_context():
            s = Supplier(name='Sin Gastos')
            db.session.add(s)
            db.session.commit()
            supplier_id = s.id
        token = get_token(client)
        r = client.get(f'/api/v1/suppliers/{supplier_id}/expenses', headers={'Authorization': f'Bearer {token}'})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['expenses'] == []
        assert data['total'] == 0

    def test_link_expenses_by_name(self, client, admin_user, app):
        from app.models.expense import Expense
        from datetime import date
        with app.app_context():
            s = Supplier(name='Distribuidora García')
            db.session.add(s)
            from app.models.expense import ExpenseCategory
            cat = ExpenseCategory(name='Test Cat', expense_type='indirecto')
            db.session.add(cat)
            db.session.flush()
            e1 = Expense(fecha=date.today(), proveedor='Distribuidora García', importe=1000, category_id=cat.id)
            e2 = Expense(fecha=date.today(), proveedor='Otro Proveedor', importe=500, category_id=cat.id)
            db.session.add_all([e1, e2])
            db.session.commit()
            supplier_id = s.id

        token = get_token(client)
        r = client.post(f'/api/v1/suppliers/{supplier_id}/link-expenses', headers={'Authorization': f'Bearer {token}'})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['linked'] == 1

        with app.app_context():
            linked = Expense.query.filter_by(supplier_id=supplier_id).count()
            assert linked == 1

    def test_supplier_analytics(self, client, admin_user, app):
        from app.models.expense import Expense, ExpenseCategory
        from datetime import date
        with app.app_context():
            s = Supplier(name='Proveedor Analytics')
            db.session.add(s)
            cat = ExpenseCategory(name='Insumos', expense_type='directo')
            db.session.add(cat)
            db.session.flush()
            for i in range(3):
                e = Expense(fecha=date.today(), proveedor='Proveedor Analytics',
                            supplier_id=s.id, importe=1000, category_id=cat.id)
                db.session.add(e)
            db.session.commit()
            supplier_id = s.id

        token = get_token(client)
        r = client.get(f'/api/v1/suppliers/{supplier_id}/analytics', headers={'Authorization': f'Bearer {token}'})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['total_periodo'] == 3000.0
        assert len(data['por_categoria']) == 1
```

- [ ] **Step 2: Verificar que fallan**

```bash
cd backend
pytest tests/test_suppliers.py::TestSupplierExpenses -v
```

Expected: FAILED (rutas no existen aún).

- [ ] **Step 3: Agregar endpoints al blueprint**

Agregar al final de `backend/app/routes/suppliers.py`:

```python
@bp.route('/<int:supplier_id>/expenses', methods=['GET'])
@token_required
@admin_required
def get_supplier_expenses(current_user, supplier_id):
    Supplier.query.get_or_404(supplier_id)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')

    query = Expense.query.filter(Expense.supplier_id == supplier_id, Expense.cancelado == False)

    if fecha_desde:
        try:
            query = query.filter(Expense.fecha >= datetime.strptime(fecha_desde, '%Y-%m-%d').date())
        except ValueError:
            return jsonify({'error': 'Formato de fecha_desde inválido. Use YYYY-MM-DD'}), 400
    if fecha_hasta:
        try:
            query = query.filter(Expense.fecha <= datetime.strptime(fecha_hasta, '%Y-%m-%d').date())
        except ValueError:
            return jsonify({'error': 'Formato de fecha_hasta inválido. Use YYYY-MM-DD'}), 400

    total = query.count()
    expenses = query.order_by(Expense.fecha.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'expenses': [e.to_dict() for e in expenses.items],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': expenses.pages
    }), 200


@bp.route('/<int:supplier_id>/link-expenses', methods=['POST'])
@token_required
@admin_required
def link_expenses(current_user, supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)

    unlinked = Expense.query.filter(
        Expense.supplier_id == None,
        func.lower(Expense.proveedor) == func.lower(supplier.name)
    ).all()

    for expense in unlinked:
        expense.supplier_id = supplier_id

    db.session.commit()
    return jsonify({'linked': len(unlinked), 'supplier_id': supplier_id}), 200


@bp.route('/<int:supplier_id>/analytics', methods=['GET'])
@token_required
@admin_required
def get_supplier_analytics(current_user, supplier_id):
    from app.models.expense import ExpenseCategory
    Supplier.query.get_or_404(supplier_id)

    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')

    query = Expense.query.filter(Expense.supplier_id == supplier_id, Expense.cancelado == False)

    if fecha_desde:
        try:
            query = query.filter(Expense.fecha >= datetime.strptime(fecha_desde, '%Y-%m-%d').date())
        except ValueError:
            pass
    if fecha_hasta:
        try:
            query = query.filter(Expense.fecha <= datetime.strptime(fecha_hasta, '%Y-%m-%d').date())
        except ValueError:
            pass

    total_periodo = float(
        db.session.query(func.sum(Expense.importe))
        .filter(Expense.supplier_id == supplier_id, Expense.cancelado == False)
        .scalar() or 0
    )

    twelve_months_ago = date.today() - relativedelta(months=12)
    monthly_totals = db.session.query(
        func.date_trunc('month', Expense.fecha).label('month'),
        func.sum(Expense.importe).label('total')
    ).filter(
        Expense.supplier_id == supplier_id,
        Expense.cancelado == False,
        Expense.fecha >= twelve_months_ago
    ).group_by('month').all()

    promedio_mensual = (
        sum(float(r.total) for r in monthly_totals) / len(monthly_totals)
        if monthly_totals else 0
    )

    por_categoria = db.session.query(
        ExpenseCategory.name,
        func.sum(Expense.importe).label('total')
    ).join(Expense, Expense.category_id == ExpenseCategory.id).filter(
        Expense.supplier_id == supplier_id,
        Expense.cancelado == False
    ).group_by(ExpenseCategory.name).all()

    last_expense = db.session.query(func.max(Expense.fecha)).filter(
        Expense.supplier_id == supplier_id
    ).scalar()

    return jsonify({
        'total_periodo': total_periodo,
        'promedio_mensual': round(promedio_mensual, 2),
        'por_categoria': [{'categoria': name, 'total': float(total)} for name, total in por_categoria],
        'ultima_compra': last_expense.isoformat() if last_expense else None,
    }), 200
```

- [ ] **Step 4: Instalar python-dateutil si no está**

```bash
cd backend
pip show python-dateutil
```

Si no está instalado: `pip install python-dateutil` y agregar a `requirements.txt`.

- [ ] **Step 5: Correr todos los tests de suppliers**

```bash
cd backend
pytest tests/test_suppliers.py -v
```

Expected: todos los tests pasan (10+ tests, todos PASSED).

- [ ] **Step 6: Commit**

```bash
git add backend/app/routes/suppliers.py backend/tests/test_suppliers.py backend/requirements.txt
git commit -m "feat: add supplier expense history, link-expenses and analytics endpoints"
```

---

## Task 5: Expenses route — aceptar supplier_id en create/update

**Files:**
- Modify: `backend/app/routes/expenses.py`
- Modify: `backend/tests/test_suppliers.py`

- [ ] **Step 1: Agregar test**

Agregar a `backend/tests/test_suppliers.py`:

```python
class TestExpenseWithSupplier:
    def test_create_expense_with_supplier_id(self, client, admin_user, app):
        from app.models.expense import ExpenseCategory
        with app.app_context():
            s = Supplier(name='Proveedor Gasto')
            db.session.add(s)
            cat = ExpenseCategory(name='Insumos Test', expense_type='directo')
            db.session.add(cat)
            db.session.commit()
            supplier_id = s.id
            cat_id = cat.id

        token = get_token(client)
        payload = {
            'fecha': '2026-04-01',
            'importe': 5000,
            'category_id': cat_id,
            'supplier_id': supplier_id,
        }
        r = client.post('/api/v1/expenses', json=payload, headers={'Authorization': f'Bearer {token}'})
        assert r.status_code == 201
        data = json.loads(r.data)
        assert data['supplier_id'] == supplier_id
        assert data['supplier_name'] == 'Proveedor Gasto'
```

- [ ] **Step 2: Verificar que el test falla**

```bash
cd backend
pytest tests/test_suppliers.py::TestExpenseWithSupplier -v
```

Expected: FAILED (`supplier_id` no está siendo guardado ni devuelto).

- [ ] **Step 3: Modificar `create_expense` en expenses.py**

En `backend/app/routes/expenses.py`, en la función `create_expense`, después de validar `category_id`, agregar:

```python
supplier_id = data.get('supplier_id')
if supplier_id:
    from app.models.supplier import Supplier
    supplier = Supplier.query.get(supplier_id)
    if not supplier or not supplier.is_active:
        return jsonify({'error': 'Proveedor inválido o inactivo'}), 400
```

En la construcción del objeto `Expense(...)`, agregar el campo:

```python
supplier_id=supplier_id,
```

- [ ] **Step 4: Modificar `update_expense` en expenses.py**

En la función `update_expense`, después de los bloques de `category_id`, agregar:

```python
if 'supplier_id' in data:
    if data['supplier_id'] is not None:
        from app.models.supplier import Supplier
        supplier = Supplier.query.get(data['supplier_id'])
        if not supplier or not supplier.is_active:
            return jsonify({'error': 'Proveedor inválido o inactivo'}), 400
    expense.supplier_id = data['supplier_id']
```

- [ ] **Step 5: Correr test**

```bash
cd backend
pytest tests/test_suppliers.py::TestExpenseWithSupplier -v
```

Expected: PASSED.

- [ ] **Step 6: Commit**

```bash
git add backend/app/routes/expenses.py backend/tests/test_suppliers.py
git commit -m "feat: expenses route accepts supplier_id on create and update"
```

---

## Task 6: Fudo sync — auto-vincular proveedor por nombre

**Files:**
- Modify: `backend/app/routes/fudo_sync.py`
- Modify: `backend/tests/test_suppliers.py`

- [ ] **Step 1: Agregar test**

Agregar a `backend/tests/test_suppliers.py`:

```python
class TestFudoAutoLink:
    def test_expense_auto_links_to_supplier_by_name(self, app):
        from app.routes.fudo_sync import _try_link_supplier
        from app.models.expense import Expense, ExpenseCategory
        from datetime import date
        with app.app_context():
            s = Supplier(name='Distribuidora López')
            db.session.add(s)
            cat = ExpenseCategory(name='Varios', expense_type='indirecto')
            db.session.add(cat)
            db.session.flush()
            e = Expense(fecha=date.today(), proveedor='Distribuidora López', importe=500, category_id=cat.id)
            db.session.add(e)
            db.session.commit()
            expense_id = e.id

            _try_link_supplier(e)
            db.session.commit()

            updated = Expense.query.get(expense_id)
            assert updated.supplier_id == s.id
```

- [ ] **Step 2: Verificar que falla**

```bash
cd backend
pytest tests/test_suppliers.py::TestFudoAutoLink -v
```

Expected: FAILED (`_try_link_supplier` no existe).

- [ ] **Step 3: Agregar `_try_link_supplier` a fudo_sync.py**

En `backend/app/routes/fudo_sync.py`, agregar la función helper después de los imports:

```python
def _try_link_supplier(expense):
    """Link expense to supplier if one exists with matching name (case-insensitive)."""
    if expense.supplier_id or not expense.proveedor:
        return
    from app.models.supplier import Supplier
    from sqlalchemy import func
    supplier = Supplier.query.filter(
        func.lower(Supplier.name) == func.lower(expense.proveedor),
        Supplier.is_active == True
    ).first()
    if supplier:
        expense.supplier_id = supplier.id
```

En `_sync_expenses_background`, dentro del bloque `else` (cuando se crea `new_expense`), agregar **antes** de `db.session.add(new_expense)`:

```python
_try_link_supplier(new_expense)
```

También para el caso de `update_existing`, dentro del bloque `if update_existing:`, después del loop de `setattr`, agregar:

```python
_try_link_supplier(existing_expense)
```

- [ ] **Step 4: Correr test**

```bash
cd backend
pytest tests/test_suppliers.py::TestFudoAutoLink -v
```

Expected: PASSED.

- [ ] **Step 5: Correr toda la suite**

```bash
cd backend
pytest tests/test_suppliers.py -v
```

Expected: todos los tests pasan.

- [ ] **Step 6: Commit**

```bash
git add backend/app/routes/fudo_sync.py backend/tests/test_suppliers.py
git commit -m "feat: auto-link expenses to suppliers by name during Fudo sync"
```

---

## Task 7: Frontend — suppliersService.js

**Files:**
- Create: `frontend/src/services/suppliersService.js`

- [ ] **Step 1: Crear el servicio**

Crear `frontend/src/services/suppliersService.js`:

```javascript
import api from './api'

const suppliersService = {
  async getSuppliers(params = {}) {
    const response = await api.get('/suppliers', { params })
    return response.data
  },

  async getSupplier(id) {
    const response = await api.get(`/suppliers/${id}`)
    return response.data
  },

  async createSupplier(data) {
    const response = await api.post('/suppliers', data)
    return response.data
  },

  async updateSupplier(id, data) {
    const response = await api.put(`/suppliers/${id}`, data)
    return response.data
  },

  async deactivateSupplier(id) {
    const response = await api.delete(`/suppliers/${id}`)
    return response.data
  },

  async getSupplierExpenses(id, params = {}) {
    const response = await api.get(`/suppliers/${id}/expenses`, { params })
    return response.data
  },

  async linkExpenses(id) {
    const response = await api.post(`/suppliers/${id}/link-expenses`)
    return response.data
  },

  async getSupplierAnalytics(id, params = {}) {
    const response = await api.get(`/suppliers/${id}/analytics`, { params })
    return response.data
  },
}

export default suppliersService
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/services/suppliersService.js
git commit -m "feat: add suppliersService frontend API client"
```

---

## Task 8: Frontend — Suppliers list page + routing + sidebar

**Files:**
- Create: `frontend/src/pages/Suppliers.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/components/layout/Sidebar.jsx`

- [ ] **Step 1: Crear Suppliers.jsx**

Crear `frontend/src/pages/Suppliers.jsx`:

```jsx
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Building2, Plus, Search, ChevronRight } from 'lucide-react'
import suppliersService from '@/services/suppliersService'

export default function Suppliers() {
  const navigate = useNavigate()
  const [suppliers, setSuppliers] = useState([])
  const [total, setTotal] = useState(0)
  const [search, setSearch] = useState('')
  const [includeInactive, setIncludeInactive] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', cuit: '', email: '', phone: '', address: '', notes: '' })
  const [saving, setSaving] = useState(false)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await suppliersService.getSuppliers({ search, include_inactive: includeInactive })
      setSuppliers(data.suppliers)
      setTotal(data.total)
    } catch (e) {
      setError('Error cargando proveedores')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [search, includeInactive])

  const handleCreate = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await suppliersService.createSupplier(form)
      setShowForm(false)
      setForm({ name: '', cuit: '', email: '', phone: '', address: '', notes: '' })
      load()
    } catch {
      setError('Error creando proveedor')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Building2 className="w-6 h-6 text-orange-600" />
          <h1 className="text-2xl font-bold text-gray-900">Proveedores</h1>
          <span className="text-sm text-gray-500">({total})</span>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors text-sm font-medium"
        >
          <Plus className="w-4 h-4" />
          Nuevo proveedor
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="mb-6 bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <h2 className="text-base font-semibold text-gray-800 mb-4">Nuevo proveedor</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
              <input
                required
                value={form.name}
                onChange={e => setForm({ ...form, name: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">CUIT</label>
              <input
                value={form.cuit}
                onChange={e => setForm({ ...form, cuit: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={form.email}
                onChange={e => setForm({ ...form, email: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Teléfono</label>
              <input
                value={form.phone}
                onChange={e => setForm({ ...form, phone: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Notas</label>
              <textarea
                value={form.notes}
                onChange={e => setForm({ ...form, notes: e.target.value })}
                rows={2}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
            </div>
          </div>
          <div className="flex gap-3 mt-4">
            <button type="submit" disabled={saving} className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 text-sm font-medium disabled:opacity-50">
              {saving ? 'Guardando...' : 'Guardar'}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50">
              Cancelar
            </button>
          </div>
        </form>
      )}

      <div className="flex items-center gap-4 mb-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            placeholder="Buscar proveedor..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
          <input
            type="checkbox"
            checked={includeInactive}
            onChange={e => setIncludeInactive(e.target.checked)}
            className="rounded"
          />
          Ver inactivos
        </label>
      </div>

      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

      {loading ? (
        <p className="text-sm text-gray-500">Cargando...</p>
      ) : suppliers.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <Building2 className="w-10 h-10 mx-auto mb-3 opacity-40" />
          <p className="text-sm">No hay proveedores registrados</p>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Nombre</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">CUIT</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Contacto</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">Total mes actual</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">Última compra</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {suppliers.map(s => (
                <tr
                  key={s.id}
                  onClick={() => navigate(`/suppliers/${s.id}`)}
                  className={`hover:bg-orange-50 cursor-pointer transition-colors ${!s.is_active ? 'opacity-50' : ''}`}
                >
                  <td className="px-4 py-3 font-medium text-gray-900">{s.name}</td>
                  <td className="px-4 py-3 text-gray-600">{s.cuit || '—'}</td>
                  <td className="px-4 py-3 text-gray-600">{s.email || s.phone || '—'}</td>
                  <td className="px-4 py-3 text-right font-medium text-gray-800">
                    {s.total_mes_actual > 0 ? `$${s.total_mes_actual.toLocaleString('es-AR')}` : '—'}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-600">
                    {s.ultima_compra ? new Date(s.ultima_compra + 'T00:00:00').toLocaleDateString('es-AR') : '—'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <ChevronRight className="w-4 h-4 text-gray-400 ml-auto" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Agregar rutas en App.jsx**

En `frontend/src/App.jsx`, agregar los imports al inicio:

```jsx
import Suppliers from './pages/Suppliers'
import SupplierDetail from './pages/SupplierDetail'
```

Dentro del bloque `<Route element={<ProtectedRoute>...}>`, agregar:

```jsx
<Route path="/suppliers" element={<Suppliers />} />
<Route path="/suppliers/:id" element={<SupplierDetail />} />
```

- [ ] **Step 3: Agregar "Compras" al Sidebar**

En `frontend/src/components/layout/Sidebar.jsx`, agregar el import del ícono:

```jsx
import { Building2 } from 'lucide-react'
```

Agregar un nuevo grupo después del grupo `finanzas` en el array `navGroups`:

```jsx
{
  id: 'compras',
  label: 'Compras',
  icon: Building2,
  activeClass: 'text-orange-700 bg-orange-50 border-orange-200',
  headerClass: 'text-orange-700 bg-orange-50',
  items: [
    { to: '/suppliers', icon: Building2, label: 'Proveedores' },
  ],
},
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Suppliers.jsx frontend/src/App.jsx frontend/src/components/layout/Sidebar.jsx
git commit -m "feat: add Suppliers list page, routing and sidebar entry"
```

---

## Task 9: Frontend — SupplierDetail page

**Files:**
- Create: `frontend/src/pages/SupplierDetail.jsx`

- [ ] **Step 1: Crear SupplierDetail.jsx**

Crear `frontend/src/pages/SupplierDetail.jsx`:

```jsx
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Building2, ArrowLeft, Link, Save, Trash2 } from 'lucide-react'
import suppliersService from '@/services/suppliersService'

const TABS = ['Contacto', 'Historial de compras']

export default function SupplierDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [supplier, setSupplier] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [expenses, setExpenses] = useState([])
  const [expTotal, setExpTotal] = useState(0)
  const [tab, setTab] = useState('Contacto')
  const [form, setForm] = useState({})
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [linking, setLinking] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [fechaDesde, setFechaDesde] = useState('')
  const [fechaHasta, setFechaHasta] = useState('')

  const loadSupplier = async () => {
    try {
      const data = await suppliersService.getSupplier(id)
      setSupplier(data)
      setForm(data)
    } catch {
      setError('No se encontró el proveedor')
    } finally {
      setLoading(false)
    }
  }

  const loadExpenses = async () => {
    try {
      const params = {}
      if (fechaDesde) params.fecha_desde = fechaDesde
      if (fechaHasta) params.fecha_hasta = fechaHasta
      const data = await suppliersService.getSupplierExpenses(id, params)
      setExpenses(data.expenses)
      setExpTotal(data.total)
    } catch {
      setError('Error cargando historial')
    }
  }

  const loadAnalytics = async () => {
    try {
      const params = {}
      if (fechaDesde) params.fecha_desde = fechaDesde
      if (fechaHasta) params.fecha_hasta = fechaHasta
      const data = await suppliersService.getSupplierAnalytics(id, params)
      setAnalytics(data)
    } catch {
      setError('Error cargando analítica')
    }
  }

  useEffect(() => { loadSupplier() }, [id])
  useEffect(() => {
    if (tab === 'Historial de compras') {
      loadExpenses()
      loadAnalytics()
    }
  }, [tab, fechaDesde, fechaHasta, id])

  const handleSave = async () => {
    setSaving(true)
    try {
      const updated = await suppliersService.updateSupplier(id, form)
      setSupplier(updated)
      setEditing(false)
    } catch {
      setError('Error actualizando proveedor')
    } finally {
      setSaving(false)
    }
  }

  const handleLink = async () => {
    setLinking(true)
    try {
      const result = await suppliersService.linkExpenses(id)
      alert(`Se vincularon ${result.linked} gastos`)
      loadExpenses()
      loadAnalytics()
    } catch {
      setError('Error vinculando gastos')
    } finally {
      setLinking(false)
    }
  }

  const handleDeactivate = async () => {
    if (!confirm('¿Desactivar este proveedor?')) return
    try {
      await suppliersService.deactivateSupplier(id)
      navigate('/suppliers')
    } catch {
      setError('Error desactivando proveedor')
    }
  }

  if (loading) return <div className="p-6 text-sm text-gray-500">Cargando...</div>
  if (error && !supplier) return <div className="p-6 text-sm text-red-600">{error}</div>

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <button onClick={() => navigate('/suppliers')} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-800 mb-6 transition-colors">
        <ArrowLeft className="w-4 h-4" />
        Volver a proveedores
      </button>

      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-orange-100 flex items-center justify-center">
            <Building2 className="w-5 h-5 text-orange-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">{supplier.name}</h1>
            {supplier.cuit && <p className="text-sm text-gray-500">CUIT: {supplier.cuit}</p>}
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleLink}
            disabled={linking}
            className="flex items-center gap-2 px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            <Link className="w-4 h-4" />
            {linking ? 'Vinculando...' : 'Vincular gastos'}
          </button>
          <button
            onClick={handleDeactivate}
            className="flex items-center gap-2 px-3 py-2 border border-red-200 rounded-lg text-sm text-red-600 hover:bg-red-50"
          >
            <Trash2 className="w-4 h-4" />
            Desactivar
          </button>
        </div>
      </div>

      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200 mb-6">
        {TABS.map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px ${
              tab === t
                ? 'border-orange-500 text-orange-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Tab: Contacto */}
      {tab === 'Contacto' && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-sm font-semibold text-gray-700">Datos de contacto</h2>
            {!editing ? (
              <button onClick={() => setEditing(true)} className="text-sm text-orange-600 hover:text-orange-700 font-medium">Editar</button>
            ) : (
              <div className="flex gap-2">
                <button onClick={handleSave} disabled={saving} className="flex items-center gap-1 text-sm text-white bg-orange-600 hover:bg-orange-700 px-3 py-1.5 rounded-lg disabled:opacity-50">
                  <Save className="w-3.5 h-3.5" />
                  {saving ? 'Guardando...' : 'Guardar'}
                </button>
                <button onClick={() => { setEditing(false); setForm(supplier) }} className="text-sm text-gray-600 hover:text-gray-800 px-3 py-1.5 border border-gray-300 rounded-lg">Cancelar</button>
              </div>
            )}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[
              { key: 'name', label: 'Nombre *', required: true },
              { key: 'cuit', label: 'CUIT' },
              { key: 'email', label: 'Email', type: 'email' },
              { key: 'phone', label: 'Teléfono' },
            ].map(({ key, label, type = 'text', required }) => (
              <div key={key}>
                <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
                {editing ? (
                  <input
                    type={type}
                    required={required}
                    value={form[key] || ''}
                    onChange={e => setForm({ ...form, [key]: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
                  />
                ) : (
                  <p className="text-sm text-gray-900">{supplier[key] || <span className="text-gray-400">—</span>}</p>
                )}
              </div>
            ))}
            <div className="sm:col-span-2">
              <label className="block text-xs font-medium text-gray-500 mb-1">Notas</label>
              {editing ? (
                <textarea
                  value={form.notes || ''}
                  onChange={e => setForm({ ...form, notes: e.target.value })}
                  rows={3}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
              ) : (
                <p className="text-sm text-gray-900">{supplier.notes || <span className="text-gray-400">—</span>}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab: Historial */}
      {tab === 'Historial de compras' && (
        <div className="space-y-4">
          {/* Filtros */}
          <div className="flex items-center gap-3 flex-wrap">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Desde</label>
              <input type="date" value={fechaDesde} onChange={e => setFechaDesde(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500" />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Hasta</label>
              <input type="date" value={fechaHasta} onChange={e => setFechaHasta(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500" />
            </div>
          </div>

          {/* Métricas */}
          {analytics && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: 'Total período', value: `$${analytics.total_periodo.toLocaleString('es-AR', { maximumFractionDigits: 0 })}` },
                { label: 'Promedio mensual', value: `$${analytics.promedio_mensual.toLocaleString('es-AR', { maximumFractionDigits: 0 })}` },
                { label: 'Última compra', value: analytics.ultima_compra ? new Date(analytics.ultima_compra + 'T00:00:00').toLocaleDateString('es-AR') : '—' },
                { label: 'Total gastos', value: expTotal },
              ].map(({ label, value }) => (
                <div key={label} className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
                  <p className="text-xs text-gray-500 mb-1">{label}</p>
                  <p className="text-lg font-bold text-gray-900">{value}</p>
                </div>
              ))}
            </div>
          )}

          {/* Desglose por categoría */}
          {analytics && analytics.por_categoria.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Por categoría</h3>
              <div className="space-y-2">
                {analytics.por_categoria.map(c => (
                  <div key={c.categoria} className="flex justify-between text-sm">
                    <span className="text-gray-600">{c.categoria}</span>
                    <span className="font-medium text-gray-900">${c.total.toLocaleString('es-AR', { maximumFractionDigits: 0 })}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tabla de gastos */}
          {expenses.length === 0 ? (
            <div className="text-center py-10 text-gray-400 text-sm">No hay gastos vinculados</div>
          ) : (
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Fecha</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Categoría</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Comentario</th>
                    <th className="text-right px-4 py-3 font-medium text-gray-600">Importe</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {expenses.map(e => (
                    <tr key={e.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-gray-700">
                        {new Date(e.fecha + 'T00:00:00').toLocaleDateString('es-AR')}
                      </td>
                      <td className="px-4 py-3 text-gray-600">{e.category_name || '—'}</td>
                      <td className="px-4 py-3 text-gray-600 max-w-xs truncate">{e.comentario || '—'}</td>
                      <td className="px-4 py-3 text-right font-medium text-gray-900">
                        ${e.importe.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Verificar que App.jsx ya tiene la ruta `/suppliers/:id`**

El import de `SupplierDetail` y la ruta ya fueron agregados en el Task 8 Step 2. Solo verificar que el archivo tiene:

```jsx
import SupplierDetail from './pages/SupplierDetail'
// ...
<Route path="/suppliers/:id" element={<SupplierDetail />} />
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/SupplierDetail.jsx
git commit -m "feat: add SupplierDetail page with contact and purchase history tabs"
```

---

## Task 10: Verificación final

- [ ] **Step 1: Correr suite completa de tests del backend**

```bash
cd backend
pytest tests/ -v
```

Expected: todos los tests existentes + los nuevos de suppliers pasan sin errores.

- [ ] **Step 2: Levantar el servidor de desarrollo y probar en el browser**

```bash
# Terminal 1
cd backend && python run.py

# Terminal 2
cd frontend && npm run dev
```

Abrir http://localhost:5173/suppliers y verificar:
- La página carga sin errores
- Se puede crear un proveedor nuevo
- El proveedor aparece en la lista
- Al hacer clic, abre el detalle
- El tab "Contacto" permite editar
- El tab "Historial" muestra los gastos vinculados y las métricas

- [ ] **Step 3: Probar flujo de vinculación**

1. Ir a un proveedor que tenga nombre coincidente con gastos existentes
2. Hacer clic en "Vincular gastos"
3. Verificar que el historial se actualiza

- [ ] **Step 4: Commit final si hay ajustes menores**

```bash
git add -A
git commit -m "feat: suppliers module complete - sub-project 1 of Fudo migration"
```
