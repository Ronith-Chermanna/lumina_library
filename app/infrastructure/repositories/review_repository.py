"""SQLAlchemy implementation of ReviewRepositoryInterface."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.review_repository import ReviewRepositoryInterface
from app.domain.models.review import Review


class ReviewRepository(ReviewRepositoryInterface):
    """Concrete review repository backed by PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, review: Review) -> Review:
        self._session.add(review)
        await self._session.flush()
        await self._session.refresh(review)
        return review

    async def get_reviews_for_book(self, book_id: uuid.UUID) -> list[Review]:
        result = await self._session.execute(
            select(Review)
            .where(Review.book_id == book_id)
            .order_by(Review.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_user_review_for_book(
        self, user_id: uuid.UUID, book_id: uuid.UUID
    ) -> Review | None:
        result = await self._session.execute(
            select(Review).where(
                Review.user_id == user_id,
                Review.book_id == book_id,
            )
        )
        return result.scalar_one_or_none()
