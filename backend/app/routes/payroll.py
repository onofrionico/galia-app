from flask import Blueprint, request, jsonify, send_file
from functools import wraps
from app.extensions import db
from app.models.payroll import Payroll
from app.models.payroll_claim import PayrollClaim
from app.models.employee import Employee
from app.models.time_tracking import TimeTracking
from app.models.work_block import WorkBlock
from app.models.shift import Shift
from app.models.user import User
from app.utils.jwt_utils import token_required
from app.utils.payroll_utils import (
    calculate_hours_from_time_tracking,
    calculate_scheduled_hours,
    calculate_hours_by_multiplier,
    calculate_employee_cost,
    calculate_payroll_with_multipliers
)
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from decimal import Decimal
import calendar
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

payroll_bp = Blueprint('payroll', __name__, url_prefix='/api/v1/payroll')

def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if not current_user.is_admin:
            return jsonify({'error': 'Se requieren permisos de administrador'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

@payroll_bp.route('/calculate/<int:employee_id>/<int:year>/<int:month>', methods=['GET'])
@token_required
@admin_required
def calculate_payroll(current_user, employee_id, year, month):
    employee = Employee.query.get_or_404(employee_id)
    
    if not employee.job_position or not employee.job_position.hourly_rate:
        return jsonify({'error': 'El empleado no tiene un puesto con tarifa horaria configurada'}), 400
    
    worked_hours, daily_records = calculate_hours_from_time_tracking(employee_id, month, year)
    scheduled_hours, scheduled_records = calculate_scheduled_hours(employee_id, month, year)
    
    hourly_rate = float(employee.job_position.hourly_rate)
    gross_salary = calculate_payroll_with_multipliers(employee_id, month, year, hourly_rate, employee.job_position)
    hours_difference = worked_hours - scheduled_hours
    
    return jsonify({
        'employee_id': employee_id,
        'employee_name': employee.full_name,
        'month': month,
        'year': year,
        'hours_worked': worked_hours,
        'scheduled_hours': scheduled_hours,
        'hours_difference': hours_difference,
        'hourly_rate': hourly_rate,
        'gross_salary': gross_salary,
        'daily_records': daily_records,
        'scheduled_records': scheduled_records
    })

@payroll_bp.route('/generate', methods=['POST'])
@token_required
@admin_required
def generate_payroll(current_user):
    
    data = request.get_json()
    employee_id = data.get('employee_id')
    month = data.get('month')
    year = data.get('year')
    notes = data.get('notes', '')
    custom_hourly_rate = data.get('hourly_rate')
    
    if not all([employee_id, month, year]):
        return jsonify({'error': 'Faltan datos requeridos'}), 400
    
    existing = Payroll.query.filter_by(
        employee_id=employee_id,
        month=month,
        year=year
    ).first()
    
    if existing:
        return jsonify({'error': 'Ya existe una nómina para este empleado en este período'}), 400
    
    employee = Employee.query.get_or_404(employee_id)
    
    if not employee.job_position or not employee.job_position.hourly_rate:
        return jsonify({'error': 'El empleado no tiene un puesto con tarifa horaria configurada'}), 400
    
    worked_hours, _ = calculate_hours_from_time_tracking(employee_id, month, year)
    scheduled_hours, _ = calculate_scheduled_hours(employee_id, month, year)
    
    if custom_hourly_rate is not None:
        hourly_rate = float(custom_hourly_rate)
        if hourly_rate <= 0:
            return jsonify({'error': 'La tarifa horaria debe ser mayor a 0'}), 400
    else:
        hourly_rate = float(employee.job_position.hourly_rate)
    
    gross_salary = calculate_payroll_with_multipliers(employee_id, month, year, hourly_rate, employee.job_position)
    
    payroll = Payroll(
        employee_id=employee_id,
        month=month,
        year=year,
        hours_worked=Decimal(str(worked_hours)),
        scheduled_hours=Decimal(str(scheduled_hours)),
        hourly_rate=Decimal(str(hourly_rate)),
        gross_salary=Decimal(str(gross_salary)),
        status='draft',
        notes=notes,
        generated_by=current_user.id
    )
    
    db.session.add(payroll)
    db.session.commit()
    
    return jsonify(payroll.to_dict()), 200

@payroll_bp.route('/<int:payroll_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_payroll(current_user, payroll_id):
    """Eliminar una nómina (solo si está en estado 'draft')"""
    payroll = Payroll.query.get_or_404(payroll_id)
    
    # Solo permitir eliminar nóminas en borrador
    if payroll.status != 'draft':
        return jsonify({
            'error': 'No se puede eliminar',
            'message': 'Solo las nóminas en estado borrador pueden ser eliminadas'
        }), 400
    
    try:
        db.session.delete(payroll)
        db.session.commit()
        return jsonify({
            'message': 'Nómina eliminada exitosamente',
            'payroll_id': payroll_id
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar nómina: {str(e)}'}), 500

@payroll_bp.route('/', methods=['GET'])
@token_required
@admin_required
def get_payrolls(current_user):
    
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    employee_id = request.args.get('employee_id', type=int)
    status = request.args.get('status')
    
    query = Payroll.query
    
    if month:
        query = query.filter_by(month=month)
    if year:
        query = query.filter_by(year=year)
    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    if status:
        query = query.filter_by(status=status)
    
    payrolls = query.order_by(Payroll.year.desc(), Payroll.month.desc()).all()
    
    return jsonify([p.to_dict() for p in payrolls])

@payroll_bp.route('/<int:payroll_id>', methods=['GET'])
@token_required
@admin_required
def get_payroll_detail(current_user, payroll_id):
    
    payroll = Payroll.query.get_or_404(payroll_id)
    
    worked_hours, daily_records = calculate_hours_from_time_tracking(
        payroll.employee_id, payroll.month, payroll.year
    )
    scheduled_hours, scheduled_records = calculate_scheduled_hours(
        payroll.employee_id, payroll.month, payroll.year
    )
    
    hours_by_type = calculate_hours_by_multiplier(
        payroll.employee_id, payroll.month, payroll.year, payroll.employee.job_position
    )
    
    result = payroll.to_dict(include_details=True)
    result['daily_records'] = daily_records
    result['scheduled_records'] = scheduled_records
    result['hours_by_type'] = hours_by_type
    
    return jsonify(result)

@payroll_bp.route('/<int:payroll_id>', methods=['PUT'])
@token_required
@admin_required
def update_payroll(current_user, payroll_id):
    
    payroll = Payroll.query.get_or_404(payroll_id)
    
    if payroll.status == 'validated':
        return jsonify({'error': 'No se puede modificar una nómina validada'}), 400
    
    data = request.get_json()
    
    if 'notes' in data:
        payroll.notes = data['notes']
    
    if 'extraordinary_amount' in data:
        payroll.extraordinary_amount = Decimal(str(data['extraordinary_amount'])) if data['extraordinary_amount'] else Decimal('0')
    
    if 'extraordinary_description' in data:
        payroll.extraordinary_description = data['extraordinary_description']
    
    if 'recalculate' in data and data['recalculate']:
        worked_hours, _ = calculate_hours_from_time_tracking(
            payroll.employee_id, payroll.month, payroll.year
        )
        scheduled_hours, _ = calculate_scheduled_hours(
            payroll.employee_id, payroll.month, payroll.year
        )
        
        base_salary = calculate_payroll_with_multipliers(
            payroll.employee_id, payroll.month, payroll.year, 
            float(payroll.hourly_rate), payroll.employee.job_position
        )
        
        extraordinary_amount = float(payroll.extraordinary_amount) if payroll.extraordinary_amount else 0
        
        payroll.hours_worked = Decimal(str(worked_hours))
        payroll.scheduled_hours = Decimal(str(scheduled_hours))
        payroll.gross_salary = Decimal(str(base_salary + extraordinary_amount))
    
    db.session.commit()
    
    return jsonify(payroll.to_dict())

@payroll_bp.route('/<int:payroll_id>/validate', methods=['POST'])
@token_required
@admin_required
def validate_payroll(current_user, payroll_id):
    payroll = Payroll.query.get_or_404(payroll_id)
    
    if payroll.status == 'validated':
        return jsonify({'error': 'Esta nómina ya está validada'}), 400
    
    payroll.status = 'validated'
    payroll.validated_at = datetime.utcnow()
    payroll.validated_by = current_user.id
    
    db.session.commit()
    
    return jsonify(payroll.to_dict())

@payroll_bp.route('/<int:payroll_id>/work-blocks', methods=['GET'])
@token_required
@admin_required
def get_payroll_work_blocks(current_user, payroll_id):
    
    payroll = Payroll.query.get_or_404(payroll_id)
    
    start_date = datetime(payroll.year, payroll.month, 1).date()
    if payroll.month == 12:
        end_date = datetime(payroll.year + 1, 1, 1).date()
    else:
        end_date = datetime(payroll.year, payroll.month + 1, 1).date()
    
    time_records = TimeTracking.query.filter(
        TimeTracking.employee_id == payroll.employee_id,
        TimeTracking.tracking_date >= start_date,
        TimeTracking.tracking_date < end_date
    ).order_by(TimeTracking.tracking_date).all()
    
    records = []
    for record in time_records:
        records.append({
            'id': record.id,
            'date': record.tracking_date.isoformat(),
            'work_blocks': [block.to_dict() for block in record.work_blocks]
        })
    
    return jsonify(records)

@payroll_bp.route('/work-blocks/<int:block_id>', methods=['PUT'])
@token_required
@admin_required
def update_work_block(current_user, block_id):
    
    block = WorkBlock.query.get_or_404(block_id)
    data = request.get_json()
    
    if 'start_time' in data:
        try:
            block.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Formato de hora inválido'}), 400
    
    if 'end_time' in data:
        try:
            block.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Formato de hora inválido'}), 400
    
    db.session.commit()
    
    return jsonify(block.to_dict())

@payroll_bp.route('/work-blocks/<int:block_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_work_block(current_user, block_id):
    
    block = WorkBlock.query.get_or_404(block_id)
    
    db.session.delete(block)
    db.session.commit()
    
    return jsonify({'message': 'Bloque eliminado exitosamente'})

@payroll_bp.route('/employees-status/<int:year>/<int:month>', methods=['GET'])
@token_required
@admin_required
def get_employees_payroll_status(current_user, year, month):
    """
    Lista empleados activos con horas registradas en el período,
    mostrando si tienen nómina generada y su estado
    """
    
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()
    
    # Obtener empleados activos
    active_employees = Employee.query.filter_by(status='activo').all()
    
    employees_status = []
    
    for employee in active_employees:
        # Verificar si tiene horas registradas en el período
        time_records = TimeTracking.query.filter(
            TimeTracking.employee_id == employee.id,
            TimeTracking.tracking_date >= start_date,
            TimeTracking.tracking_date < end_date
        ).first()
        
        # Solo incluir empleados con horas registradas
        if time_records:
            # Buscar nómina existente
            payroll = Payroll.query.filter_by(
                employee_id=employee.id,
                month=month,
                year=year
            ).first()
            
            # Calcular horas trabajadas
            worked_hours, _ = calculate_hours_from_time_tracking(employee.id, month, year)
            
            employee_data = {
                'employee_id': employee.id,
                'employee_name': employee.full_name,
                'dni': employee.dni,
                'job_position': employee.job_position.name if employee.job_position else None,
                'hours_worked': worked_hours,
                'has_payroll': payroll is not None,
                'payroll_id': payroll.id if payroll else None,
                'payroll_status': payroll.status if payroll else None,
                'payroll_validated_at': payroll.validated_at.isoformat() if payroll and payroll.validated_at else None,
                'gross_salary': float(payroll.gross_salary) if payroll else None,
                'pdf_generated': payroll.pdf_generated if payroll else False
            }
            
            employees_status.append(employee_data)
    
    # Ordenar por nombre
    employees_status.sort(key=lambda x: x['employee_name'])
    
    return jsonify({
        'year': year,
        'month': month,
        'employees': employees_status,
        'total_employees': len(employees_status),
        'with_payroll': sum(1 for e in employees_status if e['has_payroll']),
        'without_payroll': sum(1 for e in employees_status if not e['has_payroll'])
    })

@payroll_bp.route('/summary/<int:year>/<int:month>', methods=['GET'])
@token_required
@admin_required
def get_monthly_summary(current_user, year, month):
    
    payrolls = Payroll.query.filter_by(year=year, month=month).all()
    
    total_salary = sum(float(p.gross_salary) for p in payrolls)
    total_hours = sum(float(p.hours_worked) for p in payrolls)
    employee_count = len(payrolls)
    validated_count = sum(1 for p in payrolls if p.status == 'validated')
    
    return jsonify({
        'year': year,
        'month': month,
        'total_salary': total_salary,
        'total_hours': total_hours,
        'employee_count': employee_count,
        'validated_count': validated_count,
        'payrolls': [p.to_dict() for p in payrolls]
    })

@payroll_bp.route('/summary/historical', methods=['GET'])
@token_required
@admin_required
def get_historical_summary(current_user):
    
    months = request.args.get('months', 12, type=int)
    
    results = db.session.query(
        Payroll.year,
        Payroll.month,
        func.sum(Payroll.gross_salary).label('total_salary'),
        func.sum(Payroll.hours_worked).label('total_hours'),
        func.count(Payroll.id).label('employee_count')
    ).group_by(
        Payroll.year,
        Payroll.month
    ).order_by(
        Payroll.year.desc(),
        Payroll.month.desc()
    ).limit(months).all()
    
    historical_data = []
    for result in results:
        historical_data.append({
            'year': result.year,
            'month': result.month,
            'month_name': calendar.month_name[result.month],
            'total_salary': float(result.total_salary),
            'total_hours': float(result.total_hours),
            'employee_count': result.employee_count
        })
    
    return jsonify(historical_data)

@payroll_bp.route('/<int:payroll_id>/generate-pdf', methods=['POST'])
@token_required
@admin_required
def generate_payroll_pdf(current_user, payroll_id):
    
    payroll = Payroll.query.get_or_404(payroll_id)
    employee = payroll.employee
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph('COMPROBANTE DE NÓMINA', title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    company_info = [
        ['Cafetería Galia', ''],
        ['Período:', f'{calendar.month_name[payroll.month]} {payroll.year}'],
        ['Fecha de emisión:', datetime.now().strftime('%d/%m/%Y')],
    ]
    
    company_table = Table(company_info, colWidths=[2*inch, 4*inch])
    company_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 14),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#1f2937')),
    ]))
    elements.append(company_table)
    elements.append(Spacer(1, 0.3*inch))
    
    employee_info = [
        ['DATOS DEL EMPLEADO', ''],
        ['Nombre completo:', employee.full_name],
        ['DNI:', employee.dni],
        ['CUIL:', employee.cuil],
        ['Puesto:', employee.job_position.name if employee.job_position else 'N/A'],
        ['Tipo de relación:', employee.employment_relationship],
    ]
    
    employee_table = Table(employee_info, colWidths=[2*inch, 4*inch])
    employee_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 12),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#1f2937')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(employee_table)
    elements.append(Spacer(1, 0.3*inch))
    
    payroll_data = [
        ['DETALLE DE LIQUIDACIÓN', '', ''],
        ['Concepto', 'Cantidad', 'Importe'],
        ['Horas trabajadas', f"{float(payroll.hours_worked):.2f}", ''],
        ['Tarifa por hora', '', f"${float(payroll.hourly_rate):.2f}"],
        ['', '', ''],
        ['TOTAL BRUTO', '', f"${float(payroll.gross_salary):.2f}"],
    ]
    
    payroll_table = Table(payroll_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
    payroll_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 12),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#1f2937')),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f3f4f6')),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#dbeafe')),
        ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 5), (-1, 5), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(payroll_table)
    elements.append(Spacer(1, 0.5*inch))
    
    if payroll.notes:
        elements.append(Paragraph(f'<b>Observaciones:</b> {payroll.notes}', styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
    
    footer_text = f'Documento generado el {datetime.now().strftime("%d/%m/%Y %H:%M")}'
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    doc.build(elements)
    
    pdf_data = buffer.getvalue()
    buffer.close()
    
    pdf_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'payroll_pdfs')
    os.makedirs(pdf_dir, exist_ok=True)
    
    filename = f'nomina_{employee.dni}_{payroll.year}_{payroll.month:02d}.pdf'
    pdf_path = os.path.join(pdf_dir, filename)
    
    with open(pdf_path, 'wb') as f:
        f.write(pdf_data)
    
    payroll.pdf_generated = True
    payroll.pdf_path = pdf_path
    db.session.commit()
    
    return send_file(
        BytesIO(pdf_data),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

@payroll_bp.route('/<int:payroll_id>/pdf', methods=['GET'])
@token_required
@admin_required
def download_payroll_pdf(current_user, payroll_id):
    
    payroll = Payroll.query.get_or_404(payroll_id)
    
    if not payroll.pdf_generated or not payroll.pdf_path or not os.path.exists(payroll.pdf_path):
        return jsonify({'error': 'PDF no disponible. Genere el PDF primero.'}), 404
    
    return send_file(
        payroll.pdf_path,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=os.path.basename(payroll.pdf_path)
    )

# ============================================
# EMPLOYEE ENDPOINTS - Para que empleados vean sus propias nóminas
# ============================================

@payroll_bp.route('/my-payrolls', methods=['GET'])
@token_required
def get_my_payrolls(current_user):
    """Obtener las nóminas del empleado actual"""
    
    # Obtener el empleado asociado al usuario
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    if not employee:
        return jsonify({'error': 'No se encontró un empleado asociado a este usuario'}), 404
    
    # Filtros opcionales
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    status = request.args.get('status')
    
    query = Payroll.query.filter_by(employee_id=employee.id)
    
    if year:
        query = query.filter_by(year=year)
    if month:
        query = query.filter_by(month=month)
    if status:
        query = query.filter_by(status=status)
    
    # Solo mostrar nóminas validadas por admin (status='validated')
    # o que el empleado pueda ver en borrador si el admin lo permite
    payrolls = query.order_by(Payroll.year.desc(), Payroll.month.desc()).all()
    
    return jsonify([p.to_dict() for p in payrolls])

@payroll_bp.route('/my-payrolls/<int:payroll_id>', methods=['GET'])
@token_required
def get_my_payroll_detail(current_user, payroll_id):
    """Obtener detalle de una nómina del empleado actual"""
    
    # Obtener el empleado asociado al usuario
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    if not employee:
        return jsonify({'error': 'No se encontró un empleado asociado a este usuario'}), 404
    
    payroll = Payroll.query.get_or_404(payroll_id)
    
    # Verificar que la nómina pertenece al empleado
    if payroll.employee_id != employee.id:
        return jsonify({'error': 'No tiene permiso para ver esta nómina'}), 403
    
    # Obtener registros detallados
    worked_hours, daily_records = calculate_hours_from_time_tracking(
        payroll.employee_id, payroll.month, payroll.year
    )
    scheduled_hours, scheduled_records = calculate_scheduled_hours(
        payroll.employee_id, payroll.month, payroll.year
    )
    
    result = payroll.to_dict(include_details=True)
    result['daily_records'] = daily_records
    result['scheduled_records'] = scheduled_records
    
    return jsonify(result)

@payroll_bp.route('/my-payrolls/<int:payroll_id>/validate', methods=['POST'])
@token_required
def employee_validate_payroll(current_user, payroll_id):
    """Permitir que el empleado valide/acepte su nómina"""
    
    # Obtener el empleado asociado al usuario
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    if not employee:
        return jsonify({'error': 'No se encontró un empleado asociado a este usuario'}), 404
    
    payroll = Payroll.query.get_or_404(payroll_id)
    
    # Verificar que la nómina pertenece al empleado
    if payroll.employee_id != employee.id:
        return jsonify({'error': 'No tiene permiso para validar esta nómina'}), 403
    
    # Verificar que la nómina ya fue validada por el admin
    if payroll.status != 'validated':
        return jsonify({'error': 'La nómina debe ser validada primero por el administrador'}), 400
    
    # Verificar si ya fue aceptada por el empleado
    if payroll.employee_validated_at:
        return jsonify({'error': 'Esta nómina ya fue aceptada por usted'}), 400
    
    # Marcar como aceptada por el empleado
    payroll.employee_validated_at = datetime.utcnow()
    payroll.employee_validated_by = current_user.id
    
    db.session.commit()
    
    return jsonify({
        'message': 'Nómina aceptada exitosamente',
        'payroll': payroll.to_dict()
    })

@payroll_bp.route('/my-payrolls/<int:payroll_id>/pdf', methods=['GET'])
@token_required
def download_my_payroll_pdf(current_user, payroll_id):
    """Descargar PDF de nómina del empleado actual"""
    
    # Obtener el empleado asociado al usuario
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    if not employee:
        return jsonify({'error': 'No se encontró un empleado asociado a este usuario'}), 404
    
    payroll = Payroll.query.get_or_404(payroll_id)
    
    # Verificar que la nómina pertenece al empleado
    if payroll.employee_id != employee.id:
        return jsonify({'error': 'No tiene permiso para descargar esta nómina'}), 403
    
    # Verificar que el PDF existe
    if not payroll.pdf_generated or not payroll.pdf_path or not os.path.exists(payroll.pdf_path):
        return jsonify({'error': 'PDF no disponible'}), 404
    
    return send_file(
        payroll.pdf_path,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=os.path.basename(payroll.pdf_path)
    )

@payroll_bp.route('/my-payrolls/<int:payroll_id>/claim', methods=['POST'])
@token_required
def create_payroll_claim(current_user, payroll_id):
    """Crear un reclamo sobre una nómina validada"""
    
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    if not employee:
        return jsonify({'error': 'No se encontró un empleado asociado a este usuario'}), 404
    
    payroll = Payroll.query.get_or_404(payroll_id)
    
    if payroll.employee_id != employee.id:
        return jsonify({'error': 'No tiene permiso para reclamar esta nómina'}), 403
    
    if payroll.status != 'validated':
        return jsonify({'error': 'Solo se pueden reclamar nóminas validadas'}), 400
    
    if payroll.employee_validated_at:
        return jsonify({'error': 'No puede reclamar una nómina que ya aceptó'}), 400
    
    existing_claim = PayrollClaim.query.filter_by(
        payroll_id=payroll_id,
        status='pending'
    ).first()
    
    if existing_claim:
        return jsonify({'error': 'Ya existe un reclamo pendiente para esta nómina'}), 400
    
    data = request.get_json()
    claim_reason = data.get('claim_reason', '').strip()
    
    if not claim_reason:
        return jsonify({'error': 'Debe proporcionar un motivo para el reclamo'}), 400
    
    claim = PayrollClaim(
        payroll_id=payroll_id,
        employee_id=employee.id,
        claim_reason=claim_reason,
        status='pending',
        created_by=current_user.id
    )
    
    db.session.add(claim)
    db.session.commit()
    
    return jsonify({
        'message': 'Reclamo creado exitosamente',
        'claim': claim.to_dict()
    }), 201

@payroll_bp.route('/my-payrolls/<int:payroll_id>/claims', methods=['GET'])
@token_required
def get_my_payroll_claims(current_user, payroll_id):
    """Obtener reclamos de una nómina del empleado"""
    
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    if not employee:
        return jsonify({'error': 'No se encontró un empleado asociado a este usuario'}), 404
    
    payroll = Payroll.query.get_or_404(payroll_id)
    
    if payroll.employee_id != employee.id:
        return jsonify({'error': 'No tiene permiso para ver estos reclamos'}), 403
    
    claims = PayrollClaim.query.filter_by(payroll_id=payroll_id).order_by(PayrollClaim.created_at.desc()).all()
    
    return jsonify([claim.to_dict() for claim in claims])

# ============================================
# ADMIN CLAIM MANAGEMENT ENDPOINTS
# ============================================

@payroll_bp.route('/claims', methods=['GET'])
@token_required
@admin_required
def get_all_claims(current_user):
    """Obtener todos los reclamos de nóminas"""
    
    status = request.args.get('status')
    employee_id = request.args.get('employee_id', type=int)
    
    query = PayrollClaim.query
    
    if status:
        query = query.filter_by(status=status)
    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    
    claims = query.order_by(PayrollClaim.created_at.desc()).all()
    
    return jsonify([claim.to_dict() for claim in claims])

@payroll_bp.route('/claims/<int:claim_id>', methods=['GET'])
@token_required
@admin_required
def get_claim_detail(current_user, claim_id):
    """Obtener detalle de un reclamo"""
    
    claim = PayrollClaim.query.get_or_404(claim_id)
    
    return jsonify(claim.to_dict())

@payroll_bp.route('/claims/<int:claim_id>/respond', methods=['POST'])
@token_required
@admin_required
def respond_to_claim(current_user, claim_id):
    """Responder a un reclamo y ajustar la nómina si es necesario"""
    
    claim = PayrollClaim.query.get_or_404(claim_id)
    
    if claim.status != 'pending':
        return jsonify({'error': 'Este reclamo ya fue procesado'}), 400
    
    data = request.get_json()
    admin_response = data.get('admin_response', '').strip()
    action = data.get('action')
    
    if not admin_response:
        return jsonify({'error': 'Debe proporcionar una respuesta'}), 400
    
    if action not in ['approve', 'reject']:
        return jsonify({'error': 'Acción inválida. Use "approve" o "reject"'}), 400
    
    claim.admin_response = admin_response
    claim.resolved_at = datetime.utcnow()
    claim.resolved_by = current_user.id
    
    if action == 'approve':
        claim.status = 'approved'
        payroll = claim.payroll
        payroll.status = 'draft'
        payroll.validated_at = None
        payroll.validated_by = None
        payroll.employee_validated_at = None
        payroll.employee_validated_by = None
    else:
        claim.status = 'rejected'
    
    db.session.commit()
    
    return jsonify({
        'message': f'Reclamo {action == "approve" and "aprobado" or "rechazado"} exitosamente',
        'claim': claim.to_dict()
    })
