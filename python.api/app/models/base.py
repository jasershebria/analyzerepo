from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AuditMixin:
    created_at: Mapped[datetime] = mapped_column(
        "CreatedAt", DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime | None] = mapped_column("UpdatedAt", DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column("CreatedBy", String(200), nullable=True)
    updated_by: Mapped[str | None] = mapped_column("UpdatedBy", String(200), nullable=True)
    is_deleted: Mapped[bool] = mapped_column("IsDeleted", Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column("DeletedAt", DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[str | None] = mapped_column("DeletedBy", String(200), nullable=True)

    def soft_delete(self, deleted_by: str | None = None) -> None:
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = deleted_by

    def touch_updated(self, updated_by: str | None = None) -> None:
        self.updated_at = datetime.now(timezone.utc)
        self.updated_by = updated_by
