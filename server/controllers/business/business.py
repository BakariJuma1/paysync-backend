from flask import request, g
from flask_restful import Resource, Api
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
from server.models import Business, User
from server.extension import db
from . import business_bp
from server.utils.decorators import role_required
from server.utils.roles import ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON, ALL_ROLES
from server.schemas.business_schema import BusinessSchema, BusinessCreateUpdateSchema
from server.models import FinanceSettings

api = Api(business_bp)

# Schema instances
business_schema = BusinessSchema()
businesses_schema = BusinessSchema(many=True)
business_create_update_schema = BusinessCreateUpdateSchema()


# ---------------------------
# /business/my
# ---------------------------
class MyBusinessResource(Resource):
    @jwt_required()
    @role_required(*ALL_ROLES)
    def get(self):
        current_user = User.query.get_or_404(get_jwt_identity())

        if current_user.role == ROLE_OWNER:
            businesses = Business.query.filter_by(owner_id=current_user.id).all()
        else:
            businesses = [Business.query.get(current_user.business_id)] if current_user.business_id else []

        return {"businesses": businesses_schema.dump(businesses)}, 200


# ---------------------------
# /businesses and /businesses/<id>
# ---------------------------
class BusinessResource(Resource):
    @jwt_required()
    @role_required(ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON)
    def get(self, business_id=None):
        current_user = User.query.get_or_404(get_jwt_identity())

        if business_id:
            business = Business.query.get_or_404(business_id)

            # Restrict access if not owner/admin/salesperson
            if current_user.role in (ROLE_ADMIN, ROLE_SALESPERSON) and business.id != current_user.business_id:
                return {"message": "Access denied"}, 403

            return {"business": business_schema.dump(business)}, 200

        # List all businesses visible to user
        if current_user.role == ROLE_OWNER:
            businesses = Business.query.filter_by(owner_id=current_user.id).all()
        elif current_user.business_id:
            businesses = [Business.query.get(current_user.business_id)]
        else:
            businesses = []

        return {"businesses": businesses_schema.dump(businesses)}, 200

    @jwt_required()
    @role_required(ROLE_OWNER)
    def post(self):
        current_user = User.query.get_or_404(get_jwt_identity())
        json_data = request.get_json() or {}

        errors = business_create_update_schema.validate(json_data)
        if errors:
            return {"errors": errors}, 400
        
        business = Business.query.filter_by(owner_id=current_user.id).first()
        if business:
            # Update existing business instead of creating a new one
            updatable_fields = ["name", "address", "phone", "email", "website", "description"]
            for field in updatable_fields:
                if field in json_data:
                    setattr(business, field, json_data[field])
            try:
                db.session.commit()
                return {"business": business_schema.dump(business), "message": "Business updated successfully"}, 200
            except SQLAlchemyError as e:
                db.session.rollback()
                return {"message": "Database error", "details": str(e)}, 422
        else:
            try:
                business = Business(
                    name=json_data['name'].strip(),
                    owner_id=current_user.id,
                    address=json_data.get('address'),
                    phone=json_data.get('phone'),
                    email=json_data.get('email'),
                    website=json_data.get('website'),
                    description=json_data.get('description')
                )
                db.session.add(business)
                db.session.flush()
                finance_settings = FinanceSettings(business_id=business.id)
                db.session.add(finance_settings)
                db.session.refresh(business)

                # Update current_user.business_id if needed
                current_user.business_id = business.id
                db.session.commit()

                return {
                    "business": business_schema.dump(business),
                    "message": "Business created successfully"
                }, 201

            except SQLAlchemyError as e:
                db.session.rollback()
                return {"message": "Database error", "details": str(e)}, 422

    @jwt_required()
    @role_required(ROLE_OWNER)
    def put(self, business_id):
        current_user = User.query.get_or_404(get_jwt_identity())
        business = Business.query.get_or_404(business_id)

        if business.owner_id != current_user.id:
            return {"message": "Only the business owner can modify this business"}, 403

        json_data = request.get_json() or {}
        errors = business_create_update_schema.validate(json_data, partial=True)
        if errors:
            return {"errors": errors}, 400

        # Only allow safe fields to be updated
        updatable_fields = ["name", "address", "phone", "email", "website", "description"]
        for field in updatable_fields:
            if field in json_data:
                setattr(business, field, json_data[field])

        try:
            db.session.commit()
            return {"business": business_schema.dump(business), "message": "Business updated successfully"}, 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"message": "Database error", "details": str(e)}, 422

    @jwt_required()
    @role_required(ROLE_OWNER)
    def delete(self, business_id):
        current_user = User.query.get_or_404(get_jwt_identity())
        business = Business.query.get_or_404(business_id)

        if business.owner_id != current_user.id:
            return {"message": "Only the business owner can delete this business"}, 403

        try:
            db.session.delete(business)
            db.session.commit()
            return {"message": "Business deleted successfully"}, 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"message": "Database error", "details": str(e)}, 422


# ---------------------------
# Register resources
# ---------------------------
api.add_resource(MyBusinessResource, "/business/my")
api.add_resource(BusinessResource, "/businesses", "/businesses/<int:business_id>")
