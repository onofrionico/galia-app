from marshmallow import Schema, fields, validate, validates, ValidationError

class ConfigurableListSchema(Schema):
    """Schema for ConfigurableList serialization and validation"""
    id = fields.Int(dump_only=True)
    list_type = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    value = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    display_order = fields.Int(missing=0)
    is_active = fields.Bool(missing=True)
    created_at = fields.DateTime(dump_only=True)
    created_by_user_id = fields.Int(dump_only=True)
    
    @validates('list_type')
    def validate_list_type(self, value):
        """Ensure list_type is one of the allowed types"""
        allowed_types = [
            'product_category',
            'unit_of_measure',
            'payment_term',
            'supplier_type',
            'currency',
            'payment_status'
        ]
        if value not in allowed_types:
            raise ValidationError(f'list_type must be one of: {", ".join(allowed_types)}')


class ExchangeRateSchema(Schema):
    """Schema for ExchangeRate serialization and validation"""
    id = fields.Int(dump_only=True)
    from_currency = fields.Str(required=True, validate=validate.Length(equal=3))
    to_currency = fields.Str(required=True, validate=validate.Length(equal=3))
    rate = fields.Decimal(required=True, as_string=True, places=6)
    effective_date = fields.Date(required=True)
    source = fields.Str(validate=validate.OneOf(['manual', 'api', 'import']), missing='manual')
    created_at = fields.DateTime(dump_only=True)
    created_by_user_id = fields.Int(dump_only=True)
    
    @validates('rate')
    def validate_rate(self, value):
        """Ensure rate is greater than 0"""
        if value <= 0:
            raise ValidationError('Exchange rate must be greater than 0')
    
    @validates('from_currency')
    def validate_from_currency(self, value):
        """Ensure currency code is uppercase"""
        if not value.isupper():
            raise ValidationError('Currency code must be uppercase (e.g., USD, EUR)')
    
    @validates('to_currency')
    def validate_to_currency(self, value):
        """Ensure currency code is uppercase"""
        if not value.isupper():
            raise ValidationError('Currency code must be uppercase (e.g., USD, EUR)')


class ConfigurableListListSchema(Schema):
    """Schema for paginated configurable list"""
    items = fields.List(fields.Nested(ConfigurableListSchema))
    total = fields.Int()


class ExchangeRateListSchema(Schema):
    """Schema for paginated exchange rate list"""
    rates = fields.List(fields.Nested(ExchangeRateSchema))
    total = fields.Int()
