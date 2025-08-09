from flask import Blueprint, request
from flask_restful import Api, Resource
from server.models import User
from server.extension import db
from werkzeug.security import generate_password_hash
import uuid
from server.service.email_service import send_verification_email  # your existing email function
from datetime import datetime
from . import auth_bp


api = Api(auth_bp)
class OwnerSignup(Resource):
    def post(self):
        data = request.get_json()
        if not data or not all(k in data for k in ("name", "email", "password")):
            return {"message": "Missing required fields"}, 400

        if User.query.filter_by(email=data['email']).first():
            return {"message": "User with this email already exists"}, 400

        verification_token = str(uuid.uuid4())
        user = User(
            name=data['name'],
            email=data['email'],
            role='owner',
            is_verified=False
        )
        user.set_password(data['password'])

        db.session.add(user)
        db.session.commit()

        send_verification_email(user)
        return {"message": "Owner registered! Please verify your email."}, 201

api.add_resource(OwnerSignup, '/register')

