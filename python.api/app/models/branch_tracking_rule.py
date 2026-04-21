from __future__ import annotations

import fnmatch
import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, AuditMixin


class BranchTrackingRule(Base, AuditMixin):
    __tablename__ = "BranchTrackingRules"

    id: Mapped[uuid.UUID] = mapped_column("Id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        "RepositoryId", UUID(as_uuid=True), ForeignKey("Repositories.Id", ondelete="CASCADE"), nullable=False
    )
    pattern: Mapped[str] = mapped_column("Pattern", String(200), nullable=False)
    is_enabled: Mapped[bool] = mapped_column("IsEnabled", Boolean, default=True, nullable=False)
    scan_on_push: Mapped[bool] = mapped_column("ScanOnPush", Boolean, default=True, nullable=False)

    __table_args__ = (
        Index(
            "ix_branchrules_repo_pattern",
            "RepositoryId",
            "Pattern",
            unique=True,
        ),
    )

    @classmethod
    def create(cls, repository_id: uuid.UUID, pattern: str, scan_on_push: bool = True) -> "BranchTrackingRule":
        return cls(
            id=uuid.uuid4(),
            repository_id=repository_id,
            pattern=pattern.strip(),
            is_enabled=True,
            scan_on_push=scan_on_push,
        )

    def matches_branch(self, branch_name: str) -> bool:
        if self.pattern == branch_name:
            return True
        return fnmatch.fnmatch(branch_name, self.pattern)
