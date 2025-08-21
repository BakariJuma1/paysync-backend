from flask_restful import Resource, Api
from flask import request, g
from flask_jwt_extended import jwt_required
from datetime import datetime
from server.extension import db
from server.models import Payment, Debt, User, Customer
from server.schemas.payment_schema import PaymentSchema
from server.utils.change_logger import log_change
from server.utils.roles import ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON
from server.utils.decorators import role_required
from . import payment_bp
from sqlalchemy.orm import joinedload

api = Api(payment_bp)

# Schemas
payment_schema = PaymentSchema()
payments_schema = PaymentSchema(many=True)


def can_access_payment(user, payment):
    """
    Enforce business scoping:
    - Admin: all payments within their business
    - Owner: all payments within their business
    - Salesperson: only payments they recorded, within their business
    """
    if not payment.debt or not payment.debt.customer:
        return False

    if payment.debt.customer.business_id != user.business_id:
        return False

    if user.role in [ROLE_ADMIN, ROLE_OWNER]:
        return True
    if user.role == ROLE_SALESPERSON:
        return payment.received_by == user.id
    return False


class PaymentResource(Resource):

    @role_required(ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON)
    def get(self, payment_id=None):
        current_user = g.current_user

        if payment_id:
            payment = Payment.query.options(
                joinedload(Payment.debt).joinedload(Debt.customer)
            ).get_or_404(payment_id)

            if not can_access_payment(current_user, payment):
                return {"message": "Access denied"}, 403

            return payment_schema.dump(payment), 200

        # List payments based on role and business
        if current_user.role in [ROLE_ADMIN, ROLE_OWNER]:
            payments = Payment.query.options(
                joinedload(Payment.debt).joinedload(Debt.customer)
            ).join(Debt).join(Customer).filter(
                Customer.business_id == current_user.business_id
            ).all()
        else:  # salesperson
            payments = Payment.query.options(
                joinedload(Payment.debt).joinedload(Debt.customer)
            ).join(Debt).join(Customer).filter(
                Customer.business_id == current_user.business_id,
                Payment.received_by == current_user.id
            ).all()

        return payments_schema.dump(payments), 200

    @role_required(ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON)
    def post(self):
        data = request.get_json() or {}
        current_user = g.current_user

        # Validate debt exists and belongs to user's business
        debt = Debt.query.options(joinedload(Debt.customer)).get_or_404(data.get("debt_id"))
        if debt.customer.business_id != current_user.business_id:
            return {"message": "You cannot record payments for another business"}, 403

        payment = Payment(
            debt_id=data["debt_id"],
            amount=data["amount"],
            method=data.get("method"),
            received_by=current_user.id,
            payment_date=datetime.utcnow()
        )

        db.session.add(payment)

        # Update debt status
        debt.amount_paid += payment.amount
        debt.update_status()

        db.session.commit()

        log_change("Payment", payment.id, "create", payment_schema.dump(payment))
        return payment_schema.dump(payment), 201

    @role_required(ROLE_OWNER, ROLE_ADMIN)
    def delete(self, payment_id):
        current_user = g.current_user
        payment = Payment.query.options(
            joinedload(Payment.debt).joinedload(Debt.customer)
        ).get_or_404(payment_id)

        if not can_access_payment(current_user, payment):
            return {"message": "Access denied"}, 403

        # Reverse effect on debt before delete
        if payment.debt:
            payment.debt.amount_paid -= payment.amount
            payment.debt.update_status()

        log_change("Payment", payment.id, "delete", payment_schema.dump(payment))

        db.session.delete(payment)
        db.session.commit()

        return {"message": f"Payment {payment_id} deleted"}, 200

    @role_required(ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON)
    def patch(self, payment_id):
        current_user = g.current_user
        payment = Payment.query.options(
            joinedload(Payment.debt).joinedload(Debt.customer)
        ).get_or_404(payment_id)

        if not can_access_payment(current_user, payment):
            return {"message": "Access denied"}, 403

        # Salespeople can only edit their own payments
        if current_user.role == ROLE_SALESPERSON and payment.received_by != current_user.id:
            return {"error": "You can only edit payments you recorded"}, 403

        data = request.get_json() or {}

        # Adjust debt balance if amount changes
        if "amount" in data:
            old_amount = payment.amount
            new_amount = data["amount"]

            if payment.debt:
                payment.debt.amount_paid -= old_amount
                payment.debt.amount_paid += new_amount
                payment.debt.update_status()

            payment.amount = new_amount

        if "method" in data:
            payment.method = data["method"]

        if "payment_date" in data:
            try:
                payment.payment_date = datetime.fromisoformat(data["payment_date"])
            except ValueError:
                return {"error": "Invalid date format. Use ISO format."}, 400

        db.session.commit()

        log_change("Payment", payment.id, "update", payment_schema.dump(payment))
        return payment_schema.dump(payment), 200


api.add_resource(PaymentResource, "/payments", "/payments/<int:payment_id>")
