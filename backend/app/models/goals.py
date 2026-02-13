"""Pydantic models for goal-related request / response bodies."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, model_validator

from app.schemas.goals import Frequency, GoalType, ValueType

# ── Request models ───────────────────────────────────────────────────────────


class GoalCreate(BaseModel):
    title: str
    description: str = ""
    goal_type: GoalType = GoalType.ONE_TIME
    frequency: Frequency | None = None
    target_count: int = 1
    value_type: ValueType = ValueType.NONE
    value_unit: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    strava_activity_types: list[str] | None = None

    @model_validator(mode="after")
    def validate_goal_consistency(self) -> "GoalCreate":
        _validate_goal_fields(
            self.goal_type,
            self.frequency,
            self.target_count,
            self.value_type,
            self.value_unit,
        )
        return self


class GoalUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    goal_type: GoalType | None = None
    frequency: Frequency | None = None
    target_count: int | None = None
    value_type: ValueType | None = None
    value_unit: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool | None = None
    strava_activity_types: list[str] | None = None

    # Sentinel to distinguish "field not sent" from "field explicitly set to null".
    _unset = object()

    model_config = {"extra": "forbid"}


# ── Response models ──────────────────────────────────────────────────────────


class CheckInCreate(BaseModel):
    value: float | None = None
    note: str | None = None


class GoalRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: str
    goal_type: GoalType
    frequency: Frequency | None
    target_count: int
    value_type: ValueType
    value_unit: str | None
    start_date: date
    end_date: date | None
    is_active: bool
    strava_activity_types: list[str] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompletionRead(BaseModel):
    id: uuid.UUID
    goal_id: uuid.UUID
    completed_at: datetime
    period_start: date
    value: float | None
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class GoalWithProgress(GoalRead):
    """Goal enriched with current-period progress info."""

    period_completions: int = 0
    is_completed: bool = False


class PeriodTrendPoint(BaseModel):
    """Single period's completion stats for trend charts."""

    period_start: date
    completion_count: int
    target_count: int
    is_completed: bool
    sum_value: float | None = None
    avg_value: float | None = None


class GoalTrends(BaseModel):
    """Trend data for a single goal over a date range."""

    goal: GoalRead
    periods: list[PeriodTrendPoint]


class AllGoalsTrends(BaseModel):
    """Trend data for all goals over a date range."""

    goals: list[GoalTrends]


# ── Helpers ──────────────────────────────────────────────────────────────────


def _validate_goal_fields(
    goal_type: GoalType,
    frequency: Frequency | None,
    target_count: int,
    value_type: ValueType,
    value_unit: str | None,
) -> None:
    """Shared validation for create and update payloads."""
    if goal_type == GoalType.PERIODIC and frequency is None:
        msg = "frequency is required for periodic goals"
        raise ValueError(msg)
    if goal_type == GoalType.ONE_TIME:
        if frequency is not None:
            msg = "frequency must be null for one-time goals"
            raise ValueError(msg)
        if target_count != 1:
            msg = "target_count must be 1 for one-time goals"
            raise ValueError(msg)
    if value_type == ValueType.NONE and value_unit is not None:
        msg = "value_unit should be null when value_type is 'none'"
        raise ValueError(msg)
