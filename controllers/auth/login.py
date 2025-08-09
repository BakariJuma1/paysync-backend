from flask_restful import Resource,Api
from flask import request
from server.models import User
from server.extension import db
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

        access_token = create_access_token(identity=user.id, expires_delta=timedelta(hours=1))
        
        # Check if business info exists (for owners)
        business = None
        if user.role == "owner":
            business = user.businesses[0] if user.businesses else None

        return {
            "access_token": access_token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
            },
            "business_complete": bool(business and business.name)
        }, 200

api.add_resource(Login, '/login')