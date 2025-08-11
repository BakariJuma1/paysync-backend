from flask_restful import Resource, Api
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from server.models import Item, Debt, User
from server.extension import db
from . import item_bp  

api = Api(item_bp)

class ItemResource(Resource):

    @jwt_required()
    def get(self, item_id=None):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if item_id:
            item = Item.query.get_or_404(item_id)

            # Check access: user can only see items on debts they have access to
            debt = Debt.query.get(item.debt_id)
            if not debt:
                return jsonify({"message": "Associated debt not found"}), 404

            if current_user.role == 'salesman' and debt.created_by != current_user_id:
                return jsonify({"message": "Access denied"}), 403

            return jsonify(item.to_dict()), 200

        # List all items user has access to (optional: filter by debt_id query param)
        query = Item.query.join(Debt)

        if current_user.role == 'owner' or current_user.role == 'admin':
            items = query.all()
        else:
            # Salesman: only items of debts they created
            items = query.filter(Debt.created_by == current_user_id).all()

        return jsonify([item.to_dict() for item in items]), 200

    @jwt_required()
    def post(self):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        data = request.get_json() or {}

        debt_id = data.get('debt_id')
        if not debt_id:
            return jsonify({"message": "debt_id is required"}), 400

        debt = Debt.query.get(debt_id)
        if not debt:
            return jsonify({"message": "Debt not found"}), 404

        # Permission check: Only owner/admin or salesman who created the debt can add items
        if current_user.role == 'salesman' and debt.created_by != current_user_id:
            return jsonify({"message": "Access denied"}), 403

        # Validate required fields
        name = data.get('name')
        price = data.get('price')
        category = data.get('category')
        quantity = data.get('quantity')

        if not all([name, price, category, quantity]):
            return jsonify({"message": "name, price, category, and quantity are required"}), 400

        try:
            price = float(price)
            quantity = int(quantity)
        except ValueError:
            return jsonify({"message": "price must be a float and quantity must be an integer"}), 400

        item = Item(
            debt_id=debt_id,
            name=name,
            price=price,
            category=category,
            quantity=quantity
        )

        db.session.add(item)
        db.session.commit()

        # Optionally update debt totals here if needed

        return jsonify(item.to_dict()), 201

    @jwt_required()
    def put(self, item_id):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        item = Item.query.get_or_404(item_id)
        debt = Debt.query.get(item.debt_id)

        if not debt:
            return jsonify({"message": "Associated debt not found"}), 404

        # Permission check
        if current_user.role == 'salesman' and debt.created_by != current_user_id:
            return jsonify({"message": "Access denied"}), 403

        data = request.get_json() or {}

        if 'name' in data:
            item.name = data['name']
        if 'price' in data:
            try:
                item.price = float(data['price'])
            except ValueError:
                return jsonify({"message": "price must be a float"}), 400
        if 'category' in data:
            item.category = data['category']
        if 'quantity' in data:
            try:
                item.quantity = int(data['quantity'])
            except ValueError:
                return jsonify({"message": "quantity must be an integer"}), 400

        db.session.commit()

        # Recalculate debt totals
        debt.calculate_total()
        debt.update_balance()
        db.session.commit()
        return jsonify(item.to_dict()), 200

    @jwt_required()
    def delete(self, item_id):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        item = Item.query.get_or_404(item_id)
        debt = Debt.query.get(item.debt_id)

        if not debt:
            return jsonify({"message": "Associated debt not found"}), 404

        # Permission check
        if current_user.role == 'salesman' and debt.created_by != current_user_id:
            return jsonify({"message": "Access denied"}), 403

        db.session.delete(item)
        db.session.commit()

        # Recalculate debt totals
        debt.calculate_total()
        debt.update_balance()
        db.session.commit()

       

        return jsonify({"message": f"Item {item_id} deleted"}), 200

# Register resource
api.add_resource(ItemResource, '/items', '/items/<int:item_id>')
