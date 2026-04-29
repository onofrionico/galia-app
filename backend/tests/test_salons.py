import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.salon import Salon
from app.models.mesa import Mesa
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


def get_auth_token(client, email, password):
    response = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    return json.loads(response.data).get('token')


def test_create_salon(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    response = client.post(
        '/api/v1/salons',
        json={
            'name': 'Salón Principal',
            'description': 'Área principal de la cafetería'
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == 'Salón Principal'
    assert data['description'] == 'Área principal de la cafetería'
    assert data['is_active'] == True
    assert data['mesa_count'] == 0


def test_list_salons(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create 3 salons
    for i in range(3):
        client.post(
            '/api/v1/salons',
            json={'name': f'Salón {i+1}'},
            headers={'Authorization': f'Bearer {token}'}
        )

    response = client.get('/api/v1/salons', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total'] == 3
    assert len(data['salons']) == 3
    for salon in data['salons']:
        assert 'mesa_count' in salon


def test_get_salon(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create salon
    salon_resp = client.post(
        '/api/v1/salons',
        json={'name': 'Salón Principal', 'description': 'Main room'},
        headers={'Authorization': f'Bearer {token}'}
    )
    salon_id = json.loads(salon_resp.data)['id']

    response = client.get(f'/api/v1/salons/{salon_id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == salon_id
    assert data['name'] == 'Salón Principal'
    assert data['description'] == 'Main room'
    assert 'mesas' in data
    assert data['mesa_count'] == 0


def test_create_mesa(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create salon
    salon_resp = client.post(
        '/api/v1/salons',
        json={'name': 'Salón Principal'},
        headers={'Authorization': f'Bearer {token}'}
    )
    salon_id = json.loads(salon_resp.data)['id']

    # Create mesa
    response = client.post(
        f'/api/v1/salons/{salon_id}/mesas',
        json={
            'number': 1,
            'name': 'Mesa 1',
            'capacity': 4,
            'pos_x': 10.5,
            'pos_y': 20.0,
            'width': 15.0,
            'height': 15.0,
            'status': 'libre'
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['number'] == 1
    assert data['name'] == 'Mesa 1'
    assert data['capacity'] == 4
    assert data['pos_x'] == 10.5
    assert data['pos_y'] == 20.0
    assert data['width'] == 15.0
    assert data['height'] == 15.0
    assert data['status'] == 'libre'
    assert data['salon_id'] == salon_id
    assert data['is_active'] == True


def test_list_mesas(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create salon
    salon_resp = client.post(
        '/api/v1/salons',
        json={'name': 'Salón Principal'},
        headers={'Authorization': f'Bearer {token}'}
    )
    salon_id = json.loads(salon_resp.data)['id']

    # Create 3 mesas
    for i in range(3):
        client.post(
            f'/api/v1/salons/{salon_id}/mesas',
            json={
                'number': i+1,
                'name': f'Mesa {i+1}',
                'capacity': 4,
                'pos_x': 10.0 + i*5,
                'pos_y': 20.0,
                'width': 15.0,
                'height': 15.0,
            },
            headers={'Authorization': f'Bearer {token}'}
        )

    response = client.get(f'/api/v1/salons/{salon_id}/mesas', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total'] == 3
    assert len(data['mesas']) == 3
    # Verify mesas are ordered by number
    assert data['mesas'][0]['number'] == 1
    assert data['mesas'][1]['number'] == 2
    assert data['mesas'][2]['number'] == 3


def test_update_mesa_position(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create salon and mesa
    salon_resp = client.post(
        '/api/v1/salons',
        json={'name': 'Salón Principal'},
        headers={'Authorization': f'Bearer {token}'}
    )
    salon_id = json.loads(salon_resp.data)['id']

    mesa_resp = client.post(
        f'/api/v1/salons/{salon_id}/mesas',
        json={
            'number': 1,
            'name': 'Mesa 1',
            'capacity': 4,
            'pos_x': 10.0,
            'pos_y': 20.0,
            'width': 15.0,
            'height': 15.0,
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    mesa_id = json.loads(mesa_resp.data)['id']

    # Update position
    response = client.put(
        f'/api/v1/salons/{salon_id}/mesas/{mesa_id}',
        json={
            'pos_x': 25.5,
            'pos_y': 35.0,
            'width': 20.0,
            'height': 18.0
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['pos_x'] == 25.5
    assert data['pos_y'] == 35.0
    assert data['width'] == 20.0
    assert data['height'] == 18.0
    assert data['number'] == 1  # Unchanged


def test_update_mesa_status(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create salon and mesa
    salon_resp = client.post(
        '/api/v1/salons',
        json={'name': 'Salón Principal'},
        headers={'Authorization': f'Bearer {token}'}
    )
    salon_id = json.loads(salon_resp.data)['id']

    mesa_resp = client.post(
        f'/api/v1/salons/{salon_id}/mesas',
        json={
            'number': 1,
            'name': 'Mesa 1',
            'capacity': 4,
            'status': 'libre'
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    mesa_id = json.loads(mesa_resp.data)['id']

    # Update status to ocupada
    response = client.put(
        f'/api/v1/salons/{salon_id}/mesas/{mesa_id}',
        json={'status': 'ocupada'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ocupada'

    # Update status to reservada
    response = client.put(
        f'/api/v1/salons/{salon_id}/mesas/{mesa_id}',
        json={'status': 'reservada'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'reservada'


def test_delete_mesa(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create salon and mesa
    salon_resp = client.post(
        '/api/v1/salons',
        json={'name': 'Salón Principal'},
        headers={'Authorization': f'Bearer {token}'}
    )
    salon_id = json.loads(salon_resp.data)['id']

    mesa_resp = client.post(
        f'/api/v1/salons/{salon_id}/mesas',
        json={
            'number': 1,
            'name': 'Mesa 1',
            'capacity': 4,
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    mesa_id = json.loads(mesa_resp.data)['id']

    # Delete mesa
    response = client.delete(
        f'/api/v1/salons/{salon_id}/mesas/{mesa_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200

    # Verify mesa is inactive but still exists in db
    mesa_resp = client.get(
        f'/api/v1/salons/{salon_id}/mesas/{mesa_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    mesa_data = json.loads(mesa_resp.data)
    assert mesa_data['is_active'] == False


def test_create_mesa_missing_number(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create salon
    salon_resp = client.post(
        '/api/v1/salons',
        json={'name': 'Salón Principal'},
        headers={'Authorization': f'Bearer {token}'}
    )
    salon_id = json.loads(salon_resp.data)['id']

    # Create mesa without number
    response = client.post(
        f'/api/v1/salons/{salon_id}/mesas',
        json={'name': 'Mesa 1', 'capacity': 4},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400
    assert 'número' in json.loads(response.data)['error'].lower()


def test_create_salon_missing_name(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')
    response = client.post(
        '/api/v1/salons',
        json={},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400
    assert 'nombre' in json.loads(response.data)['error'].lower()


def test_update_salon(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create salon
    salon_resp = client.post(
        '/api/v1/salons',
        json={'name': 'Salón Original', 'description': 'Original description'},
        headers={'Authorization': f'Bearer {token}'}
    )
    salon_id = json.loads(salon_resp.data)['id']

    # Update salon
    response = client.put(
        f'/api/v1/salons/{salon_id}',
        json={'name': 'Salón Actualizado', 'description': 'New description'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Salón Actualizado'
    assert data['description'] == 'New description'


def test_delete_salon(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create salon
    salon_resp = client.post(
        '/api/v1/salons',
        json={'name': 'Salón Principal'},
        headers={'Authorization': f'Bearer {token}'}
    )
    salon_id = json.loads(salon_resp.data)['id']

    # Delete salon
    response = client.delete(
        f'/api/v1/salons/{salon_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200

    # Verify salon is inactive
    salon_resp = client.get(
        f'/api/v1/salons/{salon_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    data = json.loads(salon_resp.data)
    assert data['is_active'] == False


def test_mesa_count_in_salon_list(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create salon
    salon_resp = client.post(
        '/api/v1/salons',
        json={'name': 'Salón Principal'},
        headers={'Authorization': f'Bearer {token}'}
    )
    salon_id = json.loads(salon_resp.data)['id']

    # Create 2 mesas
    for i in range(2):
        client.post(
            f'/api/v1/salons/{salon_id}/mesas',
            json={'number': i+1, 'name': f'Mesa {i+1}'},
            headers={'Authorization': f'Bearer {token}'}
        )

    # Get salon and verify mesa_count
    response = client.get(f'/api/v1/salons/{salon_id}', headers={'Authorization': f'Bearer {token}'})
    data = json.loads(response.data)
    assert data['mesa_count'] == 2

    # List salons and verify mesa_count
    response = client.get('/api/v1/salons', headers={'Authorization': f'Bearer {token}'})
    data = json.loads(response.data)
    assert data['salons'][0]['mesa_count'] == 2


def test_get_mesa_by_id(client, admin_user):
    token = get_auth_token(client, 'admin@test.com', 'admin123')

    # Create salon and mesa
    salon_resp = client.post(
        '/api/v1/salons',
        json={'name': 'Salón Principal'},
        headers={'Authorization': f'Bearer {token}'}
    )
    salon_id = json.loads(salon_resp.data)['id']

    mesa_resp = client.post(
        f'/api/v1/salons/{salon_id}/mesas',
        json={
            'number': 5,
            'name': 'Mesa VIP',
            'capacity': 8,
            'pos_x': 50.0,
            'pos_y': 50.0,
            'width': 20.0,
            'height': 20.0,
            'status': 'libre'
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    mesa_id = json.loads(mesa_resp.data)['id']

    # Get mesa by id
    response = client.get(f'/api/v1/salons/{salon_id}/mesas/{mesa_id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == mesa_id
    assert data['number'] == 5
    assert data['name'] == 'Mesa VIP'
    assert data['capacity'] == 8
    assert data['pos_x'] == 50.0
    assert data['pos_y'] == 50.0
    assert data['width'] == 20.0
    assert data['height'] == 20.0
    assert data['status'] == 'libre'
