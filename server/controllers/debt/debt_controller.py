from flask_restful import Resource, Api
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from server.models import Debt, User, Item, Customer
from server.extension import db
from datetime import datetime
from . import debt_bp
from server.schemas.debt_schema import DebtSchema  # Import your schema

api = Api(debt_bp)

# Initialize schemas
debt_schema = DebtSchema()
debts_schema = DebtSchema(many=True)

class DebtResource(Resource):

    @jwt_required()
    def get(self, debt_id=None):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if debt_id:
            debt = Debt.query.get_or_404(debt_id)
            if current_user.role == 'salesman' and debt.created_by != current_user_id:
                return jsonify({"message": "Access denied"}), 403
            return debt_schema.jsonify(debt), 200
        
        # List debts filtered by role
        if current_user.role == 'owner' or current_user.role == 'admin':
            debts = Debt.query.all()
        else:  # salesman
            debts = Debt.query.filter_by(created_by=current_user_id).all()

        return debts_schema.jsonify(debts), 200

    @jwt_required()
    def post(self):
        data = request.get_json() or {}
        customer_id = data.get('customer_id')
        customer_name = data.get('customer_name')
        phone = data.get('phone')
        id_number = data.get('id_number')
        business_id = data.get('business_id')  # Required for creating customer if not exists

        current_user_id = get_jwt_identity()

        # Check if customer exists
        if not customer_id:
            if not all([customer_name, phone, id_number, business_id]):
                return jsonify({"message": "Customer details are required if customer_id is not provided"}), 400

            # Check if customer already exists for this business
            customer = Customer.query.filter_by(
                customer_name=customer_name,
                phone=phone,
                business_id=business_id
            ).first()

            if not customer:
                # Create new customer
                customer = Customer(
                    customer_name=customer_name,
                    phone=phone,
                    id_number=id_number,
                    business_id=business_id,
                    created_by=current_user_id
                )
                db.session.add(customer)
                db.session.flush()  # To get customer.id
            customer_id = customer.id
        else:
            customer = Customer.query.get_or_404(customer_id)

        due_date = None
        if data.get('due_date'):
            try:
                due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
            except ValueError:
                return jsonify({"message": "due_date must be YYYY-MM-DD format"}), 400

        debt = Debt(
            customer_id=customer_id,
            due_date=due_date,
            created_by=current_user_id
        )
        db.session.add(debt)
        db.session.flush()  # To get debt.id before adding items

        # Optional: create/update items if provided
        items_data = data.get('items', [])
        for item_data in items_data:
            item = Item(
                debt_id=debt.id,
                name=item_data.get('name'),
                quantity=item_data.get('quantity', 1),
                price=item_data.get('price', 0)
            )
            db.session.add(item)

        # Recalculate total and balance
        debt.calculate_total()
        debt.update_balance()

        db.session.commit()
        return debt_schema.jsonify(debt), 201

    @jwt_required()
    def put(self, debt_id):
        debt = Debt.query.get_or_404(debt_id)
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if current_user.role == 'salesman' and debt.created_by != current_user_id:
            return jsonify({"message": "Access denied"}), 403

        data = request.get_json() or {}

        if 'customer_id' in data:
            debt.customer_id = data['customer_id']

        if 'due_date' in data:
            try:
                debt.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
            except ValueError:
                return jsonify({"message": "due_date must be YYYY-MM-DD format"}), 400

        if 'amount_paid' in data:
            debt.amount_paid = data['amount_paid']

        # Optional: update items
        items_data = data.get('items')
        if items_data is not None:
            existing_items = {item.id: item for item in debt.items}
            for item_data in items_data:
                item_id = item_data.get('id')
                if item_id and item_id in existing_items:
                    # Update existing item
                    item = existing_items[item_id]
                    item.name = item_data.get('name', item.name)
                    item.quantity = item_data.get('quantity', item.quantity)
                    item.price = item_data.get('price', item.price)
                else:
                    # Add new item
                    item = Item(
                        debt_id=debt.id,
                        name=item_data.get('name'),
                        quantity=item_data.get('quantity', 1),
                        price=item_data.get('price', 0)
                    )
                    db.session.add(item)

            if data.get('remove_missing_items', False):
                payload_ids = [item.get('id') for item in items_data if item.get('id')]
                for item in debt.items:
                    if item.id not in payload_ids:
                        db.session.delete(item)    

        # Recalculate total and balance
        debt.calculate_total()
        debt.update_balance()

        db.session.commit()
        return debt_schema.jsonify(debt), 200

    @jwt_required()
    def delete(self, debt_id):
        debt = Debt.query.get_or_404(debt_id)
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if current_user.role != 'owner':
            return jsonify({"message": "Only owners can delete debts"}), 403

        db.session.delete(debt)
        db.session.commit()
        return jsonify({"message": f"Debt {debt_id} deleted"}), 200

api.add_resource(DebtResource, '/debts', '/debts/<int:debt_id>')