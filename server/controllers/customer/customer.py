from flask import request, jsonify
from flask_restful import Resource, Api
from flask_jwt_extended import jwt_required, get_jwt_identity
from server.models import Customer, Debt, User
from server.schemas.customer_schema import CustomerSchema
from server.extension import db
from . import customer_bp
from server.utils.decorators import role_required

api = Api(customer_bp)

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

class CustomerResource(Resource):

    @jwt_required()
    @role_required("owner", "admin", "salesperson")
    def get(self, customer_id=None):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if customer_id:
            customer = Customer.query.get_or_404(customer_id)
            # Salesperson can only access customers they gave debt to
            if current_user.role == "salesperson":
                debt_exists = Debt.query.filter_by(customer_id=customer.id, created_by=current_user_id).first()
                if not debt_exists:
                    return jsonify({"message": "Access denied"}), 403
            return customer_schema.dump(customer), 200

        # List all customers based on role
        if current_user.role in ["owner", "admin"]:
            customers = Customer.query.all()
        else:  # salesperson
            customer_ids = db.session.query(Debt.customer_id).filter_by(created_by=current_user_id).distinct()
            customers = Customer.query.filter(Customer.id.in_(customer_ids)).all()

        return customers_schema.dump(customers), 200

    @jwt_required()
    @role_required("owner", "admin")
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
        db.session.commit()
        return customer_schema.dump(customer), 201

    @jwt_required()
    @role_required("owner", "admin")
    def put(self, customer_id):
        customer = Customer.query.get_or_404(customer_id)
        data = request.get_json() or {}
        errors = customer_schema.validate(data, partial=True)
        if errors:
            return jsonify(errors), 400

        for key, value in data.items():
            if hasattr(customer, key):
                setattr(customer, key, value)

        db.session.commit()
        return customer_schema.dump(customer), 200

    @jwt_required()
    @role_required("owner")  # only owners can delete
    def delete(self, customer_id):
        customer = Customer.query.get_or_404(customer_id)
        db.session.delete(customer)
        db.session.commit()
        return jsonify({"message": f"Customer {customer_id} deleted"}), 200


# Register the resource
api.add_resource(CustomerResource, "/customers", "/customers/<int:customer_id>")
