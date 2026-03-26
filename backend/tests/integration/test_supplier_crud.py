import pytest
from datetime import datetime
from app import create_app, db
from app.models.supplier import Supplier
from app.models.user import User


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
def auth_headers(client, app):
    with app.app_context():
        user = User(
            username='admin_test',
            email='admin@test.com',
            role='administrator'
        )
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        
        response = client.post('/api/auth/login', json={
            'username': 'admin_test',
            'password': 'testpass123'
        })
        token = response.json.get('access_token')
        return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def sample_supplier_data():
    return {
        'name': 'Proveedor Test S.A.',
        'tax_id': '30-12345678-9',
        'contact_person': 'Juan Pérez',
        'phone': '+54 11 1234-5678',
        'email': 'contacto@proveedortest.com',
        'address': 'Av. Corrientes 1234, CABA',
        'payment_terms': '30 días',
        'status': 'active'
    }


class TestSupplierCreation:
    
    def test_create_supplier_success(self, client, auth_headers, sample_supplier_data):
        response = client.post(
            '/api/suppliers',
            json=sample_supplier_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json
        assert data['name'] == sample_supplier_data['name']
        assert data['tax_id'] == sample_supplier_data['tax_id']
        assert data['contact_person'] == sample_supplier_data['contact_person']
        assert data['status'] == 'active'
        assert 'id' in data
        assert 'created_at' in data
    
    def test_create_supplier_duplicate_tax_id(self, client, auth_headers, sample_supplier_data, app):
        with app.app_context():
            supplier = Supplier(**sample_supplier_data)
            db.session.add(supplier)
            db.session.commit()
        
        response = client.post(
            '/api/suppliers',
            json=sample_supplier_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert 'tax_id' in response.json.get('message', '').lower()
    
    def test_create_supplier_missing_required_fields(self, client, auth_headers):
        response = client.post(
            '/api/suppliers',
            json={'name': 'Test'},
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    def test_create_supplier_unauthorized(self, client, sample_supplier_data):
        response = client.post(
            '/api/suppliers',
            json=sample_supplier_data
        )
        
        assert response.status_code == 401


class TestSupplierRetrieval:
    
    def test_get_suppliers_list(self, client, auth_headers, app):
        with app.app_context():
            suppliers = [
                Supplier(name=f'Proveedor {i}', tax_id=f'30-1234567{i}-9', status='active')
                for i in range(5)
            ]
            db.session.add_all(suppliers)
            db.session.commit()
        
        response = client.get('/api/suppliers', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json
        assert 'suppliers' in data
        assert len(data['suppliers']) == 5
        assert 'total' in data
        assert data['total'] == 5
    
    def test_get_suppliers_with_pagination(self, client, auth_headers, app):
        with app.app_context():
            suppliers = [
                Supplier(name=f'Proveedor {i}', tax_id=f'30-1234567{i:02d}-9', status='active')
                for i in range(15)
            ]
            db.session.add_all(suppliers)
            db.session.commit()
        
        response = client.get('/api/suppliers?page=1&per_page=10', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json
        assert len(data['suppliers']) == 10
        assert data['total'] == 15
        assert data['page'] == 1
        assert data['pages'] == 2
    
    def test_get_supplier_by_id(self, client, auth_headers, sample_supplier_data, app):
        with app.app_context():
            supplier = Supplier(**sample_supplier_data)
            db.session.add(supplier)
            db.session.commit()
            supplier_id = supplier.id
        
        response = client.get(f'/api/suppliers/{supplier_id}', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json
        assert data['id'] == supplier_id
        assert data['name'] == sample_supplier_data['name']
    
    def test_get_supplier_not_found(self, client, auth_headers):
        response = client.get('/api/suppliers/99999', headers=auth_headers)
        assert response.status_code == 404


class TestSupplierSearch:
    
    def test_search_suppliers_by_name(self, client, auth_headers, app):
        with app.app_context():
            suppliers = [
                Supplier(name='Coca Cola Argentina', tax_id='30-11111111-9', status='active'),
                Supplier(name='Pepsi Argentina', tax_id='30-22222222-9', status='active'),
                Supplier(name='Arcor S.A.', tax_id='30-33333333-9', status='active'),
            ]
            db.session.add_all(suppliers)
            db.session.commit()
        
        response = client.get('/api/suppliers?search=coca', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json
        assert len(data['suppliers']) == 1
        assert 'Coca Cola' in data['suppliers'][0]['name']
    
    def test_filter_suppliers_by_status(self, client, auth_headers, app):
        with app.app_context():
            suppliers = [
                Supplier(name='Activo 1', tax_id='30-11111111-9', status='active'),
                Supplier(name='Activo 2', tax_id='30-22222222-9', status='active'),
                Supplier(name='Inactivo 1', tax_id='30-33333333-9', status='inactive'),
            ]
            db.session.add_all(suppliers)
            db.session.commit()
        
        response = client.get('/api/suppliers?status=active', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json
        assert len(data['suppliers']) == 2
        assert all(s['status'] == 'active' for s in data['suppliers'])
    
    def test_exclude_deleted_suppliers(self, client, auth_headers, app):
        with app.app_context():
            suppliers = [
                Supplier(name='Normal', tax_id='30-11111111-9', status='active', is_deleted=False),
                Supplier(name='Eliminado', tax_id='30-22222222-9', status='active', is_deleted=True),
            ]
            db.session.add_all(suppliers)
            db.session.commit()
        
        response = client.get('/api/suppliers', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json
        assert len(data['suppliers']) == 1
        assert data['suppliers'][0]['name'] == 'Normal'


class TestSupplierUpdate:
    
    def test_update_supplier_success(self, client, auth_headers, sample_supplier_data, app):
        with app.app_context():
            supplier = Supplier(**sample_supplier_data)
            db.session.add(supplier)
            db.session.commit()
            supplier_id = supplier.id
        
        updated_data = {
            'name': 'Proveedor Actualizado S.A.',
            'phone': '+54 11 9999-9999',
            'status': 'inactive'
        }
        
        response = client.put(
            f'/api/suppliers/{supplier_id}',
            json=updated_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['name'] == updated_data['name']
        assert data['phone'] == updated_data['phone']
        assert data['status'] == 'inactive'
    
    def test_update_supplier_tax_id_conflict(self, client, auth_headers, app):
        with app.app_context():
            supplier1 = Supplier(name='Proveedor 1', tax_id='30-11111111-9', status='active')
            supplier2 = Supplier(name='Proveedor 2', tax_id='30-22222222-9', status='active')
            db.session.add_all([supplier1, supplier2])
            db.session.commit()
            supplier2_id = supplier2.id
        
        response = client.put(
            f'/api/suppliers/{supplier2_id}',
            json={'tax_id': '30-11111111-9'},
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    def test_update_supplier_not_found(self, client, auth_headers):
        response = client.put(
            '/api/suppliers/99999',
            json={'name': 'Test'},
            headers=auth_headers
        )
        assert response.status_code == 404


class TestSupplierDeletion:
    
    def test_soft_delete_supplier(self, client, auth_headers, sample_supplier_data, app):
        with app.app_context():
            supplier = Supplier(**sample_supplier_data)
            db.session.add(supplier)
            db.session.commit()
            supplier_id = supplier.id
        
        response = client.delete(f'/api/suppliers/{supplier_id}', headers=auth_headers)
        
        assert response.status_code == 200
        
        with app.app_context():
            supplier = db.session.get(Supplier, supplier_id)
            assert supplier.is_deleted is True
    
    def test_delete_supplier_not_found(self, client, auth_headers):
        response = client.delete('/api/suppliers/99999', headers=auth_headers)
        assert response.status_code == 404
    
    def test_cannot_delete_supplier_with_purchases(self, client, auth_headers, app):
        with app.app_context():
            from app.models.purchase import Purchase
            
            supplier = Supplier(name='Proveedor con compras', tax_id='30-11111111-9', status='active')
            db.session.add(supplier)
            db.session.commit()
            
            purchase = Purchase(
                supplier_id=supplier.id,
                purchase_date=datetime.utcnow(),
                total_amount=1000.0,
                currency='ARS',
                payment_status='pending'
            )
            db.session.add(purchase)
            db.session.commit()
            supplier_id = supplier.id
        
        response = client.delete(f'/api/suppliers/{supplier_id}', headers=auth_headers)
        
        assert response.status_code == 400
        assert 'compras' in response.json.get('message', '').lower() or 'purchases' in response.json.get('message', '').lower()
