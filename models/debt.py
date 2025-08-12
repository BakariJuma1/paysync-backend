from datetime import datetime
from server.extension import db
from sqlalchemy_serializer import SerializerMixin

class Debt(db.Model, SerializerMixin):
    __tablename__ = 'debts'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    total = db.Column(db.Float, nullable=False, default=0)
    amount_paid = db.Column(db.Float, nullable=False, default=0)
    balance = db.Column(db.Float, nullable=False, default=0)
    due_date = db.Column(db.DateTime)
    status = db.Column(db.String, default='partial')
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    
    # Relationships
    customer = db.relationship("Customer", back_populates="debts")
    created_by_user = db.relationship("User", back_populates="debts")
    items = db.relationship("Item", back_populates="debt", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="debt", cascade="all, delete-orphan")

    serialize_rules = (
        '-customer.debts',
        '-items.debt',
        '-payments.debt',
        '-created_by_user.debts',
        # Add these to prevent deeper recursion
        '-created_by_user.payments',
        '-created_by_user.changelogs',
    )

    def calculate_total(self):
        self.total = sum(item.total_price for item in self.items)
        return self.total

    def update_balance(self):
        self.balance = self.total - self.amount_paid
        self.status = (
            'paid' if self.balance <= 0 else
            'unpaid' if self.amount_paid == 0 else
            'partial'
        )
