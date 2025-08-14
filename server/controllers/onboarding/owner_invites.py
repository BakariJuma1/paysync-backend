from flask_restful import Resource, Api
from flask_jwt_extended import get_jwt_identity
from datetime import datetime, timedelta
import os

from server.models import db, User, Business, Invitation
from server.utils.decorators import role_required
from server.service.email_invite import send_invitation_email
from server.utils.generate_invite_token import generate_invite_token
from server.utils.helper import parse_json
from server.utils.roles import ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON
from . import onboarding_bp

api = Api(onboarding_bp)


def make_response(data, code=200):
    """Ensure consistent JSON responses."""
    if isinstance(data, (dict, list)):
        return data, code
    return {"message": str(data)}, code


class InvitationResource(Resource):
    @role_required(ROLE_OWNER)
    def post(self):
        try:
            owner_id = get_jwt_identity()
            business = Business.query.filter_by(owner_id=owner_id).first()
            if not business:
                return make_response({"message": "Business not found"}, 404)

            data, error, status = parse_json(
                required_fields=["name", "email", "role"],
                allowed_roles=(ROLE_ADMIN, ROLE_SALESPERSON)
            )
            if error:
                return make_response(error, status)

            if User.query.filter_by(email=data["email"]).first():
                return make_response({"message": "User with this email already exists"}, 400)

            existing_invite = Invitation.query.filter_by(
                email=data["email"],
                business_id=business.id
            ).first()

            if existing_invite and existing_invite.expires_at > datetime.utcnow():
                return make_response({"message": "Invitation already sent to this email"}, 400)

            token = generate_invite_token()
            expires_at = datetime.utcnow() + timedelta(hours=48)

            invitation = Invitation(
                token=token,
                email=data["email"],
                name=data["name"],
                role=data["role"],
                business_id=business.id,
                created_by=owner_id,
                expires_at=expires_at
            )
            db.session.add(invitation)
            db.session.commit()

            frontend_url = os.getenv('FRONTEND_URL', '').rstrip('/')
            invite_url = f"{frontend_url}/accept-invite?token={token}"

            email_sent = send_invitation_email(
                user_email=data["email"],
                user_name=data["name"],
                business_name=business.name,
                role=data["role"],
                invite_url=invite_url
            )

            if not email_sent:
                return make_response({"message": "Invitation created but failed to send email"}, 500)

            return make_response({"message": "Invitation sent successfully"}, 201)

        except Exception as e:
            db.session.rollback()
            return make_response({"message": "Server error", "error": str(e)}, 500)


class OwnerUserManagement(Resource):
    @role_required(ROLE_OWNER)
    def get(self):
        owner_id = get_jwt_identity()
        business = Business.query.filter_by(owner_id=owner_id).first()
        if not business:
            return make_response({"message": "Business not found"}, 404)

        users = User.query.filter(
            User.business_id == business.id,
            User.id != owner_id
        ).all()

        invitations = Invitation.query.filter_by(
            business_id=business.id
        ).filter(
            Invitation.expires_at > datetime.utcnow()
        ).all()

        return make_response({
            "users": [
                {
                    "id": u.id,
                    "name": u.name,
                    "email": u.email,
                    "role": u.role,
                    "status": "active",
                    "created_at": u.created_at.isoformat()
                } for u in users
            ],
            "invitations": [
                {
                    "id": i.id,
                    "name": i.name,
                    "email": i.email,
                    "role": i.role,
                    "status": "pending",
                    "expires_at": i.expires_at.isoformat(),
                    "created_at": i.created_at.isoformat()
                } for i in invitations
            ]
        })


class OwnerUserDetail(Resource):
    @role_required(ROLE_OWNER)
    def put(self, user_id):
        owner_id = get_jwt_identity()
        business = Business.query.filter_by(owner_id=owner_id).first()
        if not business:
            return make_response({"message": "Business not found"}, 404)

        user = User.query.filter_by(id=user_id, business_id=business.id).first()
        if not user:
            return make_response({"message": "User not found or does not belong to your business"}, 404)

        data, error, status = parse_json(allowed_roles=(ROLE_ADMIN, ROLE_SALESPERSON))
        if error:
            return make_response(error, status)

        if "role" in data:
            user.role = data["role"]
            db.session.commit()

        return make_response({"message": "User updated successfully"})

    @role_required(ROLE_OWNER)
    def delete(self, user_id):
        owner_id = get_jwt_identity()
        business = Business.query.filter_by(owner_id=owner_id).first()
        if not business:
            return make_response({"message": "Business not found"}, 404)

        user = User.query.filter_by(id=user_id, business_id=business.id).first()
        if not user:
            return make_response({"message": "User not found or does not belong to your business"}, 404)

        db.session.delete(user)
        db.session.commit()
        return make_response({"message": "User deleted successfully"})


class InvitationActions(Resource):
    @role_required(ROLE_OWNER)
    def post(self, invitation_id):
        owner_id = get_jwt_identity()
        invitation = Invitation.query.filter_by(
            id=invitation_id,
            created_by=owner_id
        ).first()
        if not invitation:
            return make_response({"message": "Invitation not found"}, 404)

        if invitation.expires_at < datetime.utcnow():
            return make_response({"message": "Invitation has expired"}, 400)

        invitation.token = generate_invite_token()
        invitation.expires_at = datetime.utcnow() + timedelta(hours=48)
        db.session.commit()

        business = Business.query.get(invitation.business_id)
        frontend_url = os.getenv('FRONTEND_URL', '').rstrip('/')
        invite_url = f"{frontend_url}/accept-invite?token={invitation.token}"

        email_sent = send_invitation_email(
            user_email=invitation.email,
            user_name=invitation.name,
            business_name=business.name,
            role=invitation.role,
            invite_url=invite_url
        )

        if not email_sent:
            return make_response({"message": "Failed to resend invitation email"}, 500)

        return make_response({"message": "Invitation resent successfully"})

    @role_required(ROLE_OWNER)
    def delete(self, invitation_id):
        owner_id = get_jwt_identity()
        invitation = Invitation.query.filter_by(
            id=invitation_id,
            created_by=owner_id
        ).first()
        if not invitation:
            return make_response({"message": "Invitation not found"}, 404)

        db.session.delete(invitation)
        db.session.commit()
        return make_response({"message": "Invitation cancelled successfully"})


# Route registration
api.add_resource(InvitationResource, "/owner/invitations")
api.add_resource(OwnerUserManagement, "/owner/team")
api.add_resource(OwnerUserDetail, "/owner/team/<int:user_id>")
api.add_resource(InvitationActions, "/owner/invitations/<int:invitation_id>")
