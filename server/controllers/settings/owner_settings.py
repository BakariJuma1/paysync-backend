from flask_restful import Resource, reqparse, Api
from flask_jwt_extended import get_jwt_identity
from server.models import db, User, Business
from werkzeug.security import generate_password_hash
from server.utils.decorators import role_required
from server.utils.roles import ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON
from . import settings_bp

api = Api(settings_bp)


# BUSINESS INFO
class OwnerBusinessSettings(Resource):
    @role_required(ROLE_OWNER)
    def get(self):
        current_user_id = get_jwt_identity()
        owner = User.query.get_or_404(current_user_id)

        business = Business.query.filter_by(id=owner.business_id, owner_id=owner.id).first()
        if not business:
            return {"message": "Business not found or does not belong to you"}, 404

        return {
            "id": business.id,
            "name": business.name,
            "contact_info": business.contact_info,
            "created_at": business.created_at.isoformat()
        }

    @role_required(ROLE_OWNER)
    def put(self):
        current_user_id = get_jwt_identity()
        owner = User.query.get_or_404(current_user_id)

        business = Business.query.filter_by(id=owner.business_id, owner_id=owner.id).first()
        if not business:
            return {"message": "Business not found or does not belong to you"}, 404

        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str)
        parser.add_argument("contact_info", type=str)
        args = parser.parse_args()

        if args["name"]:
            business.name = args["name"]
        if args["contact_info"]:
            business.contact_info = args["contact_info"]

        db.session.commit()
        return {"message": "Business updated successfully"}


# OWNER USER MANAGEMENT
class OwnerUserManagement(Resource):
    @role_required(ROLE_OWNER)
    def get(self):
        current_user_id = get_jwt_identity()
        owner = User.query.get_or_404(current_user_id)

        business = Business.query.filter_by(id=owner.business_id, owner_id=owner.id).first()
        if not business:
            return {"message": "Business not found or does not belong to you"}, 404

        users = User.query.filter(
            User.business_id == business.id,
            User.id != owner.id
        ).all()

        return [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "role": u.role,
                "created_at": u.created_at.isoformat()
            }
            for u in users
        ]

    @role_required(ROLE_OWNER)
    def post(self):
        current_user_id = get_jwt_identity()
        owner = User.query.get_or_404(current_user_id)

        business = Business.query.filter_by(id=owner.business_id, owner_id=owner.id).first()
        if not business:
            return {"message": "Business not found or does not belong to you"}, 404

        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str, required=True)
        parser.add_argument("email", type=str, required=True)
        parser.add_argument("password", type=str, required=True)
        parser.add_argument(
            "role",
            type=str,
            choices=(ROLE_ADMIN, ROLE_SALESPERSON),
            required=True
        )
        args = parser.parse_args()

        if User.query.filter_by(email=args["email"]).first():
            return {"message": "Email already exists"}, 400

        new_user = User(
            name=args["name"],
            email=args["email"],
            password_hash=generate_password_hash(args["password"]),
            role=args["role"],
            business_id=business.id
        )

        db.session.add(new_user)
        db.session.commit()

        return {"message": f"{args['role'].capitalize()} created successfully"}


# UPDATE / DELETE USER
class OwnerUserDetail(Resource):
    @role_required(ROLE_OWNER)
    def put(self, user_id):
        current_user_id = get_jwt_identity()
        owner = User.query.get_or_404(current_user_id)

        business = Business.query.filter_by(id=owner.business_id, owner_id=owner.id).first()
        if not business:
            return {"message": "Business not found or does not belong to you"}, 404

        user = User.query.filter_by(id=user_id, business_id=business.id).first()
        if not user:
            return {"message": "User not found or does not belong to your business"}, 404

        parser = reqparse.RequestParser()
        parser.add_argument("role", type=str, choices=(ROLE_ADMIN, ROLE_SALESPERSON))
        parser.add_argument("password", type=str)
        args = parser.parse_args()

        if args["role"]:
            user.role = args["role"]
        if args["password"]:
            user.password_hash = generate_password_hash(args["password"])

        db.session.commit()
        return {"message": "User updated successfully"}

    @role_required(ROLE_OWNER)
    def delete(self, user_id):
        current_user_id = get_jwt_identity()
        owner = User.query.get_or_404(current_user_id)

        business = Business.query.filter_by(id=owner.business_id, owner_id=owner.id).first()
        if not business:
            return {"message": "Business not found or does not belong to you"}, 404

        user = User.query.filter_by(id=user_id, business_id=business.id).first()
        if not user:
            return {"message": "User not found or does not belong to your business"}, 404

        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted successfully"}


# ROUTE REGISTRATION
api.add_resource(OwnerBusinessSettings, '/owner/business')
api.add_resource(OwnerUserManagement, '/owner/users')
api.add_resource(OwnerUserDetail, '/owner/users/<int:user_id>')
