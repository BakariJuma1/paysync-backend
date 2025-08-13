from flask import Blueprint

dashboard_bp = Blueprint('dashboard_bp',__name__)

from .admin_dashboard import *
from .owner_dashboard import *
from .salesman_dashboard import *