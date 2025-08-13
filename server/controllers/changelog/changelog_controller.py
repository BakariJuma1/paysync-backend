import logging
from flask_restful import Resource, Api
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import ChangeLog, User
from server.extension import db
from . import changelog_bp

# Configure logger for this module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)  # Set to DEBUG for more verbosity

api = Api(changelog_bp)

class ChangeLogListResource(Resource):
    @jwt_required()
    def get(self):
        try:
            current_user_id = get_jwt_identity()
            logger.info(f"ChangeLogListResource GET called by user_id: {current_user_id}")

            user = User.query.get_or_404(current_user_id)
            logger.debug(f"User found: {user.id} with role {user.role}")

            if user.role == "owner":
                changelogs = ChangeLog.query.order_by(ChangeLog.timestamp.desc()).all()
            elif user.role == "admin":
                changelogs = ChangeLog.query.order_by(ChangeLog.timestamp.desc()).all()
            else:
                changelogs = ChangeLog.query.filter_by(changed_by=user.id)\
                                            .order_by(ChangeLog.timestamp.desc()).all()

            logger.info(f"Returning {len(changelogs)} changelog entries")
            return [log.to_dict() for log in changelogs], 200

        except Exception as e:
            logger.error("Error in ChangeLogListResource GET", exc_info=e)
            return {"error": "Internal Server Error"}, 500


class ChangeLogDetailResource(Resource):
    @jwt_required()
    def get(self, log_id):
        try:
            current_user_id = get_jwt_identity()
            logger.info(f"ChangeLogDetailResource GET called by user_id: {current_user_id} for log_id: {log_id}")

            user = User.query.get_or_404(current_user_id)
            changelog = ChangeLog.query.get_or_404(log_id)

            if user.role in ["owner", "admin"] or changelog.changed_by == user.id:
                logger.info("Access granted to changelog")
                return changelog.to_dict(), 200
            else:
                logger.warning(f"Access denied for user {user.id} to changelog {log_id}")
                return {"error": "Access denied"}, 403

        except Exception as e:
            logger.error("Error in ChangeLogDetailResource GET", exc_info=e)
            return {"error": "Internal Server Error"}, 500

    @jwt_required()
    def delete(self, log_id):
        try:
            current_user_id = get_jwt_identity()
            logger.info(f"ChangeLogDetailResource DELETE called by user_id: {current_user_id} for log_id: {log_id}")

            user = User.query.get_or_404(current_user_id)
            if user.role != "owner":
                logger.warning(f"User {user.id} with role {user.role} tried to delete changelog {log_id}")
                return {"error": "Only the owner can delete logs"}, 403

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
