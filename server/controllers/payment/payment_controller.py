from flask_restful import Resource, Api
from flask import request, jsonify, g
from flask_jwt_extended import jwt_required
from datetime import datetime
from server.extension import db
from server.models import Payment, Debt, User
from server.schemas.payment_schema import PaymentSchema
from server.utils.change_logger import log_change
from server.utils.roles import ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON
from server.utils.decorators import role_required
from . import payment_bp


api = Api(payment_bp)

# Schemas
payment_schema = PaymentSchema()
payments_schema = PaymentSchema(many=True)

class PaymentResource(Resource):

    @role_required(ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON)
    def get(self, payment_id=None):
        current_user = g.current_user

        if payment_id:
            payment = Payment.query.get_or_404(payment_id)
            return payment_schema.dump(payment), 200

        # Owners/Admins see all; salespeople see their own received payments
        if current_user.role in [ROLE_OWNER, ROLE_ADMIN]:
            payments = Payment.query.all()
        else:
            payments = Payment.query.filter_by(received_by=current_user.id).all()

        return payments_schema.dump(payments), 200

    @role_required(ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON)
    def post(self):
        data = request.get_json() or {}
        current_user = g.current_user

        # Validate debt exists
        debt = Debt.query.get_or_404(data.get("debt_id"))

        payment = Payment(
            debt_id=data["debt_id"],
            amount=data["amount"],
            method=data.get("method"),
            received_by=current_user.id,
            payment_date=datetime.utcnow()
        )

        db.session.add(payment)

        # update debt balance
        debt.amount_paid += payment.amount
        debt.update_balance()

        db.session.commit()

        log_change("Payment", payment.id, "create", payment_schema.dump(payment))
        return payment_schema.dump(payment), 201

    @role_required(ROLE_OWNER, ROLE_ADMIN)
    def delete(self, payment_id):
        payment = Payment.query.get_or_404(payment_id)

        # Reverse effect on debt before delete
        if payment.debt:
            payment.debt.amount_paid -= payment.amount
            payment.debt.update_balance()

        log_change("Payment", payment.id, "delete", payment_schema.dump(payment))

        db.session.delete(payment)
        db.session.commit()

        return {"message": f"Payment {payment_id} deleted"}, 200

    @role_required(ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON)
    def patch(self, payment_id):
        current_user = g.current_user
        payment = Payment.query.get_or_404(payment_id)

        # Salespeople can only edit their own payments
        if current_user.role == ROLE_SALESPERSON and payment.received_by != current_user.id:
            return {"error": "You can only edit payments you made"}, 403

        data = request.get_json() or {}

        # Adjust debt balance safely if amount changes
        if "amount" in data:
            old_amount = payment.amount
            new_amount = data["amount"]

            if payment.debt:
                payment.debt.amount_paid -= old_amount
                payment.debt.amount_paid += new_amount
                payment.debt.update_balance()

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
