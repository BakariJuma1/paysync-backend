from flask_restful import Resource, Api
from flask import request
from flask_jwt_extended import get_jwt_identity
from server.models import Item, Debt, User
from server.extension import db
from . import item_bp  
from server.schemas.item_schema import ItemSchema
from server.utils.decorators import role_required
from server.utils.roles import ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON

item_schema = ItemSchema()
item_list_schema = ItemSchema(many=True)
api = Api(item_bp)


def make_response(data, code=200):
    """Ensure consistent JSON response"""
    if isinstance(data, (dict, list)):
        return data, code
    return {"message": str(data)}, code


class ItemResource(Resource):

    @role_required(ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON)
    def get(self, item_id=None):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if item_id:
            item = Item.query.get_or_404(item_id)
            debt = Debt.query.get(item.debt_id)

            if not debt:
                return make_response({"message": "Associated debt not found"}, 404)

            if current_user.role == ROLE_SALESPERSON and debt.created_by != current_user_id:
                return make_response({"message": "Access denied"}, 403)

            return make_response(item_schema.dump(item))

        # List all items user has access to
        query = Item.query.join(Debt)
        if current_user.role in (ROLE_OWNER, ROLE_ADMIN):
            items = query.all()
        else:
            items = query.filter(Debt.created_by == current_user_id).all()

        return make_response(item_list_schema.dump(items))

    @role_required(ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON)
    def post(self):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        data = request.get_json() or {}

        debt_id = data.get("debt_id")
        if not debt_id:
            return make_response({"message": "debt_id is required"}, 400)

        debt = Debt.query.get(debt_id)
        if not debt:
            return make_response({"message": "Debt not found"}, 404)

        if current_user.role == ROLE_SALESPERSON and debt.created_by != current_user_id:
            return make_response({"message": "Access denied"}, 403)

        item = item_schema.load(data, session=db.session)
        item.debt_id = debt_id

        db.session.add(item)
        db.session.commit()

        return make_response(item_schema.dump(item), 201)

    @role_required(ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON)
    def put(self, item_id):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        item = Item.query.get_or_404(item_id)
        debt = Debt.query.get(item.debt_id)

        if current_user.role == ROLE_SALESPERSON and debt.created_by != current_user_id:
            return make_response({"message": "Access denied"}, 403)

        data = request.get_json() or {}
        item = item_schema.load(data, instance=item, session=db.session, partial=True)

        db.session.commit()
        debt.calculate_total()
        debt.update_balance()
        db.session.commit()

        return make_response(item_schema.dump(item))

    @role_required(ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON)
    def delete(self, item_id):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        item = Item.query.get_or_404(item_id)
        debt = Debt.query.get(item.debt_id)

        if current_user.role == ROLE_SALESPERSON and debt.created_by != current_user_id:
            return make_response({"message": "Access denied"}, 403)

        db.session.delete(item)
        db.session.commit()

        debt.calculate_total()
        debt.update_balance()
        db.session.commit()

        return make_response({"message": f"Item {item_id} deleted"})


# Register resource
api.add_resource(ItemResource, "/items", "/items/<int:item_id>")
