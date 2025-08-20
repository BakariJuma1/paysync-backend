from flask_restful import Resource, Api
from flask import request, jsonify, g
from flask_jwt_extended import jwt_required
from server.models import Debt, User, Item, Customer
from server.extension import db
from datetime import datetime
from . import debt_bp
from server.schemas.debt_schema import DebtSchema
from server.utils.change_logger import log_change
from server.utils.roles import ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON
from server.utils.decorators import role_required
from sqlalchemy.orm import joinedload

api = Api(debt_bp)

# Schemas
debt_schema = DebtSchema()
debts_schema = DebtSchema(many=True)


# -------------------------------------------
# Access Control Helper
# -------------------------------------------
def can_access_debt(user, debt):
    """
    Restrict all roles to their business only.
    - Admins: all debts in their business
    - Owners: all debts in their business
    - Salespersons: only debts they created in their business
    """
    if not debt.customer or debt.customer.business_id != user.business_id:
        return False

    if user.role in [ROLE_ADMIN, ROLE_OWNER]:
        return True
    if user.role == ROLE_SALESPERSON:
        return debt.created_by == user.id
    return False


class DebtResource(Resource):

    @role_required(ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON)
    def get(self, debt_id=None):
        current_user = g.current_user

        if debt_id:
            debt = Debt.query.options(joinedload(Debt.customer)).get_or_404(debt_id)
            if not can_access_debt(current_user, debt):
                return {"message": "Access denied"}, 403
            return debt_schema.dump(debt), 200

        # Collection fetch
        if current_user.role in [ROLE_ADMIN, ROLE_OWNER]:
            debts = Debt.query.options(joinedload(Debt.customer))\
                .join(Customer)\
                .filter(Customer.business_id == current_user.business_id).all()
        else:  # salesperson
            debts = Debt.query.options(joinedload(Debt.customer))\
                .join(Customer)\
                .filter(Customer.business_id == current_user.business_id,
                        Debt.created_by == current_user.id).all()

        return debts_schema.dump(debts), 200

    @role_required(ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON)
    def post(self):
        data = request.get_json() or {}
        current_user = g.current_user

        # Restrict creation to current user's business
        if data.get("business_id") != current_user.business_id:
            return {"message": "You cannot create debts for another business"}, 403

        # Handle customer creation or lookup 
        customer_id = data.get("customer_id")
        if not customer_id:
            required_fields = ["customer_name", "phone", "id_number", "business_id"]
            if not all(data.get(field) for field in required_fields):
                return {"message": "Customer details are required if customer_id is not provided"}, 400

            customer = Customer.query.filter_by(
                customer_name=data["customer_name"],
                phone=data["phone"],
                business_id=data["business_id"]
            ).first()

            if not customer:
                customer = Customer(
                    customer_name=data["customer_name"],
                    phone=data["phone"],
                    id_number=data["id_number"],
                    business_id=data["business_id"],
                    created_by=current_user.id
                )
                db.session.add(customer)
                db.session.flush()

            customer_id = customer.id
        else:
            customer = Customer.query.get_or_404(customer_id)
            # Enforce same business
            if customer.business_id != current_user.business_id:
                return {"message": "Access denied"}, 403

        # Handle due date 
        due_date = None
        if data.get("due_date"):
            try:
                due_date = datetime.strptime(data["due_date"], "%Y-%m-%d")
            except ValueError:
                return {"message": "due_date must be YYYY-MM-DD format"}, 400

        debt = Debt(
            customer_id=customer_id,
            due_date=due_date,
            created_by=current_user.id
        )
        db.session.add(debt)
        db.session.flush()

        for item_data in data.get("items", []):
            category = item_data.get("category") or "Uncategorized"
            db.session.add(Item(
                debt_id=debt.id,
                name=item_data.get("name"),
                quantity=item_data.get("quantity", 1),
                price=item_data.get("price", 0),
                category=category
            ))

        debt.calculate_total()
        db.session.commit()

        debt_with_customer = Debt.query.options(joinedload(Debt.customer)).get(debt.id)
        log_change("Debt", debt.id, "create", debt_schema.dump(debt_with_customer))

        return debt_schema.dump(debt_with_customer), 201

    @role_required(ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON)
    def put(self, debt_id):
        debt = Debt.query.options(joinedload(Debt.customer)).get_or_404(debt_id)
        current_user = g.current_user

        if not can_access_debt(current_user, debt):
            return {"message": "Access denied"}, 403

        data = request.get_json() or {}

        # Update core fields
        if "customer_id" in data:
            new_customer = Customer.query.get_or_404(data["customer_id"])
            if new_customer.business_id != current_user.business_id:
                return {"message": "Access denied"}, 403
            debt.customer_id = data["customer_id"]

        if "due_date" in data:
            try:
                debt.due_date = datetime.strptime(data["due_date"], "%Y-%m-%d")
            except ValueError:
                return {"message": "due_date must be YYYY-MM-DD format"}, 400

        if "amount_paid" in data:
            debt.amount_paid = data["amount_paid"]

        # Update items
        items_data = data.get("items")
        if items_data is not None:
            existing_items = {item.id: item for item in debt.items}

            for item_data in items_data:
                item_id = item_data.get("id")
                category = item_data.get("category") or "Uncategorized"

                if item_id and item_id in existing_items:
                    item = existing_items[item_id]
                    item.name = item_data.get("name", item.name)
                    item.quantity = item_data.get("quantity", item.quantity)
                    item.price = item_data.get("price", item.price)
                    item.category = category
                else:
                    db.session.add(Item(
                        debt_id=debt.id,
                        name=item_data.get("name"),
                        quantity=item_data.get("quantity", 1),
                        price=item_data.get("price", 0),
                        category=category
                    ))

            if data.get("remove_missing_items", False):
                payload_ids = {item.get("id") for item in items_data if item.get("id")}
                for item in list(debt.items):
                    if item.id not in payload_ids:
                        db.session.delete(item)

        debt.calculate_total()
        debt.update_balance()
        db.session.commit()

        updated_debt = Debt.query.options(joinedload(Debt.customer)).get(debt_id)
        log_change("Debt", debt.id, "update", debt_schema.dump(updated_debt))

        return debt_schema.dump(updated_debt), 200

    @role_required(ROLE_OWNER, ROLE_ADMIN)
    def delete(self, debt_id):
        debt = Debt.query.options(joinedload(Debt.customer)).get_or_404(debt_id)
        current_user = g.current_user

        if not can_access_debt(current_user, debt):
            return {"message": "Access denied"}, 403

        log_change("Debt", debt.id, "delete", debt_schema.dump(debt))
        db.session.delete(debt)
        db.session.commit()

        return {"message": f"Debt {debt_id} deleted"}, 200


api.add_resource(DebtResource, "/debts", "/debts/<int:debt_id>")
