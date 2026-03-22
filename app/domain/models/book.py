"""Book domain model."""

from __future__ import annotations

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Book(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A book in the library catalogue."""

    __tablename__ = "books"

    title: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    isbn: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    genre: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(32), default="English", nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Path / key to the stored file (local path or S3 key)
    file_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_content_type: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # GenAI-generated fields
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_consensus: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Aggregate rating (updated on review insert)
    average_rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    borrows = relationship("Borrow", back_populates="book", lazy="selectin")
    reviews = relationship("Review", back_populates="book", lazy="selectin")
