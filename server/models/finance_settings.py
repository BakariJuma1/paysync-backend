
from datetime import datetime
from server.extension import db
from sqlalchemy_serializer import SerializerMixin

class FinanceSettings(db.Model, SerializerMixin):
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
    
    serialize_rules = (
        '-business.finance_settings',
        '-updated_by_user.finance_settings',
    )
    
    # Relationships
    business = db.relationship("Business", backref=db.backref("finance_settings", uselist=False))
    updated_by_user = db.relationship("User", backref="finance_settings")


    def to_dict(self):
        
        return {
            'id': self.id,
            'business_id': self.business_id,
            'default_currency': self.default_currency,
            'payment_due_day': self.payment_due_day,
            'grace_period_days': self.grace_period_days,
            'late_fee_type': self.late_fee_type,
            'late_fee_value': float(self.late_fee_value),
            'late_fee_max': float(self.late_fee_max),
            'late_fee_recurring': self.late_fee_recurring,
            'interest_enabled': self.interest_enabled,
            'interest_rate': float(self.interest_rate),
            'interest_compounding': self.interest_compounding,
            'reminder_before_due': self.reminder_before_due,
            'reminder_before_days': self.reminder_before_days,
            'reminder_after_due': self.reminder_after_due,
            'reminder_after_days': self.reminder_after_days,
            'reminder_method': self.reminder_method,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': self.updated_by
        }