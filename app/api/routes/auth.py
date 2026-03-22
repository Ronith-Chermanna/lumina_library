"""Authentication routes — signup, login, profile, signout."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.middleware.auth import get_current_user_id
from app.dependencies import get_auth_service
from app.domain.schemas.auth import (
    LoginRequest,
    MessageResponse,
    ProfileUpdateRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(path="/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED,
    summary="Register a new user")
async def signup(data: SignupRequest, auth_service: AuthService = Depends(get_auth_service)) -> UserResponse:
    try:
        return await auth_service.signup(data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post(path="/login", response_model=TokenResponse, summary="Authenticate and receive JWT access token")
async def login(data: LoginRequest, auth_service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    try:
        return await auth_service.login(data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc


@router.get(path="/profile", response_model=UserResponse, summary="Get current user profile")
async def get_profile(user_id: uuid.UUID = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    try:
        return await auth_service.get_profile(user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.put(path="/profile", response_model=UserResponse, summary="Update current user profile")
async def update_profile(data: ProfileUpdateRequest, user_id: uuid.UUID = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service)) -> UserResponse:
    try:
        return await auth_service.update_profile(user_id, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc


@router.post(path="/signout", response_model=MessageResponse, summary="Sign out (client should discard the token)")
async def signout(_user_id: uuid.UUID = Depends(get_current_user_id)) -> MessageResponse:
    return MessageResponse(message="Successfully signed out")
