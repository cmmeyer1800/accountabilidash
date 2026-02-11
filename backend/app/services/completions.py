"""Completions service — check-in logic and progress queries."""

import uuid
from datetime import UTC, date, datetime, timedelta

import structlog
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.goals import CheckInCreate, GoalWithProgress
from app.schemas.goals import (
    Frequency,
    Goal,
    GoalCompletion,
)

logger = structlog.get_logger()


def compute_period_start(frequency: Frequency | None, dt: date) -> date:
    """Return the canonical start date of the period containing *dt*.

    - daily:   the date itself
    - weekly:  Monday of that week
    - monthly: 1st of the month
    - yearly:  Jan 1
    - None (one-time): the date itself
    """
    if frequency is None or frequency == Frequency.DAILY:
        return dt
    if frequency == Frequency.WEEKLY:
        return dt - timedelta(days=dt.weekday())
    if frequency == Frequency.MONTHLY:
        return dt.replace(day=1)
    if frequency == Frequency.YEARLY:
        return dt.replace(month=1, day=1)
    return dt


async def check_in(
    session: AsyncSession,
    goal_id: uuid.UUID,
    user_id: uuid.UUID,
    data: CheckInCreate,
) -> GoalCompletion:
    """Record a completion for a goal.

    Raises ValueError if the goal is already fully completed for the current period.
    """
    # Fetch goal (scoped to user).
    stmt = select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    result = await session.execute(stmt)
    goal = result.scalars().first()

    if goal is None:
        msg = "Goal not found"
        raise ValueError(msg)
    if not goal.is_active:
        msg = "Goal is not active"
        raise ValueError(msg)

    today = date.today()
    ps = compute_period_start(goal.frequency, today)

    # Count existing completions for this period.
    count_stmt = (
        select(func.count())
        .where(GoalCompletion.goal_id == goal_id)
        .where(GoalCompletion.period_start == ps)
    )
    current_count = (await session.execute(count_stmt)).scalar_one()

    if current_count >= goal.target_count:
        msg = "Goal already completed for this period"
        raise ValueError(msg)

    completion = GoalCompletion(
        goal_id=goal_id,
        completed_at=datetime.now(UTC),
        period_start=ps,
        value=data.value,
        note=data.note,
    )
    session.add(completion)
    await session.flush()
    await session.refresh(completion)
    logger.info(
        "goal_checked_in",
        goal_id=str(goal_id),
        user_id=str(user_id),
        period_start=str(ps),
    )
    return completion


async def list_goals_with_progress(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> list[GoalWithProgress]:
    """Return all active goals for a user with current-period progress."""
    # Fetch active goals.
    goals_stmt = (
        select(Goal)
        .where(Goal.user_id == user_id, Goal.is_active.is_(True))
        .order_by(Goal.created_at.desc())
    )
    goals_result = await session.execute(goals_stmt)
    goals = list(goals_result.scalars().all())

    if not goals:
        return []

    today = date.today()

    # Build a map of goal_id -> period_start for the current period.
    period_map: dict[uuid.UUID, date] = {}
    for g in goals:
        period_map[g.id] = compute_period_start(g.frequency, today)

    # Batch-query completion counts: one query per distinct period_start value.
    # Group goals by their period_start to minimise queries.
    ps_to_goal_ids: dict[date, list[uuid.UUID]] = {}
    for gid, ps in period_map.items():
        ps_to_goal_ids.setdefault(ps, []).append(gid)

    counts: dict[uuid.UUID, int] = {}
    for ps, goal_ids in ps_to_goal_ids.items():
        stmt = (
            select(GoalCompletion.goal_id, func.count())
            .where(
                GoalCompletion.goal_id.in_(goal_ids),
                GoalCompletion.period_start == ps,
            )
            .group_by(GoalCompletion.goal_id)
        )
        rows = (await session.execute(stmt)).all()
        for gid, cnt in rows:
            counts[gid] = cnt

    # Assemble response.
    result: list[GoalWithProgress] = []
    for g in goals:
        completions = counts.get(g.id, 0)
        is_completed = completions >= g.target_count
        progress = GoalWithProgress.model_validate(
            g, from_attributes=True,
        )
        progress.period_completions = completions
        progress.is_completed = is_completed
        result.append(progress)

    return result


async def list_completions_for_period(
    session: AsyncSession,
    goal_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[GoalCompletion]:
    """Return all completions for a goal in the current period."""
    stmt = select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    result = await session.execute(stmt)
    goal = result.scalars().first()
    if goal is None:
        return []

    today = date.today()
    ps = compute_period_start(goal.frequency, today)

    stmt = (
        select(GoalCompletion)
        .where(GoalCompletion.goal_id == goal_id)
        .where(GoalCompletion.period_start == ps)
        .order_by(GoalCompletion.completed_at.desc())
    )
    rows = (await session.execute(stmt)).scalars().all()
    return list(rows)
