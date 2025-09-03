from flask_restful import Resource, Api
from flask import request, g
from server.models import Debt, Customer, Item
from server.extension import db
from datetime import datetime
from . import debt_bp
from server.schemas.debt_schema import DebtSchema
from server.utils.change_logger import log_change
from server.utils.roles import ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON
from server.utils.decorators import role_required
from sqlalchemy.orm import joinedload
from server.service.debt_notifications import send_debt_receipt

api = Api(debt_bp)

# Schemas
debt_schema = DebtSchema()
debts_schema = DebtSchema(many=True)


# ---------------------------
# Access Control Helper
# ---------------------------
def can_access_debt(user, debt):
    """
    Restrict access to debts within the user's business.
    - Owners: all debts in their business
    - Admins: all debts in their business (including salesperson debts)
    - Salespersons: only debts they created
    """
    # First check if debt belongs to the user's business
    if not debt.customer or debt.customer.business_id != user.business_id:
        return False
    
    # Access control based on role
    if user.role in [ROLE_OWNER, ROLE_ADMIN]:
        return True
    if user.role == ROLE_SALESPERSON:
        return debt.created_by == user.id
    
    return False


class DebtResource(Resource):

    @role_required(ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON)
    def get(self, debt_id=None):
        current_user = g.current_user

        if debt_id:
            # Get debt with proper joins to check access
            debt = Debt.query.options(
                joinedload(Debt.customer),
                joinedload(Debt.created_by_user)  # Join the user who created the debt
            ).get_or_404(debt_id)
            
            if not can_access_debt(current_user, debt):
                return {"message": "Access denied"}, 403
            return debt_schema.dump(debt), 200

        # Fetch all debts for user's business with proper filtering
        query = Debt.query.options(
            joinedload(Debt.customer),
            joinedload(Debt.created_by_user)  # Include creator information
        ).join(Customer).filter(Customer.business_id == current_user.business_id)

        # Salespeople can only see their own debts
        if current_user.role == ROLE_SALESPERSON:
            query = query.filter(Debt.created_by == current_user.id)

        # For owners and admins, no additional filtering needed - they see all
        debts = query.order_by(Debt.created_at.desc()).all()
        
        return debts_schema.dump(debts), 200

    @role_required(ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON)
    def post(self):
        data = request.get_json() or {}
        current_user = g.current_user
        business_id = current_user.business_id

        if not business_id:
            return {"message": "Current user is not linked to a business"}, 400

        # Handle customer creation or lookup
        customer_id = data.get("customer_id")
        if not customer_id:
            required_fields = ["customer_name", "phone", "id_number"]
            if not all(data.get(field) for field in required_fields):
                return {"message": "Customer details are required if customer_id is not provided"}, 400

            customer = Customer.query.filter_by(
                customer_name=data["customer_name"],
                phone=data["phone"],
                business_id=business_id
            ).first()

            if not customer:
                customer = Customer(
                    customer_name=data["customer_name"],
                    phone=data["phone"],
                    id_number=data["id_number"],
                    email=data.get("email"),
                    business_id=business_id,
                    created_by=current_user.id
                )
                db.session.add(customer)
                db.session.flush()  
            customer_id = customer.id
        else:
            customer = Customer.query.get_or_404(customer_id)
            if customer.business_id != business_id:
                return {"message": "Access denied"}, 403

        # Handle due date
        due_date = None
        if data.get("due_date"):
            try:
                due_date = datetime.strptime(data["due_date"], "%Y-%m-%d")
            except ValueError:
                return {"message": "due_date must be YYYY-MM-DD format"}, 400

        # Handle category
        category = data.get("category", "Uncategorized")

        # Create debt
        debt = Debt(
            customer_id=customer_id,
            business_id=business_id,
            due_date=due_date,
            created_by=current_user.id,
            category=category
        )
        db.session.add(debt)
        db.session.flush()

        # Add items
        for item_data in data.get("items", []):
            db.session.add(Item(
                debt_id=debt.id,
                name=item_data.get("name"),
                quantity=item_data.get("quantity", 1),
                price=item_data.get("price", 0),
                category=item_data.get("category") or category
            ))

        debt.calculate_total()
        initial_payment = data.get("amount_paid", 0)
        if initial_payment > 0:
            from server.models.payment import Payment
            payment = Payment(
                debt_id=debt.id,
                amount=initial_payment,
                method="initial",
                received_by=current_user.id
            )
            db.session.add(payment)
        db.session.commit()
        send_debt_receipt(debt, send_email=True, send_sms=False)

        debt_with_customer = Debt.query.options(
            joinedload(Debt.customer),
            joinedload(Debt.created_by_user)
        ).get(debt.id)
        
        log_change("Debt", debt.id, "create", debt_schema.dump(debt_with_customer))

        return debt_schema.dump(debt_with_customer), 201

    @role_required(ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON)
    def put(self, debt_id):
        current_user = g.current_user
        debt = Debt.query.options(
            joinedload(Debt.customer),
            joinedload(Debt.created_by_user)
        ).get_or_404(debt_id)

        if not can_access_debt(current_user, debt):
            return {"message": "Access denied"}, 403

        data = request.get_json() or {}

        # Update customer
        if "customer_id" in data:
            new_customer = Customer.query.get_or_404(data["customer_id"])
            if new_customer.business_id != current_user.business_id:
                return {"message": "Access denied"}, 403
            debt.customer_id = new_customer.id

        # update customer email 
        if "email" in data and debt.customer:
            debt.customer.email = data["email"]

        # Update due date
        if "due_date" in data:
            try:
                debt.due_date = datetime.strptime(data["due_date"], "%Y-%m-%d")
            except ValueError:
                return {"message": "due_date must be YYYY-MM-DD format"}, 400

        # Update category
        if "category" in data:
            debt.category = data["category"]

        # Update amount_paid
        if "amount_paid" in data:
            new_payment = data["amount_paid"]
            if new_payment > 0:
                from server.models.payment import Payment
                payment = Payment(
                    debt_id=debt.id,
                    amount=new_payment,
                    method="update",
                    received_by=current_user.id,
                    payment_date=datetime.utcnow()
                )
                db.session.add(payment)

        # Update items
        items_data = data.get("items")
        if items_data is not None:
            existing_items = {item.id: item for item in debt.items}

            for item_data in items_data:
                item_id = item_data.get("id")
                if item_id and item_id in existing_items:
                    item = existing_items[item_id]
                    item.name = item_data.get("name", item.name)
                    item.quantity = item_data.get("quantity", item.quantity)
                    item.price = item_data.get("price", item.price)
                    item.category = item_data.get("category") or debt.category
                else:
                    db.session.add(Item(
                        debt_id=debt.id,
                        name=item_data.get("name"),
                        quantity=item_data.get("quantity", 1),
                        price=item_data.get("price", 0),
                        category=item_data.get("category") or debt.category
                    ))

            if data.get("remove_missing_items", False):
                payload_ids = {item.get("id") for item in items_data if item.get("id")}
                for item in list(debt.items):
                    if item.id not in payload_ids:
                        db.session.delete(item)

        db.session.flush()
        debt.calculate_total()
        debt.update_status()  # Update status based on balance
        db.session.commit()

        updated_debt = Debt.query.options(
            joinedload(Debt.customer),
            joinedload(Debt.created_by_user)
        ).get(debt_id)
        
        log_change("Debt", debt.id, "update", debt_schema.dump(updated_debt))
        return debt_schema.dump(updated_debt), 200

    @role_required(ROLE_OWNER, ROLE_ADMIN)
    def delete(self, debt_id):
        current_user = g.current_user
        debt = Debt.query.options(
            joinedload(Debt.customer),
            joinedload(Debt.created_by_user)
        ).get_or_404(debt_id)

        if not can_access_debt(current_user, debt):
            return {"message": "Access denied"}, 403

        log_change("Debt", debt.id, "delete", debt_schema.dump(debt))
        db.session.delete(debt)
        db.session.commit()
        send_debt_receipt(debt, send_email=True, send_sms=False)
        return {"message": f"Debt {debt_id} deleted"}, 200


api.add_resource(DebtResource, "/debts", "/debts/<int:debt_id>")