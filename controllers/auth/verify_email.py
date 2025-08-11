from flask import request
from flask_restful import Api, Resource
from server.models import User
from server.extension import db, jwt
from datetime import datetime, timedelta
from . import auth_bp
from server.service.email_service import send_verification_email
from flask_jwt_extended import create_access_token

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

        # Mark user as verified
        user.is_verified = True
        user.verification_token = None
        user.verification_token_expiry = None
        db.session.commit()

        # Create JWT token
        access_token = create_access_token(identity=user.id)

        # Return token + user info
        return {
            "message": "Email verified successfully.",
            "token": access_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name  
            }
        }, 200


class ResendVerification(Resource):
    RATE_LIMIT_MINUTES = 2  

    def post(self):
        data = request.get_json()
        email = data.get("email")

        if not email:
            return {"message": "Email is required."}, 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return {"message": "No account found with this email."}, 404

        if user.is_verified:
            return {"message": "Email is already verified."}, 400

        # Check rate limit
        if user.last_verification_email_sent:
            elapsed = datetime.utcnow() - user.last_verification_email_sent
            if elapsed < timedelta(minutes=self.RATE_LIMIT_MINUTES):
                remaining = self.RATE_LIMIT_MINUTES - int(elapsed.total_seconds() // 60)
                return {
                    "message": f"Please wait {remaining} more minute(s) before resending."
                }, 429

        # Send new verification email
        send_verification_email(user)

        # Update last sent time
        user.last_verification_email_sent = datetime.utcnow()
        db.session.commit()

        return {"message": "Verification email resent successfully."}, 200


api.add_resource(VerifyEmail, '/verify-email')
api.add_resource(ResendVerification, '/resend-verification')
