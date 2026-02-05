from app.extensions import db
from app.models.ml_tracking import Holiday
from datetime import datetime, date

class HolidayService:
    """Service for managing holidays and special events"""
    
    # Argentina national holidays 2026
    ARGENTINA_HOLIDAYS_2026 = [
        {'date': '2026-01-01', 'name': 'Año Nuevo', 'type': 'national', 'impact': 0.3},
        {'date': '2026-02-16', 'name': 'Carnaval', 'type': 'national', 'impact': 1.5},
        {'date': '2026-02-17', 'name': 'Carnaval', 'type': 'national', 'impact': 1.5},
        {'date': '2026-03-24', 'name': 'Día de la Memoria', 'type': 'national', 'impact': 0.5},
        {'date': '2026-04-02', 'name': 'Día del Veterano', 'type': 'national', 'impact': 0.7},
        {'date': '2026-04-03', 'name': 'Viernes Santo', 'type': 'national', 'impact': 0.8},
        {'date': '2026-05-01', 'name': 'Día del Trabajador', 'type': 'national', 'impact': 0.4},
        {'date': '2026-05-25', 'name': 'Revolución de Mayo', 'type': 'national', 'impact': 0.6},
        {'date': '2026-06-15', 'name': 'Día de la Bandera', 'type': 'national', 'impact': 0.7},
        {'date': '2026-06-20', 'name': 'Paso a la Inmortalidad del Gral. Güemes', 'type': 'national', 'impact': 0.7},
        {'date': '2026-07-09', 'name': 'Día de la Independencia', 'type': 'national', 'impact': 0.6},
        {'date': '2026-08-17', 'name': 'Paso a la Inmortalidad del Gral. San Martín', 'type': 'national', 'impact': 0.7},
        {'date': '2026-10-12', 'name': 'Día del Respeto a la Diversidad Cultural', 'type': 'national', 'impact': 0.7},
        {'date': '2026-11-23', 'name': 'Día de la Soberanía Nacional', 'type': 'national', 'impact': 0.7},
        {'date': '2026-12-08', 'name': 'Inmaculada Concepción', 'type': 'national', 'impact': 0.8},
        {'date': '2026-12-25', 'name': 'Navidad', 'type': 'national', 'impact': 0.3},
        {'date': '2026-12-31', 'name': 'Fin de Año', 'type': 'national', 'impact': 1.8},
    ]
    
    @staticmethod
    def initialize_holidays():
        """Initialize database with Argentina holidays"""
        created = 0
        
        for holiday_data in HolidayService.ARGENTINA_HOLIDAYS_2026:
            holiday_date = datetime.strptime(holiday_data['date'], '%Y-%m-%d').date()
            
            # Check if already exists
            existing = Holiday.query.filter_by(date=holiday_date).first()
            if existing:
                continue
            
            holiday = Holiday(
                date=holiday_date,
                name=holiday_data['name'],
                type=holiday_data['type'],
                impact_multiplier=holiday_data['impact']
            )
            db.session.add(holiday)
            created += 1
        
        db.session.commit()
        
        return {
            'success': True,
            'holidays_created': created
        }
    
    @staticmethod
    def is_holiday(check_date):
        """Check if a date is a holiday"""
        if isinstance(check_date, str):
            check_date = datetime.strptime(check_date, '%Y-%m-%d').date()
        
        holiday = Holiday.query.filter_by(date=check_date).first()
        return holiday is not None
    
    @staticmethod
    def get_holiday(check_date):
        """Get holiday information for a date"""
        if isinstance(check_date, str):
            check_date = datetime.strptime(check_date, '%Y-%m-%d').date()
        
        return Holiday.query.filter_by(date=check_date).first()
    
    @staticmethod
    def add_special_event(event_date, name, impact_multiplier=1.0, notes=None):
        """Add a special event (not a national holiday)"""
        if isinstance(event_date, str):
            event_date = datetime.strptime(event_date, '%Y-%m-%d').date()
        
        # Check if already exists
        existing = Holiday.query.filter_by(date=event_date).first()
        if existing:
            return {
                'success': False,
                'error': 'Event already exists for this date'
            }
        
        event = Holiday(
            date=event_date,
            name=name,
            type='special_event',
            impact_multiplier=impact_multiplier,
            notes=notes
        )
        db.session.add(event)
        db.session.commit()
        
        return {
            'success': True,
            'event': event.to_dict()
        }
    
    @staticmethod
    def get_all_holidays(year=None):
        """Get all holidays, optionally filtered by year"""
        query = Holiday.query
        
        if year:
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
            query = query.filter(Holiday.date >= start_date, Holiday.date <= end_date)
        
        holidays = query.order_by(Holiday.date).all()
        
        return {
            'success': True,
            'holidays': [h.to_dict() for h in holidays]
        }
    
    @staticmethod
    def delete_holiday(holiday_id):
        """Delete a holiday or special event"""
        holiday = Holiday.query.get(holiday_id)
        if not holiday:
            return {
                'success': False,
                'error': 'Holiday not found'
            }
        
        db.session.delete(holiday)
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Holiday deleted successfully'
        }
