import os
from app import create_app
from app.extensions import db
from app.models import User

config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

with app.app_context():
    # Find or create admin user
    admin = User.query.filter_by(email='admin@cafeteria.com').first()

    if admin:
        print(f"✓ Usuario encontrado: {admin.email}")
        # Reset password
        admin.set_password('admin123')
        admin.is_active = True
        db.session.commit()
        print("✅ Contraseña reseteada exitosamente")
        print("📧 Email: admin@cafeteria.com")
        print("🔑 Contraseña: admin123")
    else:
        print("❌ Usuario admin no encontrado")
        # Create new admin user
        admin = User(
            email='admin@cafeteria.com',
            role='admin',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Usuario admin creado exitosamente")
        print("📧 Email: admin@cafeteria.com")
        print("🔑 Contraseña: admin123")
