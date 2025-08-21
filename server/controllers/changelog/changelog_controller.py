import logging
from flask import request
from flask_restful import Resource, Api
from flask_jwt_extended import jwt_required, get_jwt_identity
from server.models import ChangeLog, User
from server.extension import db
from . import changelog_bp
from server.utils.decorators import role_required
from server.utils.roles import ROLE_OWNER, ROLE_ADMIN, ROLE_SALESPERSON, ALL_ROLES
from server.schemas.changelog_schema import ChangeLogSchema, ChangeLogCreateUpdateSchema

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

api = Api(changelog_bp)

# Schemas
changelog_schema = ChangeLogSchema()
changelogs_schema = ChangeLogSchema(many=True)
changelog_create_schema = ChangeLogCreateUpdateSchema()


def format_changelog(changelog):
    """Attach human-readable user details to changelog output."""
    user = User.query.get(changelog.changed_by)
    actor_info = {
        "id": user.id,
        "name": user.name,
        "role": user.role
    } if user else {"id": changelog.changed_by, "name": "Unknown", "role": "Unknown"}

    data = changelog_schema.dump(changelog)
    data["changed_by"] = actor_info
    return data


class ChangeLogListResource(Resource):
    @jwt_required()
    @role_required(*ALL_ROLES)
    def get(self):
        """
        Owners/Admins: see logs for their business.
        Salespersons: see only their own logs within business.
        """
        try:
            current_user = User.query.get_or_404(get_jwt_identity())
            logger.info(f"Fetching changelogs for user={current_user.name} role={current_user.role}")

            if current_user.role in (ROLE_OWNER, ROLE_ADMIN):
                changelogs = (
                    ChangeLog.query
                    .join(User, User.id == ChangeLog.changed_by)
                    .filter(User.business_id == current_user.business_id)
                    .order_by(ChangeLog.timestamp.desc())
                    .all()
                )
            else:  # Salesperson
                changelogs = (
                    ChangeLog.query
                    .join(User, User.id == ChangeLog.changed_by)
                    .filter(
                        ChangeLog.changed_by == current_user.id,
                        User.business_id == current_user.business_id
                    )
                    .order_by(ChangeLog.timestamp.desc())
                    .all()
                )

            logger.info(f"Returning {len(changelogs)} changelog entries")
            return [format_changelog(c) for c in changelogs], 200

        except Exception as e:
            logger.error("Error in ChangeLogListResource GET", exc_info=e)
            return {"error": "Internal Server Error"}, 500

    @jwt_required()
    @role_required(ROLE_OWNER, ROLE_ADMIN)
    def post(self):
        """
        Create a new changelog.
        Only Owner/Admin can create.
        """
        try:
            json_data = request.get_json()
            if not json_data:
                return {"error": "No input data provided"}, 400

            # Validate and deserialize input
            data = changelog_create_schema.load(json_data)
            changelog = ChangeLog(**data)

            db.session.add(changelog)
            db.session.commit()
            logger.info(f"Changelog created: id={changelog.id}")

            return format_changelog(changelog), 201

        except Exception as e:
            logger.error("Error in ChangeLogListResource POST", exc_info=e)
            return {"error": "Internal Server Error"}, 500


class ChangeLogDetailResource(Resource):
    @jwt_required()
    @role_required(*ALL_ROLES)
    def get(self, log_id):
        try:
            current_user = User.query.get_or_404(get_jwt_identity())
            changelog = ChangeLog.query.get_or_404(log_id)

            # Verify business scope
            actor = User.query.get(changelog.changed_by)
            if not actor or actor.business_id != current_user.business_id:
                return {"error": "Access denied"}, 403

            if current_user.role in (ROLE_OWNER, ROLE_ADMIN) or changelog.changed_by == current_user.id:
                return format_changelog(changelog), 200

            return {"error": "Access denied"}, 403

        except Exception as e:
            logger.error("Error in ChangeLogDetailResource GET", exc_info=e)
            return {"error": "Internal Server Error"}, 500

    @jwt_required()
    @role_required(ROLE_OWNER, ROLE_ADMIN)
    def put(self, log_id):
        """
        Update a changelog entry.
        Only Owner/Admin, scoped to their business.
        """
        try:
            current_user = User.query.get_or_404(get_jwt_identity())
            changelog = ChangeLog.query.get_or_404(log_id)

            actor = User.query.get(changelog.changed_by)
            if not actor or actor.business_id != current_user.business_id:
                return {"error": "Access denied"}, 403

            json_data = request.get_json()
            if not json_data:
                return {"error": "No input data provided"}, 400

            data = changelog_create_schema.load(json_data, partial=True)

            for key, value in data.items():
                setattr(changelog, key, value)

            db.session.commit()
            logger.info(f"Changelog updated: id={log_id}")

            return format_changelog(changelog), 200

        except Exception as e:
            logger.error("Error in ChangeLogDetailResource PUT", exc_info=e)
            return {"error": "Internal Server Error"}, 500

    @jwt_required()
    @role_required(ROLE_OWNER)
    def delete(self, log_id):
        """
        Delete a changelog.
        Only Owner, scoped to business.
        """
        try:
            current_user = User.query.get_or_404(get_jwt_identity())
            changelog = ChangeLog.query.get_or_404(log_id)

            actor = User.query.get(changelog.changed_by)
            if not actor or actor.business_id != current_user.business_id:
                return {"error": "Access denied"}, 403

            db.session.delete(changelog)
            db.session.commit()
            logger.info(f"Changelog deleted: id={log_id}")

            return {"message": "Changelog deleted"}, 200

        except Exception as e:
            logger.error("Error in ChangeLogDetailResource DELETE", exc_info=e)
            return {"error": "Internal Server Error"}, 500


# Register routes
api.add_resource(ChangeLogListResource, '/changelogs')
api.add_resource(ChangeLogDetailResource, '/changelogs/<int:log_id>')
