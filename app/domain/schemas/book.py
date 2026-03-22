"""Book-related schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# Request Schemas
class BookCreateRequest(BaseModel):
    """Metadata sent alongside the uploaded file."""

    title: str = Field(..., min_length=1, max_length=512)
    author: str = Field(..., min_length=1, max_length=256)
    isbn: str | None = Field(default=None, max_length=20)
    genre: str | None = Field(default=None, max_length=128)
    description: str | None = None
    language: str = Field(default="English", max_length=32)
    page_count: int | None = Field(default=None, ge=1)


class BookUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=512)
    author: str | None = Field(default=None, max_length=256)
    isbn: str | None = Field(default=None, max_length=20)
    genre: str | None = Field(default=None, max_length=128)
    description: str | None = None
    language: str | None = Field(default=None, max_length=32)
    page_count: int | None = Field(default=None, ge=1)


# Response Schemas
class BookResponse(BaseModel):
    id: uuid.UUID
    title: str
    author: str
    isbn: str | None
    genre: str | None
    description: str | None
    language: str
    page_count: int | None
    ai_summary: str | None
    review_consensus: str | None
    average_rating: float
    total_reviews: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BookListResponse(BaseModel):
    items: list[BookResponse]
    total: int
    page: int
    page_size: int


class BorrowResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    book_id: uuid.UUID
    borrowed_at: datetime
    returned_at: datetime | None
    status: str

    model_config = {"from_attributes": True}
