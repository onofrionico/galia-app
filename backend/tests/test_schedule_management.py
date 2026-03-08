import pytest
from datetime import datetime, date, time, timedelta
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.employee import Employee
from app.models.schedule import Schedule
from app.models.shift import Shift
from app.models.job_position import JobPosition
from app.services.employee_schedule_service import EmployeeScheduleService


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_user(app):
    with app.app_context():
        user = User(
            username='admin',
            email='admin@test.com',
            is_admin=True
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def employee_user(app, admin_user):
    with app.app_context():
        user = User(
            username='employee',
            email='employee@test.com',
            is_admin=False
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.flush()
        
        job_position = JobPosition(
            name='Cajero',
            hourly_rate=1500.0
        )
        db.session.add(job_position)
        db.session.flush()
        
        employee = Employee(
            user_id=user.id,
            first_name='John',
            last_name='Doe',
            dni='12345678',
            job_position_id=job_position.id,
            hire_date=date.today()
        )
        db.session.add(employee)
        db.session.commit()
        return user


def get_auth_token(client, username, password):
    response = client.post('/api/v1/auth/login', json={
        'username': username,
        'password': password
    })
    return response.json['access_token']


class TestScheduleDeletion:
    """Tests for schedule deletion with status validation"""
    
    def test_can_delete_draft_schedule(self, app, admin_user):
        """Test that draft schedules can be deleted"""
        with app.app_context():
            schedule = Schedule(
                start_date=date.today(),
                end_date=date.today() + timedelta(days=7),
                status='draft',
                created_by=admin_user.id
            )
            db.session.add(schedule)
            db.session.commit()
            
            assert schedule.can_be_deleted() is True
    
    def test_cannot_delete_published_schedule(self, app, admin_user):
        """Test that published schedules cannot be deleted"""
        with app.app_context():
            schedule = Schedule(
                start_date=date.today(),
                end_date=date.today() + timedelta(days=7),
                status='published',
                created_by=admin_user.id
            )
            db.session.add(schedule)
            db.session.commit()
            
            assert schedule.can_be_deleted() is False
    
    def test_delete_draft_schedule_endpoint(self, client, app, admin_user):
        """Test DELETE endpoint allows deletion of draft schedules"""
        with app.app_context():
            schedule = Schedule(
                start_date=date.today(),
                end_date=date.today() + timedelta(days=7),
                status='draft',
                created_by=admin_user.id
            )
            db.session.add(schedule)
            db.session.commit()
            schedule_id = schedule.id
        
        token = get_auth_token(client, 'admin', 'password123')
        response = client.delete(
            f'/api/v1/schedules/{schedule_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        assert 'eliminada exitosamente' in response.json['message']
        
        with app.app_context():
            deleted_schedule = Schedule.query.get(schedule_id)
            assert deleted_schedule is None
    
    def test_delete_published_schedule_endpoint_fails(self, client, app, admin_user):
        """Test DELETE endpoint rejects deletion of published schedules"""
        with app.app_context():
            schedule = Schedule(
                start_date=date.today(),
                end_date=date.today() + timedelta(days=7),
                status='published',
                created_by=admin_user.id
            )
            db.session.add(schedule)
            db.session.commit()
            schedule_id = schedule.id
        
        token = get_auth_token(client, 'admin', 'password123')
        response = client.delete(
            f'/api/v1/schedules/{schedule_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 403
        assert 'borrador' in response.json['error']
        
        with app.app_context():
            schedule = Schedule.query.get(schedule_id)
            assert schedule is not None


class TestShiftOrdering:
    """Tests for shift ordering with ongoing shifts first"""
    
    def test_ongoing_shifts_appear_first(self, app, admin_user, employee_user):
        """Test that ongoing shifts are ordered before upcoming shifts"""
        with app.app_context():
            employee = Employee.query.filter_by(user_id=employee_user.id).first()
            
            schedule = Schedule(
                start_date=date.today(),
                end_date=date.today() + timedelta(days=7),
                status='published',
                created_by=admin_user.id
            )
            db.session.add(schedule)
            db.session.flush()
            
            now = datetime.now()
            current_time = now.time()
            
            ongoing_shift_start = (now - timedelta(hours=1)).time()
            ongoing_shift_end = (now + timedelta(hours=2)).time()
            
            upcoming_shift_start = (now + timedelta(hours=3)).time()
            upcoming_shift_end = (now + timedelta(hours=6)).time()
            
            ongoing_shift = Shift(
                schedule_id=schedule.id,
                employee_id=employee.id,
                shift_date=date.today(),
                start_time=ongoing_shift_start,
                end_time=ongoing_shift_end,
                hours=3.0
            )
            
            upcoming_shift = Shift(
                schedule_id=schedule.id,
                employee_id=employee.id,
                shift_date=date.today(),
                start_time=upcoming_shift_start,
                end_time=upcoming_shift_end,
                hours=3.0
            )
            
            db.session.add_all([ongoing_shift, upcoming_shift])
            db.session.commit()
            
            result = EmployeeScheduleService.get_employee_upcoming_shifts(employee.id, 7)
            
            assert len(result['shifts']) == 2
            assert result['shifts'][0]['id'] == ongoing_shift.id
            assert result['shifts'][1]['id'] == upcoming_shift.id
    
    def test_future_shifts_ordered_by_date_and_time(self, app, admin_user, employee_user):
        """Test that future shifts are ordered by date and time"""
        with app.app_context():
            employee = Employee.query.filter_by(user_id=employee_user.id).first()
            
            schedule = Schedule(
                start_date=date.today(),
                end_date=date.today() + timedelta(days=7),
                status='published',
                created_by=admin_user.id
            )
            db.session.add(schedule)
            db.session.flush()
            
            tomorrow = date.today() + timedelta(days=1)
            day_after = date.today() + timedelta(days=2)
            
            shift1 = Shift(
                schedule_id=schedule.id,
                employee_id=employee.id,
                shift_date=day_after,
                start_time=time(9, 0),
                end_time=time(13, 0),
                hours=4.0
            )
            
            shift2 = Shift(
                schedule_id=schedule.id,
                employee_id=employee.id,
                shift_date=tomorrow,
                start_time=time(14, 0),
                end_time=time(18, 0),
                hours=4.0
            )
            
            shift3 = Shift(
                schedule_id=schedule.id,
                employee_id=employee.id,
                shift_date=tomorrow,
                start_time=time(9, 0),
                end_time=time(13, 0),
                hours=4.0
            )
            
            db.session.add_all([shift1, shift2, shift3])
            db.session.commit()
            
            result = EmployeeScheduleService.get_employee_upcoming_shifts(employee.id, 7)
            
            assert len(result['shifts']) == 3
            assert result['shifts'][0]['shift_date'] == tomorrow.isoformat()
            assert result['shifts'][0]['start_time'] == '09:00'
            assert result['shifts'][1]['shift_date'] == tomorrow.isoformat()
            assert result['shifts'][1]['start_time'] == '14:00'
            assert result['shifts'][2]['shift_date'] == day_after.isoformat()
    
    def test_past_shifts_excluded(self, app, admin_user, employee_user):
        """Test that past shifts are excluded from upcoming shifts"""
        with app.app_context():
            employee = Employee.query.filter_by(user_id=employee_user.id).first()
            
            schedule = Schedule(
                start_date=date.today() - timedelta(days=7),
                end_date=date.today() + timedelta(days=7),
                status='published',
                created_by=admin_user.id
            )
            db.session.add(schedule)
            db.session.flush()
            
            now = datetime.now()
            past_shift_start = (now - timedelta(hours=5)).time()
            past_shift_end = (now - timedelta(hours=2)).time()
            
            past_shift = Shift(
                schedule_id=schedule.id,
                employee_id=employee.id,
                shift_date=date.today(),
                start_time=past_shift_start,
                end_time=past_shift_end,
                hours=3.0
            )
            
            future_shift = Shift(
                schedule_id=schedule.id,
                employee_id=employee.id,
                shift_date=date.today() + timedelta(days=1),
                start_time=time(9, 0),
                end_time=time(13, 0),
                hours=4.0
            )
            
            db.session.add_all([past_shift, future_shift])
            db.session.commit()
            
            result = EmployeeScheduleService.get_employee_upcoming_shifts(employee.id, 7)
            
            assert len(result['shifts']) == 1
            assert result['shifts'][0]['id'] == future_shift.id
    
    def test_only_published_schedules_included(self, app, admin_user, employee_user):
        """Test that only shifts from published schedules are included"""
        with app.app_context():
            employee = Employee.query.filter_by(user_id=employee_user.id).first()
            
            draft_schedule = Schedule(
                start_date=date.today(),
                end_date=date.today() + timedelta(days=7),
                status='draft',
                created_by=admin_user.id
            )
            
            published_schedule = Schedule(
                start_date=date.today(),
                end_date=date.today() + timedelta(days=7),
                status='published',
                created_by=admin_user.id
            )
            
            db.session.add_all([draft_schedule, published_schedule])
            db.session.flush()
            
            draft_shift = Shift(
                schedule_id=draft_schedule.id,
                employee_id=employee.id,
                shift_date=date.today() + timedelta(days=1),
                start_time=time(9, 0),
                end_time=time(13, 0),
                hours=4.0
            )
            
            published_shift = Shift(
                schedule_id=published_schedule.id,
                employee_id=employee.id,
                shift_date=date.today() + timedelta(days=1),
                start_time=time(14, 0),
                end_time=time(18, 0),
                hours=4.0
            )
            
            db.session.add_all([draft_shift, published_shift])
            db.session.commit()
            
            result = EmployeeScheduleService.get_employee_upcoming_shifts(employee.id, 7)
            
            assert len(result['shifts']) == 1
            assert result['shifts'][0]['id'] == published_shift.id
