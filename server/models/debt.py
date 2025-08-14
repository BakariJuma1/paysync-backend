from datetime import datetime
from server.extension import db
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select, func
from server.models.payment import Payment

class Debt(db.Model):
    __tablename__ = 'debts'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    total = db.Column(db.Float, nullable=False, default=0)
    amount_paid = db.Column(db.Float, nullable=False, default=0)
    due_date = db.Column(db.DateTime)
    status = db.Column(db.String, default='partial')
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_reminder_sent = db.Column(db.DateTime)  
    reminder_count = db.Column(db.Integer, default=0)
    
    # Relationships
    customer = db.relationship("Customer", back_populates="debts")
    created_by_user = db.relationship("User", back_populates="debts")
    items = db.relationship("Item", back_populates="debt", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="debt", cascade="all, delete-orphan")
    
     # -----------------------
    # Calculate total from items
    # -----------------------
    def calculate_total(self):
        self.total = sum(item.total_price for item in self.items)
        return self.total

    # -----------------------
    # Hybrid property for balance
    # -----------------------
    @hybrid_property
    def balance(self):
        return self.total - sum(payment.amount for payment in self.payments)

    @balance.expression
    def balance(cls):
        # Use scalar_subquery for SQLAlchemy 2.x
        return cls.total - (
            select(func.coalesce(func.sum(Payment.amount), 0))
            .where(Payment.debt_id == cls.id)
            .scalar_subquery()
        )

  
    # Update status based on current balance
   
    def update_status(self):
        current_balance = self.balance
        if current_balance <= 0:
            self.status = 'paid'
        elif current_balance == self.total:
            self.status = 'unpaid'
        else:
            self.status = 'partial'