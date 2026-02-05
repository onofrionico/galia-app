from functools import wraps
from flask import jsonify
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Autenticación requerida'}), 401
        
        if not current_user.is_admin():
            return jsonify({'error': 'Permisos de administrador requeridos'}), 403
        
        return f(*args, **kwargs)
    return decorated_function
