"""Book service — CRUD, file upload, borrow/return logic."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
import io
from PyPDF2 import PdfReader

from app.domain.interfaces.book_repository import BookRepositoryInterface
from app.domain.interfaces.storage import StorageInterface
from app.domain.models.book import Book
from app.domain.models.borrow import Borrow
from app.domain.schemas.book import (
    BookCreateRequest,
    BookListResponse,
    BookResponse,
    BookUpdateRequest,
    BorrowResponse,
)

logger = logging.getLogger(__name__)


class BookService:
    """Orchestrates book management operations."""

    def __init__(
        self,
        book_repo: BookRepositoryInterface,
        storage: StorageInterface,
    ) -> None:
        self._repo = book_repo
        self._storage = storage

    async def create_book(
            self,
            data: BookCreateRequest,
            file_bytes: bytes | None = None,
            file_content_type: str = "application/octet-stream",
    ) -> BookResponse:
        """Create a book entry and optionally store an uploaded file."""

        book = Book(
            title=data.title,
            author=data.author,
            isbn=data.isbn,
            genre=data.genre,
            description=data.description,
            language=data.language,
            page_count=data.page_count,
        )

        # Persist file if provided
        if file_bytes:
            ext = "pdf" if "pdf" in file_content_type else "txt"
            key = f"{uuid.uuid4()}.{ext}"
            await self._storage.save(key, file_bytes, file_content_type)
            book.file_key = key
            book.file_content_type = file_content_type

        try:
            book = await self._repo.create(book)
        except IntegrityError:
            raise ValueError("Book with this ISBN already exists")

        return BookResponse.model_validate(book)

    async def get_book(self, book_id: uuid.UUID) -> BookResponse:
        book = await self._repo.get_by_id(book_id)
        if not book:
            raise ValueError("Book not found")
        return BookResponse.model_validate(book)

    async def list_books(
        self, page: int = 1, page_size: int = 20
    ) -> BookListResponse:
        books, total = await self._repo.list_books(page=page, page_size=page_size)
        return BookListResponse(
            items=[BookResponse.model_validate(b) for b in books],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_book(
        self, book_id: uuid.UUID, data: BookUpdateRequest
    ) -> BookResponse:
        book = await self._repo.get_by_id(book_id)
        if not book:
            raise ValueError("Book not found")

        update_fields = data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(book, field, value)

        book = await self._repo.update(book)
        return BookResponse.model_validate(book)

    async def delete_book(self, book_id: uuid.UUID) -> None:
        book = await self._repo.get_by_id(book_id)
        if not book:
            raise ValueError("Book not found")

        # Delete associated file
        if book.file_key:
            try:
                await self._storage.delete(book.file_key)
            except Exception:
                logger.warning("Failed to delete file %s", book.file_key)

        await self._repo.delete(book_id)

    async def get_book_content(self, book_id: uuid.UUID) -> str:
        """Retrieve the text content of a book for LLM processing."""
        book = await self._repo.get_by_id(book_id)
        if not book or not book.file_key:
            return ""

        try:
            raw = await self._storage.retrieve(book.file_key)
            if book.file_content_type and "pdf" in book.file_content_type:
                # Extract text from PDF

                reader = PdfReader(io.BytesIO(raw))
                text_parts: list[str] = []
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                return "\n".join(text_parts)
            return raw.decode("utf-8", errors="replace")
        except Exception:
            logger.exception("Failed to read book content for %s", book_id)
            return ""

    # Borrow / Return

    async def borrow_book(
        self, user_id: uuid.UUID, book_id: uuid.UUID
    ) -> BorrowResponse:
        book = await self._repo.get_by_id(book_id)
        if not book:
            raise ValueError("Book not found")

        active = await self._repo.get_active_borrow(user_id, book_id)
        if active:
            raise ValueError("You already have this book borrowed")

        borrow = Borrow(user_id=user_id, book_id=book_id, status="borrowed")
        borrow = await self._repo.create_borrow(borrow)
        return BorrowResponse.model_validate(borrow)

    async def return_book(
        self, user_id: uuid.UUID, book_id: uuid.UUID
    ) -> BorrowResponse:
        active = await self._repo.get_active_borrow(user_id, book_id)
        if not active:
            raise ValueError("No active borrow found for this book")

        active.status = "returned"
        active.returned_at = datetime.now(timezone.utc)
        active = await self._repo.return_borrow(active)
        return BorrowResponse.model_validate(active)
