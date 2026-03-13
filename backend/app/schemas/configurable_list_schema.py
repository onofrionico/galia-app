from marshmallow import Schema, fields, validate

class ConfigurableListSchema(Schema):
    """Schema for ConfigurableList serialization and validation"""
    id = fields.Int(dump_only=True)
    list_type = fields.Str(required=True, validate=validate.OneOf(['product_category', 'unit_of_measure', 'payment_terms']))
    value = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    display_order = fields.Int(missing=0)
    is_active = fields.Bool(missing=True)
    created_at = fields.DateTime(dump_only=True)
    created_by_user_id = fields.Int(dump_only=True)


class ExchangeRateSchema(Schema):
    """Schema for ExchangeRate serialization and validation"""
    id = fields.Int(dump_only=True)
    from_currency = fields.Str(required=True, validate=validate.OneOf(['ARS', 'USD', 'EUR', 'BRL']))
    to_currency = fields.Str(required=True, validate=validate.OneOf(['ARS', 'USD', 'EUR', 'BRL']))
    rate = fields.Decimal(required=True, as_string=True, places=6)
    effective_date = fields.Date(required=True)
    source = fields.Str(validate=validate.OneOf(['manual', 'api', 'system']), missing='manual')
    created_at = fields.DateTime(dump_only=True)
    created_by_user_id = fields.Int(dump_only=True)
