"""Authentication service — signup, login, token management."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import Settings
from app.domain.interfaces.user_repository import UserRepositoryInterface
from app.domain.models.user import User
from app.domain.schemas.auth import (
    LoginRequest,
    ProfileUpdateRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Handles user authentication flows."""

    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        settings: Settings,
    ) -> None:
        self._repo = user_repo
        self._settings = settings

    # Password helpers

    @staticmethod
    def hash_password(raw: str) -> str:
        return pwd_context.hash(raw)

    @staticmethod
    def verify_password(raw: str, hashed: str) -> bool:
        return pwd_context.verify(raw, hashed)

    # Token helpers

    def create_access_token(self, user_id: uuid.UUID) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=self._settings.jwt_access_token_expire_minutes
        )
        payload = {"sub": str(user_id), "exp": expire}
        return jwt.encode(
            payload,
            self._settings.jwt_secret_key,
            algorithm=self._settings.jwt_algorithm,
        )

    def decode_token(self, token: str) -> uuid.UUID | None:
        """Return the user_id embedded in the token, or None on failure."""
        try:
            payload = jwt.decode(
                token,
                self._settings.jwt_secret_key,
                algorithms=[self._settings.jwt_algorithm],
            )
            sub: str | None = payload.get("sub")
            if sub is None:
                return None
            return uuid.UUID(sub)
        except (JWTError, ValueError):
            return None

    # Public operations

    async def signup(self, data: SignupRequest) -> UserResponse:
        # Uniqueness checks
        if await self._repo.get_by_email(data.email):
            raise ValueError("Email already registered")
        if await self._repo.get_by_username(data.username):
            raise ValueError("Username already taken")

        user = User(
            email=data.email,
            username=data.username,
            hashed_password=self.hash_password(data.password),
            full_name=data.full_name,
        )
        user = await self._repo.create(user)
        return UserResponse.model_validate(user)

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self._repo.get_by_email(data.email)
        if not user or not self.verify_password(data.password, user.hashed_password):
            raise ValueError("Invalid email or password")
        if not user.is_active:
            raise ValueError("Account is deactivated")

        token = self.create_access_token(user.id)
        return TokenResponse(access_token=token)

    async def get_profile(self, user_id: uuid.UUID) -> UserResponse:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return UserResponse.model_validate(user)

    async def update_profile(
        self, user_id: uuid.UUID, data: ProfileUpdateRequest
    ) -> UserResponse:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        if data.full_name is not None:
            user.full_name = data.full_name
        if data.username is not None:
            existing = await self._repo.get_by_username(data.username)
            if existing and existing.id != user_id:
                raise ValueError("Username already taken")
            user.username = data.username
        user = await self._repo.update(user)
        return UserResponse.model_validate(user)
