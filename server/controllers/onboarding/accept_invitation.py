from flask import request
from flask_restful import Resource, Api
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token
from datetime import datetime

from server.models import db, User, Invitation
from server.utils.roles import ALL_ROLES
from . import onboarding_bp

api = Api(onboarding_bp)


def make_response(data, code=200):
    """Ensure consistent JSON responses."""
    if isinstance(data, (dict, list)):
        return data, code
    return {"message": str(data)}, code


class AcceptInvite(Resource):
    def post(self):
        try:
            data = request.get_json() or {}
            token = data.get("token")
            password = data.get("password")

            if not token or not password:
                return make_response({"message": "Token and password are required"}, 400)

            # Fetch invitation
            invitation = Invitation.query.filter_by(token=token).first()
            if not invitation:
                return make_response({"message": "Invalid invitation token"}, 404)

            if invitation.expires_at < datetime.utcnow():
                return make_response({"message": "Invitation token has expired"}, 400)

            # Validate role from invitation
            if invitation.role not in ALL_ROLES:
                return make_response({"message": "Invalid role in invitation"}, 400)

            # Ensure no existing user with this email
            if User.query.filter_by(email=invitation.email).first():
                return make_response({"message": "User with this email already exists"}, 400)

            # Create the user
            hashed_password = generate_password_hash(password)
            new_user = User(
                name=invitation.name,
                email=invitation.email,
                password_hash=hashed_password,
                role=invitation.role,
                is_verified=True,
                business_id=invitation.business_id,
                created_at=datetime.utcnow()
            )
            db.session.add(new_user)

            # Remove the invitation
            db.session.delete(invitation)
            db.session.commit()

            # Create access token
            access_token = create_access_token(identity=new_user.id)

            return make_response({
                "message": "Account created successfully",
                "access_token": access_token,
                "user": {
                    "id": new_user.id,
                    "name": new_user.name,
                    "email": new_user.email,
                    "role": new_user.role,
                    "is_verified": True,
                    "business_id": new_user.business_id,
                }
            }, 201)

        except Exception as e:
            db.session.rollback()
            return make_response({"message": "Server error", "error": str(e)}, 500)


# Register route
api.add_resource(AcceptInvite, "/accept-invite")
