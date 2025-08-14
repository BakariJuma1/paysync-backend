from datetime import datetime
from server.extension import db

class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=False)
    id_number = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False)

    
    # Relationships
    debts = db.relationship("Debt", back_populates='customer', cascade="all, delete-orphan")
    business = db.relationship("Business", back_populates="customers")
