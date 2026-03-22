"""Background task functions for async LLM processing.

These are invoked via FastAPI's ``BackgroundTasks`` so they run outside the
request/response cycle.  For heavier production workloads the same functions
can be wrapped in Celery tasks.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.responses import Content

from app.domain.interfaces.llm import LLMInterface
from app.infrastructure.repositories.book_repository import BookRepository
from app.infrastructure.repositories.review_repository import ReviewRepository
from app.services.book_service import BookService
from app.domain.interfaces.storage import StorageInterface

logger = logging.getLogger(__name__)


async def generate_book_summary(
    book_id: uuid.UUID,
    session_factory: async_sessionmaker[AsyncSession],
    llm: LLMInterface,
    storage: StorageInterface,
) -> None:
    """Read book content and generate an AI summary (runs in background)."""
    logger.info("Generating AI summary for book %s", book_id)
    try:
        async with session_factory() as session:
            book_repo = BookRepository(session)
            book_svc = BookService(book_repo, storage)
            book = await book_repo.get_by_id(book_id)
            if not book:
                logger.warning("Book %s not found — skipping summary", book_id)
                return

            content = await book_svc.get_book_content(book_id)
            if not content:
                logger.warning("No content for book %s — skipping summary", book_id)
                return
            logger.info(f"Content!!! {Content}")
            summary = await llm.summarize_book(content)
            logger.info(f"Summary!!! {summary}")
            book.ai_summary = summary
            await book_repo.update(book)
            await session.commit()
            logger.info("Summary generated for book %s", book_id)
    except Exception:
        logger.exception("Failed to generate summary for book %s", book_id)


async def analyze_book_reviews(
    book_id: uuid.UUID,
    session_factory: async_sessionmaker[AsyncSession],
    llm: LLMInterface,
) -> None:
    """Analyse all reviews for a book and update the rolling consensus."""
    logger.info("Analysing reviews for book %s", book_id)
    try:
        async with session_factory() as session:
            book_repo = BookRepository(session)
            review_repo = ReviewRepository(session)

            book = await book_repo.get_by_id(book_id)
            if not book:
                return

            reviews = await review_repo.get_reviews_for_book(book_id)
            if not reviews:
                return

            review_texts = [r.content for r in reviews if r.content]
            if not review_texts:
                return

            consensus = await llm.analyze_reviews(review_texts)
            book.review_consensus = consensus
            await book_repo.update(book)
            await session.commit()
            logger.info("Review consensus updated for book %s", book_id)
    except Exception:
        logger.exception("Failed to analyse reviews for book %s", book_id)


async def classify_review_sentiment(
    review_id: uuid.UUID,
    book_id: uuid.UUID,
    session_factory: async_sessionmaker[AsyncSession],
    llm: LLMInterface,
) -> None:
    """Classify the sentiment of a single review and persist the label."""
    logger.info("Classifying sentiment for review %s", review_id)
    try:
        async with session_factory() as session:
            from sqlalchemy import select
            from app.domain.models.review import Review

            result = await session.execute(
                select(Review).where(Review.id == review_id)
            )
            review = result.scalar_one_or_none()
            if not review or not review.content:
                return

            sentiment = await llm.classify_sentiment(review.content)
            review.sentiment = sentiment
            await session.merge(review)
            await session.commit()
            logger.info("Sentiment for review %s: %s", review_id, sentiment)
    except Exception:
        logger.exception("Failed to classify sentiment for review %s", review_id)
