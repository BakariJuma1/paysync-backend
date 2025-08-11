from flask import Blueprint

changelog_bp = Blueprint('changelog_bp',__name__)

from .changelog_controller import *