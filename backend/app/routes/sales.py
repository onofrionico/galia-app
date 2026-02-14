from flask import Blueprint, request, jsonify, Response
from app.extensions import db
from app.models.sale import Sale
from app.utils.jwt_utils import token_required
from datetime import datetime, date
from sqlalchemy import func, extract
import csv
import io

bp = Blueprint('sales', __name__, url_prefix='/api/v1/sales')

@bp.route('', methods=['GET'])
@token_required
def get_sales(current_user):
    """Get sales with optional filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    estado = request.args.get('estado')
    tipo_venta = request.args.get('tipo_venta')
    origen = request.args.get('origen')
    
    query = Sale.query
    
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            query = query.filter(Sale.fecha >= fecha_desde_dt)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            query = query.filter(Sale.fecha <= fecha_hasta_dt)
        except ValueError:
            pass
    
    if estado:
        query = query.filter(Sale.estado == estado)
    
    if tipo_venta:
        query = query.filter(Sale.tipo_venta == tipo_venta)
    
    if origen:
        query = query.filter(Sale.origen == origen)
    
    total = query.count()
    sales = query.order_by(Sale.fecha.desc(), Sale.creacion.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'sales': [sale.to_dict() for sale in sales.items],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': sales.pages
    }), 200


@bp.route('/stats', methods=['GET'])
@token_required
def get_sales_stats(current_user):
    """Get sales statistics"""
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    
    query = Sale.query
    
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            query = query.filter(Sale.fecha >= fecha_desde_dt)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            query = query.filter(Sale.fecha <= fecha_hasta_dt)
        except ValueError:
            pass
    
    total_ventas = query.count()
    total_monto = query.with_entities(func.sum(Sale.total)).scalar() or 0
    
    # Stats by tipo_venta
    por_tipo = db.session.query(
        Sale.tipo_venta,
        func.count(Sale.id).label('cantidad'),
        func.sum(Sale.total).label('total')
    ).filter(query.whereclause if query.whereclause is not None else True).group_by(Sale.tipo_venta).all()
    
    # Stats by medio_pago
    por_medio_pago = db.session.query(
        Sale.medio_pago,
        func.count(Sale.id).label('cantidad'),
        func.sum(Sale.total).label('total')
    ).filter(query.whereclause if query.whereclause is not None else True).group_by(Sale.medio_pago).all()
    
    # Stats by estado
    por_estado = db.session.query(
        Sale.estado,
        func.count(Sale.id).label('cantidad'),
        func.sum(Sale.total).label('total')
    ).filter(query.whereclause if query.whereclause is not None else True).group_by(Sale.estado).all()
    
    # Stats by origen
    por_origen = db.session.query(
        Sale.origen,
        func.count(Sale.id).label('cantidad'),
        func.sum(Sale.total).label('total')
    ).filter(query.whereclause if query.whereclause is not None else True).group_by(Sale.origen).all()
    
    return jsonify({
        'total_ventas': total_ventas,
        'total_monto': float(total_monto),
        'por_tipo': [{'tipo': t or 'Sin tipo', 'cantidad': c, 'total': float(tot or 0)} for t, c, tot in por_tipo],
        'por_medio_pago': [{'medio_pago': m or 'Sin especificar', 'cantidad': c, 'total': float(tot or 0)} for m, c, tot in por_medio_pago],
        'por_estado': [{'estado': e, 'cantidad': c, 'total': float(tot or 0)} for e, c, tot in por_estado],
        'por_origen': [{'origen': o or 'Directo', 'cantidad': c, 'total': float(tot or 0)} for o, c, tot in por_origen]
    }), 200


@bp.route('', methods=['POST'])
@token_required
def create_sale(current_user):
    """Create a new sale"""
    data = request.get_json()
    
    if not data.get('fecha'):
        return jsonify({'error': 'La fecha es requerida'}), 400
    
    try:
        fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400
    
    creacion = datetime.now()
    if data.get('creacion'):
        try:
            creacion = datetime.strptime(data['creacion'], '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            try:
                creacion = datetime.strptime(data['creacion'], '%Y-%m-%dT%H:%M')
            except ValueError:
                pass
    
    cerrada = None
    if data.get('cerrada'):
        try:
            cerrada = datetime.strptime(data['cerrada'], '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            try:
                cerrada = datetime.strptime(data['cerrada'], '%Y-%m-%dT%H:%M')
            except ValueError:
                pass
    
    sale = Sale(
        external_id=data.get('external_id'),
        fecha=fecha,
        creacion=creacion,
        cerrada=cerrada,
        caja=data.get('caja'),
        estado=data.get('estado', 'Cerrada'),
        cliente=data.get('cliente'),
        mesa=data.get('mesa'),
        sala=data.get('sala'),
        personas=data.get('personas'),
        camarero=data.get('camarero'),
        medio_pago=data.get('medio_pago'),
        total=data.get('total', 0),
        fiscal=data.get('fiscal', False),
        tipo_venta=data.get('tipo_venta', 'Local'),
        comentario=data.get('comentario'),
        origen=data.get('origen'),
        id_origen=data.get('id_origen')
    )
    
    db.session.add(sale)
    db.session.commit()
    
    return jsonify(sale.to_dict()), 201


@bp.route('/<int:sale_id>', methods=['GET'])
@token_required
def get_sale(current_user, sale_id):
    """Get a single sale by ID"""
    sale = Sale.query.get_or_404(sale_id)
    return jsonify(sale.to_dict()), 200


@bp.route('/<int:sale_id>', methods=['PUT'])
@token_required
def update_sale(current_user, sale_id):
    """Update a sale"""
    sale = Sale.query.get_or_404(sale_id)
    data = request.get_json()
    
    if data.get('fecha'):
        try:
            sale.fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    if data.get('cerrada'):
        try:
            sale.cerrada = datetime.strptime(data['cerrada'], '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            try:
                sale.cerrada = datetime.strptime(data['cerrada'], '%Y-%m-%dT%H:%M')
            except ValueError:
                pass
    
    updatable_fields = ['caja', 'estado', 'cliente', 'mesa', 'sala', 'personas',
                        'camarero', 'medio_pago', 'total', 'fiscal', 'tipo_venta',
                        'comentario', 'origen', 'id_origen']
    
    for field in updatable_fields:
        if field in data:
            setattr(sale, field, data[field])
    
    db.session.commit()
    return jsonify(sale.to_dict()), 200


@bp.route('/<int:sale_id>', methods=['DELETE'])
@token_required
def delete_sale(current_user, sale_id):
    """Delete a sale"""
    sale = Sale.query.get_or_404(sale_id)
    db.session.delete(sale)
    db.session.commit()
    return jsonify({'message': 'Venta eliminada correctamente'}), 200


@bp.route('/import', methods=['POST'])
@token_required
def import_sales(current_user):
    """Import sales from CSV file"""
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
                    existing = Sale.query.filter_by(external_id=int(external_id)).first()
                    if existing:
                        results['skipped'] += 1
                        continue
                
                sale = Sale.from_csv_row(row)
                
                if not sale.fecha:
                    results['errors'].append({
                        'row': row_num,
                        'data': dict(row),
                        'errors': ['La fecha es requerida o tiene formato inválido']
                    })
                    continue
                
                db.session.add(sale)
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
def export_sales(current_user):
    """Export sales to CSV"""
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    
    query = Sale.query
    
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            query = query.filter(Sale.fecha >= fecha_desde_dt)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            query = query.filter(Sale.fecha <= fecha_hasta_dt)
        except ValueError:
            pass
    
    sales = query.order_by(Sale.fecha.desc(), Sale.creacion.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Id', 'Fecha', 'Creación', 'Cerrada', 'Caja', 'Estado', 'Cliente',
        'Mesa', 'Sala', 'Personas', 'Camarero / Repartidor', 'Medio de Pago',
        'Total', 'Fiscal', 'Tipo de Venta', 'Comentario', 'Origen', 'Id. Origen'
    ])
    
    for sale in sales:
        writer.writerow([
            sale.external_id or sale.id,
            sale.fecha.strftime('%d/%m/%Y') if sale.fecha else '',
            sale.creacion.strftime('%d/%m/%Y %H:%M:%S') if sale.creacion else '',
            sale.cerrada.strftime('%d/%m/%Y %H:%M:%S') if sale.cerrada else '',
            sale.caja or '',
            sale.estado or '',
            sale.cliente or '',
            sale.mesa or '',
            sale.sala or '',
            sale.personas or '',
            sale.camarero or '',
            sale.medio_pago or '',
            sale.total or 0,
            'Si' if sale.fiscal else 'No',
            sale.tipo_venta or '',
            sale.comentario or '',
            sale.origen or '',
            sale.id_origen or ''
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=ventas_export.csv'}
    )


@bp.route('/filters', methods=['GET'])
@token_required
def get_filter_options(current_user):
    """Get available filter options"""
    estados = db.session.query(Sale.estado).distinct().all()
    tipos_venta = db.session.query(Sale.tipo_venta).distinct().all()
    origenes = db.session.query(Sale.origen).distinct().all()
    salas = db.session.query(Sale.sala).distinct().all()
    medios_pago = db.session.query(Sale.medio_pago).distinct().all()
    
    return jsonify({
        'estados': [e[0] for e in estados if e[0]],
        'tipos_venta': [t[0] for t in tipos_venta if t[0]],
        'origenes': [o[0] for o in origenes if o[0]],
        'salas': [s[0] for s in salas if s[0]],
        'medios_pago': [m[0] for m in medios_pago if m[0]]
    }), 200
