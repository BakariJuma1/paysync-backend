from flask import Blueprint

reminder_bp = Blueprint('reminder_bp',__name__)

from .reminder import *