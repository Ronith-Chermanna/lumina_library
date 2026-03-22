"""Storage interface — abstracts file persistence.

Implementations can target the local file-system, AWS S3, MinIO, or any
object store without changing calling code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class StorageInterface(ABC):
    """Contract that every storage backend must fulfil."""

    @abstractmethod
    async def save(self, key: str, data: bytes, content_type: str) -> str:
        """Persist *data* under *key* and return the canonical key/path."""
        ...

    @abstractmethod
    async def retrieve(self, key: str) -> bytes:
        """Return the raw bytes for the given key."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove the object at *key*."""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check whether an object exists at *key*."""
        ...
