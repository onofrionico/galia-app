"""
Initialize holidays in the database.
"""
from app import create_app
from app.services.holiday_service import HolidayService

app = create_app()

def initialize():
    """Initialize Argentina holidays"""
    with app.app_context():
        print("Inicializando feriados de Argentina 2026...")
        
        result = HolidayService.initialize_holidays()
        
        if result['success']:
            print(f"✅ {result['holidays_created']} feriados creados exitosamente!")
        else:
            print(f"❌ Error: {result.get('error')}")

if __name__ == '__main__':
    initialize()
