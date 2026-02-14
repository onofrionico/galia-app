from flask import Blueprint, request, jsonify, Response
from app.extensions import db
from app.models.expense import Expense, ExpenseCategory
from app.utils.decorators import admin_required
from app.utils.jwt_utils import token_required
from datetime import datetime
from sqlalchemy import func
import csv
import io

bp = Blueprint('expenses', __name__, url_prefix='/api/v1/expenses')

@bp.route('', methods=['GET'])
@token_required
@admin_required
def get_expenses(current_user):
    """Get expenses with optional filtering and pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    proveedor = request.args.get('proveedor')
    categoria = request.args.get('categoria')
    estado_pago = request.args.get('estado_pago')
    medio_pago = request.args.get('medio_pago')
    
    query = Expense.query
    
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            query = query.filter(Expense.fecha >= fecha_desde_dt)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            query = query.filter(Expense.fecha <= fecha_hasta_dt)
        except ValueError:
            pass
    
    if proveedor:
        query = query.filter(Expense.proveedor.ilike(f'%{proveedor}%'))
    
    if categoria:
        query = query.filter(Expense.categoria == categoria)
    
    if estado_pago:
        query = query.filter(Expense.estado_pago == estado_pago)
    
    if medio_pago:
        query = query.filter(Expense.medio_pago == medio_pago)
    
    total = query.count()
    expenses = query.order_by(Expense.fecha.desc(), Expense.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'expenses': [expense.to_dict() for expense in expenses.items],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': expenses.pages
    }), 200


@bp.route('/stats', methods=['GET'])
@token_required
@admin_required
def get_expense_stats(current_user):
    """Get expense statistics"""
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    
    query = Expense.query.filter(Expense.cancelado == False)
    
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            query = query.filter(Expense.fecha >= fecha_desde_dt)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            query = query.filter(Expense.fecha <= fecha_hasta_dt)
        except ValueError:
            pass
    
    total_gastos = query.count()
    total_importe = query.with_entities(func.sum(Expense.importe)).scalar() or 0
    
    por_categoria = db.session.query(
        Expense.categoria,
        func.count(Expense.id).label('cantidad'),
        func.sum(Expense.importe).label('total')
    ).filter(Expense.cancelado == False)
    
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            por_categoria = por_categoria.filter(Expense.fecha >= fecha_desde_dt)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            por_categoria = por_categoria.filter(Expense.fecha <= fecha_hasta_dt)
        except ValueError:
            pass
    
    por_categoria = por_categoria.group_by(Expense.categoria).all()
    
    por_medio_pago = db.session.query(
        Expense.medio_pago,
        func.count(Expense.id).label('cantidad'),
        func.sum(Expense.importe).label('total')
    ).filter(Expense.cancelado == False)
    
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            por_medio_pago = por_medio_pago.filter(Expense.fecha >= fecha_desde_dt)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            por_medio_pago = por_medio_pago.filter(Expense.fecha <= fecha_hasta_dt)
        except ValueError:
            pass
    
    por_medio_pago = por_medio_pago.group_by(Expense.medio_pago).all()
    
    por_proveedor = db.session.query(
        Expense.proveedor,
        func.count(Expense.id).label('cantidad'),
        func.sum(Expense.importe).label('total')
    ).filter(Expense.cancelado == False)
    
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            por_proveedor = por_proveedor.filter(Expense.fecha >= fecha_desde_dt)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            por_proveedor = por_proveedor.filter(Expense.fecha <= fecha_hasta_dt)
        except ValueError:
            pass
    
    por_proveedor = por_proveedor.group_by(Expense.proveedor).order_by(func.sum(Expense.importe).desc()).limit(10).all()
    
    return jsonify({
        'total_gastos': total_gastos,
        'total_importe': float(total_importe),
        'por_categoria': [{'categoria': c or 'Sin categoría', 'cantidad': cant, 'total': float(tot or 0)} for c, cant, tot in por_categoria],
        'por_medio_pago': [{'medio_pago': m or 'Sin especificar', 'cantidad': cant, 'total': float(tot or 0)} for m, cant, tot in por_medio_pago],
        'top_proveedores': [{'proveedor': p or 'Sin proveedor', 'cantidad': cant, 'total': float(tot or 0)} for p, cant, tot in por_proveedor]
    }), 200


@bp.route('', methods=['POST'])
@token_required
@admin_required
def create_expense(current_user):
    """Create a new expense"""
    data = request.get_json()
    
    if not data.get('fecha'):
        return jsonify({'error': 'La fecha es requerida'}), 400
    
    if not data.get('importe'):
        return jsonify({'error': 'El importe es requerido'}), 400
    
    try:
        fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400
    
    fecha_vencimiento = None
    if data.get('fecha_vencimiento'):
        try:
            fecha_vencimiento = datetime.strptime(data['fecha_vencimiento'], '%Y-%m-%d').date()
        except ValueError:
            pass
    
    expense = Expense(
        fecha=fecha,
        fecha_vencimiento=fecha_vencimiento,
        proveedor=data.get('proveedor'),
        categoria=data.get('categoria'),
        subcategoria=data.get('subcategoria'),
        comentario=data.get('comentario'),
        estado_pago=data.get('estado_pago', 'Pendiente'),
        importe=data.get('importe', 0),
        de_caja=data.get('de_caja', False),
        caja=data.get('caja'),
        medio_pago=data.get('medio_pago'),
        numero_fiscal=data.get('numero_fiscal'),
        tipo_comprobante=data.get('tipo_comprobante'),
        numero_comprobante=data.get('numero_comprobante'),
        creado_por=data.get('creado_por', current_user.username if hasattr(current_user, 'username') else 'Sistema'),
        cancelado=data.get('cancelado', False)
    )
    
    db.session.add(expense)
    db.session.commit()
    
    return jsonify(expense.to_dict()), 201


@bp.route('/<int:expense_id>', methods=['GET'])
@token_required
@admin_required
def get_expense(current_user, expense_id):
    """Get a single expense by ID"""
    expense = Expense.query.get_or_404(expense_id)
    return jsonify(expense.to_dict()), 200


@bp.route('/<int:expense_id>', methods=['PUT'])
@token_required
@admin_required
def update_expense(current_user, expense_id):
    """Update an expense"""
    expense = Expense.query.get_or_404(expense_id)
    data = request.get_json()
    
    if data.get('fecha'):
        try:
            expense.fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    if data.get('fecha_vencimiento'):
        try:
            expense.fecha_vencimiento = datetime.strptime(data['fecha_vencimiento'], '%Y-%m-%d').date()
        except ValueError:
            pass
    elif 'fecha_vencimiento' in data and not data['fecha_vencimiento']:
        expense.fecha_vencimiento = None
    
    updatable_fields = ['proveedor', 'categoria', 'subcategoria', 'comentario',
                        'estado_pago', 'importe', 'de_caja', 'caja', 'medio_pago',
                        'numero_fiscal', 'tipo_comprobante', 'numero_comprobante',
                        'creado_por', 'cancelado']
    
    for field in updatable_fields:
        if field in data:
            setattr(expense, field, data[field])
    
    db.session.commit()
    return jsonify(expense.to_dict()), 200


@bp.route('/<int:expense_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_expense(current_user, expense_id):
    """Delete an expense"""
    expense = Expense.query.get_or_404(expense_id)
    db.session.delete(expense)
    db.session.commit()
    return jsonify({'message': 'Gasto eliminado correctamente'}), 200


@bp.route('/import', methods=['POST'])
@token_required
@admin_required
def import_expenses(current_user):
    """Import expenses from CSV file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'El archivo debe ser un CSV'}), 400
    
    try:
        stream = io.StringIO(file.stream.read().decode('utf-8-sig'))
        reader = csv.DictReader(stream)
        
        results = {
            'total_rows': 0,
            'imported': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }
        
        for row_num, row in enumerate(reader, start=2):
            results['total_rows'] += 1
            
            try:
                external_id = row.get('Id', '').strip()
                
                if external_id:
                    existing = Expense.query.filter_by(external_id=int(external_id)).first()
                    if existing:
                        results['skipped'] += 1
                        continue
                
                expense = Expense.from_csv_row(row)
                
                if not expense.fecha:
                    results['errors'].append({
                        'row': row_num,
                        'data': dict(row),
                        'errors': ['La fecha es requerida o tiene formato inválido']
                    })
                    continue
                
                db.session.add(expense)
                results['imported'] += 1
                
            except Exception as e:
                results['errors'].append({
                    'row': row_num,
                    'data': dict(row),
                    'errors': [str(e)]
                })
        
        db.session.commit()
        
        return jsonify({
            'message': f"Importación completada: {results['imported']} registros importados",
            'results': results
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error procesando el archivo: {str(e)}'}), 500


@bp.route('/export', methods=['GET'])
@token_required
@admin_required
def export_expenses(current_user):
    """Export expenses to CSV"""
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    
    query = Expense.query
    
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            query = query.filter(Expense.fecha >= fecha_desde_dt)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            query = query.filter(Expense.fecha <= fecha_hasta_dt)
        except ValueError:
            pass
    
    expenses = query.order_by(Expense.fecha.desc(), Expense.id.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Id', 'Fecha', 'Fecha de vencimiento', 'Proveedor', 'Categoría', 
        'Subcategoría', 'Comentario', 'Estado del pago', 'Importe', 'De Caja',
        'Caja', 'Medio de pago', 'Número Fiscal', 'Tipo de comprobante',
        'N° de comprobante', 'Creado por', 'Cancelado'
    ])
    
    for expense in expenses:
        writer.writerow([
            expense.external_id or expense.id,
            expense.fecha.strftime('%d/%m/%Y') if expense.fecha else '',
            expense.fecha_vencimiento.strftime('%d/%m/%Y') if expense.fecha_vencimiento else '',
            expense.proveedor or '',
            expense.categoria or '',
            expense.subcategoria or '',
            expense.comentario or '',
            expense.estado_pago or '',
            expense.importe or 0,
            'Sí' if expense.de_caja else 'No',
            expense.caja or '',
            expense.medio_pago or '',
            expense.numero_fiscal or '',
            expense.tipo_comprobante or '',
            expense.numero_comprobante or '',
            expense.creado_por or '',
            'Sí' if expense.cancelado else 'No'
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=gastos_export.csv'}
    )


@bp.route('/filters', methods=['GET'])
@token_required
@admin_required
def get_filter_options(current_user):
    """Get available filter options"""
    categorias = db.session.query(Expense.categoria).distinct().all()
    proveedores = db.session.query(Expense.proveedor).distinct().all()
    estados_pago = db.session.query(Expense.estado_pago).distinct().all()
    medios_pago = db.session.query(Expense.medio_pago).distinct().all()
    
    return jsonify({
        'categorias': [c[0] for c in categorias if c[0]],
        'proveedores': [p[0] for p in proveedores if p[0]],
        'estados_pago': [e[0] for e in estados_pago if e[0]],
        'medios_pago': [m[0] for m in medios_pago if m[0]]
    }), 200


@bp.route('/categories', methods=['GET'])
@token_required
def get_categories(current_user):
    categories = ExpenseCategory.query.filter_by(is_active=True).all()
    return jsonify([category.to_dict() for category in categories]), 200
