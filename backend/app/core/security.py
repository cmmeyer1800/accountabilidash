"""Password hashing, JWT, and token encryption utilities."""

from datetime import UTC, datetime, timedelta

import bcrypt
from cryptography.fernet import Fernet, InvalidToken
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


def create_oauth_state_token(user_id: str) -> str:
    """Create a short-lived JWT for OAuth state (CSRF protection, 5 min expiry)."""
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=5)
    payload = {"sub": user_id, "purpose": "strava_oauth", "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_oauth_state_token(token: str) -> str | None:
    """Decode OAuth state JWT and return user_id (sub), or None if invalid."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("purpose") != "strava_oauth":
            return None
        return payload.get("sub")
    except JWTError:
        return None


# ── Token encryption (Strava OAuth tokens at rest) ─────────────────────────────


def encrypt_token(plain: str) -> str:
    """Encrypt a token for storage. Returns plain text if no key configured."""
    settings = get_settings()
    if not settings.token_encryption_key:
        return plain
    f = Fernet(settings.token_encryption_key.encode())
    return f.encrypt(plain.encode()).decode()


def decrypt_token(cipher: str | None) -> str | None:
    """Decrypt a stored token. Returns None if input is None. Handles legacy plain text."""
    if cipher is None:
        return None
    settings = get_settings()
    if not settings.token_encryption_key:
        return cipher
    try:
        f = Fernet(settings.token_encryption_key.encode())
        return f.decrypt(cipher.encode()).decode()
    except InvalidToken:
        return cipher  # Legacy plain-text token
