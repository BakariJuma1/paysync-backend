import secrets

def generate_invite_token():
    return secrets.token_urlsafe(32)

