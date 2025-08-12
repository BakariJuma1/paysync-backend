from flask_restful import Resource,Api
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from server.models import User
from server.extension import db
from . import auth_bp

api = Api(auth_bp)

#   Get the currently logged-in owner's info
class MeResource(Resource):
    @jwt_required()
    def get(self):
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)
        return user.to_dict(), 200

    @jwt_required()
    def put(self):
        """Full update of current owner's info"""
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)

        data = request.get_json()
        for field in ["name", "email", "phone"]:
            if field in data:
                setattr(user, field, data[field])

        db.session.commit()
        return user.to_dict(), 200

    @jwt_required()
    def patch(self):
        """Partial update of current owner's info"""
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)

        data = request.get_json()
        for key, value in data.items():
            if hasattr(user, key):
                setattr(user, key, value)

        db.session.commit()
        return user.to_dict(), 200

    @jwt_required()
    def delete(self):
        """Delete the currently logged-in owner's account"""
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)

        db.session.delete(user)
        db.session.commit()

        return {"message": "Account deleted successfully"}, 200

api.add_resource(MeResource, '/me')