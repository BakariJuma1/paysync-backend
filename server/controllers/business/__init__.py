from flask import Blueprint

business_bp = Blueprint('business_bp',__name__)

from .business import *