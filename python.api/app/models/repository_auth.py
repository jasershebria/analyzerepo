from __future__ import annotations

import uuid
from datetime import datetime
from enum import IntEnum

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, AuditMixin


class AuthType(IntEnum):
    PersonalAccessToken = 1
    OAuth = 2
    AppInstallation = 3


class RepositoryAuth(Base, AuditMixin):
    __tablename__ = "RepositoryAuths"

    id: Mapped[uuid.UUID] = mapped_column("Id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        "RepositoryId", UUID(as_uuid=True), ForeignKey("Repositories.Id", ondelete="CASCADE"), nullable=False
    )
    auth_type: Mapped[int] = mapped_column("AuthType", Integer, nullable=False)
    secret_ref: Mapped[str] = mapped_column("SecretRef", String(500), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column("ExpiresAt", DateTime(timezone=True), nullable=True)

    @classmethod
    def create(
        cls,
        repository_id: uuid.UUID,
        auth_type: int,
        secret_ref: str,
        expires_at: datetime | None = None,
    ) -> "RepositoryAuth":
        return cls(
            id=uuid.uuid4(),
            repository_id=repository_id,
            auth_type=auth_type,
            secret_ref=secret_ref,
            expires_at=expires_at,
        )
