"""SQLAlchemy implementation of PreferenceRepositoryInterface."""

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.preference_repository import PreferenceRepositoryInterface
from app.domain.models.preference import UserPreference


class PreferenceRepository(PreferenceRepositoryInterface):
    """Concrete preference repository backed by PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, preference: UserPreference) -> UserPreference:
        # Check for existing
        result = await self._session.execute(
            select(UserPreference).where(
                UserPreference.user_id == preference.user_id,
                UserPreference.tag == preference.tag,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.weight = preference.weight
            await self._session.flush()
            await self._session.refresh(existing)
            return existing

        self._session.add(preference)
        await self._session.flush()
        await self._session.refresh(preference)
        return preference

    async def get_user_preferences(
        self, user_id: uuid.UUID
    ) -> list[UserPreference]:
        result = await self._session.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        return list(result.scalars().all())

    async def delete_user_preference(
        self, user_id: uuid.UUID, tag: str
    ) -> None:
        await self._session.execute(
            delete(UserPreference).where(
                UserPreference.user_id == user_id,
                UserPreference.tag == tag,
            )
        )
        await self._session.flush()
