import os
from app import create_app
from app.extensions import db
from app.models import User

config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

with app.app_context():
    # Check if admin already exists
    admin = User.query.filter_by(email='admin@cafeteria.com').first()

    if admin:
        print("Admin user already exists")
    else:
        # Create admin user
        admin = User(
            email='admin@cafeteria.com',
            role='admin',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created successfully: admin@cafeteria.com / admin123")
