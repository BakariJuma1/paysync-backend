from flask import request  
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
        try:
            current_user_id = get_jwt_identity()
            
            # Verify business exists and user has access
            business = Business.query.get(business_id)
            if not business:
                return {"message": "Business not found"}, 404
                
            if not (current_user_id == business.owner_id or 
                    User.query.filter_by(id=current_user_id, business_id=business_id).first()):
                return {"message": "Unauthorized access to business"}, 403

            # Get or create settings
            settings = FinanceSettings.query.filter_by(business_id=business_id).first()
            if not settings:
                settings = self._create_default_settings(business_id)
            
            # Explicit serialization
            return self._serialize_settings(settings), 200

        except Exception as e:
            return {"message": "Server error", "error": str(e)}, 500

    @role_required(["owner", "admin"])
    def put(self, business_id):
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json() or {}
            
            # Verify business and access
            business = Business.query.get(business_id)
            if not business:
                return {"message": "Business not found"}, 404
                
            if not (current_user_id == business.owner_id or 
                    User.query.filter_by(id=current_user_id, business_id=business_id).first()):
                return {"message": "Unauthorized access to business"}, 403

            # Get existing settings
            settings = FinanceSettings.query.filter_by(business_id=business_id).first()
            if not settings:
                settings = self._create_default_settings(business_id)

            # Update fields
            changes = self._update_settings(settings, data, current_user_id)
            
            if changes:
                self._log_changes(settings, changes, current_user_id)
                db.session.commit()

            return self._serialize_settings(settings), 200

        except Exception as e:
            db.session.rollback()
            return {"message": "Error updating settings", "error": str(e)}, 500

    def _create_default_settings(self, business_id):
        """Create default finance settings for a business"""
        default_settings = FinanceSettings(
            business_id=business_id,
            default_currency='USD',
            payment_due_day=1,
            grace_period_days=5,
            late_fee_type='percentage',
            late_fee_value=5.0,
            late_fee_recurring=False,
            reminder_before_due=True,
            reminder_before_days=3,
            reminder_after_due=True,
            reminder_after_days=1
        )
        db.session.add(default_settings)
        db.session.commit()
        return default_settings

    def _update_settings(self, settings, data, user_id):
        """Update settings fields and track changes"""
        updatable_fields = [
            'default_currency', 'payment_due_day', 'grace_period_days',
            'late_fee_type', 'late_fee_value', 'late_fee_recurring',
            'reminder_before_due', 'reminder_before_days',
            'reminder_after_due', 'reminder_after_days'
        ]
        
        changes = {}
        for field in updatable_fields:
            if field in data:
                old_value = getattr(settings, field)
                new_value = data[field]
                if old_value != new_value:
                    setattr(settings, field, new_value)
                    changes[field] = {'old': old_value, 'new': new_value}
        
        if changes:
            settings.updated_at = datetime.utcnow()
            settings.updated_by = user_id
            
        return changes

    def _log_changes(self, settings, changes, user_id):
        """Create audit log for settings changes"""
        log = ChangeLog(
            entity_type="finance_settings",
            entity_id=settings.id,
            action="update",
            changed_by=user_id,
            details={"changes": changes}
        )
        db.session.add(log)

    def _serialize_settings(self, settings):
        """Ensure consistent JSON serialization of settings"""
        return {
            "id": settings.id,
            "business_id": settings.business_id,
            "default_currency": settings.default_currency,
            "payment_due_day": settings.payment_due_day,
            "grace_period_days": settings.grace_period_days,
            "late_fee_type": settings.late_fee_type,
            "late_fee_value": float(settings.late_fee_value),
            "late_fee_max": float(settings.late_fee_max),
            "late_fee_recurring": settings.late_fee_recurring,
            "reminder_before_due": settings.reminder_before_due,
            "reminder_before_days": settings.reminder_before_days,
            "reminder_after_due": settings.reminder_after_due,
            "reminder_after_days": settings.reminder_after_days,
            "reminder_method": settings.reminder_method,
            "created_at": settings.created_at.isoformat() if settings.created_at else None,
            "updated_at": settings.updated_at.isoformat() if settings.updated_at else None
        }

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