"""
Create ML tracking tables in the database.
"""
from app import create_app
from app.extensions import db
from app.models.ml_tracking import MLModelVersion, MLPredictionAccuracy, Holiday, PredictionAlert

app = create_app()

def create_ml_tables():
    """Create all ML tracking tables"""
    with app.app_context():
        print("Creating ML tracking tables...")
        
        # Create tables
        db.create_all()
        
        print("✅ ML tracking tables created successfully!")
        print("   - ml_model_versions")
        print("   - ml_prediction_accuracy")
        print("   - holidays")
        print("   - prediction_alerts")

if __name__ == '__main__':
    create_ml_tables()
