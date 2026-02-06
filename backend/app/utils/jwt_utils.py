from flask import request, jsonify, current_app
from functools import wraps
import jwt
from app.models.user import User

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Log para debugging
        print(f"[AUTH DEBUG] Request path: {request.path}")
        print(f"[AUTH DEBUG] Request method: {request.method}")
        print(f"[AUTH DEBUG] Headers: {dict(request.headers)}")
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            print(f"[AUTH DEBUG] Authorization header encontrado: {auth_header[:50]}...")
            try:
                token = auth_header.split(" ")[1]
                print(f"[AUTH DEBUG] Token extraído: {token[:20]}...")
            except IndexError:
                print("[AUTH DEBUG] Error al extraer token del header")
                return jsonify({'error': 'Token inválido'}), 401
        else:
            print("[AUTH DEBUG] No se encontró header Authorization")
        
        if not token:
            print("[AUTH DEBUG] Token es None, retornando 401")
            return jsonify({'error': 'Token requerido'}), 401
        
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'Usuario no encontrado'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated
