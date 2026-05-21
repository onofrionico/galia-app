from flask import Blueprint, request, jsonify, current_app
import jwt
from datetime import datetime, timedelta
from app.extensions import db
from app.models.user import User
from app.utils.jwt_utils import token_required

bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email y contraseña son requeridos'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Credenciales inválidas'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Usuario inactivo'}), 403
    
    token = jwt.encode({
        'user_id': user.id,
        'email': user.email,
        'exp': datetime.utcnow() + timedelta(days=7)
    }, current_app.config['SECRET_KEY'], algorithm='HS256')
    
    return jsonify({
        'message': 'Login exitoso',
        'token': token,
        'user': user.to_dict()
    }), 200

@bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    return jsonify({'message': 'Logout exitoso'}), 200

@bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    try:
        print(f"[AUTH ME] Getting current user: {current_user.email}")
        user_data = current_user.to_dict()
        print(f"[AUTH ME] User data: {user_data}")
        return jsonify({'user': user_data}), 200
    except Exception as e:
        import traceback
        print(f"[AUTH ME ERROR] {str(e)}")
        print(f"[AUTH ME ERROR] Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500
