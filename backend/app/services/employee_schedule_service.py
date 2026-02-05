from datetime import datetime, date, timedelta
from sqlalchemy import and_
from app.extensions import db
from app.models.schedule import Schedule
from app.models.shift import Shift
from app.models.employee import Employee

class EmployeeScheduleService:
    
    @staticmethod
    def get_employee_weekly_schedule(employee_id, start_date=None):
        """Get employee's weekly schedule starting from a specific date"""
        if start_date is None:
            start_date = date.today()
        elif isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date).date()
        
        end_date = start_date + timedelta(days=6)
        
        shifts = Shift.query.join(Schedule).filter(
            and_(
                Shift.employee_id == employee_id,
                Shift.shift_date >= start_date,
                Shift.shift_date <= end_date,
                Schedule.status == 'published'
            )
        ).order_by(Shift.shift_date, Shift.start_time).all()
        
        total_hours = sum(float(shift.hours) for shift in shifts)
        
        return {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'shifts': [shift.to_dict() for shift in shifts],
            'total_hours': total_hours,
            'shift_count': len(shifts)
        }
    
    @staticmethod
    def get_employee_monthly_schedule(employee_id, year=None, month=None):
        """Get employee's monthly schedule for a specific month"""
        if year is None or month is None:
            today = date.today()
            year = today.year
            month = today.month
        
        start_date = date(year, month, 1)
        
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        shifts = Shift.query.join(Schedule).filter(
            and_(
                Shift.employee_id == employee_id,
                Shift.shift_date >= start_date,
                Shift.shift_date <= end_date,
                Schedule.status == 'published'
            )
        ).order_by(Shift.shift_date, Shift.start_time).all()
        
        total_hours = sum(float(shift.hours) for shift in shifts)
        
        shifts_by_date = {}
        for shift in shifts:
            date_key = shift.shift_date.isoformat()
            if date_key not in shifts_by_date:
                shifts_by_date[date_key] = []
            shifts_by_date[date_key].append(shift.to_dict())
        
        return {
            'year': year,
            'month': month,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'shifts': [shift.to_dict() for shift in shifts],
            'shifts_by_date': shifts_by_date,
            'total_hours': total_hours,
            'shift_count': len(shifts)
        }
    
    @staticmethod
    def get_employee_upcoming_shifts(employee_id, days_ahead=30):
        """Get employee's upcoming shifts for the next N days"""
        start_date = date.today()
        end_date = start_date + timedelta(days=days_ahead)
        
        shifts = Shift.query.join(Schedule).filter(
            and_(
                Shift.employee_id == employee_id,
                Shift.shift_date >= start_date,
                Shift.shift_date <= end_date,
                Schedule.status == 'published'
            )
        ).order_by(Shift.shift_date, Shift.start_time).all()
        
        total_hours = sum(float(shift.hours) for shift in shifts)
        
        return {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'shifts': [shift.to_dict() for shift in shifts],
            'total_hours': total_hours,
            'shift_count': len(shifts)
        }
    
    @staticmethod
    def get_employee_schedule_summary(employee_id, start_date=None, end_date=None):
        """Get summary of employee's schedule for a date range"""
        if start_date is None:
            start_date = date.today()
        elif isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date).date()
        
        if end_date is None:
            end_date = start_date + timedelta(days=30)
        elif isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date).date()
        
        shifts = Shift.query.join(Schedule).filter(
            and_(
                Shift.employee_id == employee_id,
                Shift.shift_date >= start_date,
                Shift.shift_date <= end_date,
                Schedule.status == 'published'
            )
        ).order_by(Shift.shift_date, Shift.start_time).all()
        
        total_hours = sum(float(shift.hours) for shift in shifts)
        
        shifts_by_week = {}
        for shift in shifts:
            week_start = shift.shift_date - timedelta(days=shift.shift_date.weekday())
            week_key = week_start.isoformat()
            
            if week_key not in shifts_by_week:
                shifts_by_week[week_key] = {
                    'week_start': week_key,
                    'shifts': [],
                    'total_hours': 0
                }
            
            shifts_by_week[week_key]['shifts'].append(shift.to_dict())
            shifts_by_week[week_key]['total_hours'] += float(shift.hours)
        
        return {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_hours': total_hours,
            'shift_count': len(shifts),
            'shifts_by_week': list(shifts_by_week.values())
        }
    
    @staticmethod
    def get_next_week_schedule(employee_id):
        """Get employee's schedule for next week (starting from next Monday)"""
        today = date.today()
        days_until_next_monday = (7 - today.weekday()) % 7
        if days_until_next_monday == 0:
            days_until_next_monday = 7
        
        next_monday = today + timedelta(days=days_until_next_monday)
        
        return EmployeeScheduleService.get_employee_weekly_schedule(employee_id, next_monday)
    
    @staticmethod
    def get_current_week_schedule(employee_id):
        """Get employee's schedule for current week (starting from this Monday)"""
        today = date.today()
        days_since_monday = today.weekday()
        this_monday = today - timedelta(days=days_since_monday)
        
        return EmployeeScheduleService.get_employee_weekly_schedule(employee_id, this_monday)
