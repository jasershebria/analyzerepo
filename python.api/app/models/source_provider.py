from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, AuditMixin


class SourceProvider(Base, AuditMixin):
    __tablename__ = "SourceProviders"

    id: Mapped[uuid.UUID] = mapped_column("Id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column("Name", String(200), nullable=False)
    code: Mapped[str] = mapped_column("Code", String(50), nullable=False)
    api_base_url: Mapped[str] = mapped_column("ApiBaseUrl", String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column("IsActive", Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("ix_sourceproviders_code", "Code", unique=True),
    )

    @classmethod
    def create(cls, name: str, code: str, api_base_url: str) -> "SourceProvider":
        return cls(
            id=uuid.uuid4(),
            name=name,
            code=code.lower(),
            api_base_url=api_base_url,
            is_active=True,
        )
