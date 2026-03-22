"""User preference domain model.

Design Decision
---------------
User preferences are modelled as a **tag-weight** system.  Each row represents a
user's affinity toward a specific genre / tag with a numeric weight.  This gives
us:
  - Explicit control: users can set preferred genres.
  - Implicit enrichment: the system can boost weights when a user borrows or
    positively reviews a book of that genre.

The recommendation engine converts these rows into a user-profile vector that is
compared against book feature vectors (Content-Based Filtering).
"""

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserPreference(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A weighted tag/genre preference for a user."""

    __tablename__ = "user_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "tag", name="uq_user_tag"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tag: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # Relationships
    user = relationship("User", back_populates="preferences")
