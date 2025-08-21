from functools import wraps
from flask_jwt_extended import get_jwt, verify_jwt_in_request, get_jwt_identity
from flask import g
from server.models import User
from .roles import ROLE_SALESPERSON, ROLE_ADMIN, ROLE_OWNER, ALL_ROLES

def role_required(*roles):
    """
    Decorator to restrict access to routes based on user role.
    If no roles are passed, allows access to ALL_ROLES by default.
    Attaches the current user to g.current_user.
    """
    allowed_roles = roles or ALL_ROLES

    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            # Verify JWT first
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role")
            user_id = get_jwt_identity()

            # Fetch user from DB and attach to g
            user = User.query.get(user_id)
            if not user:
                return {"message": "User not found"}, 404
            g.current_user = user

            # Role check
            if user_role not in allowed_roles:
                return {"message": "Forbidden: Insufficient permissions"}, 403

            return fn(*args, **kwargs)
        return decorator
    return wrapper
