from flask_restful import Resource, Api
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from server.models import Item, Debt, User
from server.extension import db
from . import item_bp  
from server.schemas.item_schema import ItemSchema

item_schema = ItemSchema()
item_list_schema = ItemSchema(many=True)
api = Api(item_bp)

class ItemResource(Resource):

    @jwt_required()
    def get(self, item_id=None):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if item_id:
            item = Item.query.get_or_404(item_id)
            debt = Debt.query.get(item.debt_id)

            if not debt:
                return {"message": "Associated debt not found"}, 404

            if current_user.role == 'salesman' and debt.created_by != current_user_id:
                return {"message": "Access denied"}, 403

            return item_schema.dump(item), 200

        # List all items user has access to
        query = Item.query.join(Debt)

        if current_user.role in ('owner', 'admin'):
            items = query.all()
        else:
            items = query.filter(Debt.created_by == current_user_id).all()

        return item_list_schema.dump(items), 200

    @jwt_required()
    def post(self):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        data = request.get_json() or {}

        debt_id = data.get('debt_id')
        if not debt_id:
            return {"message": "debt_id is required"}, 400

        debt = Debt.query.get(debt_id)
        if not debt:
            return {"message": "Debt not found"}, 404

        if current_user.role == 'salesman' and debt.created_by != current_user_id:
            return {"message": "Access denied"}, 403

        # Validate fields via schema
        item = item_schema.load(data, session=db.session)
        item.debt_id = debt_id

        db.session.add(item)
        db.session.commit()

        return item_schema.dump(item), 201

    @jwt_required()
    def put(self, item_id):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        item = Item.query.get_or_404(item_id)
        debt = Debt.query.get(item.debt_id)

        if current_user.role == 'salesman' and debt.created_by != current_user_id:
            return {"message": "Access denied"}, 403

        data = request.get_json() or {}
        item = item_schema.load(data, instance=item, session=db.session, partial=True)

        db.session.commit()
        debt.calculate_total()
        debt.update_balance()
        db.session.commit()

        return item_schema.dump(item), 200

    @jwt_required()
    def delete(self, item_id):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        item = Item.query.get_or_404(item_id)
        debt = Debt.query.get(item.debt_id)

        if current_user.role == 'salesman' and debt.created_by != current_user_id:
            return {"message": "Access denied"}, 403

        db.session.delete(item)
        db.session.commit()

        debt.calculate_total()
        debt.update_balance()
        db.session.commit()

        return {"message": f"Item {item_id} deleted"}, 200

api.add_resource(ItemResource, '/items', '/items/<int:item_id>')
