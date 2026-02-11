"""Goals service — business logic for creating and listing goals."""

import uuid
from datetime import UTC, date, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.goals import GoalCreate, GoalUpdate, _validate_goal_fields
from app.schemas.goals import Goal

logger = structlog.get_logger()


async def create_goal(
    session: AsyncSession,
    user_id: uuid.UUID,
    data: GoalCreate,
) -> Goal:
    """Create a new goal for the given user."""
    goal = Goal(
        user_id=user_id,
        title=data.title,
        description=data.description,
        goal_type=data.goal_type,
        frequency=data.frequency,
        target_count=data.target_count,
        value_type=data.value_type,
        value_unit=data.value_unit,
        start_date=data.start_date or date.today(),
        end_date=data.end_date,
    )
    session.add(goal)
    await session.flush()
    await session.refresh(goal)
    logger.info("goal_created", goal_id=str(goal.id), user_id=str(user_id))
    return goal


async def list_goals(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    active_only: bool = True,
) -> list[Goal]:
    """Return all goals for a user, optionally filtered to active only."""
    stmt = select(Goal).where(Goal.user_id == user_id)
    if active_only:
        stmt = stmt.where(Goal.is_active.is_(True))
    stmt = stmt.order_by(Goal.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_goal(
    session: AsyncSession,
    goal_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Goal | None:
    """Return a single goal by ID, scoped to the owning user."""
    stmt = select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def update_goal(
    session: AsyncSession,
    goal_id: uuid.UUID,
    user_id: uuid.UUID,
    data: GoalUpdate,
) -> Goal | None:
    """Apply a partial update to an existing goal.

    Returns the updated goal, or None if not found.
    """
    goal = await get_goal(session, goal_id, user_id)
    if goal is None:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(goal, field, value)

    # Re-validate the resulting state after merging updates.
    _validate_goal_fields(
        goal.goal_type, goal.frequency, goal.target_count,
        goal.value_type, goal.value_unit,
    )

    goal.updated_at = datetime.now(UTC)
    session.add(goal)
    await session.flush()
    await session.refresh(goal)
    logger.info("goal_updated", goal_id=str(goal_id), user_id=str(user_id))
    return goal


async def delete_goal(
    session: AsyncSession,
    goal_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """Soft-delete a goal by setting is_active to False.

    Returns True if the goal was found and deactivated, False otherwise.
    """
    goal = await get_goal(session, goal_id, user_id)
    if goal is None:
        return False
    goal.is_active = False
    goal.updated_at = datetime.now(UTC)
    session.add(goal)
    await session.flush()
    logger.info("goal_deleted", goal_id=str(goal_id), user_id=str(user_id))
    return True
