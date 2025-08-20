from flask_restful import Resource, reqparse, Api
from flask_jwt_extended import get_jwt_identity
from server.models import db, User, Business
from werkzeug.security import generate_password_hash
from server.utils.decorators import role_required
from server.utils.roles import ROLE_SALESPERSON
from . import settings_bp

api = Api(settings_bp)
 

# SALESPERSON BUSINESS INFO (READ-ONLY)
class SalespersonBusinessInfo(Resource):
    @role_required(ROLE_SALESPERSON)
    def get(self):
        current_user_id = get_jwt_identity()
        salesperson = User.query.get_or_404(current_user_id)

        business = Business.query.filter_by(id=salesperson.business_id).first()
        if not business:
            return {"message": "Business not found"}, 404

        return {
            "id": business.id,
            "name": business.name,
            "contact_info": business.contact_info,
            "created_at": business.created_at.isoformat()
        }


# SALESPERSON PROFILE SETTINGS (ONLY THEIR OWN ACCOUNT)
class SalespersonProfile(Resource):
    @role_required(ROLE_SALESPERSON)
    def get(self):
        current_user_id = get_jwt_identity()
        salesperson = User.query.get_or_404(current_user_id)

        return {
            "id": salesperson.id,
            "name": salesperson.name,
            "email": salesperson.email,
            "role": salesperson.role,
            "created_at": salesperson.created_at.isoformat()
        }

    @role_required(ROLE_SALESPERSON)
    def put(self):
        current_user_id = get_jwt_identity()
        salesperson = User.query.get_or_404(current_user_id)

        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str)
        parser.add_argument("password", type=str)
        args = parser.parse_args()

        if args["name"]:
            salesperson.name = args["name"]
        if args["password"]:
            salesperson.password_hash = generate_password_hash(args["password"])

        db.session.commit()
        return {"message": "Profile updated successfully"}


# ROUTE REGISTRATION
api.add_resource(SalespersonBusinessInfo, "/salesperson/business")
api.add_resource(SalespersonProfile, "/salesperson/profile")
