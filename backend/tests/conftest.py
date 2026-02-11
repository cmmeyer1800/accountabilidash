"""Shared test fixtures.

Uses an async in-memory SQLite database so tests run without PostgreSQL.
"""

import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.database import get_session
from app.core.security import create_access_token, hash_password
from app.main import create_app
from app.schemas.user import User

# ── Async engine for tests (in-memory SQLite) ───────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite://"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)

TestSessionFactory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def event_loop():
    """Use a single event loop for all tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test, drop them after."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    """Yield a test database session."""
    async with TestSessionFactory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """Yield an httpx AsyncClient wired to the FastAPI app with DB override."""
    app = create_app()

    async def _override_get_session() -> AsyncGenerator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = _override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(session: AsyncSession) -> User:
    """Insert and return a test user with known credentials."""
    user = User(
        email="testuser@example.com",
        hashed_password=hash_password("testpassword"),
        full_name="Test User",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def inactive_user(session: AsyncSession) -> User:
    """Insert and return a deactivated test user."""
    user = User(
        email="inactive@example.com",
        hashed_password=hash_password("testpassword"),
        full_name="Inactive User",
        is_active=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def admin_user(session: AsyncSession) -> User:
    """Insert and return a superuser with known credentials."""
    user = User(
        email="admin@example.com",
        hashed_password=hash_password("adminpassword"),
        full_name="Admin User",
        is_superuser=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """Return Authorization headers with a valid JWT for test_user."""
    token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user: User) -> dict[str, str]:
    """Return Authorization headers with a valid JWT for admin_user."""
    token = create_access_token(subject=str(admin_user.id))
    return {"Authorization": f"Bearer {token}"}
