"""User repository interface."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from app.domain.models.user import User


class UserRepositoryInterface(ABC):
    """Data-access contract for User entities."""

    @abstractmethod
    async def create(self, user: User) -> User:
        """Persist a new user."""

    @abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Fetch a user by primary key."""

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by email address."""

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        """Fetch a user by username."""

    @abstractmethod
    async def update(self, user: User) -> User:
        """Merge updated fields back to the database."""

    @abstractmethod
    async def delete(self, user_id: uuid.UUID) -> None:
        """Remove a user."""
