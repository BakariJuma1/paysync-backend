
from datetime import datetime
from server.extension import db

class FinanceSettings(db.Model):
    __tablename__ = "finance_settings"
    
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False, unique=True)
    default_currency = db.Column(db.String(3), default="USD", nullable=False)
    
    # Payment terms
    payment_due_day = db.Column(db.Integer, default=1)  # Day of month payments are due
    grace_period_days = db.Column(db.Integer, default=5)  # Days after due date before late fees
    
    # Late fee rules
    late_fee_type = db.Column(db.String(20), default="percentage")  # percentage or fixed
    late_fee_value = db.Column(db.Float, default=5.0)  # 5% or fixed amount
    late_fee_max = db.Column(db.Float, default=0.0)  # 0 means no max
    late_fee_recurring = db.Column(db.Boolean, default=False)  # Apply fee every period
    
    # Interest rules
    interest_enabled = db.Column(db.Boolean, default=False)
    interest_rate = db.Column(db.Float, default=12.0)  # Annual percentage rate
    interest_compounding = db.Column(db.String(20), default="monthly")  # daily, monthly, yearly
    
    # Reminder settings
    reminder_before_due = db.Column(db.Boolean, default=True)
    reminder_before_days = db.Column(db.Integer, default=3)
    reminder_after_due = db.Column(db.Boolean, default=True)
    reminder_after_days = db.Column(db.Integer, default=1)
    reminder_method = db.Column(db.String(20), default="email")  # email, sms, both
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    
    
    
    # Relationships
    business = db.relationship("Business", backref=db.backref("finance_settings", uselist=False))
    updated_by_user = db.relationship("User", backref="finance_settings")


    