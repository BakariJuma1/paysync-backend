from datetime import datetime
from server.extension import db


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    debt_id = db.Column(db.Integer, db.ForeignKey("debts.id", ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    method = db.Column(db.String(50))  # cash, mobile money, bank
    received_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)


    # Relationships
    debt = db.relationship("Debt", back_populates="payments")
    received_by_user = db.relationship("User", back_populates="payments")
