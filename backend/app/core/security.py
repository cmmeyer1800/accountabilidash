"""Password hashing and JWT token utilities."""

from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.core.settings import get_settings

# ── Password helpers ─────────────────────────────────────────────────────────


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the plain-text password."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches the *hashed* password."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── JWT helpers ──────────────────────────────────────────────────────────────


def create_access_token(subject: str, extra: dict | None = None) -> str:
    """Create a signed JWT with *subject* as the ``sub`` claim."""
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict = {"sub": subject, "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT.  Raises ``JWTError`` on failure."""
    settings = get_settings()
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise
