from datetime import datetime
from server.extension import db


class Invitation(db.Model):
    __tablename__ = "invitations"

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # manager, salesperson
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    business = db.relationship(
        "Business",
        backref=db.backref("invitations", 
        cascade="all, delete-orphan")
        )
    
    creator = db.relationship(
        "User",
        back_populates="sent_invitations",
        overlaps="sent_by_user"
        )
    
    sent_by_user = db.relationship(
        "User",
        back_populates="sent_invitations",
        
        overlaps="creator"
        )