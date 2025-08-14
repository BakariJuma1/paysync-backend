from server.extension import ma
from server.models import Payment
from marshmallow import fields

class PaymentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Payment
        load_instance = True
        include_fk = True
        # Exclude relationships that would cause recursion
        exclude = (
            "debt.payments",
            "debt.customer",
            "debt.created_by_user",
            "received_by_user.payments",
            "received_by_user.debts",
        )

    payment_date = ma.DateTime(format="%Y-%m-%dT%H:%M:%S")
