from flask import Blueprint, request, jsonify
from datetime import datetime
from app.extensions import db
from app.models.user import User
from app.models.employee import Employee
from app.utils.jwt_utils import token_required

bp = Blueprint('profile', __name__, url_prefix='/api/v1/profile')

@bp.route('', methods=['GET'])
@token_required
def get_profile(current_user):
    """Obtener información del perfil del usuario actual"""
    try:
        profile_data = {
            'user': current_user.to_dict()
        }
        
        if current_user.employee:
            profile_data['employee'] = current_user.employee.to_dict(include_sensitive=True)
        
        return jsonify(profile_data), 200
        
    except Exception as e:
        print(f"[PROFILE ERROR] Error al obtener perfil: {str(e)}")
        return jsonify({'error': f'Error al obtener perfil: {str(e)}'}), 500

@bp.route('', methods=['PUT'])
@token_required
def update_profile(current_user):
    """Actualizar información del perfil del usuario actual"""
    try:
        data = request.get_json()
        
        if 'email' in data and data['email'] != current_user.email:
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user:
                return jsonify({'error': 'El email ya está en uso'}), 400
            current_user.email = data['email']
        
        if current_user.employee:
            employee = current_user.employee
            
            if 'first_name' in data:
                employee.first_name = data['first_name']
            
            if 'last_name' in data:
                employee.last_name = data['last_name']
            
            if 'phone' in data:
                employee.phone = data['phone']
            
            if 'address' in data:
                employee.address = data['address']
            
            if 'emergency_contact_name' in data:
                employee.emergency_contact_name = data['emergency_contact_name']
            
            if 'emergency_contact_phone' in data:
                employee.emergency_contact_phone = data['emergency_contact_phone']
            
            if 'emergency_contact_relationship' in data:
                employee.emergency_contact_relationship = data['emergency_contact_relationship']
            
            employee.updated_at = datetime.utcnow()
            employee.updated_by_id = current_user.id
        
        db.session.commit()
        
        profile_data = {
            'user': current_user.to_dict()
        }
        
        if current_user.employee:
            profile_data['employee'] = current_user.employee.to_dict(include_sensitive=True)
        
        return jsonify({
            'message': 'Perfil actualizado exitosamente',
            'profile': profile_data
        }), 200
        
    except Exception as e:
        print(f"[PROFILE ERROR] Error al actualizar perfil: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar perfil: {str(e)}'}), 500

@bp.route('/password', methods=['PUT'])
@token_required
def change_password(current_user):
    """Cambiar contraseña del usuario actual"""
    try:
        data = request.get_json()
        
        if not data.get('current_password'):
            return jsonify({'error': 'La contraseña actual es requerida'}), 400
        
        if not data.get('new_password'):
            return jsonify({'error': 'La nueva contraseña es requerida'}), 400
        
        if not current_user.check_password(data['current_password']):
            return jsonify({'error': 'La contraseña actual es incorrecta'}), 401
        
        if len(data['new_password']) < 6:
            return jsonify({'error': 'La nueva contraseña debe tener al menos 6 caracteres'}), 400
        
        if data['current_password'] == data['new_password']:
            return jsonify({'error': 'La nueva contraseña debe ser diferente a la actual'}), 400
        
        current_user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({'message': 'Contraseña actualizada exitosamente'}), 200
        
    except Exception as e:
        print(f"[PROFILE ERROR] Error al cambiar contraseña: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Error al cambiar contraseña: {str(e)}'}), 500
