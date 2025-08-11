from flask_restful import Resource, Api
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from server.models import Business, User
from server.extension import db
from datetime import datetime
from . import business_bp

api = Api(business_bp)

class BusinessResource(Resource):

    @jwt_required()
    def get(self, business_id=None):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if business_id:
            business = Business.query.get_or_404(business_id)

            # Salesman may only view businesses they belong to? Or all?
            # Adjust this logic as needed
            if current_user.role == 'salesman':
                # Example: restrict salesman to only businesses where owner is current_user?
                if business.owner_id != current_user_id:
                    return jsonify({"message": "Access denied"}), 403

            return jsonify(business.to_dict()), 200

        # List all businesses — filter by role
        if current_user.role == 'owner':
            # Owners see only their businesses
            businesses = Business.query.filter_by(owner_id=current_user_id).all()
        elif current_user.role == 'admin':
            # Admin sees all businesses
            businesses = Business.query.all()
        else:
            # Salesman might see only businesses they belong to or empty list
            businesses = Business.query.filter_by(owner_id=current_user_id).all()

        return jsonify([b.to_dict() for b in businesses]), 200

    @jwt_required()
    def post(self):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        # Only owners or admins can create businesses
        if current_user.role not in ['owner', 'admin']:
            return jsonify({"message": "Access denied"}), 403

        data = request.get_json() or {}

        name = data.get('name')
        if not name:
            return jsonify({"message": "Business name is required"}), 400

        contact_info = data.get('contact_info')

        business = Business(
            name=name,
            owner_id=current_user_id if current_user.role == 'owner' else data.get('owner_id', current_user_id),
            contact_info=contact_info
        )

        db.session.add(business)
        db.session.commit()

        return jsonify(business.to_dict()), 201

    @jwt_required()
    def put(self, business_id):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        business = Business.query.get_or_404(business_id)

        # Only owner of business or admin can update
        if current_user.role not in ['owner', 'admin'] or (current_user.role == 'owner' and business.owner_id != current_user_id):
            return jsonify({"message": "Access denied"}), 403

        data = request.get_json() or {}

        if 'name' in data:
            business.name = data['name']

        if 'contact_info' in data:
            business.contact_info = data['contact_info']

        db.session.commit()

        return jsonify(business.to_dict()), 200

    @jwt_required()
    def delete(self, business_id):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        business = Business.query.get_or_404(business_id)

        # Only owner of business or admin can delete
        if current_user.role not in ['owner', 'admin'] or (current_user.role == 'owner' and business.owner_id != current_user_id):
            return jsonify({"message": "Access denied"}), 403

        db.session.delete(business)
        db.session.commit()

        return jsonify({"message": f"Business {business_id} deleted"}), 200


# Register resource routes
api.add_resource(BusinessResource, '/businesses', '/businesses/<int:business_id>')
