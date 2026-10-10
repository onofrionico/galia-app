import logging

logger = logging.getLogger(__name__)

from app.models import Module, RolePermission, UserPermission, User

def check_module_access(user, module_name):
    """
    Check if user has access to a module.
    Priority: Admin (always true) > User permission override > Role permission

    Args:
        user: User object
        module_name: Module name (e.g., 'POS', 'Payroll')

    Returns:
        bool: True if user has access to module
    """
    if not user:
        return False

    # Admin always has access to all modules
    if user.role == 'admin':
        return True

    # Find the module
    module = Module.query.filter_by(name=module_name, is_active=True).first()
    if not module:
        return False

    # Check user-specific override first
    user_perm = UserPermission.query.filter_by(
        user_id=user.id,
        module_id=module.id
    ).first()

    if user_perm:
        return user_perm.is_granted

    # Fall back to role permission
    role_perm = RolePermission.query.filter_by(
        role=user.role,
        module_id=module.id
    ).first()

    if role_perm:
        return role_perm.is_granted

    # Default: no access
    return False


def get_user_modules(user):
    """
    Get all modules a user has access to.

    Args:
        user: User object

    Returns:
        List[Module]: List of modules user has access to
    """
    if not user:
        return []

    # Admin has access to all active modules
    if user.role == 'admin':
        return Module.query.filter_by(is_active=True).all()

    # Load everything once instead of querying per module
    active_modules = Module.query.filter_by(is_active=True).order_by(Module.id).all()
    overrides = get_user_permission_overrides(user.id)
    roles = get_role_permissions(user.role)

    return [
        m for m in active_modules
        if overrides.get(m.id, roles.get(m.id, False))
    ]


def get_role_permissions(role):
    """
    Get all permission records for a role.

    Args:
        role: Role string (e.g., 'admin', 'employee')

    Returns:
        dict: {module_id: is_granted}
    """
    perms = RolePermission.query.filter_by(role=role).all()
    return {p.module_id: p.is_granted for p in perms}


def get_user_permission_overrides(user_id):
    """
    Get user-specific permission overrides.

    Args:
        user_id: User ID

    Returns:
        dict: {module_id: is_granted}
    """
    perms = UserPermission.query.filter_by(user_id=user_id).all()
    return {p.module_id: p.is_granted for p in perms}


def sync_role_permissions(role, module_permissions):
    """
    Sync role permissions for multiple modules.
    Fully replaces the stored rows for this role.
    module_permissions: {module_id: is_granted, ...}

    Args:
        role: Role string
        module_permissions: Dict of {module_id: is_granted}

    Returns:
        bool: Success status
    """
    from app.extensions import db

    try:
        # Delete existing permissions for this role
        RolePermission.query.filter_by(role=role).delete()

        # Create new permissions
        for module_id, is_granted in module_permissions.items():
            perm = RolePermission(
                role=role,
                module_id=module_id,
                is_granted=bool(is_granted)
            )
            db.session.add(perm)

        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception('Error syncing role permissions')
        return False


def sync_user_permissions(user_id, module_permissions):
    """
    Sync user permission overrides for multiple modules.
    Fully replaces the stored rows for this user; a None value means
    'inherit from role' and no row is stored for that module.

    Args:
        user_id: User ID
        module_permissions: Dict of {module_id: is_granted}

    Returns:
        bool: Success status
    """
    from app.extensions import db

    try:
        # Delete existing overrides for this user
        UserPermission.query.filter_by(user_id=user_id).delete()

        # Create new permissions
        for module_id, is_granted in module_permissions.items():
            if is_granted is None:
                continue
            perm = UserPermission(
                user_id=user_id,
                module_id=module_id,
                is_granted=bool(is_granted)
            )
            db.session.add(perm)

        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception('Error syncing user permissions')
        return False


def reset_user_permissions(user_id):
    """
    Reset user to role-based permissions (remove all overrides).

    Args:
        user_id: User ID

    Returns:
        bool: Success status
    """
    from app.extensions import db

    try:
        UserPermission.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception('Error resetting user permissions')
        return False
