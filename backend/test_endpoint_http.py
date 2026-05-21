import os
import json
import jwt
from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.models import User

config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

# Create a test client
client = app.test_client()

with app.app_context():
    # Get admin user
    admin = User.query.filter_by(email='admin@cafeteria.com').first()

    if not admin:
        print("❌ Admin user not found")
    else:
        # Generate a valid token
        token = jwt.encode({
            'user_id': admin.id,
            'email': admin.email,
            'exp': datetime.utcnow() + timedelta(days=7)
        }, app.config['SECRET_KEY'], algorithm='HS256')

        print(f"🔑 Token generado para: {admin.email}")
        print(f"\n📡 Testando endpoint: GET /api/v1/modules/my-modules")
        print(f"   Authorization: Bearer {token[:30]}...")

        # Test the endpoint
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        response = client.get('/api/v1/modules/my-modules', headers=headers)

        print(f"\n📊 Respuesta del endpoint:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")

        if response.status_code == 200:
            data = response.get_json()
            print(f"\n✅ Respuesta exitosa:")
            print(f"   Módulos retornados: {len(data.get('modules', []))}")
            for module in data.get('modules', []):
                print(f"     • {module.get('name')}: {module.get('display_name')}")
        else:
            print(f"\n❌ Error en la respuesta:")
            print(f"   {response.get_json()}")
