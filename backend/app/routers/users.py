"""Admin user-management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_superuser
from app.models.user import UserAdminCreate, UserCreate, UserRead
from app.schemas.user import User
from app.services.auth import AuthError, register_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=201)
async def admin_create_user(
    data: UserAdminCreate,
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(get_current_superuser),
) -> User:
    """Create a user as an admin (bypasses the registration-disabled check)."""
    create_data = UserCreate(
        email=data.email,
        password=data.password,
        full_name=data.full_name,
    )
    try:
        user = await register_user(session, create_data, bypass_registration_check=True)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    # Apply admin-only fields that aren't part of normal registration
    user.is_active = data.is_active
    user.is_superuser = data.is_superuser
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user
