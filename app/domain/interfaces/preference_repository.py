"""Preference repository interface."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from app.domain.models.preference import UserPreference


class PreferenceRepositoryInterface(ABC):
    """Data-access contract for UserPreference entities."""

    @abstractmethod
    async def upsert(self, preference: UserPreference) -> UserPreference:
        """Insert or update a user preference tag."""

    @abstractmethod
    async def get_user_preferences(
        self, user_id: uuid.UUID
    ) -> list[UserPreference]:
        """Get all preferences for a user."""

    @abstractmethod
    async def delete_user_preference(
        self, user_id: uuid.UUID, tag: str
    ) -> None:
        """Remove a specific tag preference for a user."""
