import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.product_category import ProductCategory
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.supply import Supply
from app.models.product_recipe_item import ProductRecipeItem
import json
from io import BytesIO
from unittest.mock import patch, MagicMock


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
        cat = ProductCategory(name='Cafés', color='#16a34a')
        db.session.add(cat)
        db.session.commit()
        cat_id = cat.id
    return cat_id


@pytest.fixture
def supply(app):
    with app.app_context():
        supply = Supply(name='Café Arabica', unit='kg', stock_quantity=10, min_stock=2)
        db.session.add(supply)
        db.session.commit()
        supply_id = supply.id
    return supply_id


def get_auth_token(client, email, password):
    response = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    return json.loads(response.data).get('token')


def test_create_product(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    response = client.post(
        '/api/v1/products',
        json={
            'name': 'Espresso',
            'description': 'Café espresso puro',
            'category_id': category,
            'has_recipe': True
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == 'Espresso'
    assert data['category_id'] == category
    assert data['has_recipe'] == True
    assert data['is_active'] == True


def test_list_products(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create 3 products
    for i in range(3):
        client.post(
            '/api/v1/products',
            json={
                'name': f'Product {i+1}',
                'category_id': category,
            },
            headers={'Authorization': f'Bearer {token}'}
        )

    response = client.get('/api/v1/products', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total'] == 3
    assert data['page'] == 1
    assert len(data['products']) == 3


def test_create_variant(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create product
    prod_resp = client.post(
        '/api/v1/products',
        json={'name': 'Espresso', 'category_id': category},
        headers={'Authorization': f'Bearer {token}'}
    )
    prod_id = json.loads(prod_resp.data)['id']

    # Create variant
    response = client.post(
        f'/api/v1/products/{prod_id}/variants',
        json={
            'name': 'Single Shot',
            'price': 2.50,
            'stock_quantity': 100,
            'min_stock': 10
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == 'Single Shot'
    assert float(data['price']) == 2.50
    assert float(data['stock_quantity']) == 100


def test_get_variants(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create product
    prod_resp = client.post(
        '/api/v1/products',
        json={'name': 'Espresso', 'category_id': category},
        headers={'Authorization': f'Bearer {token}'}
    )
    prod_id = json.loads(prod_resp.data)['id']

    # Create 2 variants
    for i in range(2):
        client.post(
            f'/api/v1/products/{prod_id}/variants',
            json={
                'name': f'Variant {i+1}',
                'price': 2.50 + i,
                'stock_quantity': 100
            },
            headers={'Authorization': f'Bearer {token}'}
        )

    response = client.get(f'/api/v1/products/{prod_id}/variants', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total'] == 2
    assert len(data['variants']) == 2


def test_update_variant(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create product and variant
    prod_resp = client.post(
        '/api/v1/products',
        json={'name': 'Espresso', 'category_id': category},
        headers={'Authorization': f'Bearer {token}'}
    )
    prod_id = json.loads(prod_resp.data)['id']

    var_resp = client.post(
        f'/api/v1/products/{prod_id}/variants',
        json={'name': 'Single Shot', 'price': 2.50},
        headers={'Authorization': f'Bearer {token}'}
    )
    var_id = json.loads(var_resp.data)['id']

    # Update variant
    response = client.put(
        f'/api/v1/products/{prod_id}/variants/{var_id}',
        json={'name': 'Double Shot', 'price': 3.50, 'stock_quantity': 50},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Double Shot'
    assert float(data['price']) == 3.50
    assert float(data['stock_quantity']) == 50


def test_update_recipe(client, admin_user, category, supply):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create product with recipe
    prod_resp = client.post(
        '/api/v1/products',
        json={'name': 'Espresso', 'category_id': category, 'has_recipe': True},
        headers={'Authorization': f'Bearer {token}'}
    )
    prod_id = json.loads(prod_resp.data)['id']

    # Update recipe
    response = client.put(
        f'/api/v1/products/{prod_id}/recipe',
        json={
            'items': [
                {'supply_id': supply, 'quantity': 20, 'unit': 'g'}
            ]
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['recipe']) == 1
    assert data['recipe'][0]['supply_id'] == supply
    assert float(data['recipe'][0]['quantity']) == 20


def test_low_stock(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create product and variant with low stock
    prod_resp = client.post(
        '/api/v1/products',
        json={'name': 'Espresso', 'category_id': category},
        headers={'Authorization': f'Bearer {token}'}
    )
    prod_id = json.loads(prod_resp.data)['id']

    client.post(
        f'/api/v1/products/{prod_id}/variants',
        json={
            'name': 'Single Shot',
            'price': 2.50,
            'stock_quantity': 5,
            'min_stock': 10
        },
        headers={'Authorization': f'Bearer {token}'}
    )

    # Get low stock items
    response = client.get('/api/v1/products/low-stock', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total_variants'] >= 1


def test_list_products_by_category(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create two categories
    cat1_resp = client.post(
        '/api/v1/product-categories',
        json={'name': 'Cafés'},
        headers={'Authorization': f'Bearer {token}'}
    )
    cat1_id = json.loads(cat1_resp.data)['id']

    cat2_resp = client.post(
        '/api/v1/product-categories',
        json={'name': 'Panadería'},
        headers={'Authorization': f'Bearer {token}'}
    )
    cat2_id = json.loads(cat2_resp.data)['id']

    # Create products in each category
    client.post(
        '/api/v1/products',
        json={'name': 'Espresso', 'category_id': cat1_id},
        headers={'Authorization': f'Bearer {token}'}
    )

    client.post(
        '/api/v1/products',
        json={'name': 'Pan Integral', 'category_id': cat2_id},
        headers={'Authorization': f'Bearer {token}'}
    )

    # Filter by category
    response = client.get(
        f'/api/v1/products?category_id={cat1_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total'] == 1
    assert data['products'][0]['name'] == 'Espresso'


def test_search_products(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create products
    client.post(
        '/api/v1/products',
        json={'name': 'Espresso', 'category_id': category},
        headers={'Authorization': f'Bearer {token}'}
    )

    client.post(
        '/api/v1/products',
        json={'name': 'Cappuccino', 'category_id': category},
        headers={'Authorization': f'Bearer {token}'}
    )

    # Search for products
    response = client.get(
        '/api/v1/products?search=espresso',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total'] == 1
    assert data['products'][0]['name'] == 'Espresso'


def test_product_pagination(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create 5 products
    for i in range(5):
        client.post(
            '/api/v1/products',
            json={'name': f'Product {i+1}', 'category_id': category},
            headers={'Authorization': f'Bearer {token}'}
        )

    # Request page 1 with 2 items per page
    response = client.get(
        '/api/v1/products?page=1&per_page=2',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total'] == 5
    assert data['page'] == 1
    assert data['per_page'] == 2
    assert len(data['products']) == 2
    assert data['pages'] == 3


def test_create_product_missing_name(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    response = client.post(
        '/api/v1/products',
        json={'category_id': category},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400
    assert 'nombre' in json.loads(response.data)['error'].lower()


def test_create_product_missing_category(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    response = client.post(
        '/api/v1/products',
        json={'name': 'Espresso'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400
    assert 'category_id' in json.loads(response.data)['error'].lower()


def test_create_product_invalid_category(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    response = client.post(
        '/api/v1/products',
        json={'name': 'Espresso', 'category_id': 999},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 404


def test_delete_variant(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create product and variant
    prod_resp = client.post(
        '/api/v1/products',
        json={'name': 'Espresso', 'category_id': category},
        headers={'Authorization': f'Bearer {token}'}
    )
    prod_id = json.loads(prod_resp.data)['id']

    var_resp = client.post(
        f'/api/v1/products/{prod_id}/variants',
        json={'name': 'Single Shot', 'price': 2.50},
        headers={'Authorization': f'Bearer {token}'}
    )
    var_id = json.loads(var_resp.data)['id']

    # Delete variant
    response = client.delete(
        f'/api/v1/products/{prod_id}/variants/{var_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200

    # Verify variant is inactive but still exists
    var_resp = client.get(
        f'/api/v1/products/{prod_id}/variants',
        headers={'Authorization': f'Bearer {token}'}
    )
    data = json.loads(var_resp.data)
    # Only active variants are returned in the list
    assert data['total'] == 0


def test_adjust_stock(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create product and variant
    prod_resp = client.post(
        '/api/v1/products',
        json={'name': 'Espresso', 'category_id': category},
        headers={'Authorization': f'Bearer {token}'}
    )
    prod_id = json.loads(prod_resp.data)['id']

    var_resp = client.post(
        f'/api/v1/products/{prod_id}/variants',
        json={'name': 'Single Shot', 'price': 2.50, 'stock_quantity': 100},
        headers={'Authorization': f'Bearer {token}'}
    )
    var_id = json.loads(var_resp.data)['id']

    # Adjust stock
    response = client.put(
        f'/api/v1/products/{prod_id}/variants/{var_id}/stock',
        json={'stock_quantity': 50},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert float(data['stock_quantity']) == 50


def test_create_variant_missing_name(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create product
    prod_resp = client.post(
        '/api/v1/products',
        json={'name': 'Espresso', 'category_id': category},
        headers={'Authorization': f'Bearer {token}'}
    )
    prod_id = json.loads(prod_resp.data)['id']

    # Create variant without name
    response = client.post(
        f'/api/v1/products/{prod_id}/variants',
        json={'price': 2.50},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400


def test_create_variant_missing_price(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create product
    prod_resp = client.post(
        '/api/v1/products',
        json={'name': 'Espresso', 'category_id': category},
        headers={'Authorization': f'Bearer {token}'}
    )
    prod_id = json.loads(prod_resp.data)['id']

    # Create variant without price
    response = client.post(
        f'/api/v1/products/{prod_id}/variants',
        json={'name': 'Single Shot'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400


def test_get_product_with_variants(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create product
    prod_resp = client.post(
        '/api/v1/products',
        json={'name': 'Espresso', 'category_id': category},
        headers={'Authorization': f'Bearer {token}'}
    )
    prod_id = json.loads(prod_resp.data)['id']

    # Create variants
    for i in range(2):
        client.post(
            f'/api/v1/products/{prod_id}/variants',
            json={'name': f'Variant {i+1}', 'price': 2.50 + i},
            headers={'Authorization': f'Bearer {token}'}
        )

    # Get product with variants
    response = client.get(f'/api/v1/products/{prod_id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['variants']) == 2


def test_update_product(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create product
    prod_resp = client.post(
        '/api/v1/products',
        json={'name': 'Espresso', 'category_id': category},
        headers={'Authorization': f'Bearer {token}'}
    )
    prod_id = json.loads(prod_resp.data)['id']

    # Update product
    response = client.put(
        f'/api/v1/products/{prod_id}',
        json={'name': 'Espresso Premium', 'description': 'Premium quality'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Espresso Premium'
    assert data['description'] == 'Premium quality'


def test_delete_product(client, admin_user, category):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create product
    prod_resp = client.post(
        '/api/v1/products',
        json={'name': 'Espresso', 'category_id': category},
        headers={'Authorization': f'Bearer {token}'}
    )
    prod_id = json.loads(prod_resp.data)['id']

    # Delete product
    response = client.delete(f'/api/v1/products/{prod_id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200

    # Verify product is inactive
    prod_resp = client.get(f'/api/v1/products/{prod_id}', headers={'Authorization': f'Bearer {token}'})
    data = json.loads(prod_resp.data)
    assert data['is_active'] == False


@patch('app.utils.storage.ProductImageStorage.upload_product_image')
def test_upload_product_image(mock_upload, client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Mock S3 upload response
    mock_upload.return_value = 'https://bucket.s3.amazonaws.com/products/test_uuid_test.jpg'

    # Create a test image file
    image_data = BytesIO(b'fake image content')
    image_data.name = 'test.jpg'

    response = client.post(
        '/api/v1/products/upload-image',
        data={'file': (image_data, 'test.jpg')},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'image_url' in data
    assert 'https://bucket.s3.amazonaws.com/' in data['image_url']


def test_upload_product_image_no_file(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    response = client.post(
        '/api/v1/products/upload-image',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'No file provided' in data['error']


def test_upload_product_image_invalid_file_type(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create a test file with invalid extension
    invalid_file = BytesIO(b'fake file content')
    invalid_file.name = 'test.txt'

    response = client.post(
        '/api/v1/products/upload-image',
        data={'file': (invalid_file, 'test.txt')},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'Invalid file type' in data['error']


def test_upload_product_image_file_too_large(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create a mock file that is larger than 5MB
    large_file = BytesIO(b'x' * (6 * 1024 * 1024))
    large_file.name = 'large_image.jpg'

    response = client.post(
        '/api/v1/products/upload-image',
        data={'file': (large_file, 'large_image.jpg')},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 413
    data = json.loads(response.data)
    assert 'File too large' in data['error']


@patch('app.utils.storage.ProductImageStorage.upload_product_image')
def test_upload_product_image_s3_error(mock_upload, client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Mock S3 upload to raise an exception
    mock_upload.side_effect = Exception('S3 connection error')

    # Create a test image file
    image_data = BytesIO(b'fake image content')
    image_data.name = 'test.jpg'

    response = client.post(
        '/api/v1/products/upload-image',
        data={'file': (image_data, 'test.jpg')},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 500
    data = json.loads(response.data)
    assert 'Upload failed' in data['error']
