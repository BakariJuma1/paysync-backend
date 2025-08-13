from flask import Blueprint

settings_bp = Blueprint('settings_bp',__name__)

from .admin_settings import *
from .owner_settings import *
from .salesman_settings import *