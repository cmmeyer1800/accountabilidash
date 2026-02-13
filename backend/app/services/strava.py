"""Strava OAuth service — token exchange and refresh."""

import time
from typing import Any

import httpx
import structlog

from app.core.settings import get_settings

logger = structlog.get_logger()

STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
STRAVA_API_BASE = "https://www.strava.com/api/v3"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"


def build_authorization_url(state: str) -> str:
    """Build the Strava OAuth authorization URL for the user to visit."""
    settings = get_settings()
    if not settings.strava_id:
        raise ValueError("Strava OAuth not configured: STRAVA_ID is required")

    params = {
        "client_id": settings.strava_id,
        "redirect_uri": settings.strava_redirect_uri,
        "response_type": "code",
        "approval_prompt": "auto",
        "scope": "read,activity:read_all",
        "state": state,
    }
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{STRAVA_AUTH_URL}?{qs}"


async def exchange_code_for_tokens(code: str) -> dict[str, Any]:
    """Exchange an authorization code for access and refresh tokens."""
    settings = get_settings()
    if not settings.strava_id or not settings.strava_secret:
        raise ValueError("Strava OAuth not configured: STRAVA_ID and STRAVA_SECRET required")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            STRAVA_TOKEN_URL,
            data={
                "client_id": settings.strava_id,
                "client_secret": settings.strava_secret,
                "code": code,
                "grant_type": "authorization_code",
            },
        )
        response.raise_for_status()
        data = response.json()

    logger.info(
        "strava_tokens_exchanged",
        athlete_id=data.get("athlete", {}).get("id"),
    )
    return data


async def refresh_strava_token(refresh_token: str) -> dict[str, Any]:
    """Refresh an expired Strava access token."""
    settings = get_settings()
    if not settings.strava_id or not settings.strava_secret:
        raise ValueError("Strava OAuth not configured")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            STRAVA_TOKEN_URL,
            data={
                "client_id": settings.strava_id,
                "client_secret": settings.strava_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )
        response.raise_for_status()
        return response.json()


def is_token_expired(expires_at: int | None) -> bool:
    """Check if the Strava access token is expired or will expire within 1 hour."""
    if expires_at is None:
        return True
    # Strava recommends refreshing if < 1 hour (3600s) remaining
    return time.time() >= (expires_at - 3600)


async def fetch_athlete(access_token: str) -> dict[str, Any]:
    """Fetch the authenticated athlete's profile from Strava."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{STRAVA_API_BASE}/athlete",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()


async def fetch_athlete_activities(
    access_token: str,
    *,
    after: int | None = None,
    before: int | None = None,
    per_page: int = 100,
) -> list[dict[str, Any]]:
    """Fetch recent activities for the authenticated athlete.

    after/before are Unix timestamps. Activities are returned newest first.
    """
    params: dict[str, int] = {"per_page": min(per_page, 200)}
    if after is not None:
        params["after"] = after
    if before is not None:
        params["before"] = before

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{STRAVA_API_BASE}/athlete/activities",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
        )
        response.raise_for_status()
        return response.json()
