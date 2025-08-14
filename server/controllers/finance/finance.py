from flask import request
from flask_restful import Resource, Api
from flask_jwt_extended import get_jwt_identity
from datetime import datetime

from server.models import db, User, Business, FinanceSettings, ChangeLog
from server.utils.decorators import role_required
from server.utils.roles import ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON
from server.schemas.finance_schema import FinanceSettingsSchema
from . import finance_bp

finance_settings_schema = FinanceSettingsSchema()
finance_settings_list_schema = FinanceSettingsSchema(many=True)

api = Api(finance_bp)


def make_response(data, code=200):
    """Always return JSON-serializable dict/list"""
    if isinstance(data, (dict, list)):
        return data, code
    return {"message": str(data)}, code


class FinanceSettingsResource(Resource):
    @role_required(ROLE_OWNER, ROLE_ADMIN)
    def get(self, business_id):
        try:
            current_user_id = get_jwt_identity()

            # Verify business exists and user has access
            business = Business.query.get(business_id)
            if not business:
                return make_response({"message": "Business not found"}, 404)

            if not (current_user_id == business.owner_id or 
                    User.query.filter_by(id=current_user_id, business_id=business_id).first()):
                return make_response({"message": "Unauthorized access to business"}, 403)

            # Get or create settings
            settings = FinanceSettings.query.filter_by(business_id=business_id).first()
            if not settings:
                settings = self._create_default_settings(business_id)

            return make_response(finance_settings_schema.dump(settings))

        except Exception as e:
            return make_response({"message": "Server error", "error": str(e)}, 500)

    @role_required(ROLE_OWNER, ROLE_ADMIN)
    def put(self, business_id):
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            if not data:
                return make_response({"message": "No data provided"}, 400)

            business = Business.query.get(business_id)
            if not business:
                return make_response({"message": "Business not found"}, 404)

            if not (current_user_id == business.owner_id or 
                    User.query.filter_by(id=current_user_id, business_id=business_id).first()):
                return make_response({"message": "Unauthorized access to business"}, 403)

            settings = FinanceSettings.query.filter_by(business_id=business_id).first()
            if not settings:
                settings = self._create_default_settings(business_id)

            changes = self._update_settings(settings, data, current_user_id)
            if changes:
                self._log_changes(settings, changes, current_user_id)
                db.session.commit()

            return make_response(finance_settings_schema.dump(settings))

        except Exception as e:
            db.session.rollback()
            return make_response({"message": "Error updating settings", "error": str(e)}, 500)

    def _create_default_settings(self, business_id):
        default_settings = FinanceSettings(
            business_id=int(business_id),
            default_currency='USD',
            payment_due_day=1,
            grace_period_days=5,
            late_fee_type='percentage',
            late_fee_value=5.0,
            late_fee_max=0.0,
            late_fee_recurring=False,
            reminder_before_due=True,
            reminder_before_days=3,
            reminder_after_due=True,
            reminder_after_days=1,
            reminder_method='email'
        )
        db.session.add(default_settings)
        db.session.commit()
        return default_settings

    def _update_settings(self, settings, data, user_id):
        updatable_fields = [
            'default_currency', 'payment_due_day', 'grace_period_days',
            'late_fee_type', 'late_fee_value', 'late_fee_max', 'late_fee_recurring',
            'reminder_before_due', 'reminder_before_days',
            'reminder_after_due', 'reminder_after_days', 'reminder_method'
        ]
        changes = {}
        for field in updatable_fields:
            if field in data:
                old_value = getattr(settings, field)
                new_value = data[field]
                if field in ['payment_due_day', 'grace_period_days', 'reminder_before_days', 'reminder_after_days']:
                    new_value = int(new_value)
                elif field in ['late_fee_value', 'late_fee_max']:
                    new_value = float(new_value)
                elif field in ['late_fee_recurring', 'reminder_before_due', 'reminder_after_due']:
                    new_value = bool(new_value)
                if old_value != new_value:
                    setattr(settings, field, new_value)
                    changes[field] = {'old': old_value, 'new': new_value}
        if changes:
            settings.updated_at = datetime.utcnow()
            settings.updated_by = user_id
        return changes

    def _log_changes(self, settings, changes, user_id):
        log = ChangeLog(
            entity_type="finance_settings",
            entity_id=int(settings.id),
            action="update",
            changed_by=int(user_id),
            details={"changes": changes}
        )
        db.session.add(log)


class CurrencyOptionsResource(Resource):
    @role_required(ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON)
    def get(self):
        return make_response({
            "currencies": [
                {"code": "USD", "name": "US Dollar"},
                {"code": "EUR", "name": "Euro"},
                {"code": "GBP", "name": "British Pound"},
                {"code": "KES", "name": "Kenyan Shilling"},
                {"code": "UGX", "name": "Ugandan Shilling"},
                {"code": "TZS", "name": "Tanzanian Shilling"},
                {"code": "ZAR", "name": "South African Rand"},
            ]
        })


class PaymentTermsResource(Resource):
    @role_required(ROLE_OWNER, ROLE_ADMIN)
    def get(self, business_id):
        try:
            settings = FinanceSettings.query.filter_by(business_id=business_id).first()
            if not settings:
                settings = FinanceSettings(business_id=business_id)
                db.session.add(settings)
                db.session.commit()
            return make_response(finance_settings_schema.dump(settings, only=("payment_due_day", "grace_period_days")))
        except Exception as e:
            return make_response({"message": "Server error", "error": str(e)}, 500)


class LateFeeRulesResource(Resource):
    @role_required(ROLE_OWNER, ROLE_ADMIN)
    def get(self, business_id):
        try:
            settings = FinanceSettings.query.filter_by(business_id=business_id).first()
            if not settings:
                settings = FinanceSettings(business_id=business_id)
                db.session.add(settings)
                db.session.commit()
            return make_response(finance_settings_schema.dump(settings, only=(
                "late_fee_type", "late_fee_value", "late_fee_max", "late_fee_recurring"
            )))
        except Exception as e:
            return make_response({"message": "Server error", "error": str(e)}, 500)


class ReminderSettingsResource(Resource):
    @role_required(ROLE_OWNER, ROLE_ADMIN)
    def get(self, business_id):
        try:
            settings = FinanceSettings.query.filter_by(business_id=business_id).first()
            if not settings:
                settings = FinanceSettings(business_id=business_id)
                db.session.add(settings)
                db.session.commit()
            return make_response(finance_settings_schema.dump(settings, only=(
                "reminder_before_due", "reminder_before_days",
                "reminder_after_due", "reminder_after_days", "reminder_method"
            )))
        except Exception as e:
            return make_response({"message": "Server error", "error": str(e)}, 500)


# Register resources
api.add_resource(FinanceSettingsResource, "/settings/<int:business_id>")
api.add_resource(CurrencyOptionsResource, "/currencies")
api.add_resource(PaymentTermsResource, "/payment-terms/<int:business_id>")
api.add_resource(LateFeeRulesResource, "/late-fee-rules/<int:business_id>")
api.add_resource(ReminderSettingsResource, "/reminder-settings/<int:business_id>")
