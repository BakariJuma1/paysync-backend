from typing import Dict, Literal

# email template for payment reminder and receipt (separating concerns)


ReminderType = Literal["before_due", "overdue", "receipt"]

def subject_for_debt(business_name: str, debt_details: Dict, reminder_type: ReminderType) -> str:
    inv = debt_details.get("invoice_number", "N/A")
    if reminder_type == "before_due":
        return f"Upcoming Payment Due – {business_name}"
    if reminder_type == "overdue":
        return f"Payment Overdue – {business_name}"
    if reminder_type == "receipt":
        return f"Payment Receipt – {inv}"
    return f"Payment Notification – {business_name}"

def debt_email_html(business_name: str, customer_name: str, debt_details: Dict, reminder_type: ReminderType) -> str:
  
    items_rows = "".join([
        f"""
        <tr>
            <td style="border:1px solid #ddd; padding:8px;">{item.get('name','')}</td>
            <td style="border:1px solid #ddd; padding:8px; text-align:center;">{item.get('quantity',0)}</td>
            <td style="border:1px solid #ddd; padding:8px; text-align:right;">{item.get('unit_price','0.00')}</td>
            <td style="border:1px solid #ddd; padding:8px; text-align:right;">{item.get('total_price','0.00')}</td>
        </tr>
        """
        for item in debt_details.get("items", [])
    ]) or "<tr><td colspan='4' style='padding:8px; text-align:center;'>No items listed</td></tr>"

    # dynamic block
    if reminder_type == "before_due":
        message_block = f"""
            <p>This payment is due in {debt_details.get('days_until_due', 0)} days.</p>
            <p><strong>Late fees may apply if payment is not received by the due date.</strong></p>
        """
    elif reminder_type == "overdue":
        message_block = f"""
            <p>This payment is {abs(debt_details.get('days_overdue', 0))} days overdue.</p>
            <p><strong>Late fees of {debt_details.get('late_fee_amount', 'N/A')} have been applied.</strong></p>
        """
    elif reminder_type == "receipt":
        message_block = "<p>Thank you for your payment. This receipt confirms your transaction.</p>"
    else:
        message_block = "<p>Please review your account details below.</p>"

    title = "Invoice Receipt" if reminder_type == "receipt" else "Invoice Notice"

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="text-align:center; color:#444;">{business_name}</h2>
        <h3 style="text-align:center;">{title} - {debt_details.get('invoice_number', 'N/A')}</h3>
        <hr>

        <p>Hello <strong>{customer_name}</strong>,</p>
        <p>Here are the details of your account:</p>

        <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
            <tr><td style="border:1px solid #ddd; padding:8px; font-weight:bold;">Invoice #</td>
                <td style="border:1px solid #ddd; padding:8px;">{debt_details.get('invoice_number','N/A')}</td></tr>
            <tr><td style="border:1px solid #ddd; padding:8px; font-weight:bold;">Created At</td>
                <td style="border:1px solid #ddd; padding:8px;">{debt_details.get('created_at','N/A')}</td></tr>
            <tr><td style="border:1px solid #ddd; padding:8px; font-weight:bold;">Due Date</td>
                <td style="border:1px solid #ddd; padding:8px;">{debt_details.get('due_date','N/A')}</td></tr>
            <tr><td style="border:1px solid #ddd; padding:8px; font-weight:bold;">Status</td>
                <td style="border:1px solid #ddd; padding:8px;">{debt_details.get('status','N/A')}</td></tr>
        </table>

        <h3>Items Taken</h3>
        <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
            <thead>
                <tr style="background:#f5f5f5;">
                    <th style="border:1px solid #ddd; padding:8px;">Item</th>
                    <th style="border:1px solid #ddd; padding:8px;">Quantity</th>
                    <th style="border:1px solid #ddd; padding:8px;">Unit Price</th>
                    <th style="border:1px solid #ddd; padding:8px;">Total</th>
                </tr>
            </thead>
            <tbody>{items_rows}</tbody>
        </table>

        <h3>Payment Summary</h3>
        <table style="border-collapse: collapse; width: 50%; margin: 20px 0;">
            <tr><td style="border:1px solid #ddd; padding:8px; font-weight:bold;">Total</td>
                <td style="border:1px solid #ddd; padding:8px; text-align:right;">{debt_details.get('total','0.00')}</td></tr>
            <tr><td style="border:1px solid #ddd; padding:8px; font-weight:bold;">Amount Paid</td>
                <td style="border:1px solid #ddd; padding:8px; text-align:right;">{debt_details.get('amount_paid','0.00')}</td></tr>
            <tr><td style="border:1px solid #ddd; padding:8px; font-weight:bold;">Balance Due</td>
                <td style="border:1px solid #ddd; padding:8px; text-align:right;">{debt_details.get('balance','0.00')}</td></tr>
        </table>

        {message_block}

        <hr>
        <p style="text-align:center; font-size:12px; color:#888;">
            {business_name} | Generated on {debt_details.get('generated_at', 'N/A')}
        </p>
    </body>
    </html>
    """