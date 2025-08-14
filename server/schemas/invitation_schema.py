from server.extension import ma
from server.models import Invitation
from marshmallow import fields
from server.schemas.user_schema import UserSchema
from server.schemas.business_schema import BusinessSchema

class InvitationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Invitation
        load_instance = True
        include_fk = True
        exclude = (
            # Exclude anything that could cause recursion
            "creator.sent_invitations",
            "business.invitations",
            "business.owner",
            "business.members",
        )

    created_at = ma.DateTime(format="%Y-%m-%dT%H:%M:%S")
    expires_at = ma.DateTime(format="%Y-%m-%dT%H:%M:%S")

    # Nested fields
    creator = fields.Nested(UserSchema, only=("id", "name", "email", "role"))
    business = fields.Nested(BusinessSchema, only=("id", "name", "address", "phone", "email"))
