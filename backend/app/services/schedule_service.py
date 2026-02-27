from datetime import datetime, date, timedelta
from sqlalchemy import and_
from app.extensions import db
from app.models.schedule import Schedule
from app.models.shift import Shift
from app.models.employee import Employee

class ScheduleService:
    
    @staticmethod
    def create_schedule(start_date, end_date, created_by):
        """Create a new schedule"""
        schedule = Schedule(
            start_date=start_date,
            end_date=end_date,
            status='draft',
            created_by=created_by
        )
        db.session.add(schedule)
        db.session.commit()
        return schedule
    
    @staticmethod
    def get_schedule_by_id(schedule_id):
        """Get schedule by ID with shifts"""
        return Schedule.query.get(schedule_id)
    
    @staticmethod
    def get_all_schedules(limit=50):
        """Get all schedules ordered by date"""
        return Schedule.query.order_by(Schedule.start_date.desc()).limit(limit).all()
    
    @staticmethod
    def update_schedule(schedule_id, **kwargs):
        """Update schedule fields"""
        schedule = Schedule.query.get(schedule_id)
        if not schedule:
            return None
        
        for key, value in kwargs.items():
            if hasattr(schedule, key):
                setattr(schedule, key, value)
        
        schedule.updated_at = datetime.utcnow()
        db.session.commit()
        return schedule
    
    @staticmethod
    def delete_schedule(schedule_id):
        """Delete a schedule and all its shifts"""
        schedule = Schedule.query.get(schedule_id)
        if not schedule:
            return False
        
        db.session.delete(schedule)
        db.session.commit()
        return True
    
    @staticmethod
    def publish_schedule(schedule_id):
        """Publish a schedule (change status from draft to published)"""
        schedule = Schedule.query.get(schedule_id)
        if not schedule:
            return None
        
        schedule.status = 'published'
        schedule.updated_at = datetime.utcnow()
        db.session.commit()
        return schedule
    
    @staticmethod
    def add_shift(schedule_id, employee_id, shift_date, start_time, end_time, changed_by_user_id=None):
        """Add a shift to a schedule"""
        from app.services.notification_service import NotificationService
        
        shift = Shift(
            schedule_id=schedule_id,
            employee_id=employee_id,
            shift_date=shift_date,
            start_time=start_time,
            end_time=end_time
        )
        shift.calculate_hours()
        
        db.session.add(shift)
        db.session.commit()
        
        # Check if schedule is published, if so notify employee
        schedule = Schedule.query.get(schedule_id)
        if schedule and schedule.status == 'published' and changed_by_user_id:
            NotificationService.notify_shift_added(shift, changed_by_user_id)
        
        return shift
    
    @staticmethod
    def update_shift(shift_id, changed_by_user_id=None, **kwargs):
        """Update a shift"""
        from app.services.notification_service import NotificationService
        
        shift = Shift.query.get(shift_id)
        if not shift:
            return None
        
        # Store old data for notification
        old_data = {
            'shift_date': str(shift.shift_date),
            'start_time': str(shift.start_time),
            'end_time': str(shift.end_time),
            'hours': float(shift.hours)
        }
        
        for key, value in kwargs.items():
            if hasattr(shift, key):
                setattr(shift, key, value)
        
        if 'start_time' in kwargs or 'end_time' in kwargs:
            shift.calculate_hours()
        
        db.session.commit()
        
        # Check if schedule is published, if so notify employee
        schedule = Schedule.query.get(shift.schedule_id)
        if schedule and schedule.status == 'published' and changed_by_user_id:
            NotificationService.notify_shift_modified(shift, old_data, changed_by_user_id)
        
        return shift
    
    @staticmethod
    def delete_shift(shift_id, changed_by_user_id=None):
        """Delete a shift"""
        from app.services.notification_service import NotificationService
        
        shift = Shift.query.get(shift_id)
        if not shift:
            return False
        
        # Store shift data for notification
        shift_data = {
            'employee_id': shift.employee_id,
            'shift_date': str(shift.shift_date),
            'start_time': str(shift.start_time),
            'end_time': str(shift.end_time),
            'hours': float(shift.hours)
        }
        schedule_id = shift.schedule_id
        
        # Check if schedule is published
        schedule = Schedule.query.get(schedule_id)
        
        db.session.delete(shift)
        db.session.commit()
        
        # Notify if published
        if schedule and schedule.status == 'published' and changed_by_user_id:
            NotificationService.notify_shift_deleted(shift_data, schedule_id, changed_by_user_id)
        
        return True
    
    @staticmethod
    def get_shifts_by_schedule(schedule_id):
        """Get all shifts for a schedule"""
        return Shift.query.filter_by(schedule_id=schedule_id).all()
    
    @staticmethod
    def get_shifts_by_employee(employee_id, start_date=None, end_date=None):
        """Get shifts for an employee within a date range"""
        query = Shift.query.filter_by(employee_id=employee_id)
        
        if start_date:
            query = query.filter(Shift.shift_date >= start_date)
        if end_date:
            query = query.filter(Shift.shift_date <= end_date)
        
        return query.order_by(Shift.shift_date).all()
    
    @staticmethod
    def calculate_schedule_cost(schedule_id):
        """Calculate total cost of a schedule based on employee hourly rates"""
        shifts = Shift.query.filter_by(schedule_id=schedule_id).all()
        
        total_cost = 0
        hours_by_employee = {}
        
        for shift in shifts:
            employee = shift.employee
            hours = float(shift.hours)
            rate = float(employee.job_position.hourly_rate) if employee.job_position and employee.job_position.hourly_rate else 0.0
            
            if employee.id not in hours_by_employee:
                hours_by_employee[employee.id] = {
                    'employee_name': employee.full_name,
                    'hours': 0,
                    'rate': rate,
                    'cost': 0
                }
            
            hours_by_employee[employee.id]['hours'] += hours
            hours_by_employee[employee.id]['cost'] += hours * rate
            total_cost += hours * rate
        
        return {
            'total_cost': total_cost,
            'by_employee': list(hours_by_employee.values())
        }
    
    @staticmethod
    def get_employee_hours_summary(schedule_id):
        """Get summary of hours per employee for a schedule"""
        shifts = Shift.query.filter_by(schedule_id=schedule_id).all()
        
        summary = {}
        for shift in shifts:
            emp_id = shift.employee_id
            if emp_id not in summary:
                summary[emp_id] = {
                    'employee_id': emp_id,
                    'employee_name': shift.employee.full_name,
                    'total_hours': 0,
                    'shift_count': 0
                }
            
            summary[emp_id]['total_hours'] += float(shift.hours)
            summary[emp_id]['shift_count'] += 1
        
        return list(summary.values())
    
    @staticmethod
    def check_shift_conflicts(employee_id, shift_date, start_time, end_time, exclude_shift_id=None):
        """Check if a shift conflicts with existing shifts for an employee"""
        query = Shift.query.filter(
            and_(
                Shift.employee_id == employee_id,
                Shift.shift_date == shift_date
            )
        )
        
        if exclude_shift_id:
            query = query.filter(Shift.id != exclude_shift_id)
        
        existing_shifts = query.all()
        
        for existing in existing_shifts:
            if (start_time < existing.end_time and end_time > existing.start_time):
                return True, existing
        
        return False, None
