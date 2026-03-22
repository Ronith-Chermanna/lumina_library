"""Review routes — submit review, get analysis."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.middleware.auth import get_current_user_id
from app.dependencies import get_llm, get_review_service, get_session_factory
from app.domain.interfaces.llm import LLMInterface
from app.domain.schemas.review import (
    BookAnalysisResponse,
    ReviewCreateRequest,
    ReviewResponse,
)
from app.services.review_service import ReviewService
from app.tasks.background import analyze_book_reviews, classify_review_sentiment

router = APIRouter(prefix="/books", tags=["Reviews"])


@router.post(
    "/{book_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit review. Triggers async sentiment analysis.",
)
async def create_review(
    book_id: uuid.UUID,
    data: ReviewCreateRequest,
    background_tasks: BackgroundTasks,
    user_id: uuid.UUID = Depends(get_current_user_id),
    review_service: ReviewService = Depends(get_review_service),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
    llm: LLMInterface = Depends(get_llm),
) -> ReviewResponse:
    try:
        result = await review_service.create_review(user_id, book_id, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    # Trigger async sentiment + consensus tasks
    background_tasks.add_task(
        classify_review_sentiment, result.id, book_id, session_factory, llm
    )
    background_tasks.add_task(
        analyze_book_reviews, book_id, session_factory, llm
    )

    return result


@router.get(
    "/{book_id}/analysis",
    response_model=BookAnalysisResponse,
    summary="Get GenAI-aggregated summary of all reviews",
)
async def get_book_analysis(
    book_id: uuid.UUID,
    _user_id: uuid.UUID = Depends(get_current_user_id),
    review_service: ReviewService = Depends(get_review_service),
) -> BookAnalysisResponse:
    try:
        return await review_service.get_book_analysis(book_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
