"""Goal CRUD endpoints."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.goals import (
    CheckInCreate,
    CompletionRead,
    GoalCreate,
    GoalRead,
    GoalTrends,
    GoalUpdate,
    GoalWithProgress,
)
from app.schemas.user import User
from app.services.completions import (
    check_in,
    get_all_goals_trends,
    get_goal_trends,
    list_completions_for_period,
    list_goals_with_progress,
)
from app.services.goals import (
    create_goal,
    delete_goal,
    get_goal,
    list_goals,
    update_goal,
)
from app.services.strava_sync import sync_strava_to_goals

router = APIRouter(prefix="/goals", tags=["goals"])


@router.post("/sync-strava")
async def sync_strava(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Sync Strava activities to goals. Creates completions for matching activities."""
    result = await sync_strava_to_goals(session, current_user)
    return result


@router.get("/dashboard", response_model=list[GoalWithProgress])
async def dashboard(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[GoalWithProgress]:
    """Return all active goals with current-period progress for the dashboard."""
    return await list_goals_with_progress(session, current_user.id)


@router.post("/{goal_id}/check-in", response_model=CompletionRead, status_code=201)
async def goal_check_in(
    goal_id: uuid.UUID,
    data: CheckInCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CompletionRead:
    """Record a check-in for a goal."""
    try:
        completion = await check_in(session, goal_id, current_user.id, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return completion  # type: ignore[return-value]


@router.get("/{goal_id}/completions", response_model=list[CompletionRead])
async def list_goal_completions(
    goal_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[CompletionRead]:
    """List completions for a goal in the current period."""
    completions = await list_completions_for_period(
        session,
        goal_id,
        current_user.id,
    )
    return [CompletionRead.model_validate(c, from_attributes=True) for c in completions]


@router.get("/trends", response_model=list[GoalTrends])
async def get_trends(
    start_date: date = Query(..., description="Start of date range"),
    end_date: date = Query(..., description="End of date range"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[GoalTrends]:
    """Get trend data for all goals over a date range."""
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date",
        )
    return await get_all_goals_trends(
        session,
        current_user.id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/{goal_id}/trends", response_model=GoalTrends)
async def get_goal_trends_endpoint(
    goal_id: uuid.UUID,
    start_date: date = Query(..., description="Start of date range"),
    end_date: date = Query(..., description="End of date range"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> GoalTrends:
    """Get trend data for a single goal over a date range."""
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date",
        )
    trends = await get_goal_trends(
        session,
        goal_id,
        current_user.id,
        start_date=start_date,
        end_date=end_date,
    )
    if trends is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    return trends  # type: ignore[return-value]


@router.post("", response_model=GoalRead, status_code=201)
async def create(
    data: GoalCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> GoalRead:
    """Create a new goal for the authenticated user."""
    goal = await create_goal(session, current_user.id, data)
    return goal  # type: ignore[return-value]


@router.get("", response_model=list[GoalRead])
async def list_all(
    active_only: bool = True,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[GoalRead]:
    """List all goals for the authenticated user."""
    goals = await list_goals(session, current_user.id, active_only=active_only)
    return goals  # type: ignore[return-value]


@router.get("/{goal_id}", response_model=GoalRead)
async def read_one(
    goal_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> GoalRead:
    """Get a single goal by ID."""
    goal = await get_goal(session, goal_id, current_user.id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal  # type: ignore[return-value]


@router.patch("/{goal_id}", response_model=GoalRead)
async def update(
    goal_id: uuid.UUID,
    data: GoalUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> GoalRead:
    """Partially update a goal."""
    try:
        goal = await update_goal(session, goal_id, current_user.id, data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal  # type: ignore[return-value]


@router.delete("/{goal_id}", status_code=204)
async def remove(
    goal_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """Soft-delete a goal."""
    deleted = await delete_goal(session, goal_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Goal not found")
