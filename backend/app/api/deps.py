"""
Shared FastAPI dependencies used across route modules.

Kept separate from individual route files so chat.py, carbon.py, plan.py,
and challenge.py (Phase 3+) can all import `get_current_user` without
importing from each other.
"""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AuthError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise AuthError("Missing authentication token.")

    user_id = decode_access_token(credentials.credentials)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise AuthError("User no longer exists.")

    return user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Same resolution as get_current_user, but returns None instead of raising
    when there's no token — for routes that should work for guests (e.g. the
    carbon calculator, where the landing page promises "no account required
    to see your first score") while still recognizing and persisting for
    logged-in users when a token is present.
    """
    if credentials is None:
        return None

    try:
        user_id = decode_access_token(credentials.credentials)
    except AuthError:
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
