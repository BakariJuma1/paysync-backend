from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

def generate_debt_pdf(details):
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"Invoice: {details['invoice_number']}")
    y -= 30

    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Customer: {details['customer_name']}")
    y -= 20
    c.drawString(50, y, f"Business: {details['business_name']}")
    y -= 20
    c.drawString(50, y, f"Status: {details['status']}")
    y -= 30

    c.drawString(50, y, "Items:")
    y -= 20
    for item in details['items']:
        line = f"{item['name']} x {item['quantity']} @ {item['unit_price']} = {item['total_price']}"
        c.drawString(60, y, line)
        y -= 20

    y -= 10
    c.drawString(50, y, f"Total: {details['total']}")
    y -= 20
    c.drawString(50, y, f"Amount Paid: {details['amount_paid']}")
    y -= 20
    c.drawString(50, y, f"Balance: {details['balance']}")
    y -= 20
    c.drawString(50, y, f"Generated At: {details['generated_at']}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
