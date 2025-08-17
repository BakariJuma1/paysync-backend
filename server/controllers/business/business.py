from flask import request, jsonify
from flask_restful import Resource, Api
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
from server.models import Business, User
from server.extension import db
from . import business_bp
from server.utils.decorators import role_required
from server.utils.roles import ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON, ALL_ROLES
from server.schemas.business_schema import BusinessSchema, BusinessCreateUpdateSchema

api = Api(business_bp)

# Schema instances
business_schema = BusinessSchema()
businesses_schema = BusinessSchema(many=True)
business_create_update_schema = BusinessCreateUpdateSchema()


@business_bp.route('/business/my', methods=['GET'])
@jwt_required()
@role_required(*ALL_ROLES)
def get_my_business():
    current_user = User.query.get_or_404(get_jwt_identity())

    if current_user.role == ROLE_OWNER:
        business = Business.query.filter_by(owner_id=current_user.id).first()
    else:
        business = Business.query.get(current_user.business_id) if current_user.business_id else None

    if not business:
        return jsonify({"message": "No business found"}), 404

    return  business_schema.dump(business), 200


class BusinessResource(Resource):

    @jwt_required()
    @role_required(ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON)
    def get(self, business_id=None):
        current_user = User.query.get_or_404(get_jwt_identity())

        if business_id:
            business = Business.query.get_or_404(business_id)

            # Restrict access if not owner of that business
            if current_user.role in (ROLE_ADMIN, ROLE_SALESPERSON) and business.id != current_user.business_id:
                return {"message": "Access denied"}, 403

            return business_schema.dump(business), 200

        # List view by role
        if current_user.role == ROLE_OWNER:
            return businesses_schema.dump(current_user.owned_businesses), 200

        if current_user.business_id:
            return businesses_schema.dump([Business.query.get(current_user.business_id)]), 200

        return [], 200

    @jwt_required()
    @role_required(ROLE_OWNER)
    def post(self):
        current_user_id = get_jwt_identity()
        json_data = request.get_json() or {}

        # Validate incoming data
        errors = business_create_update_schema.validate(json_data)
        if errors:
            return {"errors": errors}, 400

        try:
            business = Business(
                name=json_data['name'].strip(),
                owner_id=current_user_id,
                address=json_data.get('address'),
                phone=json_data.get('phone'),
                email=json_data.get('email'),
                website=json_data.get('website'),
                description=json_data.get('description')
            )
            db.session.add(business)
            db.session.commit()
            db.session.refresh(business)

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
        current_user_id = get_jwt_identity()
        business = Business.query.get_or_404(business_id)

        if business.owner_id != current_user_id:
            return {"message": "Only the business owner can modify this business"}, 403

        json_data = request.get_json() or {}
        errors = business_create_update_schema.validate(json_data, partial=True)
        if errors:
            return {"errors": errors}, 400

        for field, value in json_data.items():
            setattr(business, field, value)

        try:
            db.session.commit()
            return business_schema.dump(business), 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"message": "Database error", "details": str(e)}, 422

    @jwt_required()
    @role_required(ROLE_OWNER)
    def delete(self, business_id):
        current_user_id = get_jwt_identity()
        business = Business.query.get_or_404(business_id)

        if business.owner_id != current_user_id:
            return {"message": "Only the business owner can delete this business"}, 403

        try:
            db.session.delete(business)
            db.session.commit()
            return {"message": "Business deleted successfully"}, 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"message": "Database error", "details": str(e)}, 422


api.add_resource(BusinessResource, '/businesses', '/businesses/<int:business_id>')
