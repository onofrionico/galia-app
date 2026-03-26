"""
Base service class with common CRUD operations
All service classes should inherit from this
"""
from flask import abort
from app.extensions import db
from app.models.audit_log import AuditLog

class BaseService:
    """Base service with common CRUD operations"""
    
    model = None
    
    @classmethod
    def get_all(cls, filters=None, page=None, per_page=None, order_by=None):
        """
        Get all records with optional filtering and pagination
        
        Args:
            filters: dict of field:value pairs to filter by
            page: page number for pagination
            per_page: items per page
            order_by: field to order by
        
        Returns:
            Query object or paginated results
        """
        query = cls.model.query
        
        if filters:
            for field, value in filters.items():
                if hasattr(cls.model, field):
                    query = query.filter(getattr(cls.model, field) == value)
        
        if order_by and hasattr(cls.model, order_by):
            query = query.order_by(getattr(cls.model, order_by))
        
        if page and per_page:
            return query.paginate(page=page, per_page=per_page, error_out=False)
        
        return query.all()
    
    @classmethod
    def get_by_id(cls, id, raise_404=True):
        """
        Get a single record by ID
        
        Args:
            id: record ID
            raise_404: whether to raise 404 if not found
        
        Returns:
            Model instance or None
        """
        record = cls.model.query.get(id)
        
        if not record and raise_404:
            abort(404, description=f"{cls.model.__name__} not found")
        
        return record
    
    @classmethod
    def create(cls, data, user_id=None, commit=True):
        """
        Create a new record
        
        Args:
            data: dict of field:value pairs
            user_id: ID of user creating the record
            commit: whether to commit immediately
        
        Returns:
            Created model instance
        """
        if user_id and hasattr(cls.model, 'created_by_user_id'):
            data['created_by_user_id'] = user_id
        
        record = cls.model(**data)
        db.session.add(record)
        
        if commit:
            db.session.commit()
            
            if user_id:
                AuditLog.log_change(
                    entity_type=cls.model.__name__,
                    entity_id=record.id,
                    action='create',
                    user_id=user_id
                )
                db.session.commit()
        
        return record
    
    @classmethod
    def update(cls, id, data, user_id=None, commit=True):
        """
        Update an existing record
        
        Args:
            id: record ID
            data: dict of field:value pairs to update
            user_id: ID of user updating the record
            commit: whether to commit immediately
        
        Returns:
            Updated model instance
        """
        record = cls.get_by_id(id)
        
        if user_id and hasattr(cls.model, 'modified_by_user_id'):
            data['modified_by_user_id'] = user_id
        
        for field, value in data.items():
            if hasattr(record, field):
                old_value = getattr(record, field)
                setattr(record, field, value)
                
                if user_id and old_value != value:
                    AuditLog.log_change(
                        entity_type=cls.model.__name__,
                        entity_id=record.id,
                        action='update',
                        user_id=user_id,
                        field_name=field,
                        old_value=old_value,
                        new_value=value
                    )
        
        if commit:
            db.session.commit()
        
        return record
    
    @classmethod
    def delete(cls, id, user_id=None, soft_delete=True, commit=True):
        """
        Delete a record (soft or hard delete)
        
        Args:
            id: record ID
            user_id: ID of user deleting the record
            soft_delete: whether to soft delete (set is_deleted=True) or hard delete
            commit: whether to commit immediately
        
        Returns:
            Deleted model instance or None
        """
        record = cls.get_by_id(id)
        
        if soft_delete and hasattr(record, 'is_deleted'):
            record.is_deleted = True
            if hasattr(record, 'modified_by_user_id') and user_id:
                record.modified_by_user_id = user_id
            
            if user_id:
                AuditLog.log_change(
                    entity_type=cls.model.__name__,
                    entity_id=record.id,
                    action='soft_delete',
                    user_id=user_id
                )
        else:
            if user_id:
                AuditLog.log_change(
                    entity_type=cls.model.__name__,
                    entity_id=record.id,
                    action='hard_delete',
                    user_id=user_id
                )
            db.session.delete(record)
        
        if commit:
            db.session.commit()
        
        return record
    
    @classmethod
    def search(cls, search_term, search_fields, filters=None, page=None, per_page=None):
        """
        Search records by term across multiple fields
        
        Args:
            search_term: term to search for
            search_fields: list of field names to search in
            filters: additional filters to apply
            page: page number for pagination
            per_page: items per page
        
        Returns:
            Query results or paginated results
        """
        query = cls.model.query
        
        if search_term:
            search_conditions = []
            for field in search_fields:
                if hasattr(cls.model, field):
                    search_conditions.append(
                        getattr(cls.model, field).ilike(f'%{search_term}%')
                    )
            
            if search_conditions:
                query = query.filter(db.or_(*search_conditions))
        
        if filters:
            for field, value in filters.items():
                if hasattr(cls.model, field):
                    query = query.filter(getattr(cls.model, field) == value)
        
        if page and per_page:
            return query.paginate(page=page, per_page=per_page, error_out=False)
        
        return query.all()
