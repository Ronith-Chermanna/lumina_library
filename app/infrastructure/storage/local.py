"""Local file-system storage adapter."""

from __future__ import annotations

import logging
from pathlib import Path

import aiofiles

from app.domain.interfaces.storage import StorageInterface

logger = logging.getLogger(__name__)


class LocalStorage(StorageInterface):
    """Stores book files on the local disk under a configurable root directory."""

    def __init__(self, root_path: Path) -> None:
        self._root = root_path
        self._root.mkdir(parents=True, exist_ok=True)
        logger.info("LocalStorage initialised at %s", self._root)

    def _resolve(self, key: str) -> Path:
        return self._root / key

    async def save(self, key: str, data: bytes, content_type: str) -> str:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "wb") as fh:
            await fh.write(data)
        logger.info("Saved %s (%s, %d bytes)", key, content_type, len(data))
        return key

    async def retrieve(self, key: str) -> bytes:
        path = self._resolve(key)
        async with aiofiles.open(path, "rb") as fh:
            return await fh.read()

    async def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.exists():
            path.unlink()
            logger.info("Deleted %s", key)

    async def exists(self, key: str) -> bool:
        return self._resolve(key).exists()
