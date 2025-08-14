from server.extension import ma
from server.models import Debt
from marshmallow import fields

class DebtSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Debt
        load_instance = True
        include_fk = True
        # Exclude relationships that would cause recursion
        exclude = (
            "customer.debts",
            "items.debt",
            "payments.debt",
            "created_by_user.debts",
            "created_by_user.payments",
            "created_by_user.changelogs"
        )

    # Nested fields
    customer = fields.Nested('CustomerSchema', exclude=('debts',), dump_only=True)
    created_by_user = fields.Nested('UserSchema', exclude=('debts', 'payments', 'changelogs'), dump_only=True)
    items = fields.Nested('ItemSchema', many=True, exclude=('debt',), dump_only=True)
    payments = fields.Nested('PaymentSchema', many=True, exclude=('debt',), dump_only=True)

    # Date formatting
    created_at = ma.DateTime(format="%Y-%m-%dT%H:%M:%S")
    updated_at = ma.DateTime(format="%Y-%m-%dT%H:%M:%S")
    due_date = ma.DateTime(format="%Y-%m-%dT%H:%M:%S")
    last_reminder_sent = ma.DateTime(format="%Y-%m-%dT%H:%M:%S")
