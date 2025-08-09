from flask import Blueprint, request
from flask_restful import Api, Resource
from models import User, db
from werkzeug.security import generate_password_hash
from service.email_service import send_verification_email  # your existing email function
from datetime import datetime
from . import auth_bp


api = Api(auth_bp)
class VerifyEmail(Resource):
    def post(self):
        data = request.get_json()
        token = data.get("token")

        if not token:
            return {"message": "Verification token is required."}, 400

        user = User.query.filter_by(verification_token=token).first()
        if not user:
            return {"message": "Invalid or expired verification token."}, 400

        if not user.verification_token_expiry or user.verification_token_expiry < datetime.utcnow():
            return {"message": "Verification token has expired."}, 400

        user.is_verified = True
        user.verification_token = None
        user.verification_token_expiry = None
        db.session.commit()

        return {"message": "Email verified successfully. You can now log in."}, 200

api.add_resource(VerifyEmail, '/verify-email')