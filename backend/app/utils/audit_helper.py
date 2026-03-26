"""
Audit logging helper functions
Provides utilities for tracking changes to entities
"""
from flask import request
from app.extensions import db
from app.models.audit_log import AuditLog

def log_entity_change(entity_type, entity_id, action, user_id=None, changes=None):
    """
    Log a change to an entity
    
    Args:
        entity_type: Type of entity (e.g., 'Supplier', 'Product')
        entity_id: ID of the entity
        action: Action performed ('create', 'update', 'delete', 'soft_delete')
        user_id: ID of user performing the action
        changes: Dict of field changes {field_name: {'old': old_value, 'new': new_value}}
    """
    ip_address = request.remote_addr if request else None
    
    if changes:
        for field_name, change in changes.items():
            AuditLog.log_change(
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                user_id=user_id,
                field_name=field_name,
                old_value=change.get('old'),
                new_value=change.get('new'),
                ip_address=ip_address
            )
    else:
        AuditLog.log_change(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            ip_address=ip_address
        )
    
    db.session.commit()

def track_model_changes(old_instance, new_data, excluded_fields=None):
    """
    Track changes between old model instance and new data
    
    Args:
        old_instance: SQLAlchemy model instance
        new_data: Dict of new values
        excluded_fields: List of fields to exclude from tracking
    
    Returns:
        Dict of changes {field_name: {'old': old_value, 'new': new_value}}
    """
    if excluded_fields is None:
        excluded_fields = ['updated_at', 'modified_by_user_id', 'version']
    
    changes = {}
    
    for field, new_value in new_data.items():
        if field in excluded_fields:
            continue
        
        if hasattr(old_instance, field):
            old_value = getattr(old_instance, field)
            
            if old_value != new_value:
                changes[field] = {
                    'old': str(old_value) if old_value is not None else None,
                    'new': str(new_value) if new_value is not None else None
                }
    
    return changes

def get_entity_audit_trail(entity_type, entity_id, limit=50):
    """
    Get audit trail for a specific entity
    
    Args:
        entity_type: Type of entity
        entity_id: ID of the entity
        limit: Maximum number of records to return
    
    Returns:
        List of audit log entries
    """
    logs = AuditLog.query.filter_by(
        entity_type=entity_type,
        entity_id=entity_id
    ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    return [log.to_dict() for log in logs]

def get_user_activity(user_id, entity_type=None, limit=100):
    """
    Get activity log for a specific user
    
    Args:
        user_id: ID of the user
        entity_type: Optional filter by entity type
        limit: Maximum number of records to return
    
    Returns:
        List of audit log entries
    """
    query = AuditLog.query.filter_by(user_id=user_id)
    
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    
    logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    return [log.to_dict() for log in logs]
