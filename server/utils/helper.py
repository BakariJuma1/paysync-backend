from flask import request

def parse_json(required_fields=None, allowed_roles=None):
    data = request.get_json(force=True) or {}

    if required_fields:
        missing = [f for f in required_fields if f not in data or not data[f]]
        if missing:
            return None, {"message": f"Missing required fields: {', '.join(missing)}"}, 400

    if allowed_roles and "role" in data and data["role"] not in allowed_roles:
        return None, {"message": f"Role must be one of: {', '.join(allowed_roles)}"}, 400

    return data, None, None

