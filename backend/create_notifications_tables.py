from app import create_app
from app.extensions import db
from app.models.notification import Notification, ScheduleChangeLog

app = create_app('production')

with app.app_context():
    db.create_all()
    print("✓ Tablas de notificaciones creadas exitosamente")
