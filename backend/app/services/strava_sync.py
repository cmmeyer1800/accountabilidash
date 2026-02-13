"""Strava activity sync — match activities to goals and create completions."""

import uuid
from datetime import UTC, date, datetime, timedelta

import structlog
from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.security import decrypt_token, encrypt_token
from app.schemas.goals import Goal, GoalCompletion, ValueType
from app.schemas.user import User
from app.services.completions import compute_period_start
from app.services.strava import (
    fetch_athlete_activities,
    is_token_expired,
    refresh_strava_token,
)

logger = structlog.get_logger()


async def sync_strava_to_goals(
    session: AsyncSession,
    user: User,
) -> dict[str, int]:
    """Fetch recent Strava activities and create completions for matching goals.

    Returns a dict with keys: activities_fetched, completions_added, goals_updated.
    """
    if not user.strava_connected or not user.strava_access_token:
        return {"activities_fetched": 0, "completions_added": 0, "goals_updated": 0}

    access_token = decrypt_token(user.strava_access_token)
    refresh_token = decrypt_token(user.strava_refresh_token)
    if is_token_expired(user.strava_expires_at) and refresh_token:
        data = await refresh_strava_token(refresh_token)
        access_token = data["access_token"]
        stmt = (
            update(User)
            .where(User.id == user.id)
            .values(
                strava_access_token=encrypt_token(data["access_token"]),
                strava_refresh_token=encrypt_token(data["refresh_token"]),
                strava_expires_at=data["expires_at"],
            )
        )
        await session.execute(stmt)
        await session.flush()

    # Fetch activities from last 31 days (covers monthly/yearly periods)
    after_ts = int((datetime.now(UTC) - timedelta(days=31)).timestamp())
    try:
        activities = await fetch_athlete_activities(
            access_token,
            after=after_ts,
            per_page=100,
        )
    except Exception as e:
        logger.warning("strava_sync_fetch_failed", error=str(e))
        return {"activities_fetched": 0, "completions_added": 0, "goals_updated": 0}

    # Goals with Strava integration
    stmt = (
        select(Goal)
        .where(Goal.user_id == user.id, Goal.is_active.is_(True))
        .where(Goal.strava_activity_types.isnot(None))
    )
    result = await session.execute(stmt)
    goals = list(result.scalars().all())

    if not goals:
        return {
            "activities_fetched": len(activities),
            "completions_added": 0,
            "goals_updated": 0,
        }

    completions_added = 0
    goals_updated: set[uuid.UUID] = set()

    for activity in activities:
        act_type = activity.get("type") or ""
        sport_type = activity.get("sport_type") or act_type
        start_date_str = activity.get("start_date") or activity.get("start_date_local", "")
        try:
            # Parse ISO date (e.g. "2024-02-13T14:30:00Z")
            act_date = date.fromisoformat(start_date_str.split("T")[0])
        except (ValueError, IndexError):
            continue

        act_id = activity.get("id")
        if act_id is None:
            continue

        distance = activity.get("distance") or 0  # meters
        moving_time = activity.get("moving_time") or 0  # seconds
        name = activity.get("name") or ""

        for goal in goals:
            types_list = goal.strava_activity_types or []
            if not types_list:
                continue

            # Match activity type: check type or sport_type
            if act_type not in types_list and sport_type not in types_list:
                continue

            # Check date range
            if act_date < goal.start_date:
                continue
            if goal.end_date and act_date > goal.end_date:
                continue

            period_start = compute_period_start(goal.frequency, act_date)

            # Already have completion for this activity?
            existing = await session.execute(
                select(GoalCompletion).where(
                    GoalCompletion.goal_id == goal.id,
                    GoalCompletion.strava_activity_id == act_id,
                )
            )
            if existing.scalar_one_or_none():
                continue

            # Count completions for this period
            count_stmt = (
                select(func.count())
                .where(GoalCompletion.goal_id == goal.id)
                .where(GoalCompletion.period_start == period_start)
            )
            current = (await session.execute(count_stmt)).scalar_one()
            if current >= goal.target_count:
                continue

            # Compute value for numeric goals (e.g. distance in km)
            value = None
            if goal.value_type == ValueType.NUMERIC and goal.value_unit:
                unit_lower = goal.value_unit.lower()
                if "km" in unit_lower or unit_lower == "k":
                    value = round(distance / 1000, 2)
                elif "mile" in unit_lower or "mi" in unit_lower:
                    value = round(distance / 1609.34, 2)
                elif "min" in unit_lower or "minute" in unit_lower:
                    value = round(moving_time / 60, 1)

            completion = GoalCompletion(
                goal_id=goal.id,
                completed_at=datetime.fromisoformat(start_date_str.replace("Z", "+00:00")),
                period_start=period_start,
                strava_activity_id=act_id,
                value=value,
                note=f"Strava: {name}" if name else "Strava activity",
            )
            session.add(completion)
            completions_added += 1
            goals_updated.add(goal.id)
            logger.info(
                "strava_completion_added",
                goal_id=str(goal.id),
                activity_id=act_id,
                period_start=str(period_start),
            )

    await session.flush()
    return {
        "activities_fetched": len(activities),
        "completions_added": completions_added,
        "goals_updated": len(goals_updated),
    }
