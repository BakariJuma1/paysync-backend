from flask_restful import Resource, Api
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
from server.models import Business, User
from server.extension import db
from . import business_bp

api = Api(business_bp)

@business_bp.route('/business/my', methods=['GET'])
@jwt_required()
def get_my_business():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if current_user.role == 'owner':
        business = Business.query.filter_by(owner_id=current_user_id).first()
    else:
        business = Business.query.get(current_user.business_id) if current_user.business_id else None
        
    if not business:
        return jsonify({"message": "No business found"}), 404
    return jsonify(business.to_dict()), 200


class BusinessResource(Resource):
    @jwt_required()
    def get(self, business_id=None):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if business_id:
            business = Business.query.get_or_404(business_id)
            
            # Permission checks
            if current_user.role == 'salesperson' and business.id != current_user.business_id:
                return {"message": "Access denied"}, 403
            if current_user.role == 'admin' and business.owner_id != current_user_id and business.id != current_user.business_id:
                return {"message": "Access denied"}, 403
                
            return business.to_dict(), 200

        # List businesses based on role
        if current_user.role == 'owner':
            return [b.to_dict() for b in current_user.owned_businesses], 200
        elif current_user.role == 'admin':
            return [b.to_dict() for b in Business.query.all()], 200
        elif current_user.business_id:
            return [Business.query.get(current_user.business_id).to_dict()], 200
        return [], 200

    @jwt_required()
    def post(self):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        # STRICT OWNER-ONLY CREATION
        if current_user.role != 'owner':
            return {"message": "Only owners can create businesses"}, 403

        data = request.get_json() or {}
        
        # Validation
        required_fields = ['name', 'address', 'phone', 'email']
        if any(field not in data or not data[field].strip() for field in required_fields):
            return {"message": "All fields are required: name, address, phone, email"}, 400

        try:
            business = Business(
                name=data['name'].strip(),
                owner_id=current_user_id,  # Always set owner to current user
                address=data['address'].strip(),
                phone=data['phone'].strip(),
                email=data['email'].strip(),
                website=data.get('website', '').strip(),
                description=data.get('description', '').strip()
            )

            db.session.add(business)
            db.session.commit()
            
            return {
                "business": business.to_dict(),
                "message": "Business created successfully"
            }, 201

        except SQLAlchemyError as e:
            db.session.rollback()
            return {"message": "Database error", "details": str(e)}, 422

    @jwt_required()
    def put(self, business_id):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        business = Business.query.get_or_404(business_id)

        # OWNER-ONLY MODIFICATION
        if current_user.role != 'owner' or business.owner_id != current_user_id:
            return {"message": "Only the business owner can modify this business"}, 403

        data = request.get_json() or {}
        updatable_fields = ['name', 'address', 'phone', 'email', 'website', 'description']

        for field in updatable_fields:
            if field in data and data[field]:
                setattr(business, field, data[field].strip())

        try:
            db.session.commit()
            return business.to_dict(), 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"message": "Database error", "details": str(e)}, 422

    @jwt_required()
    def delete(self, business_id):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        business = Business.query.get_or_404(business_id)

        # OWNER-ONLY DELETION
        if current_user.role != 'owner' or business.owner_id != current_user_id:
            return {"message": "Only the business owner can delete this business"}, 403

        try:
            db.session.delete(business)
            db.session.commit()
            return {"message": "Business deleted successfully"}, 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"message": "Database error", "details": str(e)}, 422

api.add_resource(BusinessResource, '/businesses', '/businesses/<int:business_id>')