"""LuminaLib — Application entry point.
Creates and configures the FastAPI application instance.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, books, recommendations, reviews
from app.config import get_settings
from app.domain.models.base import Base
from app.infrastructure.database import build_engine

# Import all models so Base.metadata knows about every table
from app.domain.models import user, book, borrow, review, preference  # noqa: F401

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup / shutdown lifecycle handler."""
    settings = get_settings()

    # Create tables on startup (for development)
    # but Alembic is preferred in production
    engine = build_engine(settings)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured")

    yield

    await engine.dispose()
    logger.info("Database engine disposed")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "LuminaLib — An Intelligent Library System with GenAI-powered "
            "summarisation, sentiment analysis, and ML-based recommendations."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Logging
    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    # Routes
    app.include_router(auth.router)
    app.include_router(books.router)
    app.include_router(reviews.router)
    app.include_router(recommendations.router)

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "version": settings.app_version}

    return app


# Module-level instance used by `uvicorn app.main:app`
app = create_app()
