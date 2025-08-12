from flask import Blueprint

onboarding_bp = Blueprint('onboarding_bp',__name__)

from .owner_invites import *