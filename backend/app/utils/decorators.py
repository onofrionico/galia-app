from functools import wraps
from flask import jsonify, request
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def admin_required(f):
    """Decorator to require admin role for endpoint access."""
    @wraps(f)
    def decorated_function(current_user, *args, **kwargs):
        # current_user viene del decorador @token_required
        if not current_user:
            logger.warning(
                f"[SECURITY] Unauthorized access attempt | "
                f"Path: {request.path} | Method: {request.method} | "
                f"IP: {request.remote_addr} | Time: {datetime.utcnow().isoformat()}"
            )
            return jsonify({'error': 'Autenticación requerida'}), 401
        
        if current_user.role != 'admin':
            logger.warning(
                f"[SECURITY] Forbidden access attempt | "
                f"User: {current_user.email} | Role: {current_user.role} | "
                f"Path: {request.path} | Method: {request.method} | "
                f"IP: {request.remote_addr} | Time: {datetime.utcnow().isoformat()}"
            )
            return jsonify({
                'error': 'Acceso denegado',
                'message': 'No tienes permisos para acceder a este recurso'
            }), 403
        
        return f(current_user, *args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """Decorator to require specific roles for endpoint access.
    
    Usage:
        @role_required('admin', 'manager')
        def some_endpoint(current_user):
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            if not current_user:
                logger.warning(
                    f"[SECURITY] Unauthorized access attempt | "
                    f"Path: {request.path} | Method: {request.method} | "
                    f"IP: {request.remote_addr} | Time: {datetime.utcnow().isoformat()}"
                )
                return jsonify({'error': 'Autenticación requerida'}), 401
            
            if current_user.role not in allowed_roles:
                logger.warning(
                    f"[SECURITY] Forbidden access attempt | "
                    f"User: {current_user.email} | Role: {current_user.role} | "
                    f"Required roles: {allowed_roles} | "
                    f"Path: {request.path} | Method: {request.method} | "
                    f"IP: {request.remote_addr} | Time: {datetime.utcnow().isoformat()}"
                )
                return jsonify({
                    'error': 'Acceso denegado',
                    'message': 'No tienes permisos para acceder a este recurso'
                }), 403
            
            return f(current_user, *args, **kwargs)
        return decorated_function
    return decorator

def employee_or_admin_required(f):
    """Decorator that allows both employees and admins."""
    @wraps(f)
    def decorated_function(current_user, *args, **kwargs):
        if not current_user:
            logger.warning(
                f"[SECURITY] Unauthorized access attempt | "
                f"Path: {request.path} | Method: {request.method} | "
                f"IP: {request.remote_addr} | Time: {datetime.utcnow().isoformat()}"
            )
            return jsonify({'error': 'Autenticación requerida'}), 401
        
        if current_user.role not in ['admin', 'employee']:
            logger.warning(
                f"[SECURITY] Forbidden access attempt | "
                f"User: {current_user.email} | Role: {current_user.role} | "
                f"Path: {request.path} | Method: {request.method} | "
                f"IP: {request.remote_addr} | Time: {datetime.utcnow().isoformat()}"
            )
            return jsonify({
                'error': 'Acceso denegado',
                'message': 'No tienes permisos para acceder a este recurso'
            }), 403
        
        return f(current_user, *args, **kwargs)
    return decorated_function
