"""Review schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreateRequest(BaseModel):
    rating: float = Field(..., ge=1.0, le=5.0)
    content: str | None = Field(default=None, max_length=5000)


class ReviewResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    book_id: uuid.UUID
    rating: float
    content: str | None
    sentiment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class BookAnalysisResponse(BaseModel):
    book_id: uuid.UUID
    title: str
    average_rating: float
    total_reviews: int
    ai_summary: str | None
    review_consensus: str | None
