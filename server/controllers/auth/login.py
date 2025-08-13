from flask_restful import Resource, Api
from flask import request
from server.models import User, Business
from flask_jwt_extended import create_access_token
from datetime import timedelta
from . import auth_bp

api = Api(auth_bp)

class Login(Resource):
    def post(self):
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return {"message": "Email and password required"}, 400

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return {"message": "Invalid credentials"}, 401

        if not user.is_verified:
            return {"message": "Email not verified. Please verify before logging in."}, 403

        # Get all relevant business data in one query
        business_data = None
        if user.role == "owner":
            business = Business.query.filter_by(owner_id=user.id).first()
            if business:
                business_data = {
                    "id": business.id,
                    "name": business.name,
                    "address": business.address,
                    "phone": business.phone,
                    "email": business.email,
                    "website": business.website,
                    "description": business.description
                }
        elif user.business_id:  # For non-owner roles
            business = Business.query.get(user.business_id)
            if business:
                business_data = {
                    "id": business.id,
                    "name": business.name
                }

        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=1),
            additional_claims={
                "role": user.role,
                "business_id": business.id if business else None
            }
        )

        return {
            "access_token": access_token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "business_id": user.business_id
            },
            "business": business_data,
            "has_business": bool(business_data)
        }, 200

api.add_resource(Login, '/login')