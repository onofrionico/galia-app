from flask import Blueprint, request, jsonify
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import func, and_, or_, extract
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
    """Obtener métricas principales del dashboard"""
    period_type = request.args.get('period', 'mensual')
    date_str = request.args.get('date')
    
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
        'goals': goals
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
    
    # Gastos por tipo (directo/indirecto) - basado en categoría del gasto
    # Por ahora clasificamos según el campo categoria del expense
    directos_keywords = ['mercaderia', 'mercadería', 'directo', 'insumo', 'materia', 'producto']
    
    directos = 0
    indirectos = 0
    
    expenses = Expense.query.filter(
        Expense.fecha >= start_date,
        Expense.fecha <= end_date,
        Expense.cancelado == False
    ).all()
    
    for exp in expenses:
        cat = (exp.categoria or '').lower()
        if any(kw in cat for kw in directos_keywords):
            directos += float(exp.importe)
        else:
            indirectos += float(exp.importe)
    
    return {
        'total': total,
        'directos': directos,
        'indirectos': indirectos
    }


def get_payroll_metrics(start_date, end_date):
    """Calcular métricas de sueldos/payroll para un período"""
    # Determinar mes y año del período
    # Si el período es mensual, buscamos payrolls de ese mes
    start_month = start_date.month
    start_year = start_date.year
    end_month = end_date.month
    end_year = end_date.year
    
    # Obtener payrolls del período
    query = Payroll.query.filter(
        or_(
            and_(Payroll.year == start_year, Payroll.month >= start_month),
            Payroll.year > start_year
        ),
        or_(
            and_(Payroll.year == end_year, Payroll.month <= end_month),
            Payroll.year < end_year
        )
    )
    
    payrolls = query.all()
    
    total = sum(float(p.gross_salary) for p in payrolls)
    horas = sum(float(p.hours_worked) for p in payrolls)
    
    return {
        'total': total,
        'horas': horas
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


# ==================== REPORTE DE GASTOS ====================

@bp.route('/expenses', methods=['GET'])
@token_required
@admin_required
def expenses_report(current_user):
    """Reporte detallado de gastos"""
    start_date = parse_date(request.args.get('start_date'))
    end_date = parse_date(request.args.get('end_date'))
    categoria = request.args.get('categoria')
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
    
    if categoria:
        query = query.filter(Expense.categoria.ilike(f'%{categoria}%'))
    if proveedor:
        query = query.filter(Expense.proveedor.ilike(f'%{proveedor}%'))
    
    expenses = query.all()
    
    total = sum(float(e.importe) for e in expenses)
    
    # Clasificar en directos/indirectos
    directos_keywords = ['mercaderia', 'mercadería', 'directo', 'insumo', 'materia', 'producto']
    directos = 0
    indirectos = 0
    
    by_category = {}
    by_supplier = {}
    
    for e in expenses:
        cat = e.categoria or 'Sin categoría'
        prov = e.proveedor or 'Sin proveedor'
        importe = float(e.importe)
        
        # Clasificar
        if any(kw in cat.lower() for kw in directos_keywords):
            directos += importe
        else:
            indirectos += importe
        
        # Agrupar por categoría
        if cat not in by_category:
            by_category[cat] = {'total': 0, 'count': 0}
        by_category[cat]['total'] += importe
        by_category[cat]['count'] += 1
        
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
