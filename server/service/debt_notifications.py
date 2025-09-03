# server/service/debt_notifications.py
import logging
from datetime import datetime
from io import BytesIO
from server.utils.pdf_utils import generate_debt_pdf
from server.service.finance_reminders import send_payment_reminder_email  

logger = logging.getLogger(__name__)

def send_debt_receipt(debt, send_email=True, send_sms=False):

    customer = debt.customer
    business = customer.business

    if not customer:
        logger.warning(f"Debt {debt.id} has no customer linked")
        return False

    # Build details dictionary for PDF
    details = {
        "customer_name": customer.customer_name,
        "business_name": business.name,
        "invoice_number": f"INV-{debt.id:05d}",
        "created_at": debt.created_at.strftime("%Y-%m-%d") if debt.created_at else None,
        "due_date": debt.due_date.strftime("%Y-%m-%d") if debt.due_date else None,
        "status": debt.status,
        "items": [
            {
                "name": item.name,
                "quantity": item.quantity,
                "unit_price": f"{item.price:.2f}",
                "total_price": f"{item.total_price:.2f}"
            }
            for item in debt.items
        ],
        "total": f"{debt.total:.2f}",
        "amount_paid": f"{debt.amount_paid:.2f}",
        "balance": f"{debt.balance:.2f}",
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Generate PDF buffer
    pdf_buffer = generate_debt_pdf(details)

    # Send email
    if send_email and customer.email:
        try:
            send_payment_reminder_email(
                customer_email=customer.email,
                customer_name=customer.customer_name,
                business_name=business.name,
                debt_details=details,
                reminder_type="receipt", 
                pdf_attachment=pdf_buffer  
            )
            logger.info(f"Debt receipt sent to {customer.email}")
        except Exception as e:
            logger.error(f"Failed to send debt receipt for Debt {debt.id}: {e}")

    # Send SMS (placeholder)
    if send_sms and customer.phone:
        # sms logic
        logger.info(f"Debt receipt SMS would be sent to {customer.phone}")

    return True
