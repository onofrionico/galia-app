from marshmallow import Schema, fields, validate, validates, ValidationError
from decimal import Decimal

class ProductMasterSchema(Schema):
    """Schema for ProductMaster serialization and validation"""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    description = fields.Str(allow_none=True)
    category = fields.Str(allow_none=True, validate=validate.Length(max=100))
    unit_of_measure = fields.Str(required=True, validate=validate.Length(max=50))
    status = fields.Str(validate=validate.OneOf(['active', 'archived']), missing='active')
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    created_by_user_id = fields.Int(dump_only=True)


class ProductSchema(Schema):
    """Schema for Product serialization and validation"""
    id = fields.Int(dump_only=True)
    supplier_id = fields.Int(required=True)
    product_master_id = fields.Int(allow_none=True)
    name = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    sku = fields.Str(required=True, validate=validate.Length(min=2, max=50))
    category = fields.Str(allow_none=True, validate=validate.Length(max=100))
    unit_of_measure = fields.Str(required=True, validate=validate.Length(max=50))
    current_price = fields.Decimal(required=True, as_string=True, places=2)
    status = fields.Str(validate=validate.OneOf(['active', 'discontinued', 'archived']), missing='active')
    is_deleted = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    created_by_user_id = fields.Int(dump_only=True)
    modified_by_user_id = fields.Int(dump_only=True)
    
    # Nested relationships
    supplier = fields.Nested('SupplierSchema', dump_only=True, only=['id', 'name'])
    product_master = fields.Nested(ProductMasterSchema, dump_only=True, only=['id', 'name'])
    
    @validates('current_price')
    def validate_price(self, value):
        """Ensure price is greater than 0"""
        if value <= 0:
            raise ValidationError('Price must be greater than 0')
    
    @validates('sku')
    def validate_sku(self, value):
        """Ensure SKU contains only alphanumeric characters and hyphens"""
        import re
        if not re.match(r'^[a-zA-Z0-9-]+$', value):
            raise ValidationError('SKU can only contain alphanumeric characters and hyphens')


class ProductListSchema(Schema):
    """Schema for paginated product list"""
    products = fields.List(fields.Nested(ProductSchema))
    total = fields.Int()
    page = fields.Int()
    per_page = fields.Int()
    pages = fields.Int()
