from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from io import BytesIO

def generate_dashboard_pdf(dashboard_data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']

    # --- BUSINESS TITLE ---
    business_name = dashboard_data.get('business', {}).get('name', 'Business')
    elements.append(Paragraph(f"{business_name} - Business Report", title_style))
    elements.append(Spacer(1, 12))

    # --- DASHBOARD SUMMARY ---
    summary = dashboard_data.get('summary', {})
    elements.append(Paragraph("Summary", subtitle_style))
    summary_data = [
        ["Total Debts", summary.get("total_debts", 0)],
        ["Total Amount", f"{summary.get('total_amount', 0):.2f}"],
        ["Total Paid", f"{summary.get('total_paid', 0):.2f}"],
        ["Total Balance", f"{summary.get('total_balance', 0):.2f}"],
        ["Recovery Rate (%)", f"{summary.get('recovery_rate', 0):.2f}"],
        ["Average Repayment Days", f"{summary.get('avg_repayment_days', 0):.2f}"]
    ]
    table = Table(summary_data, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN',(0,0),(-1,-1),'LEFT')
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))

    # --- CUSTOMER DEBTS ---
    elements.append(Paragraph("Top Debtors", subtitle_style))
    customers = dashboard_data.get("customer_segmentation", {}).get("top_debtors", [])
    if customers:
        cust_data = [["Customer", "Phone", "Amount Due", "Status"]]
        for cust in customers:
            cust_data.append([
                cust['customer'],
                cust['phone'],
                f"{cust['amount']:.2f}",
                cust['status']
            ])
        cust_table = Table(cust_data, hAlign='LEFT')
        cust_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black)
        ]))
        elements.append(cust_table)
    else:
        elements.append(Paragraph("No customer debt data available", normal_style))
    elements.append(Spacer(1, 12))

    # --- UPCOMING PAYMENTS ---
    elements.append(Paragraph("Upcoming Payments (next 30 days)", subtitle_style))
    upcoming = dashboard_data.get("upcoming_due_payments", [])
    if upcoming:
        upcoming_data = [["Customer", "Due Date", "Amount"]]
        for p in upcoming:
            upcoming_data.append([
                p['customer'],
                p['due_date'],
                f"{p['amount']:.2f}"
            ])
        table_up = Table(upcoming_data, hAlign='LEFT')
        table_up.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black)
        ]))
        elements.append(table_up)
    else:
        elements.append(Paragraph("No upcoming payments", normal_style))
    elements.append(Spacer(1, 12))

    # --- OVERDUE DEBTS ---
    elements.append(Paragraph("Overdue Debts", subtitle_style))
    overdue = dashboard_data.get("overdue_debts", [])
    if overdue:
        overdue_data = [["Customer", "Due Date", "Balance", "Salesperson"]]
        for d in overdue:
            overdue_data.append([
                d['customer'],
                d['due_date'],
                f"{d['balance']:.2f}",
                d['salesperson']
            ])
        table_od = Table(overdue_data, hAlign='LEFT')
        table_od.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black)
        ]))
        elements.append(table_od)
    else:
        elements.append(Paragraph("No overdue debts", normal_style))
    elements.append(Spacer(1, 12))

    # --- TEAM PERFORMANCE ---
    elements.append(Paragraph("Team Performance", subtitle_style))
    team = dashboard_data.get("team_performance", [])
    if team:
        team_data = [["Salesperson", "Debts Count", "Total Assigned", "Total Collected"]]
        for t in team:
            team_data.append([
                t['salesperson'],
                t['debts_count'],
                f"{t['total_assigned']:.2f}",
                f"{t['total_collected']:.2f}"
            ])
        team_table = Table(team_data, hAlign='LEFT')
        team_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black)
        ]))
        elements.append(team_table)
    else:
        elements.append(Paragraph("No team performance data", normal_style))
    elements.append(Spacer(1, 12))

    # --- COMMUNICATION LOGS ---
    elements.append(Paragraph("Recent Communications", subtitle_style))
    logs = dashboard_data.get("communication_logs", [])
    if logs:
        logs_data = [["Message", "Timestamp", "Debt ID"]]
        for l in logs:
            logs_data.append([
                l['message'],
                l['timestamp'],
                l['debt_id']
            ])
        logs_table = Table(logs_data, hAlign='LEFT')
        logs_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black)
        ]))
        elements.append(logs_table)
    else:
        elements.append(Paragraph("No recent communications", normal_style))
    elements.append(Spacer(1, 12))

    # --- Build PDF ---
    doc.build(elements)
    buffer.seek(0)
    return buffer
