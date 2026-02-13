"""add strava fields to goals and completions

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-13

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "goals",
        sa.Column("strava_activity_types", sa.JSON(), nullable=True),
    )
    op.add_column(
        "goal_completions",
        sa.Column("strava_activity_id", sa.BigInteger(), nullable=True),
    )
    op.create_index(
        op.f("ix_goal_completions_strava_activity_id"),
        "goal_completions",
        ["strava_activity_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_goal_completions_strava_activity_id"),
        table_name="goal_completions",
    )
    op.drop_column("goal_completions", "strava_activity_id")
    op.drop_column("goals", "strava_activity_types")
