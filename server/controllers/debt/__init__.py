from flask import Blueprint

debt_bp = Blueprint('debt_bp',__name__)

from .debt_controller import *