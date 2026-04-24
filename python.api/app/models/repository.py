from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, AuditMixin
from app.models.repository_auth import RepositoryAuth, AuthType
from app.models.branch_tracking_rule import BranchTrackingRule


class Repository(Base, AuditMixin):
    __tablename__ = "Repositories"

    id: Mapped[uuid.UUID] = mapped_column("Id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column("Name", String(200), nullable=False)
    web_url: Mapped[str] = mapped_column("WebUrl", String(500), nullable=False)
    clone_url: Mapped[str | None] = mapped_column("CloneUrl", String(500), nullable=True)
    default_branch: Mapped[str] = mapped_column("DefaultBranch", String(100), default="main", nullable=False)
    provider_id: Mapped[uuid.UUID] = mapped_column(
        "ProviderId", UUID(as_uuid=True), ForeignKey("SourceProviders.Id"), nullable=False
    )
    provider_repo_id: Mapped[str | None] = mapped_column("ProviderRepoId", String(100), nullable=True)
    provider_workspace_id: Mapped[str | None] = mapped_column("ProviderWorkspaceId", String(100), nullable=True)
    last_seen_at_utc: Mapped[datetime | None] = mapped_column("LastSeenAtUtc", DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column("IsActive", Boolean, default=True, nullable=False)
    cloned_directory: Mapped[str | None] = mapped_column("ClonedDirectory", String(500), nullable=True)

    auth: Mapped[RepositoryAuth | None] = relationship(
        "RepositoryAuth", uselist=False, cascade="all, delete-orphan", lazy="joined"
    )
    branch_rules: Mapped[list[BranchTrackingRule]] = relationship(
        "BranchTrackingRule", cascade="all, delete-orphan", lazy="selectin"
    )

    @classmethod
    def create(
        cls,
        name: str,
        provider_id: uuid.UUID,
        web_url: str,
        provider_repo_id: str,
        clone_url: str,
        default_branch: str,
        auth_type: int,
        secret_ref: str,
        branch_rules: list[tuple[str, bool]],
    ) -> "Repository":
        repo_id = uuid.uuid4()
        repo = cls(
            id=repo_id,
            name=name,
            provider_id=provider_id,
            web_url=web_url,
            provider_repo_id=provider_repo_id,
            clone_url=clone_url,
            default_branch=default_branch,
            is_active=True,
        )
        repo.auth = RepositoryAuth.create(repo_id, auth_type, secret_ref)
        repo.branch_rules = [
            BranchTrackingRule.create(repo_id, pattern, scan_on_push)
            for pattern, scan_on_push in branch_rules
        ]
        return repo
