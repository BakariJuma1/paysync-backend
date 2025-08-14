from server.extension import ma
from server.models import FinanceSettings
from marshmallow import fields
from server.schemas.user_schema import UserSchema
from server.schemas.business_schema import BusinessSchema

class FinanceSettingsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = FinanceSettings
        load_instance = True
        include_fk = True
       
        exclude = ()

    created_at = ma.DateTime(format="%Y-%m-%dT%H:%M:%S")
    updated_at = ma.DateTime(format="%Y-%m-%dT%H:%M:%S")

    # Nested fields
    updated_by_user = fields.Nested(UserSchema, only=("id", "name", "email"))
    business = fields.Nested(BusinessSchema, only=("id", "name"))
