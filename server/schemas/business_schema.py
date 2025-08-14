from marshmallow import fields
from server.extension import ma
from server.models import Business
from server.schemas.user_schema import UserSchema
from server.schemas.customer_schema import CustomerSchema


# For reading responses
class BusinessSchema(ma.SQLAlchemyAutoSchema):
    owner = fields.Nested(
        UserSchema,
        only=("id", "name", "email", "role"),
        dump_only=True
    )
    members = fields.List(
        fields.Nested(UserSchema, only=("id", "name", "role")),
        dump_only=True
    )
    customers = fields.List(
        # Removed "email" because CustomerSchema does not have it
        fields.Nested(CustomerSchema, only=("id", "customer_name", "phone", "id_number")),
        dump_only=True
    )

    class Meta:
        model = Business
        load_instance = True
        include_fk = True
        dump_only = ("id", "created_at")


# For creating/updating
class BusinessCreateUpdateSchema(ma.SQLAlchemySchema):
    name = fields.String(required=True)
    owner_id = fields.Integer(required=True)
    address = fields.String(required=False, allow_none=True)
    phone = fields.String(required=False, allow_none=True)
    email = fields.String(required=False, allow_none=True)
    website = fields.String(required=False, allow_none=True)
    description = fields.String(required=False, allow_none=True)
