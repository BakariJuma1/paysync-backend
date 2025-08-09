from datetime import datetime
from server.extension import db
from sqlalchemy_serializer import SerializerMixin

class ChangeLog(db.Model, SerializerMixin):
    __tablename__ = "changelogs"

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    action = db.Column(db.String(50))  # create, update, delete
    changed_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.JSON)

    serialize_rules = ('-changed_by_user.changelogs',)

    # Relationships
    changed_by_user = db.relationship("User", back_populates="changelogs")
