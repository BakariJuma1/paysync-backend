import logging
from flask_restful import Resource, Api
from flask_jwt_extended import jwt_required, get_jwt_identity
from server.models import ChangeLog, User
from server.extension import db
from . import changelog_bp
from server.utils.decorators import role_required
from server.utils.roles import ROLE_OWNER, ROLE_ADMIN, ALL_ROLES

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

api = Api(changelog_bp)


class ChangeLogListResource(Resource):
    @jwt_required()
    @role_required(*ALL_ROLES)
    def get(self):
        """
        Owners and Admins see all logs.
        Salespersons see only their own logs.
        """
        try:
            current_user = User.query.get_or_404(get_jwt_identity())
            logger.info(f"Fetching changelogs for user_id={current_user.id} role={current_user.role}")

            if current_user.role in (ROLE_OWNER, ROLE_ADMIN):
                changelogs = ChangeLog.query.order_by(ChangeLog.timestamp.desc()).all()
            else:
                changelogs = (
                    ChangeLog.query
                    .filter_by(changed_by=current_user.id)
                    .order_by(ChangeLog.timestamp.desc())
                    .all()
                )

            logger.info(f"Returning {len(changelogs)} changelog entries")
            return [log.to_dict() for log in changelogs], 200

        except Exception as e:
            logger.error("Error in ChangeLogListResource GET", exc_info=e)
            return {"error": "Internal Server Error"}, 500


class ChangeLogDetailResource(Resource):
    @jwt_required()
    @role_required(*ALL_ROLES)
    def get(self, log_id):
        try:
            current_user = User.query.get_or_404(get_jwt_identity())
            changelog = ChangeLog.query.get_or_404(log_id)

            logger.info(f"User {current_user.id} requests changelog {log_id}")

            if current_user.role in (ROLE_OWNER, ROLE_ADMIN) or changelog.changed_by == current_user.id:
                return changelog.to_dict(), 200

            logger.warning(f"Access denied: user {current_user.id} to changelog {log_id}")
            return {"error": "Access denied"}, 403

        except Exception as e:
            logger.error("Error in ChangeLogDetailResource GET", exc_info=e)
            return {"error": "Internal Server Error"}, 500

    @jwt_required()
    @role_required(ROLE_OWNER)
    def delete(self, log_id):
        try:
            changelog = ChangeLog.query.get_or_404(log_id)

            db.session.delete(changelog)
            db.session.commit()
            logger.info(f"Changelog {log_id} deleted successfully")

            return {"message": "Changelog deleted"}, 200

        except Exception as e:
            logger.error("Error in ChangeLogDetailResource DELETE", exc_info=e)
            return {"error": "Internal Server Error"}, 500


api.add_resource(ChangeLogListResource, '/changelogs')
api.add_resource(ChangeLogDetailResource, '/changelogs/<int:log_id>')
