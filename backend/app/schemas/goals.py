"""Goal and GoalCompletion database schemas (SQLModel tables)."""

import uuid
from datetime import UTC, date, datetime
from enum import StrEnum

from sqlalchemy import Column, DateTime, Index
from sqlmodel import Field, SQLModel


class GoalType(StrEnum):
    PERIODIC = "periodic"
    ONE_TIME = "one_time"


class Frequency(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class ValueType(StrEnum):
    NONE = "none"
    NUMERIC = "numeric"
    TEXT = "text"


class Goal(SQLModel, table=True):
    __tablename__ = "goals"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        sa_column_kwargs={"nullable": False},
        foreign_key="users.id",
        index=True,
    )
    title: str = Field(max_length=256)
    description: str = Field(default="", max_length=1024)
    goal_type: GoalType = Field(default=GoalType.ONE_TIME)
    frequency: Frequency | None = Field(default=None)
    target_count: int = Field(default=1, ge=1)
    value_type: ValueType = Field(default=ValueType.NONE)
    value_unit: str | None = Field(default=None, max_length=32)
    start_date: date = Field(default_factory=date.today)
    end_date: date | None = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class GoalCompletion(SQLModel, table=True):
    __tablename__ = "goal_completions"
    __table_args__ = (
        Index("ix_goal_completions_goal_period", "goal_id", "period_start"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    goal_id: uuid.UUID = Field(
        sa_column_kwargs={"nullable": False},
        foreign_key="goals.id",
        index=True,
    )
    completed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    period_start: date = Field(nullable=False)
    value: float | None = Field(default=None)
    note: str | None = Field(default=None, max_length=512)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
