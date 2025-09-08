from flask import request, g
from flask_restful import Resource, Api
from flask_jwt_extended import jwt_required, get_jwt_identity
from server.models import Customer, Debt, User
from server.schemas.customer_schema import CustomerSchema
from server.extension import db
from . import customer_bp
from server.utils.decorators import role_required
from server.utils.roles import ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON
from server.utils.change_logger import log_change
from server.schemas.debt_schema import DebtSchema

api = Api(customer_bp)

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)
debt_schema = DebtSchema()
debts_schema = DebtSchema(many=True)

def can_access_customer(user, customer, allow_sales=False):
    if customer.business_id != user.business_id:
        return False
    if user.role in [ROLE_OWNER, ROLE_ADMIN]:
        return True
    if user.role == ROLE_SALESPERSON and allow_sales:
        debt_exists = Debt.query.filter_by(
            customer_id=customer.id,
            created_by=user.id
        ).first()
        return debt_exists is not None
    return False


class CustomerResource(Resource):

    @jwt_required()
    @role_required(ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON)
    def get(self, customer_id=None):
        current_user = User.query.get_or_404(get_jwt_identity())

        if customer_id:
            customer = Customer.query.get_or_404(customer_id)
            if not can_access_customer(current_user, customer, allow_sales=True):
                return {"message": "Access denied"}, 403
            debts = Debt.query.filter_by(customer_id=customer.id).all()
            debts_data = debts_schema.dump(debts)

            return {
                "customer": customer_schema.dump(customer), 
                "debts": debts_data
            }, 200
        print("Current user ID:", current_user.id)
        print("Current user role:", current_user.role)
        print("Current user business_id:", current_user.business_id)


        # List customers
        if current_user.role in [ROLE_OWNER, ROLE_ADMIN]:
            customers = Customer.query.filter_by(
                business_id=current_user.business_id
            ).all()
        else:  # Salesperson
            customer_ids = (
                db.session.query(Debt.customer_id)
                .filter_by(created_by=current_user.id)
                .distinct()
            )
            customers = Customer.query.filter(
                Customer.id.in_(customer_ids),
                Customer.business_id == current_user.business_id
            ).all()

            customers_with_debts = []
            for customer in customers:
                debts=Debt.query.filter_by(customer_id=customer.id).all()
                debts_data = debts_schema.dump(debts)
                customers_with_debts.append(
                    {
                        "customer": customer_schema.dump(customer),
                        "debts": debts_data
                    }
                )

        return {"customers": customers_with_debts}, 200

    @jwt_required()
    @role_required(ROLE_OWNER, ROLE_ADMIN)
    def post(self):
        current_user = User.query.get_or_404(get_jwt_identity())
        data = request.get_json() or {}
        errors = customer_schema.validate(data)
        if errors:
            return {"errors": errors}, 400

        if data.get("business_id") != current_user.business_id:
            return {"message": "Invalid business assignment"}, 403

        customer = Customer(
            customer_name=data["customer_name"],
            phone=data["phone"],
            id_number=data["id_number"],
            email=data["email"],
            business_id=current_user.business_id,
            created_by=current_user.id
        )

        db.session.add(customer)
        db.session.flush()
        log_change("Customer", customer.id, "create", customer_schema.dump(customer))
        db.session.commit()

        return {"customer": customer_schema.dump(customer)}, 201

    @jwt_required()
    @role_required(ROLE_OWNER, ROLE_ADMIN)
    def put(self, customer_id):
        current_user = User.query.get_or_404(get_jwt_identity())
        customer = Customer.query.get_or_404(customer_id)

        if not can_access_customer(current_user, customer):
            return {"message": "Access denied"}, 403

        data = request.get_json() or {}
        errors = customer_schema.validate(data, partial=True)
        if errors:
            return {"errors": errors}, 400

        for key, value in data.items():
            if hasattr(customer, key) and key != "business_id":
                setattr(customer, key, value)

        db.session.add(customer)
        db.session.flush()
        log_change("Customer", customer.id, "update", customer_schema.dump(customer))
        db.session.commit()

        return {"customer": customer_schema.dump(customer)}, 200

    @jwt_required()
    @role_required(ROLE_OWNER)
    def delete(self, customer_id):
        current_user = User.query.get_or_404(get_jwt_identity())
        customer = Customer.query.get_or_404(customer_id)

        if not can_access_customer(current_user, customer):
            return {"message": "Access denied"}, 403

        log_change("Customer", customer.id, "delete", customer_schema.dump(customer))
        db.session.delete(customer)
        db.session.commit()

        return {"message": f"Customer {customer_id} deleted"}, 200


api.add_resource(CustomerResource, "/customers", "/customers/<int:customer_id>")
