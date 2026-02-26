from datetime import datetime, timedelta, date
from decimal import Decimal
from app.models.time_tracking import TimeTracking
from app.models.shift import Shift
from app.models.ml_tracking import Holiday


def calculate_hours_from_time_tracking(employee_id, month, year):
    """
    Calcula las horas trabajadas de un empleado en un mes específico
    basándose en los registros de time tracking.
    
    Args:
        employee_id: ID del empleado
        month: Mes (1-12)
        year: Año
        
    Returns:
        tuple: (total_hours, daily_records)
            - total_hours: Total de horas trabajadas (float)
            - daily_records: Lista de registros diarios con bloques de trabajo
    """
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()
    
    time_records = TimeTracking.query.filter(
        TimeTracking.employee_id == employee_id,
        TimeTracking.tracking_date >= start_date,
        TimeTracking.tracking_date < end_date
    ).all()
    
    total_hours = Decimal('0.00')
    daily_records = []
    
    for record in time_records:
        day_hours = Decimal('0.00')
        blocks = []
        
        for block in record.work_blocks:
            start = datetime.combine(datetime.today(), block.start_time)
            end = datetime.combine(datetime.today(), block.end_time)
            
            if end < start:
                end += timedelta(days=1)
            
            duration = end - start
            block_hours = Decimal(str(duration.total_seconds() / 3600))
            day_hours += block_hours
            
            blocks.append({
                'id': block.id,
                'start_time': block.start_time.strftime('%H:%M'),
                'end_time': block.end_time.strftime('%H:%M'),
                'hours': float(block_hours)
            })
        
        total_hours += day_hours
        daily_records.append({
            'date': record.tracking_date.isoformat(),
            'hours': float(day_hours),
            'blocks': blocks
        })
    
    return float(total_hours), daily_records


def calculate_scheduled_hours(employee_id, month, year):
    """
    Calcula las horas programadas de un empleado en un mes específico
    basándose en los turnos asignados.
    
    Args:
        employee_id: ID del empleado
        month: Mes (1-12)
        year: Año
        
    Returns:
        tuple: (total_hours, scheduled_records)
            - total_hours: Total de horas programadas (float)
            - scheduled_records: Lista de registros de turnos programados
    """
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()
    
    shifts = Shift.query.filter(
        Shift.employee_id == employee_id,
        Shift.shift_date >= start_date,
        Shift.shift_date < end_date
    ).all()
    
    total_hours = sum(float(shift.hours) for shift in shifts)
    
    scheduled_records = []
    for shift in shifts:
        scheduled_records.append({
            'date': shift.shift_date.isoformat(),
            'start_time': shift.start_time.strftime('%H:%M'),
            'end_time': shift.end_time.strftime('%H:%M'),
            'hours': float(shift.hours)
        })
    
    return total_hours, scheduled_records


def is_weekend(work_date):
    """
    Verifica si una fecha es fin de semana (domingo).
    
    Args:
        work_date: Fecha a verificar (date object)
        
    Returns:
        bool: True si es domingo (weekday() == 6)
    """
    if isinstance(work_date, str):
        work_date = datetime.fromisoformat(work_date).date()
    return work_date.weekday() == 6


def is_holiday(work_date):
    """
    Verifica si una fecha es feriado consultando la tabla de feriados.
    
    Args:
        work_date: Fecha a verificar (date object o string ISO)
        
    Returns:
        bool: True si es feriado
    """
    if isinstance(work_date, str):
        work_date = datetime.fromisoformat(work_date).date()
    
    holiday = Holiday.query.filter_by(date=work_date).first()
    return holiday is not None


def calculate_employee_cost(hours_worked, hourly_rate, work_date=None, job_position=None):
    """
    Calcula el costo total de un empleado basado en horas trabajadas y tarifa horaria.
    Aplica multiplicadores según el día de la semana y feriados.
    
    Prioridad de multiplicadores:
    1. Feriado (holiday_rate_multiplier)
    2. Domingo (sunday_rate_multiplier)
    3. Fin de semana - sábado (weekend_rate_multiplier)
    
    Args:
        hours_worked: Horas trabajadas (float o int)
        hourly_rate: Tarifa horaria (float, int o Decimal)
        work_date: Fecha de trabajo (date object o string ISO) - opcional
        job_position: Objeto JobPosition con multiplicadores - opcional
        
    Returns:
        float: Costo total redondeado a 2 decimales
    """
    if hourly_rate is None or hours_worked is None:
        return 0.0
    
    base_cost = float(hours_worked) * float(hourly_rate)
    
    if work_date and job_position:
        if isinstance(work_date, str):
            work_date = datetime.fromisoformat(work_date).date()
        
        # Prioridad 1: Feriado
        if is_holiday(work_date) and job_position.holiday_rate_multiplier:
            multiplier = float(job_position.holiday_rate_multiplier)
            base_cost *= multiplier
        # Prioridad 2: Domingo
        elif is_weekend(work_date) and job_position.sunday_rate_multiplier:
            multiplier = float(job_position.sunday_rate_multiplier)
            base_cost *= multiplier
        # Prioridad 3: Fin de semana (sábado u otros días de fin de semana)
        elif work_date.weekday() in [5, 6] and job_position.weekend_rate_multiplier:
            multiplier = float(job_position.weekend_rate_multiplier)
            base_cost *= multiplier
    
    return round(base_cost, 2)


def calculate_total_hours_from_dict(hours, minutes):
    """
    Convierte horas y minutos a un total de horas en formato decimal.
    
    Args:
        hours: Horas (int)
        minutes: Minutos (int)
        
    Returns:
        float: Total de horas en formato decimal
    """
    return hours + (minutes / 60.0)
