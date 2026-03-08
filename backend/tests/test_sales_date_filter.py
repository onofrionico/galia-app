"""
Tests para verificar corrección de filtros de fecha en ventas
"""
import pytest
from datetime import datetime, date, timedelta
from flask import Flask
from app import create_app
from app.extensions import db
from app.models.sale import Sale
from app.models.user import User


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def auth_headers(app, client):
    """Create authenticated user and return auth headers"""
    with app.app_context():
        # Create admin user
        admin = User(
            username='admin',
            email='admin@test.com',
            role='admin'
        )
        admin.set_password('password123')
        db.session.add(admin)
        db.session.commit()
        
        # Login
        response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'password123'
        })
        
        token = response.json['token']
        return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def sample_sales(app):
    """Create sample sales for testing"""
    with app.app_context():
        sales = [
            Sale(
                fecha=date(2026, 3, 5),
                creacion=datetime(2026, 3, 5, 10, 0, 0),
                estado='Cerrada',
                total=1000.00,
                tipo_venta='Local'
            ),
            Sale(
                fecha=date(2026, 3, 8),
                creacion=datetime(2026, 3, 8, 14, 30, 0),
                estado='Cerrada',
                total=1500.00,
                tipo_venta='Delivery'
            ),
            Sale(
                fecha=date(2026, 3, 10),
                creacion=datetime(2026, 3, 10, 16, 0, 0),
                estado='En curso',
                total=2000.00,
                tipo_venta='Local'
            ),
            Sale(
                fecha=date(2026, 3, 15),
                creacion=datetime(2026, 3, 15, 12, 0, 0),
                estado='Cerrada',
                total=2500.00,
                tipo_venta='Mostrador'
            ),
        ]
        
        for sale in sales:
            db.session.add(sale)
        
        db.session.commit()
        return sales


class TestSalesDateFilter:
    """Test sales date filtering functionality"""
    
    def test_filter_by_fecha_desde(self, client, auth_headers, sample_sales):
        """Should filter sales from a specific date onwards"""
        response = client.get(
            '/api/v1/sales?fecha_desde=2026-03-08',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json
        
        # Should return 3 sales (March 8, 10, 15)
        assert data['total'] == 3
        
        # All sales should be on or after March 8
        for sale in data['sales']:
            sale_date = datetime.strptime(sale['fecha'], '%Y-%m-%d').date()
            assert sale_date >= date(2026, 3, 8)
    
    def test_filter_by_fecha_hasta(self, client, auth_headers, sample_sales):
        """Should filter sales up to a specific date"""
        response = client.get(
            '/api/v1/sales?fecha_hasta=2026-03-10',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json
        
        # Should return 3 sales (March 5, 8, 10)
        assert data['total'] == 3
        
        # All sales should be on or before March 10
        for sale in data['sales']:
            sale_date = datetime.strptime(sale['fecha'], '%Y-%m-%d').date()
            assert sale_date <= date(2026, 3, 10)
    
    def test_filter_by_date_range(self, client, auth_headers, sample_sales):
        """Should filter sales within a date range"""
        response = client.get(
            '/api/v1/sales?fecha_desde=2026-03-08&fecha_hasta=2026-03-10',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json
        
        # Should return 2 sales (March 8, 10)
        assert data['total'] == 2
        
        # All sales should be within the range
        for sale in data['sales']:
            sale_date = datetime.strptime(sale['fecha'], '%Y-%m-%d').date()
            assert date(2026, 3, 8) <= sale_date <= date(2026, 3, 10)
    
    def test_filter_single_day(self, client, auth_headers, sample_sales):
        """Should filter sales for a single day"""
        response = client.get(
            '/api/v1/sales?fecha_desde=2026-03-08&fecha_hasta=2026-03-08',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json
        
        # Should return 1 sale (March 8)
        assert data['total'] == 1
        assert data['sales'][0]['fecha'] == '2026-03-08'
    
    def test_invalid_fecha_desde_format(self, client, auth_headers, sample_sales):
        """Should return error for invalid fecha_desde format"""
        response = client.get(
            '/api/v1/sales?fecha_desde=08-03-2026',
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert 'error' in response.json
        assert 'fecha_desde' in response.json['error'].lower()
    
    def test_invalid_fecha_hasta_format(self, client, auth_headers, sample_sales):
        """Should return error for invalid fecha_hasta format"""
        response = client.get(
            '/api/v1/sales?fecha_hasta=2026/03/10',
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert 'error' in response.json
        assert 'fecha_hasta' in response.json['error'].lower()
    
    def test_no_date_filter_returns_all(self, client, auth_headers, sample_sales):
        """Should return all sales when no date filter is applied"""
        response = client.get(
            '/api/v1/sales',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json
        
        # Should return all 4 sales
        assert data['total'] == 4


class TestSalesStatsDateFilter:
    """Test sales statistics with date filtering"""
    
    def test_stats_filter_by_date_range(self, client, auth_headers, sample_sales):
        """Should calculate stats for date range"""
        response = client.get(
            '/api/v1/sales/stats?fecha_desde=2026-03-08&fecha_hasta=2026-03-10',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json
        
        # Should count 2 sales (March 8, 10)
        assert data['total_ventas'] == 2
        
        # Total should be 1500 + 2000 = 3500
        assert data['total_monto'] == 3500.00
    
    def test_stats_no_filter(self, client, auth_headers, sample_sales):
        """Should calculate stats for all sales when no filter"""
        response = client.get(
            '/api/v1/sales/stats',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json
        
        # Should count all 4 sales
        assert data['total_ventas'] == 4
        
        # Total should be 1000 + 1500 + 2000 + 2500 = 7000
        assert data['total_monto'] == 7000.00
    
    def test_stats_invalid_date_format(self, client, auth_headers, sample_sales):
        """Should return error for invalid date format in stats"""
        response = client.get(
            '/api/v1/sales/stats?fecha_desde=invalid-date',
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert 'error' in response.json


class TestSalesExportDateFilter:
    """Test sales export with date filtering"""
    
    def test_export_with_date_filter(self, client, auth_headers, sample_sales):
        """Should export only sales within date range"""
        response = client.get(
            '/api/v1/sales/export?fecha_desde=2026-03-08&fecha_hasta=2026-03-10',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.content_type == 'text/csv; charset=utf-8'
        
        # Parse CSV content
        csv_content = response.data.decode('utf-8')
        lines = csv_content.strip().split('\n')
        
        # Should have header + 2 data rows
        assert len(lines) == 3
    
    def test_export_all_sales(self, client, auth_headers, sample_sales):
        """Should export all sales when no filter"""
        response = client.get(
            '/api/v1/sales/export',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Parse CSV content
        csv_content = response.data.decode('utf-8')
        lines = csv_content.strip().split('\n')
        
        # Should have header + 4 data rows
        assert len(lines) == 5
    
    def test_export_invalid_date_format(self, client, auth_headers, sample_sales):
        """Should return error for invalid date format in export"""
        response = client.get(
            '/api/v1/sales/export?fecha_desde=2026-13-45',
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert 'error' in response.json


class TestDateBoundaryConditions:
    """Test edge cases and boundary conditions for date filtering"""
    
    def test_filter_with_future_date(self, client, auth_headers, sample_sales):
        """Should return empty result for future dates"""
        response = client.get(
            '/api/v1/sales?fecha_desde=2027-01-01',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['total'] == 0
    
    def test_filter_with_past_date(self, client, auth_headers, sample_sales):
        """Should return all sales for very old start date"""
        response = client.get(
            '/api/v1/sales?fecha_desde=2020-01-01',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['total'] == 4
    
    def test_filter_inverted_range(self, client, auth_headers, sample_sales):
        """Should return empty when fecha_desde > fecha_hasta"""
        response = client.get(
            '/api/v1/sales?fecha_desde=2026-03-15&fecha_hasta=2026-03-05',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['total'] == 0


class TestDateFormatConsistency:
    """Test that dates are consistently formatted in responses"""
    
    def test_sale_fecha_format(self, client, auth_headers, sample_sales):
        """Sale fecha should be in YYYY-MM-DD format"""
        response = client.get(
            '/api/v1/sales',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json
        
        for sale in data['sales']:
            # Should match YYYY-MM-DD format
            fecha = sale['fecha']
            assert len(fecha) == 10
            assert fecha[4] == '-'
            assert fecha[7] == '-'
            
            # Should be parseable as date
            parsed = datetime.strptime(fecha, '%Y-%m-%d').date()
            assert isinstance(parsed, date)
    
    def test_datetime_fields_format(self, client, auth_headers, sample_sales):
        """DateTime fields should be in ISO format"""
        response = client.get(
            '/api/v1/sales',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json
        
        for sale in data['sales']:
            if sale['creacion']:
                # Should be parseable as ISO datetime
                parsed = datetime.fromisoformat(sale['creacion'])
                assert isinstance(parsed, datetime)
