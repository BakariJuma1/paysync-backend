from server.extension import db
from server.models import ChangeLog
from flask_jwt_extended import get_jwt_identity
from datetime import datetime

def log_change(entity_type, entity_id, action, details=None):
    try:
        user_id = get_jwt_identity()
    except RuntimeError:
        user_id = None  # In case JWT is not active in this context

    log_entry = ChangeLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        changed_by=user_id,
        timestamp=datetime.utcnow(),
        details=details or {}
    )
    db.session.add(log_entry)
    
