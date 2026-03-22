"""Review repository interface."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from app.domain.models.review import Review


class ReviewRepositoryInterface(ABC):
    """Data-access contract for Review entities."""

    @abstractmethod
    async def create(self, review: Review) -> Review:
        """Persist a new review."""

    @abstractmethod
    async def get_reviews_for_book(self, book_id: uuid.UUID) -> list[Review]:
        """Return all reviews for a given book."""

    @abstractmethod
    async def get_user_review_for_book(
        self, user_id: uuid.UUID, book_id: uuid.UUID
    ) -> Review | None:
        """Check if a user already reviewed a book."""
