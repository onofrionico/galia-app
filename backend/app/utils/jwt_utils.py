from flask import request, jsonify, current_app
from functools import wraps
import jwt
from app.models.user import User


def _debug(message):
    """Traza de autenticación solo en modo debug. Nunca imprimir el header Authorization ni el token."""
    if current_app.debug:
        print(f"[AUTH DEBUG] {message}")


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        _debug(f"{request.method} {request.path}")

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                _debug("Error al extraer token del header")
                return jsonify({'error': 'Token inválido'}), 401
        else:
            _debug("No se encontró header Authorization")

        if not token:
            _debug("Token es None, retornando 401")
            return jsonify({'error': 'Token requerido'}), 401

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                _debug("Usuario no encontrado en BD")
                return jsonify({'error': 'Usuario no encontrado'}), 401
            if not current_user.is_active:
                _debug("Usuario inactivo")
                return jsonify({'error': 'Usuario inactivo'}), 401
            _debug(f"Usuario autenticado: {current_user.id}")
        except jwt.ExpiredSignatureError:
            _debug("Token expirado")
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError as e:
            _debug(f"Token inválido: {str(e)}")
            return jsonify({'error': 'Token inválido'}), 401

        return f(current_user, *args, **kwargs)

    return decorated
