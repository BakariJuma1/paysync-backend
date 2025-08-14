from flask_restful import Resource, Api
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from server.models import User
from server.extension import db
from . import auth_bp
from server.utils.decorators import role_required  
from server.schemas.user_schema import UserSchema

api = Api(auth_bp)
user_schema = UserSchema()

class MeResource(Resource):
    @jwt_required()
    def get(self):
        user = User.query.get_or_404(get_jwt_identity())
        return user_schema.dump(user), 200

    @jwt_required()
    @role_required("owner")
    def put(self):
        user = User.query.get_or_404(get_jwt_identity())
        data = request.get_json()
        for field in ["name", "email", "phone"]:
            if field in data:
                setattr(user, field, data[field])
        db.session.commit()
        return user_schema.dump(user), 200

    @jwt_required()
    def patch(self):
        user = User.query.get_or_404(get_jwt_identity())
        data = request.get_json()
        allowed_fields = ["name", "email", "phone"]
        if user.role == "owner":
            allowed_fields.append("password")
        for field in allowed_fields:
            if field in data:
                if field == "password":
                    user.set_password(data[field])
                else:
                    setattr(user, field, data[field])
        db.session.commit()
        return user_schema.dump(user), 200

    @jwt_required()
    @role_required("owner")
    def delete(self):
        user = User.query.get_or_404(get_jwt_identity())
        db.session.delete(user)
        db.session.commit()
        return {"message": "Account deleted successfully"}, 200

api.add_resource(MeResource, '/me')
