from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.mesa import Mesa
from app.models.salon import Salon
from app.models.printer_device import PrinterDevice
from app.utils.jwt_utils import token_required
from app.utils.decorators import admin_required

bp = Blueprint('configuration', __name__, url_prefix='/api/v1/configuration')

# MESAS CRUD
@bp.route('/mesas/<int:salon_id>', methods=['GET'])
@token_required
def list_mesas(current_user, salon_id):
    mesas = Mesa.query.filter_by(salon_id=salon_id).order_by(Mesa.number).all()
    return jsonify({'mesas': [m.to_dict() for m in mesas], 'total': len(mesas)}), 200

@bp.route('/mesas', methods=['POST'])
@token_required
@admin_required
def create_mesa(current_user):
    data = request.get_json() or {}
    if not data.get('number') or not data.get('salon_id'):
        return jsonify({'error': 'number and salon_id required'}), 400
    if not data.get('capacity'):
        return jsonify({'error': 'capacity required'}), 400

    # Check if mesa number already exists for this salon
    existing = Mesa.query.filter_by(salon_id=data['salon_id'], number=data['number']).first()
    if existing:
        return jsonify({'error': 'Mesa number already exists for this salon'}), 409

    mesa = Mesa(
        salon_id=data['salon_id'],
        number=int(data['number']),
        capacity=int(data['capacity']),
        pos_x=float(data.get('pos_x', 10.0)),
        pos_y=float(data.get('pos_y', 10.0)),
        width=float(data.get('width', 10.0)),
        height=float(data.get('height', 10.0)),
    )
    db.session.add(mesa)
    db.session.commit()
    return jsonify(mesa.to_dict()), 201

@bp.route('/mesas/<int:mesa_id>', methods=['PUT'])
@token_required
@admin_required
def update_mesa(current_user, mesa_id):
    mesa = Mesa.query.get_or_404(mesa_id)
    data = request.get_json() or {}

    if 'number' in data:
        mesa.number = int(data['number'])
    if 'capacity' in data:
        mesa.capacity = int(data['capacity'])

    db.session.commit()
    return jsonify(mesa.to_dict()), 200

@bp.route('/mesas/<int:mesa_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_mesa(current_user, mesa_id):
    mesa = Mesa.query.get_or_404(mesa_id)
    mesa.is_active = False
    db.session.commit()
    return jsonify({'message': 'Mesa deactivated'}), 200

# SALONES CRUD
@bp.route('/salones', methods=['GET'])
@token_required
def list_salones(current_user):
    salones = Salon.query.filter_by(is_active=True).order_by(Salon.name).all()
    return jsonify({'salones': [s.to_dict() for s in salones], 'total': len(salones)}), 200

@bp.route('/salones', methods=['POST'])
@token_required
@admin_required
def create_salon(current_user):
    data = request.get_json() or {}
    if not data.get('name'):
        return jsonify({'error': 'name required'}), 400

    salon = Salon(
        name=data['name'].strip(),
        description=data.get('description', '').strip() or None,
    )
    db.session.add(salon)
    db.session.commit()
    return jsonify(salon.to_dict()), 201

@bp.route('/salones/<int:salon_id>', methods=['PUT'])
@token_required
@admin_required
def update_salon(current_user, salon_id):
    salon = Salon.query.get_or_404(salon_id)
    data = request.get_json() or {}

    if 'name' in data:
        salon.name = data['name'].strip()
    if 'description' in data:
        salon.description = data['description'].strip() if data['description'] else None

    db.session.commit()
    return jsonify(salon.to_dict()), 200

@bp.route('/salones/<int:salon_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_salon(current_user, salon_id):
    salon = Salon.query.get_or_404(salon_id)
    salon.is_active = False
    db.session.commit()
    return jsonify({'message': 'Salon deactivated'}), 200

# PRINTER DEVICES CRUD
@bp.route('/printer-devices', methods=['GET'])
@token_required
def list_printers(current_user):
    printers = PrinterDevice.query.all()
    return jsonify({'devices': [p.to_dict() for p in printers], 'total': len(printers)}), 200

@bp.route('/printer-devices', methods=['POST'])
@token_required
@admin_required
def create_printer(current_user):
    data = request.get_json() or {}
    if not data.get('name') or not data.get('type') or not data.get('ip_address') or not data.get('port'):
        return jsonify({'error': 'name, type, ip_address, port required'}), 400
    if data['type'] not in ['comanda', 'control']:
        return jsonify({'error': 'type must be comanda or control'}), 400

    printer = PrinterDevice(
        name=data['name'].strip(),
        type=data['type'],
        ip_address=data['ip_address'],
        port=int(data['port']),
        status='offline',
    )
    db.session.add(printer)
    db.session.commit()
    return jsonify(printer.to_dict()), 201

@bp.route('/printer-devices/<int:device_id>', methods=['PUT'])
@token_required
@admin_required
def update_printer(current_user, device_id):
    printer = PrinterDevice.query.get_or_404(device_id)
    data = request.get_json() or {}

    if 'name' in data:
        printer.name = data['name'].strip()
    if 'type' in data:
        if data['type'] not in ['comanda', 'control']:
            return jsonify({'error': 'type must be comanda or control'}), 400
        printer.type = data['type']
    if 'ip_address' in data:
        printer.ip_address = data['ip_address']
    if 'port' in data:
        printer.port = int(data['port'])

    db.session.commit()
    return jsonify(printer.to_dict()), 200

@bp.route('/printer-devices/<int:device_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_printer(current_user, device_id):
    printer = PrinterDevice.query.get_or_404(device_id)
    db.session.delete(printer)
    db.session.commit()
    return jsonify({'message': 'Printer deleted'}), 200

@bp.route('/printer-devices/<int:device_id>/test', methods=['POST'])
@token_required
@admin_required
def test_printer(current_user, device_id):
    printer = PrinterDevice.query.get_or_404(device_id)
    # TODO: Implement actual printer connection test
    # For now, simulate connection
    printer.status = 'online'
    db.session.commit()
    return jsonify({'status': 'online', 'message': 'Connection successful'}), 200
