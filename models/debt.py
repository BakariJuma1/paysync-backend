from server.extension import db
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime


class Debt(db.Model,SerializerMixin):
    __tablename__ = 'debts'

    id = db.Column(db.Integer,primary_key=True)
    customer_id = db.Column(db.Integer,db.ForeignKey('customers.id',ondelete='CASCADE'),nullable=False)
    total = db.Column(db.Float,nullable=False)
    amount_paid = db.Column(db.Float,nullable=False)
    balance = db.Column(db.Float,nullable=False)
    due_date = db.Column(db.DateTime)
    status = db.Column(db.String,default='partial')

    created_at = db.Column(db.DateTime,default=datetime.utcnow)
    updated_at = db.Column(db.DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)

    # relationships
    customer = db.relationship("Customer",back_populates="debts")
    serialize_rules = ('-customer.debts')

    def update_balance(self):
        self.balance = self.total -self.amount_paid
        self.status = (
            'paid' if self.balance <=0 else
            'unpaid' if self.amount_paid == 0 else
            'partial'
        )