from server.extension import ma
from server.models import User
from marshmallow import fields

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        include_fk = True  # Include foreign keys like business_id
        exclude = (
            "password_hash",
            "verification_token",
            "reset_token",
            "verification_secret",
            "owned_businesses",  # Avoid recursion
            "businesses",        # Avoid recursion
            "debts",             # Avoid recursion
            "payments",          # Avoid recursion
            "changelogs",        # Avoid recursion
            "sent_invitations",  # Avoid recursion
        )

    created_at = ma.DateTime(format="%Y-%m-%dT%H:%M:%S")
    verification_token_expiry = ma.DateTime(format="%Y-%m-%dT%H:%M:%S")
    reset_token_expiry = ma.DateTime(format="%Y-%m-%dT%H:%M:%S")
    last_verification_email_sent = ma.DateTime(format="%Y-%m-%dT%H:%M:%S")

    # Nested relationships
    debts = fields.Nested("DebtSchema", many=True, exclude=("created_by_user",))
    payments = fields.Nested("PaymentSchema", many=True, exclude=("received_by_user",))
    businesses = fields.Nested("BusinessSchema", many=True, exclude=("owner",))
