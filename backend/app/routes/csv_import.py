from flask import Blueprint, jsonify, make_response, request
from io import StringIO
import csv
from datetime import datetime, time
from app.extensions import db
from app.models.user import User
from app.models.employee import Employee
from app.models.time_tracking import TimeTracking
from app.models.work_block import WorkBlock
from app.utils.decorators import admin_required
from app.utils.jwt_utils import token_required

csv_import_bp = Blueprint('csv_import', __name__, url_prefix='/api/v1/csv-import')

@csv_import_bp.route('/status', methods=['GET'])
def status():
    """Check CSV import module status"""
    return jsonify({'status': 'available', 'message': 'CSV import module ready'}), 200

@csv_import_bp.route('/template', methods=['GET'])
def download_template():
    """Download CSV template for time tracking import"""
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['fecha', 'entrada', 'salida', 'mail'])
    
    # Write example rows
    writer.writerow(['5/1/2026', '16:00', '21:15', 'maria.gonzalez@galia.com'])
    writer.writerow(['10/1/2026', '17:00', '21:00', 'maria.gonzalez@galia.com'])
    writer.writerow(['15/1/2026', '16:30', '20:30', 'juan.perez@galia.com'])
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=plantilla_importacion.csv'
    
    return response

@csv_import_bp.route('/time-tracking', methods=['POST'])
@token_required
@admin_required
def import_time_tracking(current_user):
    """Import time tracking data from CSV file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No se encontró archivo en la solicitud'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'El archivo debe ser un CSV'}), 400
    
    try:
        # Read CSV file
        stream = StringIO(file.stream.read().decode('utf-8'))
        csv_reader = csv.DictReader(stream)
        
        results = {
            'total_rows': 0,
            'imported': 0,
            'errors': []
        }
        
        for row_num, row in enumerate(csv_reader, start=2):
            results['total_rows'] += 1
            errors = []
            
            # Validate required fields
            if not row.get('fecha'):
                errors.append('Falta el campo "fecha"')
            if not row.get('entrada'):
                errors.append('Falta el campo "entrada"')
            if not row.get('salida'):
                errors.append('Falta el campo "salida"')
            if not row.get('mail'):
                errors.append('Falta el campo "mail"')
            
            if errors:
                results['errors'].append({
                    'row': row_num,
                    'data': row,
                    'errors': errors
                })
                continue
            
            # Parse date (format: DD/MM/YYYY or D/M/YYYY)
            try:
                date_parts = row['fecha'].strip().split('/')
                if len(date_parts) != 3:
                    raise ValueError('Formato de fecha inválido')
                day, month, year = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
                tracking_date = datetime(year, month, day).date()
            except (ValueError, IndexError) as e:
                errors.append(f'Formato de fecha inválido: {row["fecha"]}. Use DD/MM/YYYY')
                results['errors'].append({
                    'row': row_num,
                    'data': row,
                    'errors': errors
                })
                continue
            
            # Parse times (format: HH:MM)
            try:
                start_parts = row['entrada'].strip().split(':')
                if len(start_parts) != 2:
                    raise ValueError('Formato de hora de entrada inválido')
                start_time = time(int(start_parts[0]), int(start_parts[1]))
            except (ValueError, IndexError) as e:
                errors.append(f'Formato de hora de entrada inválido: {row["entrada"]}. Use HH:MM')
                results['errors'].append({
                    'row': row_num,
                    'data': row,
                    'errors': errors
                })
                continue
            
            try:
                end_parts = row['salida'].strip().split(':')
                if len(end_parts) != 2:
                    raise ValueError('Formato de hora de salida inválido')
                end_time = time(int(end_parts[0]), int(end_parts[1]))
            except (ValueError, IndexError) as e:
                errors.append(f'Formato de hora de salida inválido: {row["salida"]}. Use HH:MM')
                results['errors'].append({
                    'row': row_num,
                    'data': row,
                    'errors': errors
                })
                continue
            
            # Validate start < end
            if start_time >= end_time:
                errors.append('La hora de entrada debe ser anterior a la hora de salida')
                results['errors'].append({
                    'row': row_num,
                    'data': row,
                    'errors': errors
                })
                continue
            
            # Find employee by email
            email = row['mail'].strip()
            user = User.query.filter_by(email=email).first()
            if not user:
                errors.append(f'No se encontró usuario con email: {email}')
                results['errors'].append({
                    'row': row_num,
                    'data': row,
                    'errors': errors
                })
                continue
            
            employee = Employee.query.filter_by(user_id=user.id).first()
            if not employee:
                errors.append(f'No se encontró empleado para el email: {email}')
                results['errors'].append({
                    'row': row_num,
                    'data': row,
                    'errors': errors
                })
                continue
            
            # Get or create TimeTracking record
            time_tracking = TimeTracking.query.filter_by(
                employee_id=employee.id,
                tracking_date=tracking_date
            ).first()
            
            if not time_tracking:
                time_tracking = TimeTracking(
                    employee_id=employee.id,
                    tracking_date=tracking_date
                )
                db.session.add(time_tracking)
                db.session.flush()
            
            # Check for overlapping work blocks
            overlapping = False
            for existing_block in time_tracking.work_blocks:
                if (start_time < existing_block.end_time and end_time > existing_block.start_time):
                    overlapping = True
                    errors.append(f'Bloque de trabajo superpuesto con {existing_block.start_time.strftime("%H:%M")}-{existing_block.end_time.strftime("%H:%M")}')
                    break
            
            if overlapping:
                results['errors'].append({
                    'row': row_num,
                    'data': row,
                    'errors': errors
                })
                continue
            
            # Create work block
            work_block = WorkBlock(
                time_tracking_id=time_tracking.id,
                start_time=start_time,
                end_time=end_time
            )
            db.session.add(work_block)
            results['imported'] += 1
        
        db.session.commit()
        
        return jsonify({'results': results}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"[CSV IMPORT ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error al procesar el archivo: {str(e)}'}), 500
