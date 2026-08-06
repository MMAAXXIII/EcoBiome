import os
import time

import jwt
from jwt.exceptions import InvalidTokenError

ALGO = "HS256"


def _jwt_secret() -> str:
    secret = os.environ.get("ECOBIOME_JWT_SECRET", "")
    if len(secret.encode("utf-8")) < 32:
        raise RuntimeError(
            "ECOBIOME_JWT_SECRET doit contenir au moins 32 octets."
        )
    return secret

def create_token(username: str):
    payload = {
        'user': username,
        'exp': time.time() + 3600
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=ALGO)

def verify_token(token: str):
    try:
        return jwt.decode(token, _jwt_secret(), algorithms=[ALGO])
    except InvalidTokenError:
        return None
