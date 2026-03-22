"""Recommendation routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.middleware.auth import get_current_user_id
from app.dependencies import get_recommendation_service
from app.domain.schemas.recommendation import RecommendationResponse
from app.services.recommendation_service import RecommendationService

router = APIRouter(tags=["Intelligence"])


@router.get(
    "/recommendations",
    response_model=RecommendationResponse,
    summary="Get ML-based suggestions for the current user",
)
async def get_recommendations(
    user_id: uuid.UUID = Depends(get_current_user_id),
    rec_service: RecommendationService = Depends(get_recommendation_service),
) -> RecommendationResponse:
    try:
        return await rec_service.recommend(user_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation engine error: {exc}",
        ) from exc
