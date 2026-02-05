from app import create_app
from app.extensions import db
from app.models import Notification, ScheduleChangeLog, StaffingMetrics, StaffingPrediction

app = create_app()

with app.app_context():
    # Create the new tables
    db.create_all()
    print("✓ Nuevas tablas creadas exitosamente:")
    print("  - notifications")
    print("  - schedule_change_logs")
    print("  - staffing_metrics")
    print("  - staffing_predictions")
