from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime

def generate_debt_pdf(details, multiple_debts=False):
    """
    Generate a PDF for a single debt or multiple debts for a customer.

    Args:
        details (dict): Debt details or multiple debts details.
        multiple_debts (bool): True if generating for multiple debts.

    Returns:
        BytesIO: PDF buffer
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 50
    line_height = 18

    def draw_debt(d):
        y = height - margin
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin, y, f"Invoice: {d.get('invoice_number', 'N/A')}")
        y -= 30

        c.setFont("Helvetica", 12)
        c.drawString(margin, y, f"Customer: {d.get('customer_name', 'N/A')}")
        y -= line_height
        c.drawString(margin, y, f"Business: {d.get('business_name', 'N/A')}")
        y -= line_height
        c.drawString(margin, y, f"Status: {d.get('status', 'N/A')}")
        y -= 30

        c.drawString(margin, y, "Items:")
        y -= line_height
        for item in d.get('items', []):
            line = f"{item['name']} x {item['quantity']} @ {item['unit_price']} = {item['total_price']}"
            c.drawString(margin + 10, y, line)
            y -= line_height

        y -= 10
        c.drawString(margin, y, f"Total: {d.get('total', '0.00')}")
        y -= line_height
        c.drawString(margin, y, f"Amount Paid: {d.get('amount_paid', '0.00')}")
        y -= line_height
        c.drawString(margin, y, f"Balance: {d.get('balance', '0.00')}")
        y -= line_height
        generated_at = d.get('generated_at', datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        c.drawString(margin, y, f"Generated At: {generated_at}")
        y -= line_height + 10

        return y

    if multiple_debts:
        for debt in details.get("debts", []):
            y_pos = draw_debt(debt)
            c.showPage()  # New page for each debt
    else:
        draw_debt(details)
        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer
