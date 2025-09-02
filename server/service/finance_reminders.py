# server/service/finance_reminders.py
import os
import logging
import resend
from server.models import Debt, Customer, Business, FinanceSettings

logger = logging.getLogger(__name__)

# Configure Resend API key once
resend.api_key = os.getenv("RESEND_API_KEY")


def send_payment_reminder_email(customer_email, customer_name, business_name, debt_details, reminder_type):
    """
    Send a payment reminder email to a customer using Resend
    """
    sender = os.getenv("MAIL_DEFAULT_SENDER", f"{business_name} <no-reply@isaacjuma.site>")

    if reminder_type == "before_due":
        subject = f"Upcoming Payment Due: {business_name}"
    else:
        subject = f"Payment Overdue: {business_name}"

    html_content = f"""
    <html>
    <body>
        <h1>{'Payment Reminder' if reminder_type == 'before_due' else 'Payment Overdue'}</h1>
        <p>Hello <strong>{customer_name}</strong>,</p>
        <p>Here is your payment summary for invoice <strong>{debt_details.get('invoice_number', 'N/A')}</strong>:</p>
        
        <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Invoice #</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{debt_details.get('invoice_number', 'N/A')}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Due Date</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{debt_details.get('due_date', 'N/A')}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Amount Paid</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{debt_details.get('amount_paid', 'N/A')}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Amount Due</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{debt_details.get('amount_due', 'N/A')}</td>
            </tr>
        </table>

        <h3>Items Taken</h3>
        <ul>
            {"".join([f"<li>{item}</li>" for item in debt_details.get('items', [])])}
        </ul>

        {f"<p>This payment is due in {debt_details.get('days_until_due', 0)} days.</p>" if reminder_type == 'before_due' else 
          f"<p>This payment is {abs(debt_details.get('days_overdue', 0))} days overdue.</p>"}

        {f"<p><strong>Late fees may apply if payment is not received by the due date.</strong></p>" if reminder_type == 'before_due' else 
          f"<p><strong>Late fees of {debt_details.get('late_fee_amount', 'N/A')} have been applied.</strong></p>"}

        <p>Please make your payment at your earliest convenience.</p>
        <p>If you've already made this payment, please disregard this notice.</p>
        <p>Best regards,<br>{business_name}</p>
    </body>
    </html>
    """

    try:
        response = resend.Emails.send({
            "from": sender,
            "to": customer_email,
            "subject": subject,
            "html": html_content,
        })
        logger.info(
            f"Payment reminder email sent to {customer_email}. "
            f"Type: {reminder_type}. Response: {response}"
        )
        return True
    except Exception as e:
        logger.error(
            f"Failed to send payment reminder to {customer_email}. Resend error: {e}"
        )
        return False
