from flask import Blueprint, request, jsonify
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import func, and_, or_, extract, cast, text
from sqlalchemy import Date as SQLDate
from app.utils.decorators import admin_required
from app.utils.jwt_utils import token_required
from app.extensions import db
from app.models.sale import Sale
from app.models.expense import Expense, ExpenseCategory
from app.models.payroll import Payroll
from app.models.shift import Shift
from app.models.report_goal import ReportGoal, DashboardSnapshot

bp = Blueprint('reports', __name__, url_prefix='/api/v1/reports')


def parse_date(date_str):
    """Parse date string to date object"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None


def get_period_dates(period_type, reference_date=None):
    """Get start and end dates for a given period type"""
    if reference_date is None:
        reference_date = date.today()
    
    if period_type == 'diario':
        return reference_date, reference_date
    elif period_type == 'semanal':
        start = reference_date - timedelta(days=reference_date.weekday())
        end = start + timedelta(days=6)
        return start, end
    elif period_type == 'mensual':
        start = reference_date.replace(day=1)
        next_month = start.replace(day=28) + timedelta(days=4)
        end = next_month - timedelta(days=next_month.day)
        return start, end
    elif period_type == 'trimestral':
        quarter = (reference_date.month - 1) // 3
        start = date(reference_date.year, quarter * 3 + 1, 1)
        if quarter == 3:
            end = date(reference_date.year, 12, 31)
        else:
            end = date(reference_date.year, (quarter + 1) * 3 + 1, 1) - timedelta(days=1)
        return start, end
    elif period_type == 'anual':
        start = date(reference_date.year, 1, 1)
        end = date(reference_date.year, 12, 31)
        return start, end
    else:
        return reference_date, reference_date


# ==================== DASHBOARD ====================

@bp.route('/dashboard', methods=['GET'])
@token_required
@admin_required
def get_dashboard(current_user):
    """Obtener métricas principales del dashboard
    
    Query params:
    - period: diario, semanal, mensual, trimestral, anual (usado si no se especifican fechas)
    - date: fecha de referencia para el período (YYYY-MM-DD)
    - start_date: fecha inicio del rango (YYYY-MM-DD) - tiene prioridad sobre period
    - end_date: fecha fin del rango (YYYY-MM-DD) - tiene prioridad sobre period
    """
    period_type = request.args.get('period', 'mensual')
    date_str = request.args.get('date')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Prioridad: rango de fechas explícito > período relativo
    if start_date_str and end_date_str:
        start_date = parse_date(start_date_str)
        end_date = parse_date(end_date_str)
        if not start_date or not end_date:
            return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400
        if start_date > end_date:
            start_date, end_date = end_date, start_date
        period_type = 'custom'
    else:
        reference_date = parse_date(date_str) if date_str else date.today()
        start_date, end_date = get_period_dates(period_type, reference_date)
    
    # Calcular período anterior para comparación
    period_length = (end_date - start_date).days + 1
    prev_end_date = start_date - timedelta(days=1)
    prev_start_date = prev_end_date - timedelta(days=period_length - 1)
    
    # Métricas de ventas
    sales_data = get_sales_metrics(start_date, end_date)
    prev_sales_data = get_sales_metrics(prev_start_date, prev_end_date)
    
    # Métricas de gastos
    expenses_data = get_expenses_metrics(start_date, end_date)
    prev_expenses_data = get_expenses_metrics(prev_start_date, prev_end_date)
    
    # Métricas de sueldos/payroll
    payroll_data = get_payroll_metrics(start_date, end_date)
    prev_payroll_data = get_payroll_metrics(prev_start_date, prev_end_date)
    
    # Calcular rentabilidad
    total_ingresos = sales_data['total']
    total_gastos = expenses_data['total']
    total_sueldos = payroll_data['total']
    resultado_neto = total_ingresos - total_gastos - total_sueldos

    # Calcular GAO (Grado de Apalancamiento Operativo)
    apalancamiento = calculate_gao(
        ventas=total_ingresos,
        costos_variables=expenses_data['directos'],
        resultado_operativo=resultado_neto
    )

    rentabilidad = (resultado_neto / total_ingresos * 100) if total_ingresos > 0 else 0
    
    # Calcular variaciones
    def calc_variation(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 1)
    
    # Obtener metas activas
    goals = get_goals_progress(sales_data, expenses_data, payroll_data, total_ingresos)
    
    return jsonify({
        'period': {
            'type': period_type,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'ventas': {
            'total': sales_data['total'],
            'cantidad': sales_data['count'],
            'ticket_promedio': sales_data['ticket_promedio'],
            'variacion': calc_variation(sales_data['total'], prev_sales_data['total'])
        },
        'gastos': {
            'total': expenses_data['total'],
            'directos': expenses_data['directos'],
            'indirectos': expenses_data['indirectos'],
            'variacion': calc_variation(expenses_data['total'], prev_expenses_data['total'])
        },
        'sueldos': {
            'total': payroll_data['total'],
            'horas_trabajadas': payroll_data['horas'],
            'variacion': calc_variation(payroll_data['total'], prev_payroll_data['total'])
        },
        'rentabilidad': {
            'resultado_neto': resultado_neto,
            'margen_porcentaje': round(rentabilidad, 1),
            'margen_bruto': total_ingresos - expenses_data['directos'],
            'margen_bruto_porcentaje': round((total_ingresos - expenses_data['directos']) / total_ingresos * 100, 1) if total_ingresos > 0 else 0
        },
        'punto_equilibrio': calculate_break_even_point(
            total_ingresos,
            expenses_data['directos'],
            expenses_data['indirectos'],
            payroll_data['total']
        ),
        'goals': goals,
        'apalancamiento': apalancamiento
    }), 200


def get_sales_metrics(start_date, end_date):
    """Calcular métricas de ventas para un período"""
    result = db.session.query(
        func.coalesce(func.sum(Sale.total), 0).label('total'),
        func.count(Sale.id).label('count')
    ).filter(
        Sale.fecha >= start_date,
        Sale.fecha <= end_date,
        Sale.estado == 'Cerrada'
    ).first()
    
    total = float(result.total) if result.total else 0
    count = result.count or 0
    
    return {
        'total': total,
        'count': count,
        'ticket_promedio': round(total / count, 2) if count > 0 else 0
    }


def get_expenses_metrics(start_date, end_date):
    """Calcular métricas de gastos para un período"""
    # Total de gastos
    total_result = db.session.query(
        func.coalesce(func.sum(Expense.importe), 0)
    ).filter(
        Expense.fecha >= start_date,
        Expense.fecha <= end_date,
        Expense.cancelado == False
    ).scalar()
    
    total = float(total_result) if total_result else 0
    
    # Gastos por tipo (directo/indirecto) - basado en expense_type de la categoría
    from app.models.expense import ExpenseCategory
    
    directos_result = db.session.query(
        func.coalesce(func.sum(Expense.importe), 0)
    ).outerjoin(ExpenseCategory, Expense.category_id == ExpenseCategory.id).filter(
        Expense.fecha >= start_date,
        Expense.fecha <= end_date,
        Expense.cancelado == False,
        ExpenseCategory.expense_type == 'directo'
    ).scalar()
    
    # Indirectos incluye gastos con expense_type='indirecto' O sin categoría (NULL)
    indirectos_result = db.session.query(
        func.coalesce(func.sum(Expense.importe), 0)
    ).outerjoin(ExpenseCategory, Expense.category_id == ExpenseCategory.id).filter(
        Expense.fecha >= start_date,
        Expense.fecha <= end_date,
        Expense.cancelado == False,
        or_(ExpenseCategory.expense_type == 'indirecto', Expense.category_id.is_(None))
    ).scalar()
    
    directos = float(directos_result) if directos_result else 0
    indirectos = float(indirectos_result) if indirectos_result else 0
    
    return {
        'total': total,
        'directos': directos,
        'indirectos': indirectos
    }


def get_payroll_metrics(start_date, end_date):
    """Calcular métricas de sueldos/payroll para un período"""
    start_month = start_date.month
    start_year = start_date.year
    end_month = end_date.month
    end_year = end_date.year

    # Nóminas regulares (meses 1-12) filtradas por rango año/mes
    regular_payrolls = Payroll.query.filter(
        Payroll.month <= 12,
        or_(
            and_(Payroll.year == start_year, Payroll.month >= start_month),
            Payroll.year > start_year
        ),
        or_(
            and_(Payroll.year == end_year, Payroll.month <= end_month),
            Payroll.year < end_year
        )
    ).all()

    # SAC/aguinaldos (mes 13 o 14) incluidos cuando el año cae en el rango
    sac_payrolls = Payroll.query.filter(
        Payroll.month > 12,
        Payroll.year >= start_year,
        Payroll.year <= end_year
    ).all()

    payrolls = regular_payrolls + sac_payrolls

    # gross_salary + extraordinary_amount cubre tanto sueldos normales como aguinaldos
    total = sum(float(p.gross_salary) + float(p.extraordinary_amount or 0) for p in payrolls)
    horas = sum(float(p.hours_worked) for p in payrolls)

    return {
        'total': total,
        'horas': horas
    }


def calculate_break_even_point(ventas, costos_directos, costos_indirectos, sueldos):
    """
    Calcula el punto de equilibrio.
    
    Punto de Equilibrio = Costos Fijos / Margen de Contribución
    
    Donde:
    - Costos Fijos = Gastos Indirectos + Sueldos
    - Costos Variables = Gastos Directos (mercadería, insumos)
    - Margen de Contribución = 1 - (Costos Variables / Ventas)
    
    Returns:
        dict con punto de equilibrio en pesos y porcentaje de cobertura actual
    """
    costos_fijos = costos_indirectos + sueldos
    costos_variables = costos_directos
    
    # Si no hay ventas, no podemos calcular el margen de contribución
    if ventas <= 0:
        return {
            'punto_equilibrio_pesos': 0,
            'costos_fijos': costos_fijos,
            'costos_variables': costos_variables,
            'margen_contribucion_porcentaje': 0,
            'cobertura_actual_porcentaje': 0,
            'estado': 'sin_datos',
            'diferencia': -costos_fijos
        }
    
    # Ratio de costos variables sobre ventas
    ratio_costos_variables = costos_variables / ventas
    
    # Margen de contribución = 1 - ratio_costos_variables
    margen_contribucion = 1 - ratio_costos_variables
    
    # Si el margen de contribución es 0 o negativo, no hay punto de equilibrio alcanzable
    if margen_contribucion <= 0:
        return {
            'punto_equilibrio_pesos': None,
            'costos_fijos': costos_fijos,
            'costos_variables': costos_variables,
            'margen_contribucion_porcentaje': round(margen_contribucion * 100, 1),
            'cobertura_actual_porcentaje': 0,
            'estado': 'inalcanzable',
            'diferencia': ventas - costos_fijos - costos_variables
        }
    
    # Punto de equilibrio en pesos
    punto_equilibrio = costos_fijos / margen_contribucion
    
    # Porcentaje de cobertura actual (ventas / punto de equilibrio)
    cobertura = (ventas / punto_equilibrio * 100) if punto_equilibrio > 0 else 0
    
    # Diferencia respecto al punto de equilibrio
    diferencia = ventas - punto_equilibrio
    
    # Estado: por_debajo, en_equilibrio, por_encima
    if diferencia < -100:
        estado = 'por_debajo'
    elif diferencia > 100:
        estado = 'por_encima'
    else:
        estado = 'en_equilibrio'
    
    return {
        'punto_equilibrio_pesos': round(punto_equilibrio, 2),
        'costos_fijos': round(costos_fijos, 2),
        'costos_variables': round(costos_variables, 2),
        'margen_contribucion_porcentaje': round(margen_contribucion * 100, 1),
        'cobertura_actual_porcentaje': round(cobertura, 1),
        'estado': estado,
        'diferencia': round(diferencia, 2),
        'ventas_faltantes': round(abs(diferencia), 2) if diferencia < 0 else 0,
        'excedente': round(diferencia, 2) if diferencia > 0 else 0
    }


def calculate_gao(ventas, costos_variables, resultado_operativo):
    """
    Calcula el Grado de Apalancamiento Operativo (GAO).

    GAO = Margen de Contribución Total / Resultado Operativo
    Margen de Contribución Total = Ventas - Costos Variables
    """
    if ventas <= 0:
        return {
            'gao': None,
            'margen_contribucion_total': 0.0,
            'resultado_operativo': resultado_operativo,
            'interpretacion': None,
            'recomendacion': None,
            'estado': 'sin_datos'
        }

    margen_contribucion_total = ventas - costos_variables

    if margen_contribucion_total <= 0:
        return {
            'gao': None,
            'margen_contribucion_total': round(margen_contribucion_total, 2),
            'resultado_operativo': round(resultado_operativo, 2),
            'interpretacion': None,
            'recomendacion': None,
            'estado': 'margen_negativo'
        }

    if resultado_operativo <= 0:
        return {
            'gao': None,
            'margen_contribucion_total': round(margen_contribucion_total, 2),
            'resultado_operativo': round(resultado_operativo, 2),
            'interpretacion': None,
            'recomendacion': None,
            'estado': 'en_perdida'
        }

    gao = margen_contribucion_total / resultado_operativo

    if gao < 1.5:
        interpretacion = 'bajo'
        recomendacion = 'precio'
    elif gao <= 3.0:
        interpretacion = 'medio'
        recomendacion = 'equilibrado'
    else:
        interpretacion = 'alto'
        recomendacion = 'volumen'

    return {
        'gao': round(gao, 2),
        'margen_contribucion_total': round(margen_contribucion_total, 2),
        'resultado_operativo': round(resultado_operativo, 2),
        'interpretacion': interpretacion,
        'recomendacion': recomendacion,
        'estado': 'ok'
    }


def get_goals_progress(sales_data, expenses_data, payroll_data, total_ingresos):
    """Calcular progreso hacia las metas configuradas"""
    goals = ReportGoal.get_active_goals()
    result = []
    
    for goal in goals:
        current_value = 0
        
        if goal.goal_type == 'ventas':
            current_value = sales_data['total']
        elif goal.goal_type == 'rentabilidad':
            if total_ingresos > 0:
                resultado = total_ingresos - expenses_data['total'] - payroll_data['total']
                current_value = (resultado / total_ingresos) * 100
        elif goal.goal_type == 'gastos_directos':
            if total_ingresos > 0:
                current_value = (expenses_data['directos'] / total_ingresos) * 100
        elif goal.goal_type == 'gastos_indirectos':
            if total_ingresos > 0:
                current_value = (expenses_data['indirectos'] / total_ingresos) * 100
        elif goal.goal_type == 'costo_laboral':
            if total_ingresos > 0:
                current_value = (payroll_data['total'] / total_ingresos) * 100
        elif goal.goal_type == 'productividad':
            if payroll_data['horas'] > 0:
                current_value = sales_data['total'] / payroll_data['horas']
        
        target = float(goal.target_value)
        if goal.comparison_type == 'mayor_o_igual':
            progress = (current_value / target * 100) if target > 0 else 0
            on_track = current_value >= target
        else:
            progress = ((target - current_value) / target * 100) + 100 if target > 0 else 0
            on_track = current_value <= target
        
        result.append({
            'id': goal.id,
            'type': goal.goal_type,
            'target_value': target,
            'target_unit': goal.target_unit,
            'current_value': round(current_value, 2),
            'progress': min(round(progress, 1), 100),
            'on_track': on_track,
            'comparison_type': goal.comparison_type
        })
    
    return result


# ==================== METAS/GOALS ====================

@bp.route('/goals', methods=['GET'])
@token_required
@admin_required
def get_goals(current_user):
    """Listar todas las metas activas"""
    goals = ReportGoal.get_active_goals()
    return jsonify([g.to_dict() for g in goals]), 200


@bp.route('/goals', methods=['POST'])
@token_required
@admin_required
def create_goal(current_user):
    """Crear una nueva meta"""
    data = request.get_json()
    
    if not data.get('goal_type') or data['goal_type'] not in ReportGoal.GOAL_TYPES:
        return jsonify({'error': 'goal_type inválido'}), 400
    
    if not data.get('target_value'):
        return jsonify({'error': 'target_value es requerido'}), 400
    
    # Desactivar meta anterior del mismo tipo si existe
    existing = ReportGoal.query.filter(
        ReportGoal.goal_type == data['goal_type'],
        ReportGoal.is_active == True
    ).first()
    
    if existing:
        existing.is_active = False
        existing.valid_to = date.today()
    
    goal = ReportGoal(
        goal_type=data['goal_type'],
        period_type=data.get('period_type', 'mensual'),
        target_value=data['target_value'],
        target_unit=data.get('target_unit', 'monto'),
        comparison_type=data.get('comparison_type', 'mayor_o_igual'),
        valid_from=parse_date(data.get('valid_from')) or date.today(),
        valid_to=parse_date(data.get('valid_to')),
        notes=data.get('notes'),
        created_by_id=current_user.id
    )
    
    db.session.add(goal)
    db.session.commit()
    
    return jsonify(goal.to_dict()), 201


@bp.route('/goals/<int:goal_id>', methods=['PUT'])
@token_required
@admin_required
def update_goal(current_user, goal_id):
    """Actualizar una meta existente"""
    goal = ReportGoal.query.get_or_404(goal_id)
    data = request.get_json()
    
    if 'target_value' in data:
        goal.target_value = data['target_value']
    if 'period_type' in data:
        goal.period_type = data['period_type']
    if 'target_unit' in data:
        goal.target_unit = data['target_unit']
    if 'comparison_type' in data:
        goal.comparison_type = data['comparison_type']
    if 'notes' in data:
        goal.notes = data['notes']
    if 'is_active' in data:
        goal.is_active = data['is_active']
    
    db.session.commit()
    return jsonify(goal.to_dict()), 200


@bp.route('/goals/<int:goal_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_goal(current_user, goal_id):
    """Desactivar una meta"""
    goal = ReportGoal.query.get_or_404(goal_id)
    goal.is_active = False
    goal.valid_to = date.today()
    db.session.commit()
    return jsonify({'message': 'Meta desactivada'}), 200


# ==================== REPORTE DE VENTAS ====================

@bp.route('/sales', methods=['GET'])
@token_required
@admin_required
def sales_report(current_user):
    """Reporte detallado de ventas con filtros"""
    start_date = parse_date(request.args.get('start_date'))
    end_date = parse_date(request.args.get('end_date'))
    tipo_venta = request.args.get('tipo_venta')
    medio_pago = request.args.get('medio_pago')
    sala = request.args.get('sala')
    camarero = request.args.get('camarero')
    
    if not start_date:
        start_date, end_date = get_period_dates('mensual')
    if not end_date:
        end_date = date.today()
    
    query = Sale.query.filter(
        Sale.fecha >= start_date,
        Sale.fecha <= end_date,
        Sale.estado == 'Cerrada'
    )
    
    if tipo_venta:
        query = query.filter(Sale.tipo_venta == tipo_venta)
    if medio_pago:
        query = query.filter(Sale.medio_pago == medio_pago)
    if sala:
        query = query.filter(Sale.sala == sala)
    if camarero:
        query = query.filter(Sale.camarero.ilike(f'%{camarero}%'))
    
    sales = query.all()
    
    # Calcular totales
    total = sum(float(s.total) for s in sales)
    count = len(sales)
    
    # Agrupar por tipo de venta
    by_type = {}
    for s in sales:
        t = s.tipo_venta or 'Sin tipo'
        if t not in by_type:
            by_type[t] = {'total': 0, 'count': 0}
        by_type[t]['total'] += float(s.total)
        by_type[t]['count'] += 1
    
    # Agrupar por medio de pago
    by_payment = {}
    for s in sales:
        p = s.medio_pago or 'Sin especificar'
        if p not in by_payment:
            by_payment[p] = {'total': 0, 'count': 0}
        by_payment[p]['total'] += float(s.total)
        by_payment[p]['count'] += 1
    
    # Agrupar por sala
    by_sala = {}
    for s in sales:
        sl = s.sala or 'Sin sala'
        if sl not in by_sala:
            by_sala[sl] = {'total': 0, 'count': 0}
        by_sala[sl]['total'] += float(s.total)
        by_sala[sl]['count'] += 1
    
    return jsonify({
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'summary': {
            'total': total,
            'count': count,
            'ticket_promedio': round(total / count, 2) if count > 0 else 0
        },
        'by_type': by_type,
        'by_payment': by_payment,
        'by_sala': by_sala,
        'sales': [s.to_dict() for s in sales[:100]]  # Limitar a 100 registros
    }), 200


@bp.route('/sales/by-employee', methods=['GET'])
@token_required
@admin_required
def sales_by_employee(current_user):
    """Ventas agrupadas por empleado/camarero"""
    start_date = parse_date(request.args.get('start_date'))
    end_date = parse_date(request.args.get('end_date'))
    
    if not start_date:
        start_date, end_date = get_period_dates('mensual')
    if not end_date:
        end_date = date.today()
    
    result = db.session.query(
        Sale.camarero,
        func.sum(Sale.total).label('total'),
        func.count(Sale.id).label('count'),
        func.avg(Sale.total).label('ticket_promedio')
    ).filter(
        Sale.fecha >= start_date,
        Sale.fecha <= end_date,
        Sale.estado == 'Cerrada',
        Sale.camarero.isnot(None),
        Sale.camarero != ''
    ).group_by(Sale.camarero).order_by(func.sum(Sale.total).desc()).all()
    
    return jsonify({
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'by_employee': [{
            'camarero': r.camarero,
            'total': float(r.total) if r.total else 0,
            'count': r.count,
            'ticket_promedio': round(float(r.ticket_promedio), 2) if r.ticket_promedio else 0
        } for r in result]
    }), 200


@bp.route('/sales/evolution', methods=['GET'])
@token_required
@admin_required
def sales_evolution(current_user):
    """Evolución de ventas por día"""
    start_date = parse_date(request.args.get('start_date'))
    end_date = parse_date(request.args.get('end_date'))
    
    if not start_date:
        start_date, end_date = get_period_dates('mensual')
    if not end_date:
        end_date = date.today()
    
    result = db.session.query(
        Sale.fecha,
        func.sum(Sale.total).label('total'),
        func.count(Sale.id).label('count')
    ).filter(
        Sale.fecha >= start_date,
        Sale.fecha <= end_date,
        Sale.estado == 'Cerrada'
    ).group_by(Sale.fecha).order_by(Sale.fecha).all()
    
    return jsonify({
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'evolution': [{
            'fecha': r.fecha.isoformat(),
            'total': float(r.total) if r.total else 0,
            'count': r.count
        } for r in result]
    }), 200


@bp.route('/expenses/report', methods=['GET'])
@token_required
@admin_required
def expenses_report(current_user):
    """Reporte detallado de gastos"""
    from app.models.expense import ExpenseCategory
    
    start_date = parse_date(request.args.get('start_date'))
    end_date = parse_date(request.args.get('end_date'))
    category_id = request.args.get('category_id', type=int)
    proveedor = request.args.get('proveedor')
    
    if not start_date:
        start_date, end_date = get_period_dates('mensual')
    if not end_date:
        end_date = date.today()
    
    query = Expense.query.filter(
        Expense.fecha >= start_date,
        Expense.fecha <= end_date,
        Expense.cancelado == False
    )
    
    if category_id:
        query = query.filter(Expense.category_id == category_id)
    if proveedor:
        query = query.filter(Expense.proveedor.ilike(f'%{proveedor}%'))
    
    expenses = query.all()
    
    total = sum(float(e.importe) for e in expenses)
    
    # Clasificar en directos/indirectos usando expense_type de la categoría
    directos = 0
    indirectos = 0
    
    by_category = {}
    by_supplier = {}
    
    for e in expenses:
        cat_name = e.category_rel.name if e.category_rel else 'Sin categoría'
        expense_type = e.category_rel.expense_type if e.category_rel else 'indirecto'
        prov = e.proveedor or 'Sin proveedor'
        importe = float(e.importe)
        
        # Clasificar usando expense_type
        if expense_type == 'directo':
            directos += importe
        else:
            indirectos += importe
        
        # Agrupar por categoría
        if cat_name not in by_category:
            by_category[cat_name] = {'total': 0, 'count': 0, 'expense_type': expense_type}
        by_category[cat_name]['total'] += importe
        by_category[cat_name]['count'] += 1
        
        # Agrupar por proveedor
        if prov not in by_supplier:
            by_supplier[prov] = {'total': 0, 'count': 0}
        by_supplier[prov]['total'] += importe
        by_supplier[prov]['count'] += 1
    
    # Ordenar proveedores por total
    sorted_suppliers = sorted(by_supplier.items(), key=lambda x: x[1]['total'], reverse=True)
    
    return jsonify({
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'summary': {
            'total': total,
            'directos': directos,
            'indirectos': indirectos,
            'count': len(expenses)
        },
        'by_category': by_category,
        'by_supplier': dict(sorted_suppliers[:20]),  # Top 20 proveedores
        'expenses': [e.to_dict() for e in expenses[:100]]
    }), 200


@bp.route('/expenses/evolution', methods=['GET'])
@token_required
@admin_required
def expenses_evolution(current_user):
    """Evolución de gastos por día"""
    start_date = parse_date(request.args.get('start_date'))
    end_date = parse_date(request.args.get('end_date'))
    
    if not start_date:
        start_date, end_date = get_period_dates('mensual')
    if not end_date:
        end_date = date.today()
    
    result = db.session.query(
        Expense.fecha,
        func.sum(Expense.importe).label('total'),
        func.count(Expense.id).label('count')
    ).filter(
        Expense.fecha >= start_date,
        Expense.fecha <= end_date,
        Expense.cancelado == False
    ).group_by(Expense.fecha).order_by(Expense.fecha).all()
    
    return jsonify({
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'evolution': [{
            'fecha': r.fecha.isoformat(),
            'total': float(r.total) if r.total else 0,
            'count': r.count
        } for r in result]
    }), 200


# ==================== BALANCE ====================

@bp.route('/balance', methods=['GET'])
@token_required
@admin_required
def balance_report(current_user):
    """Balance/Estado de resultados"""
    start_date = parse_date(request.args.get('start_date'))
    end_date = parse_date(request.args.get('end_date'))
    
    if not start_date:
        start_date, end_date = get_period_dates('mensual')
    if not end_date:
        end_date = date.today()
    
    # Ingresos (ventas)
    sales_data = get_sales_metrics(start_date, end_date)
    
    # Gastos
    expenses_data = get_expenses_metrics(start_date, end_date)
    
    # Sueldos
    payroll_data = get_payroll_metrics(start_date, end_date)
    
    # Cálculos
    total_ingresos = sales_data['total']
    total_egresos = expenses_data['total'] + payroll_data['total']
    resultado_neto = total_ingresos - total_egresos
    
    margen_bruto = total_ingresos - expenses_data['directos']
    margen_bruto_pct = (margen_bruto / total_ingresos * 100) if total_ingresos > 0 else 0
    
    margen_neto_pct = (resultado_neto / total_ingresos * 100) if total_ingresos > 0 else 0
    
    return jsonify({
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'ingresos': {
            'ventas': sales_data['total'],
            'cantidad_ventas': sales_data['count']
        },
        'egresos': {
            'gastos_directos': expenses_data['directos'],
            'gastos_indirectos': expenses_data['indirectos'],
            'sueldos': payroll_data['total'],
            'total': total_egresos
        },
        'resultado': {
            'margen_bruto': margen_bruto,
            'margen_bruto_porcentaje': round(margen_bruto_pct, 1),
            'resultado_neto': resultado_neto,
            'margen_neto_porcentaje': round(margen_neto_pct, 1)
        },
        'ratios': {
            'gastos_directos_sobre_ventas': round(expenses_data['directos'] / total_ingresos * 100, 1) if total_ingresos > 0 else 0,
            'gastos_indirectos_sobre_ventas': round(expenses_data['indirectos'] / total_ingresos * 100, 1) if total_ingresos > 0 else 0,
            'costo_laboral_sobre_ventas': round(payroll_data['total'] / total_ingresos * 100, 1) if total_ingresos > 0 else 0
        }
    }), 200


# ==================== PRODUCTIVIDAD ====================

@bp.route('/productivity', methods=['GET'])
@token_required
@admin_required
def productivity_report(current_user):
    """Métricas de productividad laboral"""
    start_date = parse_date(request.args.get('start_date'))
    end_date = parse_date(request.args.get('end_date'))
    
    if not start_date:
        start_date, end_date = get_period_dates('mensual')
    if not end_date:
        end_date = date.today()
    
    # Ventas
    sales_data = get_sales_metrics(start_date, end_date)
    
    # Horas trabajadas y sueldos
    payroll_data = get_payroll_metrics(start_date, end_date)
    
    # Métricas de productividad
    ventas_por_hora = sales_data['total'] / payroll_data['horas'] if payroll_data['horas'] > 0 else 0
    costo_laboral_pct = (payroll_data['total'] / sales_data['total'] * 100) if sales_data['total'] > 0 else 0
    
    # Meta de productividad
    goal = ReportGoal.get_goal_by_type('productividad')
    meta_productividad = float(goal.target_value) if goal else 0
    
    return jsonify({
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'ventas_total': sales_data['total'],
        'horas_trabajadas': payroll_data['horas'],
        'costo_laboral': payroll_data['total'],
        'ventas_por_hora': round(ventas_por_hora, 2),
        'costo_laboral_porcentaje': round(costo_laboral_pct, 1),
        'meta_productividad': meta_productividad,
        'cumple_meta': ventas_por_hora >= meta_productividad if meta_productividad > 0 else None
    }), 200


# ==================== CATEGORÍAS DE GASTOS ====================

@bp.route('/expense-categories', methods=['GET'])
@token_required
@admin_required
def get_expense_categories(current_user):
    """Listar categorías de gastos"""
    categories = ExpenseCategory.query.filter_by(is_active=True).all()
    return jsonify([c.to_dict() for c in categories]), 200


@bp.route('/expense-categories', methods=['POST'])
@token_required
@admin_required
def create_expense_category(current_user):
    """Crear categoría de gasto"""
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': 'name es requerido'}), 400
    
    if ExpenseCategory.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Ya existe una categoría con ese nombre'}), 400
    
    category = ExpenseCategory(
        name=data['name'],
        description=data.get('description'),
        expense_type=data.get('expense_type', 'indirecto')
    )
    
    db.session.add(category)
    db.session.commit()
    
    return jsonify(category.to_dict()), 201


@bp.route('/expense-categories/<int:category_id>', methods=['PUT'])
@token_required
@admin_required
def update_expense_category(current_user, category_id):
    """Actualizar categoría de gasto"""
    category = ExpenseCategory.query.get_or_404(category_id)
    data = request.get_json()
    
    if 'name' in data:
        category.name = data['name']
    if 'description' in data:
        category.description = data['description']
    if 'expense_type' in data:
        category.expense_type = data['expense_type']
    if 'is_active' in data:
        category.is_active = data['is_active']
    
    db.session.commit()
    return jsonify(category.to_dict()), 200


# ==================== TIME ANALYSIS ====================

def distribute_shift_hours(start_time, end_time):
    """
    Distribuye las horas de un turno entre franjas horarias.
    Retorna dict {hora: fraccion_horas}.
    Ejemplo: start=16:00, end=17:45 → {16: 1.0, 17: 0.75}
    Maneja turnos que cruzan medianoche.
    """
    start_min = start_time.hour * 60 + start_time.minute
    end_min = end_time.hour * 60 + end_time.minute

    if end_min <= start_min:
        end_min += 24 * 60

    slots = {}
    current_min = start_min

    while current_min < end_min:
        hora = (current_min // 60) % 24
        minutos_hasta_fin_hora = 60 - (current_min % 60)
        minutos_restantes = end_min - current_min
        fraccion_min = min(minutos_hasta_fin_hora, minutos_restantes)
        slots[hora] = slots.get(hora, 0) + fraccion_min / 60.0
        current_min += fraccion_min

    return slots


def _days_in_range_by_dow(start_date, end_date):
    """Cuenta cuántas veces aparece cada día de semana (0=lunes) en el rango."""
    counts = {i: 0 for i in range(7)}
    current = start_date
    while current <= end_date:
        counts[current.weekday()] += 1
        current += timedelta(days=1)
    return counts


DOW_NAMES = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']


def get_sales_by_weekday(start_date, end_date):
    """Ventas agrupadas por día de semana (0=lunes … 6=domingo)."""
    import sqlalchemy

    days_in_range = _days_in_range_by_dow(start_date, end_date)

    local_cerrada = Sale.cerrada + text("INTERVAL '-3 hours'")
    dow_expr = func.extract('dow', local_cerrada)
    rows = db.session.query(
        dow_expr.label('dow_pg'),
        func.sum(Sale.total).label('sum_ventas'),
        func.count(Sale.id).label('count_ventas')
    ).filter(
        cast(local_cerrada, SQLDate) >= start_date,
        cast(local_cerrada, SQLDate) <= end_date,
        Sale.estado == 'Cerrada',
        Sale.cerrada.isnot(None)
    ).group_by(dow_expr).all()

    # Convert DOW: extract('dow') returns 0=Sunday in both SQLite and PostgreSQL
    # Convert to Python convention: 0=Monday
    by_dow = {i: {'sum_ventas': 0.0, 'count_ventas': 0} for i in range(7)}
    for row in rows:
        py_dow = (int(row.dow_pg) - 1) % 7  # 0(Sun)->6, 1(Mon)->0, ..., 6(Sat)->5
        by_dow[py_dow]['sum_ventas'] = float(row.sum_ventas or 0)
        by_dow[py_dow]['count_ventas'] = row.count_ventas or 0

    output = []
    for dow in range(7):
        dias = days_in_range[dow]
        sum_v = by_dow[dow]['sum_ventas']
        output.append({
            'dow': dow,
            'nombre': DOW_NAMES[dow],
            'sum_ventas': round(sum_v, 2),
            'count_ventas': by_dow[dow]['count_ventas'],
            'promedio_ventas': round(sum_v / dias, 2) if dias > 0 else 0,
            'dias_en_rango': dias
        })
    return output


def get_sales_by_hour(start_date, end_date):
    """Ventas agrupadas por hora del día (0–23), en hora local Argentina (UTC-3)."""
    local_cerrada = Sale.cerrada + text("INTERVAL '-3 hours'")
    hour_expr = func.extract('hour', local_cerrada)
    rows = db.session.query(
        hour_expr.label('hora'),
        func.sum(Sale.total).label('sum_ventas'),
        func.count(Sale.id).label('count_ventas')
    ).filter(
        cast(local_cerrada, SQLDate) >= start_date,
        cast(local_cerrada, SQLDate) <= end_date,
        Sale.estado == 'Cerrada',
        Sale.cerrada.isnot(None)
    ).group_by(hour_expr).order_by(hour_expr).all()

    output = []
    for row in rows:
        sum_v = float(row.sum_ventas or 0)
        count_v = row.count_ventas or 0
        output.append({
            'hora': int(row.hora),
            'sum_ventas': round(sum_v, 2),
            'count_ventas': count_v,
            'promedio_ventas': round(sum_v / count_v, 2) if count_v > 0 else 0
        })
    return output


def get_labor_by_weekday(start_date, end_date, tasa_horaria):
    """Costo laboral por día de semana (0=lunes … 6=domingo)."""
    days_in_range = _days_in_range_by_dow(start_date, end_date)

    shifts = Shift.query.filter(
        Shift.shift_date >= start_date,
        Shift.shift_date <= end_date
    ).all()

    by_dow = {i: {'sum_horas': 0.0, 'sum_costo': 0.0} for i in range(7)}
    for shift in shifts:
        dow = shift.shift_date.weekday()  # 0=Monday
        horas = float(shift.hours)
        by_dow[dow]['sum_horas'] += horas
        by_dow[dow]['sum_costo'] += horas * tasa_horaria

    output = []
    for dow in range(7):
        dias = days_in_range[dow]
        output.append({
            'dow': dow,
            'nombre': DOW_NAMES[dow],
            'sum_horas': round(by_dow[dow]['sum_horas'], 2),
            'sum_costo': round(by_dow[dow]['sum_costo'], 2),
            'promedio_horas': round(by_dow[dow]['sum_horas'] / dias, 2) if dias > 0 else 0,
            'promedio_costo': round(by_dow[dow]['sum_costo'] / dias, 2) if dias > 0 else 0,
            'dias_en_rango': dias
        })
    return output


def get_labor_by_hour(start_date, end_date, tasa_horaria):
    """Costo laboral por franja horaria, distribuyendo fracciones por turno."""
    total_dias = (end_date - start_date).days + 1

    shifts = Shift.query.filter(
        Shift.shift_date >= start_date,
        Shift.shift_date <= end_date
    ).all()

    by_hour = {}
    for shift in shifts:
        slots = distribute_shift_hours(shift.start_time, shift.end_time)
        for hora, fraccion in slots.items():
            if hora not in by_hour:
                by_hour[hora] = {'sum_horas': 0.0, 'sum_costo': 0.0}
            by_hour[hora]['sum_horas'] += fraccion
            by_hour[hora]['sum_costo'] += fraccion * tasa_horaria

    output = []
    for hora in sorted(by_hour.keys()):
        output.append({
            'hora': hora,
            'sum_horas': round(by_hour[hora]['sum_horas'], 2),
            'sum_costo': round(by_hour[hora]['sum_costo'], 2),
            'promedio_horas': round(by_hour[hora]['sum_horas'] / total_dias, 2),
            'promedio_costo': round(by_hour[hora]['sum_costo'] / total_dias, 2)
        })
    return output


@bp.route('/time-analysis', methods=['GET'])
@token_required
@admin_required
def time_analysis(current_user):
    """Análisis de ventas y costo laboral por día de semana y hora."""
    start_date = parse_date(request.args.get('start_date'))
    end_date = parse_date(request.args.get('end_date'))

    if not start_date:
        start_date, end_date = get_period_dates('mensual')
    if not end_date:
        end_date = date.today()

    payroll_data = get_payroll_metrics(start_date, end_date)
    total_sueldos = payroll_data['total']
    # Usar horas reales de turnos del período para que la tasa sea consistente
    # con la distribución que se hace en get_labor_by_weekday/get_labor_by_hour
    total_shift_horas = db.session.query(
        func.sum(Shift.hours)
    ).filter(
        Shift.shift_date >= start_date,
        Shift.shift_date <= end_date
    ).scalar() or 0
    tasa_horaria = float(total_sueldos) / float(total_shift_horas) if total_shift_horas > 0 else 0

    sales_wd = get_sales_by_weekday(start_date, end_date)
    sales_hr = get_sales_by_hour(start_date, end_date)
    labor_wd = get_labor_by_weekday(start_date, end_date, tasa_horaria)
    labor_hr = get_labor_by_hour(start_date, end_date, tasa_horaria)

    cross = []
    for i in range(7):
        ventas = sales_wd[i]['sum_ventas']
        costo = labor_wd[i]['sum_costo']
        cross.append({
            'dow': i,
            'nombre': DOW_NAMES[i],
            'sum_ventas': ventas,
            'sum_costo': costo,
            'ratio': round(costo / ventas * 100, 1) if ventas > 0 else None
        })

    return jsonify({
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'tasa_horaria': round(tasa_horaria, 2),
        'by_weekday': {
            'ventas': sales_wd,
            'labor': labor_wd,
            'cross': cross
        },
        'by_hour': {
            'ventas': sales_hr,
            'labor': labor_hr
        }
    }), 200
