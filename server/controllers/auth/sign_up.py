from flask import Blueprint, request
from flask_restful import Api, Resource
from server.models import User
from server.extension import db
from server.service.email_service import send_verification_email  
from . import auth_bp
import pyotp


api = Api(auth_bp)
class OwnerSignup(Resource):
    def post(self):
        data = request.get_json()
        if not data or not all(k in data for k in ("name", "email", "password")):
            return {"message": "Missing required fields"}, 400

        if User.query.filter_by(email=data['email']).first():
            return {"message": "User with this email already exists"}, 400

        
        user = User(
            name=data['name'],
            email=data['email'],
            role='user',
            is_verified=False
        )
        user.set_password(data['password'])
         
        secret = pyotp.random_base32()
        user.verification_secret = secret

        db.session.add(user)
        db.session.commit()

        totp = pyotp.TOTP(secret)
        otp_code = totp.now()
       
        send_verification_email(user,otp_code)
        return {
            "message": "Owner registered! Please verify your email.",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role
            }
        }, 201

api.add_resource(OwnerSignup, '/register')

