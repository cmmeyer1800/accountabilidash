"""Authentication endpoints: register, login, current-user lookup, and Strava OAuth."""

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_oauth_state_token,
    decode_oauth_state_token,
    decrypt_token,
    encrypt_token,
)
from app.models.user import Token, UserCreate, UserLogin, UserRead
from app.schemas.user import User
from app.services.auth import AuthError, authenticate_user, register_user
from app.services.strava import (
    build_authorization_url,
    exchange_code_for_tokens,
    fetch_athlete,
    is_token_expired,
    refresh_strava_token,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=201)
async def register(
    data: UserCreate,
    session: AsyncSession = Depends(get_session),
) -> User:
    """Register a new user account."""
    try:
        return await register_user(session, data)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/login", response_model=Token)
async def login(
    data: UserLogin,
    session: AsyncSession = Depends(get_session),
) -> Token:
    """Authenticate and return a JWT access token."""
    try:
        user = await authenticate_user(session, data.email, data.password)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)


@router.get("/me", response_model=UserRead)
async def read_current_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Return the currently authenticated user."""
    return current_user


# ── Strava OAuth ────────────────────────────────────────────────────────────


@router.get("/strava/connect")
async def strava_connect(
    current_user: User = Depends(get_current_user),
) -> RedirectResponse:
    """Redirect the authenticated user to Strava to authorize and link their account."""
    try:
        state = create_oauth_state_token(str(current_user.id))
        url = build_authorization_url(state)
        return RedirectResponse(url=url, status_code=302)
    except ValueError as exc:
        logger.exception("strava connect failed")
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/strava/connect-url")
async def strava_connect_url(
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Return the Strava authorization URL for the frontend to redirect to (auth required)."""
    try:
        state = create_oauth_state_token(str(current_user.id))
        url = build_authorization_url(state)
        return {"url": url}
    except ValueError as exc:
        logger.exception("strava connect failed")
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/strava/callback")
async def strava_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    """Handle Strava OAuth callback: exchange code for tokens and link to user."""
    from app.core.settings import get_settings

    settings = get_settings()
    frontend_url = settings.frontend_url.rstrip("/")

    if error == "access_denied":
        return RedirectResponse(url=f"{frontend_url}/account?strava=denied", status_code=302)

    if not code or not state:
        return RedirectResponse(url=f"{frontend_url}/account?strava=error", status_code=302)

    user_id = decode_oauth_state_token(state)
    if not user_id:
        return RedirectResponse(url=f"{frontend_url}/account?strava=error", status_code=302)

    try:
        data = await exchange_code_for_tokens(code)
    except Exception:
        return RedirectResponse(url=f"{frontend_url}/account?strava=error", status_code=302)

    athlete = data.get("athlete", {})
    athlete_id = str(athlete.get("id")) if athlete.get("id") else None

    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    stmt = (
        update(User)
        .where(User.id == uuid.UUID(user_id))
        .values(
            strava_athlete_id=athlete_id,
            strava_access_token=encrypt_token(access_token) if access_token else None,
            strava_refresh_token=encrypt_token(refresh_token) if refresh_token else None,
            strava_expires_at=data.get("expires_at"),
        )
    )
    await session.execute(stmt)
    await session.commit()

    return RedirectResponse(url=f"{frontend_url}/account?strava=connected", status_code=302)


@router.get("/strava/me")
async def strava_me(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Fetch the current user's Strava athlete profile (requires linked Strava account)."""
    if not current_user.strava_connected or not current_user.strava_access_token:
        raise HTTPException(
            status_code=404,
            detail="Strava account not linked. Connect Strava first.",
        )

    access_token = decrypt_token(current_user.strava_access_token)
    refresh_token = decrypt_token(current_user.strava_refresh_token)
    if is_token_expired(current_user.strava_expires_at) and refresh_token:
        data = await refresh_strava_token(refresh_token)
        access_token = data["access_token"]
        stmt = (
            update(User)
            .where(User.id == current_user.id)
            .values(
                strava_access_token=encrypt_token(data["access_token"]),
                strava_refresh_token=encrypt_token(data["refresh_token"]),
                strava_expires_at=data["expires_at"],
            )
        )
        await session.execute(stmt)
        await session.commit()

    athlete = await fetch_athlete(access_token)
    return athlete
