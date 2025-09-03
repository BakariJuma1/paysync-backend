import logging
from datetime import datetime
from server.utils.pdf_utils import generate_debt_pdf
from server.utils.email_templates import subject_for_debt, debt_email_html
from server.service.notifications.email_sender import send_email, make_pdf_attachment
from server.service.notifications.sms_sender import send_sms 
import os 

logger = logging.getLogger(__name__)

def _build_debt_details(debt):
    customer = debt.customer
    business = customer.business if customer else None
    return {
        "customer_name": customer.customer_name if customer else "N/A",
        "business_name": business.name if business else "N/A",
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

def send_debt_notification(debt, kind: str = "receipt", via_email: bool = True, via_sms: bool = False) -> bool:
   
    customer = debt.customer
    if not customer:
        logger.warning(f"Debt {debt.id} has no customer linked")
        return False

    business = customer.business
    details = _build_debt_details(debt)

    # Build email components
    subject = subject_for_debt(business.name, details, kind)  
    html = debt_email_html(business.name, customer.customer_name, details, kind)  

    # PDF
    pdf_buffer = generate_debt_pdf(details)  
    attachment = make_pdf_attachment(
        filename=f"Invoice-{details.get('invoice_number','N/A')}.pdf",
        pdf_buffer=pdf_buffer,
    )

    # Email channel
    if via_email and customer.email:
        try:
            send_email(
                to=customer.email,
                subject=subject,
                html=html,
                attachments=[attachment],
                sender=os.getenv("MAIL_DEFAULT_SENDER", f"{business.name} <no-reply@{business.name.lower().replace(' ', '')}.com>")
            )
            logger.info(f"Debt {debt.id}: email sent to {customer.email} [{kind}]")
        except Exception as e:
            logger.error(f"Debt {debt.id}: failed to send email [{kind}] -> {e}")

    #
    if via_sms and customer.phone:
        # future  implimentation 
        logger.info(f"[SMS placeholder] Debt {debt.id}: would send SMS to {customer.phone} [{kind}]")

    return True
