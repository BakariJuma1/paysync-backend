from flask_restful import Resource,Api
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import ChangeLog, User
from server.extension import db
from . import changelog_bp

api = Api(changelog_bp)
class ChangeLogListResource(Resource):
    @jwt_required()
    def get(self):
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)

        if user.role == "owner":
            # Owner sees all changelogs
            changelogs = ChangeLog.query.order_by(ChangeLog.timestamp.desc()).all()
        elif user.role == "admin":
            # Admin sees all changelogs but read-only
            changelogs = ChangeLog.query.order_by(ChangeLog.timestamp.desc()).all()
        else:
            # Salesman/Manager sees only their own changelogs
            changelogs = ChangeLog.query.filter_by(changed_by=user.id)\
                                        .order_by(ChangeLog.timestamp.desc()).all()

        return [log.to_dict() for log in changelogs], 200


class ChangeLogDetailResource(Resource):
    @jwt_required()
    def get(self, log_id):
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)

        changelog = ChangeLog.query.get_or_404(log_id)

        if user.role == "owner":
            return changelog.to_dict(), 200
        elif user.role == "admin":
            return changelog.to_dict(), 200
        elif changelog.changed_by == user.id:
            return changelog.to_dict(), 200
        else:
            return {"error": "Access denied"}, 403

    @jwt_required()
    def delete(self, log_id):
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)

        if user.role != "owner":
            return {"error": "Only the owner can delete logs"}, 403

        changelog = ChangeLog.query.get_or_404(log_id)
        db.session.delete(changelog)
        db.session.commit()

        return {"message": "Changelog deleted"}, 200

api.add_resource(ChangeLogListResource, '/changelogs')
api.add_resource(ChangeLogDetailResource, '/changelogs/<int:log_id>')