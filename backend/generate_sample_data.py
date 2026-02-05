"""
Script to generate sample historical data for ML training.
This creates realistic staffing metrics and sales data for the past 8 weeks.
"""
from app import create_app
from app.extensions import db
from app.models.staffing_metrics import StaffingMetrics
from app.models.sale import Sale
from datetime import datetime, timedelta, time
import random

app = create_app()

def generate_sample_data():
    """Generate 8 weeks of sample data"""
    with app.app_context():
        print("Generando datos de muestra para entrenamiento ML...")
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(weeks=8)
        
        current_date = start_date
        records_created = 0
        
        while current_date <= end_date:
            day_of_week = current_date.weekday()
            is_weekend = day_of_week >= 5
            
            # Generate data for business hours (8-20)
            for hour in range(8, 21):
                # Simulate realistic patterns
                base_sales = 5
                
                # Weekend boost
                if is_weekend:
                    base_sales += 3
                
                # Lunch hour boost (12-14)
                if 12 <= hour <= 14:
                    base_sales += 8
                
                # Dinner hour boost (19-21)
                if 19 <= hour <= 21:
                    base_sales += 6
                
                # Morning dip
                if 8 <= hour <= 10:
                    base_sales -= 2
                
                # Add randomness
                sales_count = max(0, int(base_sales + random.gauss(0, 2)))
                sales_amount = sales_count * random.uniform(400, 600)
                
                # Calculate appropriate staffing (1 per 8-10 sales)
                employees_scheduled = max(1, int(sales_count / 9) + random.choice([0, 1]))
                
                # Create metric
                metric = StaffingMetrics(
                    date=current_date,
                    hour=hour,
                    day_of_week=day_of_week,
                    employees_scheduled=employees_scheduled,
                    employees_present=employees_scheduled,  # Assume all showed up
                    sales_count=sales_count,
                    sales_amount=sales_amount,
                    is_holiday=False
                )
                
                db.session.add(metric)
                records_created += 1
            
            current_date += timedelta(days=1)
            
            # Commit every week
            if current_date.weekday() == 0:
                db.session.commit()
                print(f"  ✓ Semana completada: {current_date}")
        
        db.session.commit()
        
        print(f"\n✅ Datos generados exitosamente:")
        print(f"   - {records_created} registros de métricas")
        print(f"   - Período: {start_date} a {end_date}")
        print(f"   - Listo para entrenar el modelo ML")

if __name__ == '__main__':
    generate_sample_data()
