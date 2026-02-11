"""Application settings managed via environment variables.

Uses pydantic-settings so every value can be overridden with an env var or
a `.env` file placed in the project root.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────
    app_name: str = "Accountabilidash"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"  # development | staging | production

    # ── Server ───────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    allowed_origins: list[str] = ["http://localhost:3000"]

    # ── Database ─────────────────────────────────────────────────────────
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "accountabilidash"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url_sync(self) -> str:
        """Synchronous URL used by Alembic migrations."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── Auth / JWT ───────────────────────────────────────────────────────
    secret_key: str = "CHANGE-ME-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    allow_registration: bool = True  # Set False to disable public sign-up

    # ── Logging ──────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_json: bool = False  # Set True in production for structured JSON logs


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance (read once, reused everywhere)."""
    return Settings()
