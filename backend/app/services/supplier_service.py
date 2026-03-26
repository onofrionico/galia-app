"""
Supplier service layer
Business logic for supplier management
"""
from flask import abort
from sqlalchemy import or_
from app.extensions import db
from app.models.supplier import Supplier
from app.services.base_service import BaseService


class SupplierService(BaseService):
    model = Supplier
    
    @classmethod
    def create_supplier(cls, data, user_id=None):
        """
        Create a new supplier with validation
        
        Args:
            data: dict with supplier fields
            user_id: ID of user creating the supplier
        
        Returns:
            Created Supplier instance
        """
        # Check for duplicate tax_id only if tax_id is provided
        tax_id = data.get('tax_id')
        if tax_id and tax_id.strip():  # Only check if tax_id is not empty
            existing = Supplier.query.filter_by(tax_id=tax_id).first()
            if existing:
                abort(400, description='Ya existe un proveedor con ese CUIT/Tax ID')
        
        return cls.create(data, user_id=user_id)
    
    @classmethod
    def update_supplier(cls, supplier_id, data, user_id=None):
        """
        Update supplier with validation
        
        Args:
            supplier_id: ID of supplier to update
            data: dict with fields to update
            user_id: ID of user updating
        
        Returns:
            Updated Supplier instance
        """
        supplier = cls.get_by_id(supplier_id)
        
        # Check for duplicate tax_id if changing it (only if new tax_id is not empty)
        if 'tax_id' in data and data['tax_id'] != supplier.tax_id:
            new_tax_id = data['tax_id']
            if new_tax_id and new_tax_id.strip():  # Only check if new tax_id is not empty
                existing = Supplier.query.filter_by(tax_id=new_tax_id).first()
                if existing:
                    abort(400, description='Ya existe un proveedor con ese CUIT/Tax ID')
        
        return cls.update(supplier_id, data, user_id=user_id)
    
    @classmethod
    def delete_supplier(cls, supplier_id, user_id=None):
        """
        Soft delete a supplier with validation
        
        Args:
            supplier_id: ID of supplier to delete
            user_id: ID of user deleting
        
        Returns:
            Deleted Supplier instance
        """
        supplier = cls.get_by_id(supplier_id)
        
        # Check if supplier has purchases
        if supplier.purchases.count() > 0:
            abort(400, description='No se puede eliminar un proveedor con compras asociadas. Considere archivarlo.')
        
        return cls.delete(supplier_id, user_id=user_id, soft_delete=True)
    
    @classmethod
    def search_suppliers(cls, search_term=None, status=None, page=1, per_page=25):
        """
        Search suppliers with filters and pagination
        
        Args:
            search_term: text to search in name, tax_id, contact_person
            status: filter by status (active, inactive, archived)
            page: page number
            per_page: items per page
        
        Returns:
            Paginated query result
        """
        query = Supplier.query.filter_by(is_deleted=False)
        
        if search_term:
            search_pattern = f'%{search_term}%'
            query = query.filter(
                or_(
                    Supplier.name.ilike(search_pattern),
                    Supplier.tax_id.ilike(search_pattern),
                    Supplier.contact_person.ilike(search_pattern),
                    Supplier.email.ilike(search_pattern)
                )
            )
        
        if status:
            query = query.filter_by(status=status)
        
        query = query.order_by(Supplier.name.asc())
        
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    @classmethod
    def get_supplier_with_stats(cls, supplier_id):
        """
        Get supplier with additional statistics
        
        Args:
            supplier_id: ID of supplier
        
        Returns:
            dict with supplier data and stats
        """
        supplier = cls.get_by_id(supplier_id)
        
        supplier_dict = supplier.to_dict()
        supplier_dict['products_count'] = supplier.products.filter_by(is_deleted=False).count()
        supplier_dict['purchases_count'] = supplier.purchases.filter_by(is_deleted=False).count()
        
        return supplier_dict
