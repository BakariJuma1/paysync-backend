from functools import wraps
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from flask import jsonify
from .roles import ROLE_SALESPERSON, ROLE_ADMIN, ROLE_OWNER

# restrict access to specific roles
def role_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role")

            if user_role not in roles:
                return jsonify({"message": "Forbidden: Insufficient permissions"}), 403

            return fn(*args, **kwargs)
        return decorator
    return wrapper
