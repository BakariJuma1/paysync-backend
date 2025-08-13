from flask_restful import Resource, Api
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from server.models import User
from server.extension import db
from . import auth_bp
from server.utils.decorators import role_required  

api = Api(auth_bp)

class MeResource(Resource):
    @jwt_required()
    def get(self):
        """Get the currently logged-in user's info"""
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)
        return user.to_dict(), 200

    @jwt_required()
    @role_required("owner")
    def put(self):
        """Full update of current owner's info (restricted fields)"""
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
        """Partial update of current user's info (restricted fields)"""
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)

        data = request.get_json()

        # Restrict allowed fields by role
        if user.role != "owner":
            allowed_fields = ["name", "email", "phone"]
        else:
            allowed_fields = ["name", "email", "phone", "password"]

        for field in allowed_fields:
            if field in data:
                if field == "password":
                    user.set_password(data[field])  
                else:
                    setattr(user, field, data[field])

        db.session.commit()
        return user.to_dict(), 200

    @jwt_required()
    @role_required("owner")
    def delete(self):
        """Delete the currently logged-in owner's account"""
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)

        db.session.delete(user)
        db.session.commit()

        return {"message": "Account deleted successfully"}, 200

api.add_resource(MeResource, '/me')
