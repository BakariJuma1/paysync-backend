# server/utils/reminders.py
from datetime import datetime, timedelta
from flask import has_request_context
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import or_
from server.extension import db
from server.models import ChangeLog, Debt

REMINDER_COOLDOWN_DAYS = 1  # avoid resending within 24h

def should_send_today_qexpr(now=None):
    """SQL expression to ensure we didn't send within cooldown window."""
    now = now or datetime.utcnow()
    cutoff = now - timedelta(days=REMINDER_COOLDOWN_DAYS)
    return or_(Debt.last_reminder_sent.is_(None), Debt.last_reminder_sent < cutoff)

def log_reminder(debt, channel, reminder_type, status="sent", actor_user_id=None):
    """Create a ChangeLog row for a reminder (works with/without request ctx)."""
    try:
        if actor_user_id is None and has_request_context():
            actor_user_id = get_jwt_identity()
    except Exception:
        actor_user_id = actor_user_id  # leave as passed (None/system)

    entry = ChangeLog(
        entity_type="Debt",
        entity_id=debt.id,
        action="reminder",
        changed_by=actor_user_id,  # None == system/auto
        details={
            "channel": channel,                
            "reminder_type": reminder_type,     
            "status": status,
            "debt_status": debt.status,
            "balance": float(debt.balance),
            "due_date": debt.due_date.isoformat() if debt.due_date else None,
        }
    )
    db.session.add(entry)
