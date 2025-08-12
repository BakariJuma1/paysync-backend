# routes/finance.py
from flask_restful import Resource, Api
from flask_jwt_extended import get_jwt_identity
from server.models import db, User, Business, FinanceSettings, ChangeLog
from server.utils.decorators import role_required
from server.utils.helper import parse_json
from datetime import datetime
from . import finance_bp

api = Api(finance_bp)

class FinanceSettingsResource(Resource):
    @role_required(["owner", "admin"])
    def get(self, business_id):
        current_user_id = get_jwt_identity()
        
        # Verify user has access to this business
        business = Business.query.get(business_id)
        if not business:
            return {"message": "Business not found"}, 404
            
        if not (current_user_id == business.owner_id or 
                User.query.filter_by(id=current_user_id, business_id=business_id).first()):
            return {"message": "Unauthorized access to business"}, 403

        settings = FinanceSettings.query.filter_by(business_id=business_id).first()
        if not settings:
            # Create default settings if they don't exist
            settings = FinanceSettings(business_id=business_id)
            db.session.add(settings)
            db.session.commit()
        
        return settings.to_dict()

    @role_required(["owner", "admin"])
    def put(self, business_id):
        current_user_id = get_jwt_identity()
        
        # Verify user has access to this business
        business = Business.query.get(business_id)
        if not business:
            return {"message": "Business not found"}, 404
            
        if not (current_user_id == business.owner_id or 
                User.query.filter_by(id=current_user_id, business_id=business_id).first()):
            return {"message": "Unauthorized access to business"}, 403

        data, error, status = parse_json(
            optional_fields=[
                "default_currency",
                "payment_due_day", "grace_period_days",
                "late_fee_type", "late_fee_value", "late_fee_max", "late_fee_recurring",
                "interest_enabled", "interest_rate", "interest_compounding",
                "reminder_before_due", "reminder_before_days",
                "reminder_after_due", "reminder_after_days",
                "reminder_method"
            ]
        )
        if error:
            return error, status

        settings = FinanceSettings.query.filter_by(business_id=business_id).first()
        if not settings:
            settings = FinanceSettings(business_id=business_id)
            db.session.add(settings)

        # Track changes for audit log
        changes = {}
        for field, value in data.items():
            if hasattr(settings, field) and getattr(settings, field) != value:
                changes[field] = {
                    "old": getattr(settings, field),
                    "new": value
                }
                setattr(settings, field, value)

        settings.updated_by = current_user_id
        settings.updated_at = datetime.utcnow()

        # Log the changes if any were made
        if changes:
            log = ChangeLog(
                entity_type="finance_settings",
                entity_id=settings.id,
                action="update",
                changed_by=current_user_id,
                details={"changes": changes}
            )
            db.session.add(log)

        db.session.commit()

        return {"message": "Finance settings updated successfully", "settings": settings.to_dict()}


class CurrencyOptionsResource(Resource):
    @role_required(["owner", "admin", "salesperson"])
    def get(self):
        return {
            "currencies": [
                {"code": "USD", "name": "US Dollar"},
                {"code": "EUR", "name": "Euro"},
                {"code": "GBP", "name": "British Pound"},
                {"code": "KES", "name": "Kenyan Shilling"},
                {"code": "UGX", "name": "Ugandan Shilling"},
                {"code": "TZS", "name": "Tanzanian Shilling"},
                {"code": "ZAR", "name": "South African Rand"},
            ]
        }


class PaymentTermsResource(Resource):
    @role_required(["owner", "admin"])
    def get(self, business_id):
        current_user_id = get_jwt_identity()
        
        # Verify user has access to this business
        business = Business.query.get(business_id)
        if not business:
            return {"message": "Business not found"}, 404
            
        if not (current_user_id == business.owner_id or 
                User.query.filter_by(id=current_user_id, business_id=business_id).first()):
            return {"message": "Unauthorized access to business"}, 403

        settings = FinanceSettings.query.filter_by(business_id=business_id).first()
        if not settings:
            settings = FinanceSettings(business_id=business_id)
            db.session.add(settings)
            db.session.commit()
        
        return {
            "payment_due_day": settings.payment_due_day,
            "grace_period_days": settings.grace_period_days
        }


class LateFeeRulesResource(Resource):
    @role_required(["owner", "admin"])
    def get(self, business_id):
        current_user_id = get_jwt_identity()
        
        # Verify user has access to this business
        business = Business.query.get(business_id)
        if not business:
            return {"message": "Business not found"}, 404
            
        if not (current_user_id == business.owner_id or 
                User.query.filter_by(id=current_user_id, business_id=business_id).first()):
            return {"message": "Unauthorized access to business"}, 403

        settings = FinanceSettings.query.filter_by(business_id=business_id).first()
        if not settings:
            settings = FinanceSettings(business_id=business_id)
            db.session.add(settings)
            db.session.commit()
        
        return {
            "late_fee_type": settings.late_fee_type,
            "late_fee_value": settings.late_fee_value,
            "late_fee_max": settings.late_fee_max,
            "late_fee_recurring": settings.late_fee_recurring
        }


class ReminderSettingsResource(Resource):
    @role_required(["owner", "admin"])
    def get(self, business_id):
        current_user_id = get_jwt_identity()
        
        # Verify user has access to this business
        business = Business.query.get(business_id)
        if not business:
            return {"message": "Business not found"}, 404
            
        if not (current_user_id == business.owner_id or 
                User.query.filter_by(id=current_user_id, business_id=business_id).first()):
            return {"message": "Unauthorized access to business"}, 403

        settings = FinanceSettings.query.filter_by(business_id=business_id).first()
        if not settings:
            settings = FinanceSettings(business_id=business_id)
            db.session.add(settings)
            db.session.commit()
        
        return {
            "reminder_before_due": settings.reminder_before_due,
            "reminder_before_days": settings.reminder_before_days,
            "reminder_after_due": settings.reminder_after_due,
            "reminder_after_days": settings.reminder_after_days,
            "reminder_method": settings.reminder_method
        }


# Register resources
api.add_resource(FinanceSettingsResource, "/settings/<int:business_id>")
api.add_resource(CurrencyOptionsResource, "/currencies")
api.add_resource(PaymentTermsResource, "/payment-terms/<int:business_id>")
api.add_resource(LateFeeRulesResource, "/late-fee-rules/<int:business_id>")
api.add_resource(ReminderSettingsResource, "/reminder-settings/<int:business_id>")