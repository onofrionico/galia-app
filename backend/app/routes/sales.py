from flask import Blueprint, request, jsonify, Response
from app.extensions import db
from app.models.sale import Sale
from app.models.payment import Payment
from app.models.mesa import Mesa
from app.models.product_variant import ProductVariant
from app.models.sale_item import SaleItem
from app.services.stock_service import deduct_stock_for_sale
from app.utils.jwt_utils import token_required
from app.utils.decorators import admin_required
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import func, extract
import csv
import io
import pytz

bp = Blueprint('sales', __name__, url_prefix='/api/v1/sales')

@bp.route('', methods=['GET'])
@token_required
@admin_required
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
            return jsonify({'error': 'Formato de fecha_desde inválido. Use YYYY-MM-DD'}), 400
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            query = query.filter(Sale.fecha <= fecha_hasta_dt)
        except ValueError:
            return jsonify({'error': 'Formato de fecha_hasta inválido. Use YYYY-MM-DD'}), 400
    
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
@admin_required
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
            return jsonify({'error': 'Formato de fecha_desde inválido. Use YYYY-MM-DD'}), 400
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            query = query.filter(Sale.fecha <= fecha_hasta_dt)
        except ValueError:
            return jsonify({'error': 'Formato de fecha_hasta inválido. Use YYYY-MM-DD'}), 400
    
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


@bp.route('/create-from-items', methods=['POST'])
@token_required
def create_sale_from_items(current_user):
    """
    Crear una venta nueva con items y deducción automática de stock.
    Body: {
      "items": [{"product_variant_id": int, "quantity": int}, ...],
      "mesa_id": int (opcional),
      "medio_pago": str (default: "Efectivo")
    }
    """
    data = request.get_json() or {}
    items = data.get('items', [])
    mesa_id = data.get('mesa_id')
    medio_pago = data.get('medio_pago', 'Efectivo')

    if not items:
        return jsonify({'error': 'Al menos un item es requerido'}), 400

    try:
        deduct_stock_for_sale(items)
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

    sale = Sale(
        fecha=date.today(),
        creacion=datetime.utcnow(),
        medio_pago=medio_pago,
        source='galia',
        mesa_id=mesa_id,
        total=Decimal(0),
        estado='En curso',
        tipo_venta='Local',
    )

    total = Decimal(0)
    for item in items:
        variant = ProductVariant.query.get(item['product_variant_id'])
        quantity = item['quantity']
        unit_price = variant.price
        subtotal = Decimal(str(unit_price)) * quantity
        total += subtotal

        sale_item = SaleItem(
            sale=sale,
            product_variant_id=variant.id,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=subtotal,
        )
        db.session.add(sale_item)

    sale.total = total
    db.session.add(sale)
    db.session.commit()

    return jsonify(sale.to_dict()), 201


@bp.route('', methods=['POST'])
@token_required
def create_sale(current_user):
    """Create a new sale"""
    data = request.get_json()

    fecha = datetime.utcnow().date()

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
        camarero_nombre=data.get('camarero_nombre'),
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
    """Obtener detalle de venta con items"""
    sale = Sale.query.get_or_404(sale_id)
    data = sale.to_dict()
    items = SaleItem.query.filter_by(sale_id=sale_id).all()
    data['items'] = [i.to_dict() for i in items]
    return jsonify(data), 200


@bp.route('/<int:sale_id>', methods=['PUT'])
@token_required
def update_sale(current_user, sale_id):
    """Update a sale with legacy and enhanced fields"""
    sale = Sale.query.get_or_404(sale_id)
    data = request.get_json() or {}

    # Legacy fields (original CSV-based fields)
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

    legacy_fields = ['caja', 'estado', 'cliente', 'mesa', 'sala', 'personas',
                     'camarero_nombre', 'camarero_id', 'medio_pago', 'total', 'fiscal', 'tipo_venta',
                     'comentario', 'origen', 'id_origen']

    for field in legacy_fields:
        if field in data:
            setattr(sale, field, data[field])

    # Enhanced sale flow fields (Task 6)
    if 'numero_personas' in data:
        try:
            sale.numero_personas = int(data['numero_personas'])
        except (ValueError, TypeError):
            return jsonify({'error': 'numero_personas must be an integer'}), 400

    if 'comentarios' in data:
        sale.comentarios = data['comentarios']

    if 'status' in data:
        if data['status'] not in ['abierta', 'pagando', 'cerrada']:
            return jsonify({'error': 'status must be one of: abierta, pagando, cerrada'}), 400
        sale.status = data['status']

    if 'descuento_tipo' in data:
        sale.descuento_tipo = data['descuento_tipo']
        if data['descuento_tipo'] == 'porcentaje':
            try:
                valor = float(data.get('descuento_valor', 0))
                sale.descuento_valor = valor
                sale.descuento_monto = float(sale.total) * (valor / 100)
            except (ValueError, TypeError):
                return jsonify({'error': 'descuento_valor must be a valid number'}), 400
        elif data['descuento_tipo'] == 'monto_fijo':
            try:
                valor = float(data.get('descuento_valor', 0))
                sale.descuento_valor = valor
                sale.descuento_monto = valor
            except (ValueError, TypeError):
                return jsonify({'error': 'descuento_valor must be a valid number'}), 400
        else:
            return jsonify({'error': 'descuento_tipo must be porcentaje or monto_fijo'}), 400

    db.session.commit()
    return jsonify(sale.to_dict()), 200


@bp.route('/<int:sale_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_sale(current_user, sale_id):
    """Delete a sale"""
    sale = Sale.query.get_or_404(sale_id)
    db.session.delete(sale)
    db.session.commit()
    return jsonify({'message': 'Venta eliminada correctamente'}), 200


@bp.route('/import', methods=['POST'])
@token_required
@admin_required
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
@admin_required
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
            return jsonify({'error': 'Formato de fecha_desde inválido. Use YYYY-MM-DD'}), 400
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            query = query.filter(Sale.fecha <= fecha_hasta_dt)
        except ValueError:
            return jsonify({'error': 'Formato de fecha_hasta inválido. Use YYYY-MM-DD'}), 400
    
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
            sale.camarero_nombre or '',
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
@admin_required
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


@bp.route('/daily-summary', methods=['GET'])
@token_required
def get_daily_summary(current_user):
    """Stats del día: total vendido, cantidad de ventas, top productos"""
    today = date.today()

    sales = Sale.query.filter(
        Sale.fecha == today,
        Sale.source == 'galia'
    ).all()

    total_vendido = sum(float(s.total) for s in sales)
    cantidad_ventas = len(sales)

    top_products = db.session.query(
        ProductVariant.id,
        ProductVariant.name,
        func.sum(SaleItem.quantity).label('cantidad'),
        func.sum(SaleItem.subtotal).label('total')
    ).join(SaleItem).join(Sale).filter(
        Sale.fecha == today,
        Sale.source == 'galia'
    ).group_by(ProductVariant.id, ProductVariant.name).order_by(
        func.sum(SaleItem.subtotal).desc()
    ).limit(5).all()

    top_list = []
    for variant_id, name, cantidad, total in top_products:
        top_list.append({
            'product_variant_id': variant_id,
            'name': name,
            'quantity': cantidad,
            'total': float(total) if total else 0,
        })

    low_stock = db.session.query(ProductVariant).filter(
        ProductVariant.stock_quantity <= ProductVariant.min_stock,
        ProductVariant.is_active == True
    ).count()

    return jsonify({
        'total_vendido': total_vendido,
        'cantidad_ventas': cantidad_ventas,
        'top_products': top_list,
        'bajo_stock_count': low_stock,
    }), 200


@bp.route('/top-products', methods=['GET'])
@token_required
def get_top_products(current_user):
    """Ranking de productos más vendidos con filtro de fecha"""
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    limit = request.args.get('limit', 10, type=int)

    query = db.session.query(
        ProductVariant.id,
        ProductVariant.name,
        func.sum(SaleItem.quantity).label('cantidad'),
        func.sum(SaleItem.subtotal).label('total')
    ).join(SaleItem).join(Sale).filter(Sale.source == 'galia')

    if fecha_desde:
        try:
            desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            query = query.filter(Sale.fecha >= desde)
        except ValueError:
            pass

    if fecha_hasta:
        try:
            hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            query = query.filter(Sale.fecha <= hasta)
        except ValueError:
            pass

    results = query.group_by(ProductVariant.id, ProductVariant.name).order_by(
        func.sum(SaleItem.subtotal).desc()
    ).limit(limit).all()

    top_list = []
    for variant_id, name, cantidad, total in results:
        top_list.append({
            'product_variant_id': variant_id,
            'name': name,
            'quantity': cantidad,
            'total': float(total) if total else 0,
        })

    return jsonify({'top_products': top_list}), 200


@bp.route('/<int:sale_id>/payments', methods=['POST'])
@token_required
def register_payment(current_user, sale_id):
    """Register a payment for a sale"""
    sale = Sale.query.get_or_404(sale_id)
    data = request.get_json() or {}

    if not data.get('amount') or not data.get('method'):
        return jsonify({'error': 'amount and method required'}), 400

    try:
        amount = float(data['amount'])
    except (ValueError, TypeError):
        return jsonify({'error': 'amount must be a valid number'}), 400

    if amount <= 0:
        return jsonify({'error': 'amount must be positive'}), 400

    payment = Payment(
        sale_id=sale_id,
        amount=amount,
        method=data['method'],
        user_id=current_user.id,
    )
    sale.total_paid = float(sale.total_paid or 0) + amount

    db.session.add(payment)
    db.session.commit()

    return jsonify({
        'payment': payment.to_dict(),
        'sale': sale.to_dict(),
        'remaining': float(sale.total) - float(sale.total_paid),
    }), 201


@bp.route('/<int:sale_id>/close', methods=['POST'])
@token_required
def close_sale(current_user, sale_id):
    """Close a sale and mark the mesa as available"""
    sale = Sale.query.get_or_404(sale_id)

    # Check if fully paid
    if float(sale.total_paid or 0) < float(sale.total):
        return jsonify({'error': 'Sale not fully paid'}), 400

    sale.status = 'cerrada'
    if sale.mesa_id:
        mesa = Mesa.query.get(sale.mesa_id)
        if mesa:
            mesa.status = 'libre'

    db.session.commit()

    return jsonify(sale.to_dict()), 200
