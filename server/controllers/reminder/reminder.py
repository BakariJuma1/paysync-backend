from flask_restful import Resource, Api
from flask import request, make_response
from flask_jwt_extended import get_jwt_identity
from server.utils.decorators import role_required
from server.utils.roles import ROLE_OWNER
from server.models import db, Debt, User, Business, FinanceSettings

from server.utils.reminders import log_reminder
from server.service.debt_notifications import  send_debt_notification
from datetime import datetime
from . import reminder_bp
from server.utils.pdf_utils import generate_debt_pdf 

api = Api(reminder_bp)


class SendSingleReminder(Resource):
    @role_required(ROLE_OWNER)
    def post(self, debt_id):
        user_id = get_jwt_identity()
        debt = Debt.query.get_or_404(debt_id)

        # Ensure the debt belongs to owner’s business
        owner = User.query.get_or_404(user_id)
        if debt.business_id != owner.business_id:
            return {"message": "Not authorized for this debt"}, 403

        business = Business.query.get_or_404(debt.business_id)
        settings = getattr(business, "finance_settings", None)
        if not settings:
            settings = FinanceSettings(business_id=business.id)
            db.session.add(settings)

        # Recalculate totals & status
        debt.calculate_total()
        debt.update_status()
        db.session.add(debt)
        balance = float(debt.balance)

        # Build reminder details
        details = {
            "debt_id": debt.id,
            "invoice_number": f"INV-{debt.id:05d}",
            "customer_name": debt.customer.customer_name,
            "business_name": business.name,
            "created_at": debt.created_at.strftime("%Y-%m-%d") if debt.created_at else None,
            "due_date": debt.due_date.strftime("%Y-%m-%d") if debt.due_date else None,
            "amount_due": f"{balance:.2f} {settings.default_currency}",
            "status": debt.status,
            "items": [
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit_price": f"{item.price:.2f}",
                    "total_price": f"{item.total_price:.2f}",
                }
                for item in debt.items
            ],
            "total": f"{debt.total:.2f}",
            "amount_paid": f"{debt.amount_paid:.2f}",
            "balance": f"{debt.balance:.2f}",
            "late_fee_amount": f"{getattr(debt, 'late_fee_amount', 0.00):.2f}",
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Handle optional PDF download
        if request.args.get("download", "false").lower() == "true":
            pdf_buffer = generate_debt_pdf(details)
            response = make_response(pdf_buffer.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=reminder_{debt.id}.pdf'
            return response

        
        reminder_type = "before_due" if (debt.due_date and debt.due_date >= datetime.utcnow()) else "after_due"
        if reminder_type == "before_due":
            details["days_until_due"] = (debt.due_date - datetime.utcnow()).days if debt.due_date else None
        else:
            details["days_overdue"] = (datetime.utcnow() - debt.due_date).days if debt.due_date else None

        # Send notifications  reminder
        ok = send_debt_notification(
            debt,
            via_email=True,
            via_sms=False,
        )
        if ok:
            debt.last_reminder_sent = datetime.utcnow()
            debt.reminder_count = (debt.reminder_count or 0) + 1
            db.session.add(debt)
            log_reminder(debt, "email", "manual", "sent", actor_user_id=user_id)
            db.session.commit()
            return {"message": f"Reminder sent to {debt.customer.customer_name}"}, 200
        else:
            log_reminder(debt, "email", "manual", "failed", actor_user_id=user_id)
            db.session.commit()
            return {"message": "Failed to send reminder"}, 502


# business owner  send bulk reminders for debts in their business
class RunOwnerBulkReminders(Resource):
    @role_required(ROLE_OWNER)
    def post(self):
        user_id = get_jwt_identity()
        owner = User.query.get_or_404(user_id)
        business = Business.query.get_or_404(owner.business_id)

        # Fetch all active debts for this business
        debts = Debt.query.filter_by(business_id=business.id).all()
        sent_count, failed_count = 0, 0

        for debt in debts:
            if debt.balance <= 0:
                continue

          
            if debt.due_date and debt.due_date >= datetime.utcnow():
                reminder_type = "before_due"
            else:
                reminder_type = "after_due"

            ok = send_debt_notification(
                debt,
                kind=reminder_type,
                via_email=True,
                via_sms=False,
            )

            if ok:
                debt.last_reminder_sent = datetime.utcnow()
                debt.reminder_count = (debt.reminder_count or 0) + 1
                db.session.add(debt)
                log_reminder(debt, "email", "bulk", "sent", actor_user_id=user_id)
                sent_count += 1
            else:
                log_reminder(debt, "email", "bulk", "failed", actor_user_id=user_id)
                failed_count += 1

        db.session.commit()

        return {
            "message": f"Bulk reminder job executed",
            "sent": sent_count,
            "failed": failed_count
        }, 200


api.add_resource(SendSingleReminder, "/reminders/debts/<int:debt_id>")
api.add_resource(RunOwnerBulkReminders, "/reminders/run")
