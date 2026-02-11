"""Authentication service — business logic for user registration and login."""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.security import hash_password, verify_password
from app.core.settings import get_settings
from app.models.user import UserCreate
from app.schemas.user import User

logger = structlog.get_logger()


class AuthError(Exception):
    """Raised when an authentication operation fails."""

    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code


async def register_user(
    session: AsyncSession,
    data: UserCreate,
    *,
    bypass_registration_check: bool = False,
) -> User:
    """Create a new user.

    Raises ``AuthError`` if registration is disabled (unless *bypass_registration_check*
    is True, e.g. when an admin creates a user) or the email is taken.
    """
    if not bypass_registration_check:
        settings = get_settings()
        if not settings.allow_registration:
            logger.warning("registration_failed", reason="registration_disabled")
            raise AuthError("Registration is currently disabled.", status_code=403)

    stmt = select(User).where(User.email == data.email)
    result = await session.execute(stmt)
    if result.scalars().first() is not None:
        logger.warning("registration_failed", reason="email_taken", email=data.email)
        raise AuthError("A user with this email already exists.", status_code=409)

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    logger.info("user_registered", user_id=str(user.id), email=user.email)
    return user


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User:
    """Verify credentials and return the user.  Raises ``AuthError`` on failure."""
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    user = result.scalars().first()

    if user is None or not verify_password(password, user.hashed_password):
        logger.warning("login_failed", email=email)
        raise AuthError("Invalid email or password.", status_code=401)

    if not user.is_active:
        logger.warning("login_inactive_user", email=email)
        raise AuthError("User account is disabled.", status_code=403)

    logger.info("user_authenticated", user_id=str(user.id))
    return user
