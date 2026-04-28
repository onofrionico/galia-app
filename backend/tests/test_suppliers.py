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
