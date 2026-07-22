"""
Auth routes: register, login, and the current-user lookup used by the
frontend to check session state on load.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import AuthError, EcoMindError
from app.core.logging import get_logger
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.assessment import Assessment
from app.models.challenge import Challenge
from app.models.chat_log import ChatLog
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, DeleteAccountRequest, Token, UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)


@router.post("/register", response_model=Token, status_code=201)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> Token:
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise EcoMindError("An account with this email already exists.", status_code=409)

    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("Registered new user %s", user.id)
    return Token(access_token=create_access_token(user.id))


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)) -> Token:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    # Same error for "no such user" and "wrong password" — don't leak which one it was.
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise AuthError("Incorrect email or password.")

    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
async def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise AuthError("Current password is incorrect.")

    current_user.hashed_password = hash_password(payload.new_password)
    await db.commit()

    logger.info("Password changed for user %s", current_user.id)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    payload: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    if not verify_password(payload.password, current_user.hashed_password):
        raise AuthError("Password is incorrect.")

    user_id = current_user.id

    # No cascade delete is configured at the DB/ORM level for
    # Assessment/ChatLog/Challenge's user_id foreign key, so deleting a user
    # with any history would otherwise violate the FK constraint (Postgres)
    # or leave orphaned rows (SQLite, which doesn't enforce FKs by default).
    # Deleting explicitly here keeps behavior identical and correct
    # regardless of which database is running.
    await db.execute(delete(Assessment).where(Assessment.user_id == user_id))
    await db.execute(delete(ChatLog).where(ChatLog.user_id == user_id))
    await db.execute(delete(Challenge).where(Challenge.user_id == user_id))
    await db.delete(current_user)
    await db.commit()

    logger.info("Account and all associated data deleted: %s", user_id)
