"""FastAPI application factory and lifespan management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import close_db, init_db
from app.core.logging import setup_logging
from app.core.settings import get_settings
from app.middleware.request_logging import RequestLoggingMiddleware
from app.routers import auth, goals, health, users

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Startup / shutdown lifecycle hook."""
    settings = get_settings()

    # ── Startup ──────────────────────────────────────────────────────────
    setup_logging(settings)
    init_db(settings)
    logger.info(
        "app_startup",
        app=settings.app_name,
        environment=settings.environment,
    )

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    await close_db()
    logger.info("app_shutdown")


def create_app() -> FastAPI:
    """Application factory — builds and returns the configured FastAPI app."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── Middleware (order matters — outermost first) ──────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    # ── Routers ──────────────────────────────────────────────────────────
    api_prefix = "/api/v1"
    app.include_router(health.router, prefix=api_prefix)
    app.include_router(auth.router, prefix=api_prefix)
    app.include_router(users.router, prefix=api_prefix)
    app.include_router(goals.router, prefix=api_prefix)

    return app


app = create_app()
