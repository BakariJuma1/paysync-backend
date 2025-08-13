from functools import wraps
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from flask import jsonify

 
    # Restrict access to users with certain roles.
    # Example: @role_required("owner", "admin")
    
def role_required(*roles):
   
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()  
            claims = get_jwt()
            if "role" not in claims or claims["role"] not in roles:
                return jsonify({"message": "Forbidden: Insufficient permissions"}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper