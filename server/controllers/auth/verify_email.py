from flask import request
from flask_restful import Api, Resource
from server.models import User, Business
from server.extension import db, jwt
from datetime import datetime, timedelta
from . import auth_bp
from server.service.email_service import send_verification_email
from flask_jwt_extended import create_access_token
import pyotp
from server.utils.roles import ROLE_OWNER

api = Api(auth_bp)

class VerifyEmail(Resource):
    def post(self):
        data = request.get_json()
        email = data.get("email")
        otp = data.get("otp")

        if not email or not otp:
            return {"message": "Email and OTP code are required."}, 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return {"message": "User not found."}, 404

        if user.is_verified:
            return {"message": "User already verified."}, 400

        if not user.verification_secret:
            return {"message": "Verification secret not found. Please request a new code."}, 400

        totp = pyotp.TOTP(user.verification_secret,interval=250)
        if not totp.verify(otp, valid_window=3):  
            return {"message": "Invalid or expired OTP code."}, 400

        # Mark user as verified and clear secret (optional)
        user.is_verified = True
        user.verification_secret = None
        user.role = ROLE_OWNER
        db.session.commit()

        access_token = create_access_token(
            identity=user.id,
            additional_claims={"role": user.role}
            )

        has_business = Business.query.filter_by(owner_id=user.id).first() is not None

        return {
            "message": "Email verified successfully.",
            "token": access_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role":user.role,
                "has_business": has_business
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

        # Rate limit check (optional)
        if user.last_verification_email_sent:
            elapsed = datetime.utcnow() - user.last_verification_email_sent
            if elapsed < timedelta(minutes=self.RATE_LIMIT_MINUTES):
                remaining = self.RATE_LIMIT_MINUTES - int(elapsed.total_seconds() // 60)
                return {
                    "message": f"Please wait {remaining} more minute(s) before resending."
                }, 429

        # Generate current OTP and send email
        totp = pyotp.TOTP(user.verification_secret,interval=250)
        current_otp = totp.now()

        send_verification_email(user, current_otp)

        # Update last sent time
        user.last_verification_email_sent = datetime.utcnow()
        db.session.commit()

        return {"message": "Verification email resent successfully."}, 200



api.add_resource(VerifyEmail, '/verify-email')
api.add_resource(ResendVerification, '/resend-verification')
