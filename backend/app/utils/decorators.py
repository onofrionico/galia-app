from functools import wraps
from flask import jsonify

def admin_required(f):
    @wraps(f)
    def decorated_function(current_user, *args, **kwargs):
        # current_user viene del decorador @token_required
        if not current_user:
            return jsonify({'error': 'Autenticación requerida'}), 401
        
        if current_user.role != 'admin':
            return jsonify({'error': 'Permisos de administrador requeridos'}), 403
        
        return f(current_user, *args, **kwargs)
    return decorated_function
