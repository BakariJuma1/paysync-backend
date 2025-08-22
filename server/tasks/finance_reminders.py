from datetime import datetime, timedelta
import logging
from sqlalchemy import and_
from server import db, create_app
from server.models import Debt, Customer, Business, FinanceSettings
from server.service.finance_reminders import send_payment_reminder_email
from server.utils.reminders import should_send_today_qexpr, log_reminder

logger = logging.getLogger(__name__)

def process_payment_reminders():
    """Run for ALL businesses on schedule."""
    app = create_app()
    with app.app_context():
        try:
            businesses = Business.query.join(FinanceSettings).all()
            for business in businesses:
                process_business_reminders(business)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error processing payment reminders: {e}", exc_info=True)
            db.session.rollback()

def process_business_reminders(business, actor_user_id=None):
    """Run for ONE business (used by scheduler or manual bulk trigger)."""
    settings = getattr(business, "finance_settings", None)
    if not settings:
        return

    if getattr(settings, "reminder_before_due", False):
        _process_before_due(business, settings, actor_user_id)

    if getattr(settings, "reminder_after_due", False):
        _process_after_due(business, settings, actor_user_id)

def _process_before_due(business, settings, actor_user_id=None):
    """Payments due within N days (before due)."""
    now = datetime.utcnow()
    window_end = now + timedelta(days=settings.reminder_before_days)

    debts = (
        Debt.query.join(Customer)
        .filter(
            Customer.business_id == business.id,
            Debt.status.in_(["unpaid", "partial"]),
            Debt.due_date.isnot(None),
            Debt.due_date.between(now, window_end),
            should_send_today_qexpr(now)              # cooldown
        )
        .all()
    )

    for debt in debts:
        cust = debt.customer
        if not getattr(cust, "email", None):
            continue

        days_until_due = (debt.due_date - now).days
        debt_details = {
            "debt_id": debt.id,
            "invoice_number": f"INV-{debt.id:05d}",
            "due_date": debt.due_date.strftime("%Y-%m-%d"),
            "amount_due": f"{float(debt.balance):.2f} {settings.default_currency}",
            "status": debt.status,
            "days_until_due": days_until_due,
        }

        ok = send_payment_reminder_email(
            cust.email, cust.customer_name, business.name, debt_details, "before_due"
        )
        if ok:
            debt.last_reminder_sent = now
            debt.reminder_count = (debt.reminder_count or 0) + 1
            db.session.add(debt)
            log_reminder(debt, "email", "before_due", "sent", actor_user_id)
        else:
            log_reminder(debt, "email", "before_due", "failed", actor_user_id)

def _process_after_due(business, settings, actor_user_id=None):
    """Overdue payments within N days back (after due)."""
    now = datetime.utcnow()
    window_start = now - timedelta(days=settings.reminder_after_days)

    debts = (
        Debt.query.join(Customer)
        .filter(
            Customer.business_id == business.id,
            Debt.status.in_(["unpaid", "partial"]),
            Debt.due_date.isnot(None),
            Debt.due_date <= now,
            Debt.due_date >= window_start,
            should_send_today_qexpr(now)              # cooldown
        )
        .all()
    )

    for debt in debts:
        cust = debt.customer
        if not getattr(cust, "email", None):
            continue

        days_overdue = (now - debt.due_date).days

        # Late fee calculation
        late_fee_amount = 0
        if settings.late_fee_type != "none" and days_overdue > settings.grace_period_days:
            if settings.late_fee_type == "percentage":
                late_fee_amount = float(debt.balance) * (settings.late_fee_value / 100.0)
                if settings.late_fee_max and settings.late_fee_max > 0:
                    late_fee_amount = min(late_fee_amount, settings.late_fee_max)
            else:
                late_fee_amount = settings.late_fee_value

        debt_details = {
            "debt_id": debt.id,
            "invoice_number": f"INV-{debt.id:05d}",
            "due_date": debt.due_date.strftime("%Y-%m-%d"),
            "amount_due": f"{float(debt.balance):.2f} {settings.default_currency}",
            "status": debt.status,
            "days_overdue": days_overdue,
            "late_fee_amount": f"{late_fee_amount:.2f} {settings.default_currency}" if late_fee_amount else "None",
        }

        ok = send_payment_reminder_email(
            cust.email, cust.customer_name, business.name, debt_details, "after_due"
        )
        if ok:
            debt.last_reminder_sent = now
            debt.reminder_count = (debt.reminder_count or 0) + 1
            db.session.add(debt)
            log_reminder(debt, "email", "after_due", "sent", actor_user_id)
        else:
            log_reminder(debt, "email", "after_due", "failed", actor_user_id)
