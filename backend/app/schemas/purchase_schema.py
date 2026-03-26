from marshmallow import Schema, fields, validate, validates, ValidationError, validates_schema
from datetime import datetime, timedelta

class PurchaseItemSchema(Schema):
    """Schema for PurchaseItem serialization and validation"""
    id = fields.Int(dump_only=True)
    purchase_id = fields.Int(dump_only=True)
    product_id = fields.Int(required=True)
    product_name_snapshot = fields.Str(dump_only=True)
    sku_snapshot = fields.Str(dump_only=True)
    quantity = fields.Decimal(required=True, as_string=True, places=4)
    unit_price = fields.Decimal(required=True, as_string=True, places=2)
    catalog_price_at_time = fields.Decimal(allow_none=True, as_string=True, places=2)
    total_price = fields.Decimal(dump_only=True, as_string=True, places=2)
    notes = fields.Str(allow_none=True)
    
    # Nested product info for display
    product = fields.Nested('ProductSchema', dump_only=True, only=['id', 'name', 'sku', 'current_price'])
    
    @validates('quantity')
    def validate_quantity(self, value):
        """Ensure quantity is greater than 0"""
        if value <= 0:
            raise ValidationError('Quantity must be greater than 0')
    
    @validates('unit_price')
    def validate_unit_price(self, value):
        """Ensure unit price is greater than 0"""
        if value <= 0:
            raise ValidationError('Unit price must be greater than 0')


class PurchaseSchema(Schema):
    """Schema for Purchase serialization and validation"""
    id = fields.Int(dump_only=True)
    supplier_id = fields.Int(required=True)
    related_expense_id = fields.Int(allow_none=True)
    purchase_date = fields.Date(required=True)
    total_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    currency = fields.Str(validate=validate.OneOf(['ARS', 'USD', 'EUR', 'BRL']), missing='ARS')
    exchange_rate = fields.Decimal(allow_none=True, as_string=True, places=6)
    invoice_number = fields.Str(allow_none=True, validate=validate.Length(max=100))
    cae_number = fields.Str(allow_none=True, validate=validate.Length(max=100))
    payment_status = fields.Str(validate=validate.OneOf(['pending', 'paid', 'partial', 'cancelled']), missing='pending')
    notes = fields.Str(allow_none=True)
    is_deleted = fields.Bool(dump_only=True)
    deleted_at = fields.DateTime(dump_only=True)
    version = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    created_by_user_id = fields.Int(dump_only=True)
    modified_by_user_id = fields.Int(dump_only=True)
    
    # Nested relationships
    supplier = fields.Nested('SupplierSchema', dump_only=True, only=['id', 'name', 'tax_id'])
    items = fields.List(fields.Nested(PurchaseItemSchema), required=True)
    
    @validates('purchase_date')
    def validate_purchase_date(self, value):
        """Ensure purchase date is not in the future and not more than 1 year in the past"""
        today = datetime.now().date()
        if value > today:
            raise ValidationError('Purchase date cannot be in the future')
        
        one_year_ago = today - timedelta(days=365)
        if value < one_year_ago:
            raise ValidationError('Purchase date cannot be more than 1 year in the past')
    
    @validates_schema
    def validate_items(self, data, **kwargs):
        """Ensure at least one item is present"""
        items = data.get('items', [])
        if not items or len(items) == 0:
            raise ValidationError('At least one purchase item is required', 'items')


class PurchaseListSchema(Schema):
    """Schema for paginated purchase list"""
    purchases = fields.List(fields.Nested(PurchaseSchema))
    total = fields.Int()
    page = fields.Int()
    per_page = fields.Int()
    pages = fields.Int()
