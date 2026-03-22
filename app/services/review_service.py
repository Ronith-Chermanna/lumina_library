"""Review service — submit reviews, trigger sentiment analysis."""

from __future__ import annotations

import logging
import uuid

from app.domain.interfaces.book_repository import BookRepositoryInterface
from app.domain.interfaces.review_repository import ReviewRepositoryInterface
from app.domain.models.review import Review
from app.domain.schemas.review import BookAnalysisResponse, ReviewCreateRequest, ReviewResponse

logger = logging.getLogger(__name__)


class ReviewService:
    """Handles review submission and analysis retrieval."""

    def __init__(
        self,
        review_repo: ReviewRepositoryInterface,
        book_repo: BookRepositoryInterface,
    ) -> None:
        self._review_repo = review_repo
        self._book_repo = book_repo

    async def create_review(
        self,
        user_id: uuid.UUID,
        book_id: uuid.UUID,
        data: ReviewCreateRequest,
    ) -> ReviewResponse:
        """Submit a review — user must have borrowed the book."""
        # Verify book exists
        book = await self._book_repo.get_by_id(book_id)
        if not book:
            raise ValueError("Book not found")

        # Verify user has borrowed the book
        has_borrowed = await self._book_repo.has_user_borrowed(user_id, book_id)
        if not has_borrowed:
            raise ValueError("You must borrow this book before reviewing it")

        # Check for duplicate review
        existing = await self._review_repo.get_user_review_for_book(user_id, book_id)
        if existing:
            raise ValueError("You have already reviewed this book")

        review = Review(
            user_id=user_id,
            book_id=book_id,
            rating=data.rating,
            content=data.content,
        )
        review = await self._review_repo.create(review)

        # Update book aggregate rating
        all_reviews = await self._review_repo.get_reviews_for_book(book_id)
        total = len(all_reviews)
        avg = sum(r.rating for r in all_reviews) / total if total else 0.0
        book.average_rating = round(avg, 2)
        book.total_reviews = total
        await self._book_repo.update(book)

        return ReviewResponse.model_validate(review)

    async def get_book_analysis(
        self, book_id: uuid.UUID
    ) -> BookAnalysisResponse:
        """Return the GenAI-aggregated summary of all reviews for a book."""
        book = await self._book_repo.get_by_id(book_id)
        if not book:
            raise ValueError("Book not found")

        return BookAnalysisResponse(
            book_id=book.id,
            title=book.title,
            average_rating=book.average_rating,
            total_reviews=book.total_reviews,
            ai_summary=book.ai_summary,
            review_consensus=book.review_consensus,
        )
