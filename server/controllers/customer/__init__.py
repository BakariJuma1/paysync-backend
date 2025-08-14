from flask import Blueprint

customer_bp = Blueprint('customer_bp',__name__)

from .customer import *