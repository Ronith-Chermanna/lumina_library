"""JWT authentication dependency for FastAPI."""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import Settings, get_settings

bearer_scheme = HTTPBearer()


def _decode_token(token: str, settings: Settings) -> uuid.UUID | None:
    """Decode a JWT and return the embedded user_id, or None on failure."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        sub: str | None = payload.get("sub")
        if sub is None:
            return None
        return uuid.UUID(sub)
    except (JWTError, ValueError):
        return None


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> uuid.UUID:
    """Extract and validate the user ID from the JWT bearer token.

    This is a lightweight dependency — it does NOT hit the database.
    If you need the full User object, compose with a repo lookup.
    """
    user_id = _decode_token(credentials.credentials, settings)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
