from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Module, RolePermission, UserPermission, User
from app.utils.jwt_utils import token_required
from app.utils.decorators import admin_required
from app.utils.permissions import (
    check_module_access,
    get_user_modules,
    get_role_permissions,
    get_user_permission_overrides,
    sync_role_permissions,
    sync_user_permissions,
    reset_user_permissions
)

permissions_bp = Blueprint('permissions', __name__, url_prefix='/api/v1/permissions')


@permissions_bp.route('/modules', methods=['GET'])
@token_required
@admin_required
def list_all_modules(current_user):
    """Get all available modules (admin only)"""
    try:
        modules = Module.query.filter_by(is_active=True).order_by(Module.category, Module.name).all()
        return jsonify({
            'modules': [m.to_dict() for m in modules]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@permissions_bp.route('/modules/my-modules', methods=['GET'])
@token_required
def get_my_modules(current_user):
    """Get modules accessible to current user"""
    try:
        print(f"[MODULES] Getting modules for user: {current_user.email} (role: {current_user.role})")
        modules = get_user_modules(current_user)
        print(f"[MODULES] Found {len(modules)} modules")
        result = [m.to_dict() for m in modules]
        print(f"[MODULES] Returning modules: {[m['name'] for m in result]}")
        return jsonify({
            'modules': result
        }), 200
    except Exception as e:
        import traceback
        print(f"[MODULES ERROR] {str(e)}")
        print(f"[MODULES ERROR] Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@permissions_bp.route('/role/<role>', methods=['GET'])
@token_required
@admin_required
def get_role_permissions_endpoint(current_user, role):
    """Get permissions for a specific role (admin only)"""
    try:
        # Get all modules
        modules = Module.query.filter_by(is_active=True).all()

        # Get role permissions
        perms = RolePermission.query.filter_by(role=role).all()
        perm_dict = {p.module_id: p.is_granted for p in perms}

        # Build response
        permissions = []
        for module in modules:
            permissions.append({
                'module_id': module.id,
                'module_name': module.name,
                'display_name': module.display_name,
                'is_granted': perm_dict.get(module.id, False)
            })

        return jsonify({
            'role': role,
            'permissions': permissions
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@permissions_bp.route('/role/<role>', methods=['PUT'])
@token_required
@admin_required
def update_role_permissions(current_user, role):
    """Update permissions for a specific role (admin only)"""
    try:
        data = request.get_json()
        if not data or 'permissions' not in data:
            return jsonify({'error': 'Missing permissions data'}), 400

        # Build module_permissions dict
        module_permissions = {}
        for perm in data['permissions']:
            module_id = perm.get('module_id')
            is_granted = perm.get('is_granted', False)
            module_permissions[module_id] = is_granted

        # Sync permissions
        if sync_role_permissions(role, module_permissions):
            return jsonify({'message': f'Permissions updated for role {role}'}), 200
        else:
            return jsonify({'error': 'Failed to update permissions'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@permissions_bp.route('/user/<int:user_id>', methods=['GET'])
@token_required
@admin_required
def get_user_permissions_endpoint(current_user, user_id):
    """Get permission overrides for a user (admin only)"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Get all modules
        modules = Module.query.filter_by(is_active=True).all()

        # Get user overrides
        user_perms = UserPermission.query.filter_by(user_id=user_id).all()
        user_perm_dict = {p.module_id: p.is_granted for p in user_perms}

        # Get role permissions as baseline
        role_perms = RolePermission.query.filter_by(role=user.role).all()
        role_perm_dict = {p.module_id: p.is_granted for p in role_perms}

        # Build response
        permissions = []
        for module in modules:
            perm = {
                'module_id': module.id,
                'module_name': module.name,
                'display_name': module.display_name,
                'role_permission': role_perm_dict.get(module.id, False),
            }

            # If user has override, show it
            if module.id in user_perm_dict:
                perm['is_granted'] = user_perm_dict[module.id]
                perm['is_override'] = True
            else:
                perm['is_granted'] = role_perm_dict.get(module.id, False)
                perm['is_override'] = False

            permissions.append(perm)

        return jsonify({
            'user_id': user_id,
            'user_email': user.email,
            'role': user.role,
            'permissions': permissions
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@permissions_bp.route('/user/<int:user_id>', methods=['PUT'])
@token_required
@admin_required
def update_user_permissions(current_user, user_id):
    """Update permission overrides for a user (admin only)"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()
        if not data or 'permissions' not in data:
            return jsonify({'error': 'Missing permissions data'}), 400

        # Build module_permissions dict
        module_permissions = {}
        for perm in data['permissions']:
            module_id = perm.get('module_id')
            is_granted = perm.get('is_granted', False)
            # Only store if it's an override (different from role default)
            module_permissions[module_id] = is_granted

        # Sync permissions
        if sync_user_permissions(user_id, module_permissions):
            return jsonify({'message': f'Permissions updated for user {user.email}'}), 200
        else:
            return jsonify({'error': 'Failed to update permissions'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@permissions_bp.route('/user/<int:user_id>/reset', methods=['POST'])
@token_required
@admin_required
def reset_user_permissions_endpoint(current_user, user_id):
    """Reset user to role-based permissions (admin only)"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if reset_user_permissions(user_id):
            return jsonify({'message': f'Permissions reset for user {user.email}'}), 200
        else:
            return jsonify({'error': 'Failed to reset permissions'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
