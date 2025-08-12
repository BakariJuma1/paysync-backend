# server/tasks/finance_reminders.py
from datetime import datetime, timedelta
from server import db, create_app
from server.models import Debt, Customer, Business, FinanceSettings
from server.service.finance_reminders import send_payment_reminder_email
import logging

logger = logging.getLogger(__name__)

def process_payment_reminders():
    """Process all payment reminders that need to be sent"""
    app = create_app()
    with app.app_context():
        try:
            # Get all businesses with finance settings
            businesses = Business.query.join(FinanceSettings).all()
            
            for business in businesses:
                settings = business.finance_settings
                
                if not settings:
                    continue
                
                # Process before-due reminders
                if settings.reminder_before_due:
                    process_before_due_reminders(business, settings)
                
                # Process after-due reminders
                if settings.reminder_after_due:
                    process_after_due_reminders(business, settings)
                
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error processing payment reminders: {e}")
            db.session.rollback()

def process_before_due_reminders(business, settings):
    """Process reminders for payments that are about to be due"""
    reminder_date = datetime.utcnow() + timedelta(days=settings.reminder_before_days)
    
    debts = Debt.query.join(Customer).filter(
        Debt.customer.has(business_id=business.id),
        Debt.status.in_(['unpaid', 'partial']),
        Debt.due_date.between(datetime.utcnow(), reminder_date),
        Debt.last_reminder_sent != Debt.due_date  # Don't send multiple for same due date
    ).all()
    
    for debt in debts:
        customer = debt.customer
        days_until_due = (debt.due_date - datetime.utcnow()).days
        
        debt_details = {
            'debt_id': debt.id,
            'invoice_number': f"INV-{debt.id:05d}",
            'due_date': debt.due_date.strftime('%Y-%m-%d'),
            'amount_due': f"{debt.balance:.2f} {settings.default_currency}",
            'status': debt.status,
            'days_until_due': days_until_due
        }
        
        if send_payment_reminder_email(
            customer.email,
            customer.customer_name,
            business.name,
            debt_details,
            'before_due'
        ):
            debt.last_reminder_sent = datetime.utcnow()
            db.session.add(debt)

def process_after_due_reminders(business, settings):
    """Process reminders for overdue payments"""
    reminder_date = datetime.utcnow() - timedelta(days=settings.reminder_after_days)
    
    debts = Debt.query.join(Customer).filter(
        Debt.customer.has(business_id=business.id),
        Debt.status.in_(['unpaid', 'partial']),
        Debt.due_date <= datetime.utcnow(),
        Debt.due_date >= reminder_date,
        Debt.last_reminder_sent != Debt.due_date  # Don't send multiple for same due date
    ).all()
    
    for debt in debts:
        customer = debt.customer
        days_overdue = (datetime.utcnow() - debt.due_date).days
        
        # Calculate late fee if applicable
        late_fee_amount = 0
        if settings.late_fee_type != 'none' and days_overdue > settings.grace_period_days:
            if settings.late_fee_type == 'percentage':
                late_fee_amount = debt.balance * (settings.late_fee_value / 100)
                if settings.late_fee_max > 0:
                    late_fee_amount = min(late_fee_amount, settings.late_fee_max)
            else:
                late_fee_amount = settings.late_fee_value
        
        debt_details = {
            'debt_id': debt.id,
            'invoice_number': f"INV-{debt.id:05d}",
            'due_date': debt.due_date.strftime('%Y-%m-%d'),
            'amount_due': f"{debt.balance:.2f} {settings.default_currency}",
            'status': debt.status,
            'days_overdue': days_overdue,
            'late_fee_amount': f"{late_fee_amount:.2f} {settings.default_currency}" if late_fee_amount else "None"
        }
        
        if send_payment_reminder_email(
            customer.email,
            customer.customer_name,
            business.name,
            debt_details,
            'after_due'
        ):
            debt.last_reminder_sent = datetime.utcnow()
            db.session.add(debt)