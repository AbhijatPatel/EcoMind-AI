"""
Password hashing and JWT handling.

bcrypt is used directly (not passlib) to avoid passlib's dependency on a
bcrypt backend detection layer that has repeatedly broken across versions.
JWTs are signed with HS256 using the app's single jwt_secret — this is
fine for a single backend service; if EcoMind AI ever splits into multiple
services verifying tokens independently, this should move to RS256 with a
public/private keypair so only the auth service holds the signing key.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import get_settings
from app.core.errors import AuthError

ALGORITHM_CLAIM = "sub"  # JWT subject claim holds the user id


def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        # Malformed hash (shouldn't happen outside data corruption) — treat as invalid, don't crash.
        return False


def create_access_token(user_id: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {ALGORITHM_CLAIM: user_id, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    """Returns the user id encoded in the token, or raises AuthError."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise AuthError("Session expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid authentication token.")

    user_id = payload.get(ALGORITHM_CLAIM)
    if not user_id:
        raise AuthError("Invalid authentication token.")
    return user_id
