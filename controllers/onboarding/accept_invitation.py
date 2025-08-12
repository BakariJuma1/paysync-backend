from flask import request
from flask_restful import Resource,Api
from werkzeug.security import generate_password_hash
from server.models import db, User, Invitation
from flask_jwt_extended import create_access_token
from datetime import datetime
from . import onboarding_bp

api = Api(onboarding_bp)

class AcceptInvite(Resource):
    def post(self):
        data = request.get_json()
        token = data.get("token")
        password = data.get("password")
        
        if not token or not password:
            return {"message": "Token and password are required"}, 400
        
        invitation = Invitation.query.filter_by(token=token).first()
        
        if not invitation:
            return {"message": "Invalid invitation token"}, 404
        
        if invitation.expires_at < datetime.utcnow():
            return {"message": "Invitation token has expired"}, 400
        
        # Check if user already exists with that email (just in case)
        if User.query.filter_by(email=invitation.email).first():
            return {"message": "User with this email already exists"}, 400
        
        # Create the user with hashed password
        hashed_password = generate_password_hash(password)
        new_user = User(
            name=invitation.name,
            email=invitation.email,
            password_hash=hashed_password,
            role=invitation.role,
            verified=True,
            business_id=invitation.business_id,
            created_at=datetime.utcnow()
        )
        db.session.add(new_user)
        
        # Remove invitation
        db.session.delete(invitation)
        
        db.session.commit()
        
        # Generate JWT token for new user
        access_token = create_access_token(identity=new_user.id)
        
        return {
            "message": "Account created successfully",
            "access_token": access_token,
            "user": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email,
                "role": new_user.role,
                "business_id": new_user.business_id,
            }
        }, 201
api.add_resource(AcceptInvite, "/accept-invite")
