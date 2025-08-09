from flask_restful import Resource,Api
from flask import request,Blueprint
from werkzeug.security import generate_password_hash
from server.models import User
from datetime import datetime
from server.extension import db
from . import auth_bp


api = Api(auth_bp)
class ResetPassword(Resource):
    def post(self):
        data = request.get_json()
        token = data.get("token")
        new_password = data.get("new_password")

        if not token or not new_password:
            return {"message": "Token and new password are required."}, 400

        user = User.query.filter_by(reset_token=token).first()
        if not user:
            return {"message": "Invalid reset token."}, 400

        if not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
            return {"message": "Reset token has expired."}, 400

        # Update password
        user.password_hash = generate_password_hash(new_password)
        # Clear reset token fields
        user.reset_token = None
        user.reset_token_expiry = None

        db.session.commit()

        return {"message": "Password reset successful. You can now log in."}, 200

api.add_resource(ResetPassword, '/reset-password')
