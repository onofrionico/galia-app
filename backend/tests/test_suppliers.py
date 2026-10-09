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
    data = json.loads(response.data)
    return data.get('access_token') or data.get('token')


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


def _auth(client):
    return {'Authorization': f'Bearer {get_token(client)}'}


def _seed_supplier_with_expenses(app):
    from app.models.expense import Expense, ExpenseCategory
    from datetime import date
    with app.app_context():
        s = Supplier(name='Prov Fechas')
        cat = ExpenseCategory(name='Cat Fechas', expense_type='directo')
        db.session.add_all([s, cat])
        db.session.flush()
        db.session.add(Expense(fecha=date(2026, 1, 10), proveedor='x', supplier_id=s.id, importe=100, category_id=cat.id))
        db.session.add(Expense(fecha=date(2026, 3, 10), proveedor='x', supplier_id=s.id, importe=250, category_id=cat.id))
        db.session.commit()
        return s.id, cat.id


class TestAnalyticsDateFilters:
    def test_filters_apply_to_totals(self, client, admin_user, app):
        supplier_id, _ = _seed_supplier_with_expenses(app)
        r = client.get(f'/api/v1/suppliers/{supplier_id}/analytics?fecha_desde=2026-03-01&fecha_hasta=2026-03-31',
                       headers=_auth(client))
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['total_periodo'] == 250.0
        assert data['por_categoria'][0]['total'] == 250.0
        assert data['promedio_mensual'] == 250.0

    def test_invalid_date_returns_400(self, client, admin_user, app):
        supplier_id, _ = _seed_supplier_with_expenses(app)
        r = client.get(f'/api/v1/suppliers/{supplier_id}/analytics?fecha_desde=nope', headers=_auth(client))
        assert r.status_code == 400
        assert 'error' in json.loads(r.data)


class TestSupplierInputHardening:
    def test_create_with_null_optional_fields(self, client, admin_user):
        r = client.post('/api/v1/suppliers', json={'name': 'Nulo', 'cuit': None, 'email': None, 'phone': None,
                                                   'address': None, 'notes': None}, headers=_auth(client))
        assert r.status_code == 201
        assert json.loads(r.data)['cuit'] is None

    def test_create_with_null_name(self, client, admin_user):
        r = client.post('/api/v1/suppliers', json={'name': None}, headers=_auth(client))
        assert r.status_code == 400

    def test_update_with_null_name(self, client, admin_user, app):
        with app.app_context():
            s = Supplier(name='Con Nombre')
            db.session.add(s)
            db.session.commit()
            supplier_id = s.id
        r = client.put(f'/api/v1/suppliers/{supplier_id}', json={'name': None}, headers=_auth(client))
        assert r.status_code == 400

    def test_expenses_per_page_is_capped(self, client, admin_user, app):
        supplier_id, _ = _seed_supplier_with_expenses(app)
        r = client.get(f'/api/v1/suppliers/{supplier_id}/expenses?per_page=100000', headers=_auth(client))
        assert r.status_code == 200
        assert json.loads(r.data)['per_page'] == 200


class TestExpenseSupplierValidation:
    def _expense_id(self, app, supplier_id, cat_id):
        from app.models.expense import Expense
        from datetime import date
        with app.app_context():
            e = Expense(fecha=date(2026, 3, 1), proveedor='x', supplier_id=supplier_id, importe=10, category_id=cat_id)
            db.session.add(e)
            db.session.commit()
            return e.id

    def test_update_same_inactive_supplier_ok(self, client, admin_user, app):
        supplier_id, cat_id = _seed_supplier_with_expenses(app)
        expense_id = self._expense_id(app, supplier_id, cat_id)
        with app.app_context():
            Supplier.query.get(supplier_id).is_active = False
            db.session.commit()
        r = client.put(f'/api/v1/expenses/{expense_id}',
                       json={'comentario': 'nuevo', 'supplier_id': supplier_id}, headers=_auth(client))
        assert r.status_code == 200

    def test_update_to_inactive_supplier_rejected(self, client, admin_user, app):
        supplier_id, cat_id = _seed_supplier_with_expenses(app)
        expense_id = self._expense_id(app, None, cat_id)
        with app.app_context():
            Supplier.query.get(supplier_id).is_active = False
            db.session.commit()
        r = client.put(f'/api/v1/expenses/{expense_id}', json={'supplier_id': supplier_id}, headers=_auth(client))
        assert r.status_code == 400

    def test_update_non_integer_supplier_400(self, client, admin_user, app):
        supplier_id, cat_id = _seed_supplier_with_expenses(app)
        expense_id = self._expense_id(app, supplier_id, cat_id)
        r = client.put(f'/api/v1/expenses/{expense_id}', json={'supplier_id': 'abc'}, headers=_auth(client))
        assert r.status_code == 400

    def test_update_nonexistent_supplier_400(self, client, admin_user, app):
        supplier_id, cat_id = _seed_supplier_with_expenses(app)
        expense_id = self._expense_id(app, supplier_id, cat_id)
        r = client.put(f'/api/v1/expenses/{expense_id}', json={'supplier_id': 99999}, headers=_auth(client))
        assert r.status_code == 400

    def test_create_non_integer_supplier_400(self, client, admin_user, app):
        _, cat_id = _seed_supplier_with_expenses(app)
        r = client.post('/api/v1/expenses', json={'fecha': '2026-04-01', 'importe': 5, 'category_id': cat_id,
                                                  'supplier_id': 'abc'}, headers=_auth(client))
        assert r.status_code == 400


def test_employee_cannot_list_suppliers(client, app):
    with app.app_context():
        user = User(email='emp@test.com', role='employee', is_active=True)
        user.set_password('emp12345')
        db.session.add(user)
        db.session.commit()
    token = client.post('/api/v1/auth/login', json={'email': 'emp@test.com', 'password': 'emp12345'}).get_json()['token']
    response = client.get('/api/v1/suppliers', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
