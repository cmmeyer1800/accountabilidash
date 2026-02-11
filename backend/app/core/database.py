"""Async database engine and session management.

Usage in route handlers / services:

    async def my_route(session: AsyncSession = Depends(get_session)):
        ...
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.settings import Settings

# Module-level engine & session factory — initialised at startup via `init_db`.
_engine = None
_async_session_factory = None


def init_db(settings: Settings) -> None:
    """Create the async engine and session factory.  Call once at startup."""
    global _engine, _async_session_factory

    _engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    _async_session_factory = sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_session() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency that yields an async database session."""
    if _async_session_factory is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")

    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_db() -> None:
    """Dispose of the engine's connection pool.  Call at shutdown."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


async def create_all_tables() -> None:
    """Create tables from SQLModel metadata (dev convenience — prefer Alembic)."""
    if _engine is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")

    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
