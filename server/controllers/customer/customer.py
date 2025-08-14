from flask import request, jsonify
from flask_restful import Resource, Api
from flask_jwt_extended import jwt_required, get_jwt_identity
from server.models import Customer, Debt, User
from server.schemas.customer_schema import CustomerSchema
from server.extension import db
from . import customer_bp
from server.utils.decorators import role_required
from server.utils.roles import ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON
from server.utils.change_logger import log_change

api = Api(customer_bp)

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)


class CustomerResource(Resource):

    @jwt_required()
    @role_required(ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON)
    def get(self, customer_id=None):
        current_user_id = get_jwt_identity()
        current_user = User.query.get_or_404(current_user_id)

        if customer_id:
            customer = Customer.query.get_or_404(customer_id)

            # Salesperson restriction: only see customers tied to their debts
            if current_user.role == ROLE_SALESPERSON:
                debt_exists = Debt.query.filter_by(
                    customer_id=customer.id,
                    created_by=current_user_id
                ).first()
                if not debt_exists:
                    return jsonify({"message": "Access denied"}), 403

            return customer_schema.dump(customer), 200

        # Owners/Admins: see all customers
        if current_user.role in (ROLE_OWNER, ROLE_ADMIN):
            customers = Customer.query.all()
        else:
            # Salesperson: see only customers linked to their debts
            customer_ids = (
                db.session.query(Debt.customer_id)
                .filter_by(created_by=current_user_id)
                .distinct()
            )
            customers = Customer.query.filter(Customer.id.in_(customer_ids)).all()

        return customers_schema.dump(customers), 200

    @jwt_required()
    @role_required(ROLE_OWNER, ROLE_ADMIN)
    def post(self):
        data = request.get_json() or {}
        errors = customer_schema.validate(data)
        if errors:
            return jsonify(errors), 400

        customer = Customer(
            customer_name=data["customer_name"],
            phone=data["phone"],
            id_number=data["id_number"],
            business_id=data["business_id"],
            created_by=get_jwt_identity()
        )

        db.session.add(customer)
        db.session.flush()
        log_change("Customer", customer.id, "create", customer_schema.dump(customer))
        db.session.commit()

        return customer_schema.dump(customer), 201

    @jwt_required()
    @role_required(ROLE_OWNER, ROLE_ADMIN)
    def put(self, customer_id):
        customer = Customer.query.get_or_404(customer_id)
        data = request.get_json() or {}
        errors = customer_schema.validate(data, partial=True)
        if errors:
            return jsonify(errors), 400

        for key, value in data.items():
            if hasattr(customer, key):
                setattr(customer, key, value)

        db.session.add(customer)
        db.session.flush()
        log_change("Customer", customer.id, "update", customer_schema.dump(customer))
        db.session.commit()

        return customer_schema.dump(customer), 200

    @jwt_required()
    @role_required(ROLE_OWNER)
    def delete(self, customer_id):
        customer = Customer.query.get_or_404(customer_id)
        log_change("Customer", customer.id, "delete", customer_schema.dump(customer))
        db.session.delete(customer)
        db.session.commit()

        return jsonify({"message": f"Customer {customer_id} deleted"}), 200


api.add_resource(CustomerResource, "/customers", "/customers/<int:customer_id>")
