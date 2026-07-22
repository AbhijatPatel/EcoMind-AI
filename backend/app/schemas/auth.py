"""
Auth request/response schemas.

Schemas are the boundary that keeps ORM models out of API responses —
UserOut never includes hashed_password, even by accident, because that
field simply isn't declared on it.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class DeleteAccountRequest(BaseModel):
    # Require re-entering the password for a destructive, irreversible
    # action — a valid session token alone (e.g. left logged in on a shared
    # device) shouldn't be enough to delete the account.
    password: str
