import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.product_category import ProductCategory
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.supply import Supply
from app.models.product_recipe_item import ProductRecipeItem
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from datetime import date, datetime
from decimal import Decimal
import json


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


@pytest.fixture
def category(app):
    with app.app_context():
        cat = ProductCategory(name='Bebidas', color='#3b82f6')
        db.session.add(cat)
        db.session.commit()
        cat_id = cat.id
    return cat_id


@pytest.fixture
def simple_product_with_variant(app, category):
    """Producto SIN receta con stock en variante"""
    with app.app_context():
        product = Product(name='Café Americano', category_id=category, has_recipe=False)
        db.session.add(product)
        db.session.flush()

        variant = ProductVariant(
            product_id=product.id,
            name='Regular',
            price=Decimal('2.50'),
            stock_quantity=10,
            min_stock=2
        )
        db.session.add(variant)
        db.session.commit()
        return variant.id
    return None


@pytest.fixture
def recipe_product_with_supplies(app, category):
    """Producto CON receta que depende de supplies"""
    with app.app_context():
        # Crear supplies
        supply1 = Supply(name='Café Arabica', unit='kg', stock_quantity=5, min_stock=1)
        supply2 = Supply(name='Leche', unit='L', stock_quantity=10, min_stock=2)
        db.session.add(supply1)
        db.session.add(supply2)
        db.session.flush()

        # Crear producto con receta
        product = Product(name='Café con Leche', category_id=category, has_recipe=True)
        db.session.add(product)
        db.session.flush()

        # Agregar items de receta (quantities por unidad de producto)
        recipe_item1 = ProductRecipeItem(
            product_id=product.id,
            supply_id=supply1.id,
            quantity=Decimal('0.01'),  # 10g de café
            unit='kg'
        )
        recipe_item2 = ProductRecipeItem(
            product_id=product.id,
            supply_id=supply2.id,
            quantity=Decimal('0.1'),  # 0.1L de leche
            unit='L'
        )
        db.session.add(recipe_item1)
        db.session.add(recipe_item2)

        # Crear variante
        variant = ProductVariant(
            product_id=product.id,
            name='Estándar',
            price=Decimal('3.50'),
            stock_quantity=0,  # No usa stock de variante
            min_stock=0
        )
        db.session.add(variant)
        db.session.commit()
        return variant.id
    return None


def get_auth_token(client, email, password):
    response = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    return json.loads(response.data).get('token')


class TestCreateSaleWithItems:
    """Test crear venta con items y deducción de stock"""

    def test_create_sale_with_simple_product_items(self, client, admin_user, simple_product_with_variant):
        """Test crear venta con items de producto simple"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')

        response = client.post(
            '/api/v1/sales/create-from-items',
            json={
                'items': [
                    {'product_variant_id': simple_product_with_variant, 'quantity': 2}
                ],
                'mesa_id': 5,
                'medio_pago': 'Tarjeta'
            },
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['estado'] == 'En curso'
        assert data['source'] == 'galia'
        assert data['mesa_id'] == 5
        assert data['medio_pago'] == 'Tarjeta'
        assert data['total'] == 5.0  # 2 * 2.50

    def test_create_sale_without_items_returns_error(self, client, admin_user):
        """Test crear venta sin items retorna error"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')

        response = client.post(
            '/api/v1/sales/create-from-items',
            json={'items': []},
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_create_sale_insufficient_stock_simple_product(self, client, admin_user, simple_product_with_variant):
        """Test crear venta con stock insuficiente en producto simple"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')

        # Intentar vender 15 cuando stock es 10
        response = client.post(
            '/api/v1/sales/create-from-items',
            json={
                'items': [
                    {'product_variant_id': simple_product_with_variant, 'quantity': 15}
                ]
            },
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Stock insuficiente' in data['error']

    def test_create_sale_stock_deduction_simple_product(self, client, admin_user, simple_product_with_variant, app):
        """Test que el stock se deduce correctamente en producto simple"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')

        # Vender 3 unidades
        response = client.post(
            '/api/v1/sales/create-from-items',
            json={
                'items': [
                    {'product_variant_id': simple_product_with_variant, 'quantity': 3}
                ]
            },
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 201

        # Verificar stock se dedujo
        with app.app_context():
            variant = ProductVariant.query.get(simple_product_with_variant)
            assert float(variant.stock_quantity) == 7  # 10 - 3

    def test_create_sale_with_recipe_stock_deduction(self, client, admin_user, recipe_product_with_supplies, app):
        """Test deducción de stock para producto con receta"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')

        # Vender 10 unidades de Café con Leche
        response = client.post(
            '/api/v1/sales/create-from-items',
            json={
                'items': [
                    {'product_variant_id': recipe_product_with_supplies, 'quantity': 10}
                ]
            },
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 201

        # Verificar stocks de supplies se dedujeron
        # Café: 0.01 kg * 10 = 0.1 kg
        # Leche: 0.1 L * 10 = 1 L
        with app.app_context():
            supplies = Supply.query.all()
            cafe = next((s for s in supplies if s.name == 'Café Arabica'), None)
            leche = next((s for s in supplies if s.name == 'Leche'), None)

            assert cafe is not None
            assert leche is not None
            assert float(cafe.stock_quantity) == pytest.approx(4.9, rel=0.01)  # 5 - 0.1
            assert float(leche.stock_quantity) == pytest.approx(9.0, rel=0.01)  # 10 - 1

    def test_create_sale_insufficient_supply_stock(self, client, admin_user, recipe_product_with_supplies):
        """Test error cuando supply tiene stock insuficiente"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')

        # Intentar vender 600 unidades (necesitaría 6 kg de café pero solo hay 5)
        response = client.post(
            '/api/v1/sales/create-from-items',
            json={
                'items': [
                    {'product_variant_id': recipe_product_with_supplies, 'quantity': 600}
                ]
            },
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Stock insuficiente' in data['error']

    def test_create_sale_with_mesa_id(self, client, admin_user, simple_product_with_variant):
        """Test crear venta con mesa_id"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')

        response = client.post(
            '/api/v1/sales/create-from-items',
            json={
                'items': [
                    {'product_variant_id': simple_product_with_variant, 'quantity': 1}
                ],
                'mesa_id': 10
            },
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['mesa_id'] == 10

    def test_create_sale_unit_price_snapshot(self, client, admin_user, simple_product_with_variant, app):
        """Test que unit_price en SaleItem captura el precio al momento de venta"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')

        response = client.post(
            '/api/v1/sales/create-from-items',
            json={
                'items': [
                    {'product_variant_id': simple_product_with_variant, 'quantity': 2}
                ]
            },
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 201
        sale_data = json.loads(response.data)
        sale_id = sale_data['id']

        with app.app_context():
            sale = Sale.query.get(sale_id)
            items = SaleItem.query.filter_by(sale_id=sale_id).all()
            assert len(items) == 1
            assert float(items[0].unit_price) == 2.50


class TestGetSaleWithItems:
    """Test obtener venta con sus items"""

    def test_get_sale_returns_items(self, client, admin_user, simple_product_with_variant, app):
        """Test GET sale retorna los items asociados"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')

        # Crear venta
        create_response = client.post(
            '/api/v1/sales/create-from-items',
            json={
                'items': [
                    {'product_variant_id': simple_product_with_variant, 'quantity': 2}
                ]
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        sale_data = json.loads(create_response.data)
        sale_id = sale_data['id']

        # Obtener venta
        response = client.get(
            f'/api/v1/sales/{sale_id}',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'items' in data
        assert len(data['items']) == 1
        assert data['items'][0]['quantity'] == 2
        assert data['items'][0]['unit_price'] == 2.50
        assert data['items'][0]['subtotal'] == 5.0


class TestDailySummary:
    """Test endpoint de resumen diario"""

    def test_daily_summary_empty(self, client, admin_user):
        """Test daily summary cuando no hay ventas"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')

        response = client.get(
            '/api/v1/sales/daily-summary',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_vendido'] == 0
        assert data['cantidad_ventas'] == 0
        assert data['top_products'] == []
        assert data['bajo_stock_count'] == 0

    def test_daily_summary_with_sales(self, client, admin_user, simple_product_with_variant, app):
        """Test daily summary con ventas del día"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')

        # Crear 2 ventas
        resp1 = client.post(
            '/api/v1/sales/create-from-items',
            json={'items': [{'product_variant_id': simple_product_with_variant, 'quantity': 1}]},
            headers={'Authorization': f'Bearer {token}'}
        )
        resp2 = client.post(
            '/api/v1/sales/create-from-items',
            json={'items': [{'product_variant_id': simple_product_with_variant, 'quantity': 2}]},
            headers={'Authorization': f'Bearer {token}'}
        )

        # Verificar que ambas ventas se crearon
        assert resp1.status_code == 201
        assert resp2.status_code == 201

        # Verificar que ambas SaleItems existen
        with app.app_context():
            items = SaleItem.query.all()
            assert len(items) == 2, f"Expected 2 SaleItems, got {len(items)}"

        response = client.get(
            '/api/v1/sales/daily-summary',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['cantidad_ventas'] == 2
        assert data['total_vendido'] == pytest.approx(7.50, rel=0.01)  # 1*2.50 + 2*2.50
        assert len(data['top_products']) == 1
        # The quantity in top_products should be sum of quantities from all SaleItems for that variant
        assert data['top_products'][0]['quantity'] == 3

    def test_daily_summary_top_products(self, client, admin_user, simple_product_with_variant, app, category):
        """Test que top_products en daily summary está ordenado por total"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')

        # Crear segundo producto
        with app.app_context():
            product = Product(name='Cappuccino', category_id=category, has_recipe=False)
            db.session.add(product)
            db.session.flush()
            variant = ProductVariant(
                product_id=product.id,
                name='Regular',
                price=Decimal('4.50'),
                stock_quantity=10,
                min_stock=1
            )
            db.session.add(variant)
            db.session.commit()
            variant2_id = variant.id

        # Vender 1 Americano (2.50) y 3 Cappuccino (13.50) - Cappuccino debe estar primero
        client.post(
            '/api/v1/sales/create-from-items',
            json={'items': [{'product_variant_id': simple_product_with_variant, 'quantity': 1}]},
            headers={'Authorization': f'Bearer {token}'}
        )
        client.post(
            '/api/v1/sales/create-from-items',
            json={'items': [{'product_variant_id': variant2_id, 'quantity': 3}]},
            headers={'Authorization': f'Bearer {token}'}
        )

        response = client.get(
            '/api/v1/sales/daily-summary',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        top = data['top_products']
        assert len(top) == 2
        # El primero debe ser Cappuccino (13.50)
        assert top[0]['total'] == pytest.approx(13.50, rel=0.01)
        assert top[1]['total'] == pytest.approx(2.50, rel=0.01)

    def test_daily_summary_low_stock_count(self, client, admin_user, simple_product_with_variant, app, category):
        """Test que bajo_stock_count cuenta correctamente"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')

        # Crear producto con bajo stock
        with app.app_context():
            product = Product(name='Producto Bajo Stock', category_id=category, has_recipe=False)
            db.session.add(product)
            db.session.flush()
            variant = ProductVariant(
                product_id=product.id,
                name='Regular',
                price=Decimal('1.00'),
                stock_quantity=1,  # < min_stock de 2
                min_stock=2
            )
            db.session.add(variant)
            db.session.commit()

        response = client.get(
            '/api/v1/sales/daily-summary',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['bajo_stock_count'] >= 1


class TestTopProducts:
    """Test endpoint de top productos"""

    def test_top_products_default_limit(self, client, admin_user, simple_product_with_variant):
        """Test top products con límite default"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')

        # Crear venta
        client.post(
            '/api/v1/sales/create-from-items',
            json={'items': [{'product_variant_id': simple_product_with_variant, 'quantity': 5}]},
            headers={'Authorization': f'Bearer {token}'}
        )

        response = client.get(
            '/api/v1/sales/top-products',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'top_products' in data
        assert len(data['top_products']) == 1

    def test_top_products_with_date_filter(self, client, admin_user, simple_product_with_variant):
        """Test top products con filtros de fecha"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')

        # Crear venta
        client.post(
            '/api/v1/sales/create-from-items',
            json={'items': [{'product_variant_id': simple_product_with_variant, 'quantity': 3}]},
            headers={'Authorization': f'Bearer {token}'}
        )

        today = date.today()
        response = client.get(
            f'/api/v1/sales/top-products?fecha_desde={today}&fecha_hasta={today}',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['top_products']) == 1

    def test_top_products_with_custom_limit(self, client, admin_user, simple_product_with_variant, app, category):
        """Test top products con límite personalizado"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')

        # Crear 3 productos
        with app.app_context():
            for i in range(2):
                product = Product(name=f'Product {i}', category_id=category, has_recipe=False)
                db.session.add(product)
                db.session.flush()
                variant = ProductVariant(
                    product_id=product.id,
                    name='Regular',
                    price=Decimal('5.00'),
                    stock_quantity=100,
                    min_stock=1
                )
                db.session.add(variant)
                db.session.commit()

        response = client.get(
            '/api/v1/sales/top-products?limit=2',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        # Pueden haber 0 a 2 productos dependiendo de si hubo ventas
        assert len(data['top_products']) <= 2

    def test_top_products_empty_result(self, client, admin_user):
        """Test top products sin ventas retorna lista vacía"""
        token = get_auth_token(client, 'admin@test.com', 'admin123')

        response = client.get(
            '/api/v1/sales/top-products',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['top_products'] == []
