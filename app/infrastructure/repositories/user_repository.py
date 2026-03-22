"""SQLAlchemy implementation of UserRepositoryInterface."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.user_repository import UserRepositoryInterface
from app.domain.models.user import User


class UserRepository(UserRepositoryInterface):
    """Concrete user repository backed by PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user: User) -> User:
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def update(self, user: User) -> User:
        merged = await self._session.merge(user)
        await self._session.flush()
        await self._session.refresh(merged)
        return merged

    async def delete(self, user_id: uuid.UUID) -> None:
        user = await self.get_by_id(user_id)
        if user:
            await self._session.delete(user)
            await self._session.flush()
