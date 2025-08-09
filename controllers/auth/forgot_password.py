from flask_restful import Resource,Api
from flask import request,Blueprint
import secrets
from datetime import datetime, timedelta
from server.models import User, db
from server.service.password_reset import send_password_reset_email
from . import auth_bp


api = Api(auth_bp)
class ForgotPassword(Resource):
    def post(self):
        data = request.get_json()
        email = data.get("email")

        if not email:
            return {"message": "Email is required"}, 400

        user = User.query.filter_by(email=email).first()

        # Security: respond with success even if user not found
        if user:
            reset_token = secrets.token_urlsafe(32)
            user.reset_token = reset_token
            user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=15)
            db.session.commit()

            # Send email with the token
            send_password_reset_email(user.email, user.name, reset_token)

        return {
            "message": "If an account with that email exists, a reset token has been sent."
        }, 200
    
api.add_resource(ForgotPassword, '/forgot-password')