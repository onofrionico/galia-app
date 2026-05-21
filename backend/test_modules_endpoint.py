import os
import jwt
from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.models import User
from app.utils.permissions import get_user_modules, check_module_access

config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

with app.app_context():
    # Get admin user
    admin = User.query.filter_by(email='admin@cafeteria.com').first()

    if not admin:
        print("❌ Admin user not found")
    else:
        print(f"✅ Admin user found: {admin.email}")
        print(f"   Role: {admin.role}")
        print(f"   Active: {admin.is_active}")

        # Test get_user_modules
        modules = get_user_modules(admin)
        print(f"\n📊 Módulos del admin: {len(modules)}")
        for module in modules:
            print(f"  • {module.name}: {module.display_name}")

        # Test check_module_access
        print(f"\n🔐 Verificando acceso a módulos:")
        test_modules = ['POS', 'Payroll', 'Reports', 'Employees', 'Dashboard']
        for module_name in test_modules:
            has_access = check_module_access(admin, module_name)
            status = "✓" if has_access else "✗"
            print(f"  {status} {module_name}: {has_access}")

        # Test token generation
        print(f"\n🔑 Generando token de prueba...")
        token = jwt.encode({
            'user_id': admin.id,
            'email': admin.email,
            'exp': datetime.utcnow() + timedelta(days=7)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        print(f"   Token: {token[:50]}...")
        print(f"\n✅ Todo parece estar funcionando correctamente")
