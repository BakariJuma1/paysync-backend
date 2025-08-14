from marshmallow import fields, post_load
from server.extension import ma
from server.models import ChangeLog
from server.schemas.user_schema import UserSchema  


# For reading responses
class ChangeLogSchema(ma.SQLAlchemyAutoSchema):
    changed_by_user = fields.Nested(
        UserSchema,
        only=("id", "name", "email", "role"),
        dump_only=True
    )
    changed_by_name = fields.Method("get_user_name")
    timestamp = ma.DateTime(format="%Y-%m-%dT%H:%M:%S")

    class Meta:
        model = ChangeLog
        load_instance = True
        include_fk = True
        dump_only = ("id", "timestamp")
        exclude = ("changed_by_user.changelogs",)

    def get_user_name(self, obj):
        return obj.changed_by_user.name if obj.changed_by_user else None


# For creating/updating
class ChangeLogCreateUpdateSchema(ma.SQLAlchemySchema):
    entity_type = fields.String(required=True)
    entity_id = fields.Integer(required=True)
    action = fields.String(required=True)  
    changed_by = fields.Integer(required=True)
    details = fields.Dict(required=False)

    @post_load
    def make_changelog(self, data, **kwargs):
        return ChangeLog(**data)
