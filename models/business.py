from datetime import datetime
from extension import db
from sqlalchemy_serializer import SerializerMixin

class Business(db.Model, SerializerMixin):
    __tablename__ = "businesses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    contact_info = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    serialize_rules = ('-owner.businesses',)

    # Relationships
    owner = db.relationship("User", back_populates="businesses")
    customers = db.relationship("Customer", back_populates="business", cascade="all, delete-orphan")
