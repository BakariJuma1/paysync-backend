from flask_restful import Resource, Api
from flask import make_response
from flask_jwt_extended import get_jwt_identity
from server.utils.decorators import role_required
from server.utils.roles import ROLE_OWNER
from server.models import db, Debt, User, Business, Customer
from . import export_bp
from server.utils.pdf_utils import generate_debt_pdf  # We'll adjust this function to accept multiple debts

api = Api(export_bp)

class ExportCustomerReceipt(Resource):
    @role_required(ROLE_OWNER)
    def get(self, customer_id):
        """
        Export a PDF receipt for all debts of a specific customer.
        """
        # Step 1: Identify owner and customer
        user_id = get_jwt_identity()
        owner = User.query.get_or_404(user_id)
        customer = Customer.query.get_or_404(customer_id)

        # Step 2: Ensure customer belongs to this owner's business
        if customer.business_id != owner.business_id:
            return {"message": "Not authorized for this customer"}, 403

        business = Business.query.get_or_404(customer.business_id)

        # Step 3: Collect all debts for this customer
        debts = Debt.query.filter_by(customer_id=customer.id).all()
        if not debts:
            return {"message": "No debts found for this customer"}, 404

        # Step 4: Build a details dictionary for PDF
        details = {
            "customer_name": customer.customer_name,
            "business_name": business.name,
            "currency": getattr(business.finance_settings, "default_currency", "USD"),
            "debts": [
                {
                    "debt_id": d.id,
                    "invoice_number": f"INV-{d.id:05d}",
                    "created_at": d.created_at.strftime("%Y-%m-%d") if d.created_at else None,
                    "due_date": d.due_date.strftime("%Y-%m-%d") if d.due_date else None,
                    "status": d.status,
                    "items": [
                        {
                            "name": item.name,
                            "quantity": item.quantity,
                            "unit_price": f"{item.price:.2f}",
                            "total_price": f"{item.total_price:.2f}",
                        }
                        for item in d.items
                    ],
                    "total": f"{d.total:.2f}",
                    "amount_paid": f"{d.amount_paid:.2f}",
                    "balance": f"{d.balance:.2f}",
                }
                for d in debts
            ],
        }

       
        pdf_buffer = generate_debt_pdf(details, multiple_debts=True)

        
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=receipts_customer_{customer.id}.pdf'
        return response

api.add_resource(ExportCustomerReceipt, "/export/receipt/customer/<int:customer_id>")
