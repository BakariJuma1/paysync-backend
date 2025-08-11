from flask_restful import Resource,Api
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from server.models import Debt, User
from server.extension import db
from datetime import datetime
from . import debt_bp

api = Api(debt_bp)
class DebtResource(Resource):

    @jwt_required()
    def get(self, debt_id=None):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if debt_id:
            debt = Debt.query.get_or_404(debt_id)

            # Role check: salesman can only access debts they created
            if current_user.role == 'salesman' and debt.created_by != current_user_id:
                return jsonify({"message": "Access denied"}), 403

            return jsonify(debt.to_dict()), 200
        
        # List debts filtered by role
        if current_user.role == 'owner':
            debts = Debt.query.all()
        elif current_user.role == 'admin':
            # You may filter based on org or other logic here
            debts = Debt.query.all()
        else:  # salesman
            debts = Debt.query.filter_by(created_by=current_user_id).all()

        return jsonify([debt.to_dict() for debt in debts]), 200

    @jwt_required()
    def post(self):
        data = request.get_json() or {}

        customer_id = data.get('customer_id')
        if not customer_id:
            return jsonify({"message": "customer_id is required"}), 400
        
        due_date_str = data.get('due_date')
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({"message": "due_date must be YYYY-MM-DD format"}), 400

        current_user_id = get_jwt_identity()

        debt = Debt(
            customer_id=customer_id,
            due_date=due_date,
            total=data.get('total', 0),
            amount_paid=data.get('amount_paid', 0),
            created_by=current_user_id
        )
        debt.update_balance()

        db.session.add(debt)
        db.session.commit()

        return jsonify(debt.to_dict()), 201

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

        if 'total' in data:
            debt.total = data['total']

        if 'amount_paid' in data:
            debt.amount_paid = data['amount_paid']

        debt.update_balance()
        db.session.commit()

        return jsonify(debt.to_dict()), 200

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