from flask_restful import Resource, reqparse, Api
from flask_jwt_extended import get_jwt_identity
from server.models import db, User, Business
from werkzeug.security import generate_password_hash
from server.utils.decorators import role_required
from . import settings_bp

api = Api(settings_bp)



# BUSINESS INFO
class OwnerBusinessSettings(Resource):
    @role_required("owner")
    def get(self):
        owner_id = get_jwt_identity()
        business = Business.query.filter_by(owner_id=owner_id).first()

        if not business:
            return {"message": "Business not found"}, 404

        return {
            "id": business.id,
            "name": business.name,
            "contact_info": business.contact_info,
            "created_at": business.created_at.isoformat()
        }

    @role_required("owner")
    def put(self):
        owner_id = get_jwt_identity()
        business = Business.query.filter_by(owner_id=owner_id).first()

        if not business:
            return {"message": "Business not found"}, 404

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



# TEAM MANAGEMENT

class OwnerUserManagement(Resource):
    @role_required("owner")
    def get(self):
        owner_id = get_jwt_identity()
        business = Business.query.filter_by(owner_id=owner_id).first()

        if not business:
            return {"message": "Business not found"}, 404

        # Fetch all users in this business except the owner
        users = User.query.filter(
            User.business_id == business.id,
            User.id != owner_id
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

    @role_required("owner")
    def post(self):
        owner_id = get_jwt_identity()
        business = Business.query.filter_by(owner_id=owner_id).first()

        if not business:
            return {"message": "Business not found"}, 404

        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str, required=True)
        parser.add_argument("email", type=str, required=True)
        parser.add_argument("password", type=str, required=True)
        parser.add_argument("role", type=str, choices=("manager", "salesperson"), required=True)
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
    @role_required("owner")
    def put(self, user_id):
        owner_id = get_jwt_identity()
        business = Business.query.filter_by(owner_id=owner_id).first()

        if not business:
            return {"message": "Business not found"}, 404

        # Ensure this user belongs to the owner's business
        user = User.query.filter_by(id=user_id, business_id=business.id).first()
        if not user:
            return {"message": "User not found or does not belong to your business"}, 404

        parser = reqparse.RequestParser()
        parser.add_argument("role", type=str, choices=("manager", "salesperson"))
        parser.add_argument("password", type=str)
        args = parser.parse_args()

        if args["role"]:
            user.role = args["role"]
        if args["password"]:
            user.password_hash = generate_password_hash(args["password"])

        db.session.commit()
        return {"message": "User updated successfully"}

    @role_required("owner")
    def delete(self, user_id):
        owner_id = get_jwt_identity()
        business = Business.query.filter_by(owner_id=owner_id).first()

        if not business:
            return {"message": "Business not found"}, 404

        # Ensure this user belongs to the owner's business
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
