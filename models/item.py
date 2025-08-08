from server.extension import db
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime

class Item(db.Model,SerializerMixin):
    __tablename__ ='items'

    debt_id = db.Column(db.Integer,db.ForeignKey)
    name = db.Column(db.String,nullable=False)
    price = db.Column(db.Float,nullable=False)
    category = db.Column(db.String,nullable=False)
    quantity = db.Column(db.Integer,nullable=False)
    total_price = db.Column(db.Float,nullable=False)