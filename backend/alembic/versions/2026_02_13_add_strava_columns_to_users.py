"""add strava columns to users

Revision ID: a1b2c3d4e5f6
Revises: 46a3ee2fb0d1
Create Date: 2026-02-13

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "46a3ee2fb0d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("strava_athlete_id", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("strava_access_token", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("strava_refresh_token", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("strava_expires_at", sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "strava_expires_at")
    op.drop_column("users", "strava_refresh_token")
    op.drop_column("users", "strava_access_token")
    op.drop_column("users", "strava_athlete_id")
