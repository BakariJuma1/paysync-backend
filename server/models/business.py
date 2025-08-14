from datetime import datetime
from server.extension import db
from server.models.user import User

class Business(db.Model):
    __tablename__ = "businesses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    address = db.Column(db.String(255), nullable=True)    
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    owner = db.relationship(
        "User",
        foreign_keys=[owner_id],
        back_populates="owned_businesses"
    )

    #  Users (salespeople/admins) belonging to this business
    members = db.relationship(
        "User",
        foreign_keys=[User.business_id],
        backref="business_membership",
        overlaps="business"
    )
    customers = db.relationship("Customer", back_populates="business", cascade="all, delete-orphan")
