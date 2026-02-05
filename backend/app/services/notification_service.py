from app.extensions import db
from app.models.notification import Notification, ScheduleChangeLog
from app.models.shift import Shift
from app.models.employee import Employee
from datetime import datetime

class NotificationService:
    
    @staticmethod
    def create_notification(user_id, title, message, notification_type, 
                          related_schedule_id=None, related_shift_id=None):
        """Create a notification for a user"""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            related_schedule_id=related_schedule_id,
            related_shift_id=related_shift_id
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    
    @staticmethod
    def notify_shift_added(shift, changed_by_user_id):
        """Notify employee when a shift is added"""
        employee = shift.employee
        if employee.user_id:
            title = "Nuevo turno asignado"
            message = f"Se te ha asignado un turno el {shift.shift_date} de {shift.start_time.strftime('%H:%M')} a {shift.end_time.strftime('%H:%M')}"
            
            NotificationService.create_notification(
                user_id=employee.user_id,
                title=title,
                message=message,
                notification_type='shift_added',
                related_schedule_id=shift.schedule_id,
                related_shift_id=shift.id
            )
            
            # Log the change
            log = ScheduleChangeLog(
                schedule_id=shift.schedule_id,
                shift_id=shift.id,
                change_type='shift_added',
                changed_by=changed_by_user_id,
                affected_employee_id=employee.id,
                new_data={
                    'shift_date': str(shift.shift_date),
                    'start_time': str(shift.start_time),
                    'end_time': str(shift.end_time),
                    'hours': float(shift.hours)
                }
            )
            db.session.add(log)
            db.session.commit()
    
    @staticmethod
    def notify_shift_modified(shift, old_data, changed_by_user_id):
        """Notify employee when their shift is modified"""
        employee = shift.employee
        if employee.user_id:
            title = "Turno modificado"
            message = f"Tu turno del {shift.shift_date} ha sido modificado. Nuevo horario: {shift.start_time.strftime('%H:%M')} a {shift.end_time.strftime('%H:%M')}"
            
            NotificationService.create_notification(
                user_id=employee.user_id,
                title=title,
                message=message,
                notification_type='shift_modified',
                related_schedule_id=shift.schedule_id,
                related_shift_id=shift.id
            )
            
            # Log the change
            log = ScheduleChangeLog(
                schedule_id=shift.schedule_id,
                shift_id=shift.id,
                change_type='shift_modified',
                changed_by=changed_by_user_id,
                affected_employee_id=employee.id,
                old_data=old_data,
                new_data={
                    'shift_date': str(shift.shift_date),
                    'start_time': str(shift.start_time),
                    'end_time': str(shift.end_time),
                    'hours': float(shift.hours)
                }
            )
            db.session.add(log)
            db.session.commit()
    
    @staticmethod
    def notify_shift_deleted(shift_data, schedule_id, changed_by_user_id):
        """Notify employee when their shift is deleted"""
        employee = Employee.query.get(shift_data['employee_id'])
        if employee and employee.user_id:
            title = "Turno eliminado"
            message = f"Tu turno del {shift_data['shift_date']} de {shift_data['start_time']} a {shift_data['end_time']} ha sido eliminado"
            
            NotificationService.create_notification(
                user_id=employee.user_id,
                title=title,
                message=message,
                notification_type='shift_deleted',
                related_schedule_id=schedule_id
            )
            
            # Log the change
            log = ScheduleChangeLog(
                schedule_id=schedule_id,
                change_type='shift_deleted',
                changed_by=changed_by_user_id,
                affected_employee_id=employee.id,
                old_data=shift_data
            )
            db.session.add(log)
            db.session.commit()
    
    @staticmethod
    def get_user_notifications(user_id, unread_only=False):
        """Get notifications for a user"""
        query = Notification.query.filter_by(user_id=user_id)
        if unread_only:
            query = query.filter_by(is_read=False)
        return query.order_by(Notification.created_at.desc()).all()
    
    @staticmethod
    def mark_as_read(notification_id):
        """Mark a notification as read"""
        notification = Notification.query.get(notification_id)
        if notification:
            notification.is_read = True
            db.session.commit()
        return notification
    
    @staticmethod
    def mark_all_as_read(user_id):
        """Mark all notifications as read for a user"""
        Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
        db.session.commit()
