from marshmallow import Schema, fields, validate, validates, ValidationError

class SupplierSchema(Schema):
    """Schema for Supplier serialization and validation"""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    tax_id = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    contact_person = fields.Str(allow_none=True, validate=validate.Length(max=200))
    phone = fields.Str(allow_none=True, validate=validate.Length(max=50))
    email = fields.Email(allow_none=True, validate=validate.Length(max=200))
    address = fields.Str(allow_none=True)
    payment_terms = fields.Str(allow_none=True, validate=validate.Length(max=100))
    status = fields.Str(validate=validate.OneOf(['active', 'inactive', 'archived']), missing='active')
    is_deleted = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    created_by_user_id = fields.Int(dump_only=True)
    modified_by_user_id = fields.Int(dump_only=True)
    
    @validates('name')
    def validate_name(self, value):
        """Ensure name is not only whitespace"""
        if not value or not value.strip():
            raise ValidationError('Name cannot be empty or only whitespace')


class SupplierListSchema(Schema):
    """Schema for paginated supplier list"""
    suppliers = fields.List(fields.Nested(SupplierSchema))
    total = fields.Int()
    page = fields.Int()
    per_page = fields.Int()
    pages = fields.Int()
