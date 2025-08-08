from extension import db
from sqlalchemy_serializer import SerializerMixin

class Item(db.Model, SerializerMixin):
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    debt_id = db.Column(db.Integer, db.ForeignKey("debts.id", ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    serialize_rules = ('-debt.items',)

    # Relationship
    debt = db.relationship("Debt", back_populates="items")
    
    """Always calculate instead of storing to avoid stale data."""
    @property
    def total_price(self):
        
        return self.quantity * self.price
