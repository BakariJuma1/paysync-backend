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
    sender = os.getenv("MAIL_DEFAULT_SENDER", f"{business_name} <no-reply@isaac-juma.site>")

    if reminder_type == "before_due":
        subject = f"Upcoming Payment Due: {business_name}"
    else:
        subject = f"Payment Overdue: {business_name}"

    # Build items table HTML
    items_rows = "".join([
        f"""
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">{item.get('name', '')}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align:center;">{item.get('quantity', 0)}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align:right;">{item.get('unit_price', '0.00')}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align:right;">{item.get('total_price', '0.00')}</td>
        </tr>
        """
        for item in debt_details.get("items", [])
    ]) or "<tr><td colspan='4' style='padding:8px; text-align:center;'>No items listed</td></tr>"

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="text-align:center; color:#444;">{business_name}</h2>
        <h3 style="text-align:center;">Invoice Receipt - {debt_details.get('invoice_number', 'N/A')}</h3>
        <hr>

        <p>Hello <strong>{customer_name}</strong>,</p>
        <p>Here are the details of your account:</p>

        <!-- Invoice Summary -->
        <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Invoice #</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{debt_details.get('invoice_number', 'N/A')}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Created At</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{debt_details.get('created_at', 'N/A')}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Due Date</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{debt_details.get('due_date', 'N/A')}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Status</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{debt_details.get('status', 'N/A')}</td>
            </tr>
        </table>

        <!-- Items Table -->
        <h3>Items Taken</h3>
        <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
            <thead>
                <tr style="background:#f5f5f5;">
                    <th style="border: 1px solid #ddd; padding: 8px;">Item</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Quantity</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Unit Price</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Total</th>
                </tr>
            </thead>
            <tbody>
                {items_rows}
            </tbody>
        </table>

        <!-- Payment Summary -->
        <h3>Payment Summary</h3>
        <table style="border-collapse: collapse; width: 50%; margin: 20px 0;">
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Total</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align:right;">{debt_details.get('total', '0.00')}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Amount Paid</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align:right;">{debt_details.get('amount_paid', '0.00')}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Balance Due</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align:right;">{debt_details.get('balance', '0.00')}</td>
            </tr>
        </table>

        <!-- Reminder Text -->
        {f"<p>This payment is due in {debt_details.get('days_until_due', 0)} days.</p>" if reminder_type == 'before_due' else 
          f"<p>This payment is {abs(debt_details.get('days_overdue', 0))} days overdue.</p>"}

        {f"<p><strong>Late fees may apply if payment is not received by the due date.</strong></p>" if reminder_type == 'before_due' else 
          f"<p><strong>Late fees of {debt_details.get('late_fee_amount', 'N/A')} have been applied.</strong></p>"}

        <p>Please make your payment at your earliest convenience.</p>
        <p>If you've already made this payment, please disregard this notice.</p>

        <hr>
        <p style="text-align:center; font-size: 12px; color:#888;">{business_name} | Generated on {debt_details.get('generated_at', 'N/A')}</p>
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
