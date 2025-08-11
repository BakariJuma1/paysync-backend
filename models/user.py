from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from server.extension import db
from sqlalchemy_serializer import SerializerMixin

class User(db.Model, SerializerMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="salesperson")  # owner, admin, salesperson
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verification_token = db.Column(db.String(128), unique=True, nullable=True)
    verification_token_expiry = db.Column(db.DateTime, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    reset_token = db.Column(db.String(128), unique=True, nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    last_verification_email_sent = db.Column(db.DateTime, nullable=True)
    # for salesperson,admin belong to a single bizz
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=True)
    verification_secret = db.Column(db.String(64), nullable=True)  



    # for owner, can have multiple businesses
    owned_businesses = db.relationship(
        "Business",
        foreign_keys="Business.owner_id",
        back_populates="owner"
    )

    serialize_rules = (
        '-owned_businesses.owner',   
        '-businesses.owner', 
        '-debts.created_by_user',
        '-payments.received_by_user',
        '-changelogs.changed_by_user',
        '-businesses.owner'
    )

    # Relationships
    debts = db.relationship("Debt", back_populates="created_by_user")
    payments = db.relationship("Payment", back_populates="received_by_user")
    changelogs = db.relationship("ChangeLog", back_populates="changed_by_user")
    businesses = db.relationship("Business", back_populates="owner", foreign_keys=[business_id])


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
