from marshmallow import fields
from server.extension import ma
from server.models import ChangeLog
from server.schemas.user_schema import UserSchema  # Make sure this exists

# For reading responses
class ChangeLogSchema(ma.SQLAlchemyAutoSchema):
    changed_by_user = fields.Nested(
        UserSchema,
        only=("id", "name", "email", "role"),  
        dump_only=True
    )

    class Meta:
        model = ChangeLog
        load_instance = True
        include_fk = True
        exclude = ("changed_by_user.changelogs",)


# For creating/updating 
class ChangeLogCreateUpdateSchema(ma.SQLAlchemySchema):
    entity_type = fields.String(required=True)
    entity_id = fields.Integer(required=True)
    action = fields.String(required=True)  # create, update, delete
    changed_by = fields.Integer(required=True)
    details = fields.Dict(required=False)
