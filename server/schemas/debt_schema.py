from server.extension import ma
from server.models import Debt
from marshmallow import fields, post_dump
from server.schemas.payment_schema import PaymentSchema 

class DebtSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Debt
        load_instance = True
        include_fk = True
        
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
    payments = fields.Nested(PaymentSchema, many=True, exclude=('debt',), dump_only=True)

    # Date formatting
    created_at = ma.DateTime(format="%Y-%m-%dT%H:%M:%S")
    updated_at = ma.DateTime(format="%Y-%m-%dT%H:%M:%S")
    due_date = ma.DateTime(format="%Y-%m-%dT%H:%M:%S")
    last_reminder_sent = ma.DateTime(format="%Y-%m-%dT%H:%M:%S")

    customer_name = fields.Method("get_customer_name", dump_only=True)
    phone = fields.Method("get_customer_phone", dump_only=True)

    def get_customer_name(self, obj):
        return obj.customer.customer_name if obj.customer else None

    def get_customer_phone(self, obj):
        return obj.customer.phone if obj.customer else None

    @post_dump
    def ensure_customer_info(self, data, **kwargs):
        if 'customer' in data and data['customer']:
            if 'customer_name' not in data or data['customer_name'] is None:
                data['customer_name'] = data['customer'].get('customer_name')
            if 'phone' not in data or data['phone'] is None:
                data['phone'] = data['customer'].get('phone')
        return data