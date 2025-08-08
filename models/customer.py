from server.extension import db
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime

class Customer(db.Model,SerializerMixin):
    __tablename__ = 'customers'

    id = db.Column(db.Integer,primary_key=True)
    customer_name = db.Column(db.String,nullable=False)
    phone = db.Column(db.String,nullable=False)
    id_number = db.Column(db.String,nullable=False)
    created_at = db.Column(db.DateTime,default=datetime.utcnow)
    updated_at = db.Column(db.DateTime,default=datetime.utcnow(),onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)



    # relations
    debts = db.relationship("Debt",back_populates='customer',cascade="all,delete,passive_deletes=True")
    serialize_rules = ('-debts.customer',)

    