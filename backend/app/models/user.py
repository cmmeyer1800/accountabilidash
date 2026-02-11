"""Pydantic models for user-related request / response bodies."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

# ── Request models ───────────────────────────────────────────────────────────


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class UserAdminCreate(BaseModel):
    """Model for admin-created users — allows setting roles and status."""

    email: EmailStr
    password: str
    full_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ── Response models ──────────────────────────────────────────────────────────


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
