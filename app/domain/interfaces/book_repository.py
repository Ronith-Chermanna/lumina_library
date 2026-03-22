"""Book repository interface."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from app.domain.models.book import Book
from app.domain.models.borrow import Borrow


class BookRepositoryInterface(ABC):
    """Data-access contract for Book entities."""

    @abstractmethod
    async def create(self, book: Book) -> Book:
        """Persist a new book."""

    @abstractmethod
    async def get_by_id(self, book_id: uuid.UUID) -> Book | None:
        """Fetch a book by primary key."""

    @abstractmethod
    async def list_books(
        self, *, page: int = 1, page_size: int = 20
    ) -> tuple[list[Book], int]:
        """Return a page of books and total count."""

    @abstractmethod
    async def update(self, book: Book) -> Book:
        """Merge updated fields."""

    @abstractmethod
    async def delete(self, book_id: uuid.UUID) -> None:
        """Delete a book."""

    @abstractmethod
    async def get_all_books(self) -> list[Book]:
        """Return every book (used by recommendation engine)."""

    # Borrow operations

    @abstractmethod
    async def create_borrow(self, borrow: Borrow) -> Borrow:
        """Record a borrow event."""

    @abstractmethod
    async def get_active_borrow(
        self, user_id: uuid.UUID, book_id: uuid.UUID
    ) -> Borrow | None:
        """Find an active (un-returned) borrow for a user+book pair."""

    @abstractmethod
    async def return_borrow(self, borrow: Borrow) -> Borrow:
        """Mark a borrow as returned."""

    @abstractmethod
    async def get_user_borrows(self, user_id: uuid.UUID) -> list[Borrow]:
        """Get all borrows for a user."""

    @abstractmethod
    async def has_user_borrowed(
        self, user_id: uuid.UUID, book_id: uuid.UUID
    ) -> bool:
        """Check if a user has ever borrowed a specific book."""
