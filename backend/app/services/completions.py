"""Completions service — check-in logic and progress queries."""

import uuid
from datetime import UTC, date, datetime, timedelta

import structlog
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.goals import (
    CheckInCreate,
    GoalTrends,
    GoalWithProgress,
    PeriodTrendPoint,
)
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
            g,
            from_attributes=True,
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
    result = await session.execute(stmt)
    return list(result.scalars().all())


def iter_periods_in_range(
    frequency: Frequency | None,
    start_date: date,
    end_date: date,
) -> list[date]:
    """Yield all period_start dates within [start_date, end_date]."""
    if frequency is None or frequency == Frequency.DAILY:
        days = (end_date - start_date).days + 1
        return [start_date + timedelta(days=i) for i in range(days)]
    if frequency == Frequency.WEEKLY:
        first = compute_period_start(Frequency.WEEKLY, start_date)
        periods: list[date] = []
        cur = first
        while cur <= end_date:
            periods.append(cur)
            cur += timedelta(days=7)
        return periods
    if frequency == Frequency.MONTHLY:
        periods = []
        cur = compute_period_start(Frequency.MONTHLY, start_date)
        while cur <= end_date:
            periods.append(cur)
            if cur.month == 12:
                cur = cur.replace(year=cur.year + 1, month=1)
            else:
                cur = cur.replace(month=cur.month + 1)
        return periods
    if frequency == Frequency.YEARLY:
        periods = []
        cur = compute_period_start(Frequency.YEARLY, start_date)
        while cur <= end_date:
            periods.append(cur)
            cur = cur.replace(year=cur.year + 1)
        return periods
    return [start_date]


async def get_goal_trends(
    session: AsyncSession,
    goal_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    start_date: date,
    end_date: date,
) -> GoalTrends | None:
    """Return trend data for a single goal over a date range."""
    goal = await _get_goal_if_owned(session, goal_id, user_id)
    if goal is None:
        return None

    return await _build_goal_trends(session, goal, start_date, end_date)


async def get_all_goals_trends(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    start_date: date,
    end_date: date,
) -> list[GoalTrends]:
    """Return trend data for all active goals over a date range."""
    stmt = (
        select(Goal)
        .where(Goal.user_id == user_id, Goal.is_active.is_(True))
        .order_by(Goal.created_at.desc())
    )
    result = await session.execute(stmt)
    goals = list(result.scalars().all())
    if not goals:
        return []

    return [await _build_goal_trends(session, g, start_date, end_date) for g in goals]


async def _get_goal_if_owned(
    session: AsyncSession,
    goal_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Goal | None:
    stmt = select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def _build_goal_trends(
    session: AsyncSession,
    goal: Goal,
    start_date: date,
    end_date: date,
) -> GoalTrends:
    """Build trend data for one goal."""
    from app.models.goals import GoalRead

    periods = iter_periods_in_range(goal.frequency, start_date, end_date)
    if not periods:
        return GoalTrends(
            goal=GoalRead.model_validate(goal, from_attributes=True),
            periods=[],
        )

    stmt = (
        select(
            GoalCompletion.period_start,
            func.count().label("cnt"),
            func.sum(GoalCompletion.value).label("sum_val"),
            func.avg(GoalCompletion.value).label("avg_val"),
        )
        .where(
            GoalCompletion.goal_id == goal.id,
            GoalCompletion.period_start >= start_date,
            GoalCompletion.period_start <= end_date,
        )
        .group_by(GoalCompletion.period_start)
    )
    rows = (await session.execute(stmt)).all()
    by_period: dict[date, tuple[int, float | None, float | None]] = {}
    for ps, cnt, sum_val, avg_val in rows:
        by_period[ps] = (cnt, sum_val, avg_val)

    points: list[PeriodTrendPoint] = []
    for ps in periods:
        cnt, sum_val, avg_val = by_period.get(ps, (0, None, None))
        is_completed = cnt >= goal.target_count
        points.append(
            PeriodTrendPoint(
                period_start=ps,
                completion_count=cnt,
                target_count=goal.target_count,
                is_completed=is_completed,
                sum_value=float(sum_val) if sum_val is not None else None,
                avg_value=float(avg_val) if avg_val is not None else None,
            )
        )

    return GoalTrends(
        goal=GoalRead.model_validate(goal, from_attributes=True),
        periods=points,
    )
