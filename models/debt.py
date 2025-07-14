from server.extension import db
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime


class Debt(db.Model,SerializerMixin):
    __tablename__ = 'debts'

    id = db.Column(db.Integer,primary_key=True)