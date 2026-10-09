from functools import wraps
from flask import jsonify, request
import logging
from datetime import datetime
from app.utils.permissions import check_module_access

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
    decorated_function._access_control = 'admin'
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


def module_required(module_name):
    """Exige acceso al módulo `module_name` (admin siempre pasa). Va debajo de @token_required."""
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

            if not check_module_access(current_user, module_name):
                logger.warning(
                    f"[SECURITY] Forbidden access attempt | "
                    f"User: {current_user.email} | Role: {current_user.role} | "
                    f"Required module: {module_name} | "
                    f"Path: {request.path} | Method: {request.method} | "
                    f"IP: {request.remote_addr} | Time: {datetime.utcnow().isoformat()}"
                )
                return jsonify({
                    'error': 'Acceso denegado',
                    'message': f'No tienes acceso al módulo {module_name}'
                }), 403

            return f(current_user, *args, **kwargs)
        decorated_function._access_control = f'module:{module_name}'
        return decorated_function
    return decorator


def authenticated_only(f):
    """Marca un endpoint como accesible para cualquier usuario autenticado.

    No agrega validaciones: deja explícita la decisión para el test de cobertura de permisos.
    Va debajo de @token_required.
    """
    f._access_control = 'authenticated'
    return f