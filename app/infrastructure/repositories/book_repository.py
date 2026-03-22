"""SQLAlchemy implementation of BookRepositoryInterface."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.book_repository import BookRepositoryInterface
from app.domain.models.book import Book
from app.domain.models.borrow import Borrow


class BookRepository(BookRepositoryInterface):
    """Concrete book repository backed by PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, book: Book) -> Book:
        self._session.add(book)
        await self._session.flush()
        await self._session.refresh(book)
        return book

    async def get_by_id(self, book_id: uuid.UUID) -> Book | None:
        return await self._session.get(Book, book_id)

    async def list_books(
        self, *, page: int = 1, page_size: int = 20
    ) -> tuple[list[Book], int]:
        # Total count
        count_result = await self._session.execute(
            select(func.count()).select_from(Book)
        )
        total = count_result.scalar_one()

        # Paginated results
        offset = (page - 1) * page_size
        result = await self._session.execute(
            select(Book).order_by(Book.created_at.desc()).offset(offset).limit(page_size)
        )
        books = list(result.scalars().all())
        return books, total

    async def update(self, book: Book) -> Book:
        merged = await self._session.merge(book)
        await self._session.flush()
        await self._session.refresh(merged)
        return merged

    async def delete(self, book_id: uuid.UUID) -> None:
        book = await self.get_by_id(book_id)
        if book:
            await self._session.delete(book)
            await self._session.flush()

    async def get_all_books(self) -> list[Book]:
        result = await self._session.execute(select(Book))
        return list(result.scalars().all())

    # ── Borrow operations ──────────────────────────────────

    async def create_borrow(self, borrow: Borrow) -> Borrow:
        self._session.add(borrow)
        await self._session.flush()
        await self._session.refresh(borrow)
        return borrow

    async def get_active_borrow(
        self, user_id: uuid.UUID, book_id: uuid.UUID
    ) -> Borrow | None:
        result = await self._session.execute(
            select(Borrow).where(
                Borrow.user_id == user_id,
                Borrow.book_id == book_id,
                Borrow.status == "borrowed",
            )
        )
        return result.scalar_one_or_none()

    async def return_borrow(self, borrow: Borrow) -> Borrow:
        merged = await self._session.merge(borrow)
        await self._session.flush()
        await self._session.refresh(merged)
        return merged

    async def get_user_borrows(self, user_id: uuid.UUID) -> list[Borrow]:
        result = await self._session.execute(
            select(Borrow).where(Borrow.user_id == user_id)
        )
        return list(result.scalars().all())

    async def has_user_borrowed(
        self, user_id: uuid.UUID, book_id: uuid.UUID
    ) -> bool:
        result = await self._session.execute(
            select(func.count()).select_from(Borrow).where(
                Borrow.user_id == user_id,
                Borrow.book_id == book_id,
            )
        )
        return (result.scalar_one() or 0) > 0
