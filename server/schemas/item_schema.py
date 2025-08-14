from server.extension import ma
from server.models import Item
from marshmallow import fields

class ItemSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Item
        load_instance = True
        include_fk = True  # Include debt_id foreign key
        exclude = (
            "debt",  
        )

   
    debt = fields.Nested("DebtSchema", exclude=("items", "payments", "customer"))

    # Calculated field
    total_price = fields.Method("get_total_price", dump_only=True)

    def get_total_price(self, obj):
        return obj.total_price
