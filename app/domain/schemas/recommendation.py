"""Recommendation schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class RecommendationItem(BaseModel):
    book_id: uuid.UUID
    title: str
    author: str
    genre: str | None
    score: float = Field(..., description="Relevance score 0.0 – 1.0")

    model_config = {"from_attributes": True}


class RecommendationResponse(BaseModel):
    user_id: uuid.UUID
    recommendations: list[RecommendationItem]
