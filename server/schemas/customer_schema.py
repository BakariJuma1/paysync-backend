from marshmallow import Schema, fields, post_load
from server.models import Customer
from server.schemas.debt_schema import DebtSchema

class CustomerSchema(Schema):
    id = fields.Int(dump_only=True)
    customer_name = fields.Str(required=True)
    phone = fields.Str(required=True)
    id_number = fields.Str(required=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    created_by = fields.Int(required=True)
    business_id = fields.Int(required=True)

    
    debts = fields.Nested("DebtSchema", many=True, exclude=("customer",), dump_only=True)

    @post_load
    def make_customer(self, data, **kwargs):
        return Customer(**data)
