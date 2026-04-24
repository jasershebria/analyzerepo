from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.repository import Repository
from app.models.repository_auth import RepositoryAuth
from app.models.branch_tracking_rule import BranchTrackingRule
from app.models.source_provider import SourceProvider
from app.schemas.common import PagedResult
from app.schemas.repository import (
    CreateRepositoryRequest,
    CreateRepositoryResponse,
    GetAllRepositoriesQuery,
    GetRepositoryResponse,
    RepositoryDto,
    UpdateRepositoryRequest,
    UpdateRepositoryResponse,
    TestConnectionRequest,
    TestConnectionResponse,
    BranchRuleDto,
    GitBranchDto,
)
from app.services.provider_clients.base import ProviderAuth
from app.services.provider_clients.factory import RepoProviderClientFactory


class RepositoryService:
    def __init__(self, db: AsyncSession, client_factory: RepoProviderClientFactory) -> None:
        self._db = db
        self._factory = client_factory

    # ── GET ALL ──────────────────────────────────────────────────────────────

    async def get_all(self, query: GetAllRepositoriesQuery) -> PagedResult[RepositoryDto]:
        stmt = select(Repository)

        if not query.include_deleted:
            stmt = stmt.where(Repository.is_deleted.is_(False))

        if query.search_term:
            term = query.search_term.lower()
            stmt = stmt.where(
                Repository.name.ilike(f"%{term}%") | Repository.web_url.ilike(f"%{term}%")
            )

        if query.provider_id:
            stmt = stmt.where(Repository.provider_id == query.provider_id)

        if query.is_active is not None:
            stmt = stmt.where(Repository.is_active == query.is_active)

        stmt = stmt.order_by(Repository.created_at.desc())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count: int = (await self._db.execute(count_stmt)).scalar_one()

        skip = query.skip_count if query.skip_count > 0 else max(0, (query.page_index - 1) * query.max_result_count)
        rows = (await self._db.execute(stmt.offset(skip).limit(query.max_result_count))).scalars().all()

        return PagedResult(
            total_count=total_count,
            items=[RepositoryDto(id=r.id, name=r.name, web_url=r.web_url, created_at=r.created_at) for r in rows],
        )

    # ── GET ONE ──────────────────────────────────────────────────────────────

    async def get_by_id(self, repo_id: uuid.UUID) -> GetRepositoryResponse | None:
        stmt = (
            select(Repository)
            .where(Repository.id == repo_id, Repository.is_deleted.is_(False))
            .options(selectinload(Repository.branch_rules), joinedload(Repository.auth))
        )
        repo = (await self._db.execute(stmt)).scalar_one_or_none()
        if repo is None:
            return None
        return self._to_full_dto(repo)

    # ── CREATE ───────────────────────────────────────────────────────────────

    async def create(self, req: CreateRepositoryRequest) -> CreateRepositoryResponse:
        provider = (
            await self._db.execute(
                select(SourceProvider).where(
                    SourceProvider.id == req.provider_id, SourceProvider.is_active.is_(True)
                )
            )
        ).scalar_one_or_none()

        if provider is None:
            raise ValueError(f"Provider '{req.provider_id}' not found or is inactive.")

        already_exists = (
            await self._db.execute(
                select(Repository).where(
                    Repository.provider_id == req.provider_id,
                    Repository.provider_repo_id == req.provider_repo_id,
                )
            )
        ).scalar_one_or_none()

        if already_exists:
            raise ValueError(f"Repository '{req.name}' already exists for this provider.")

        repo = Repository.create(
            name=req.name,
            provider_id=req.provider_id,
            web_url=req.web_url,
            provider_repo_id=req.provider_repo_id,
            clone_url=req.clone_url,
            default_branch=req.default_branch,
            auth_type=req.authentication_type.value,
            secret_ref=req.secret_ref,
            branch_rules=[(r.pattern, r.scan_on_push) for r in req.branch_rules],
        )

        self._db.add(repo)
        await self._db.commit()
        await self._db.refresh(repo)
        return CreateRepositoryResponse(
            id=repo.id,
            name=repo.name,
            provider_id=repo.provider_id,
            web_url=repo.web_url,
            created_at=repo.created_at,
        )

    # ── UPDATE ───────────────────────────────────────────────────────────────

    async def update(self, repo_id: uuid.UUID, req: UpdateRepositoryRequest) -> UpdateRepositoryResponse:
        stmt = (
            select(Repository)
            .where(Repository.id == repo_id, Repository.is_deleted.is_(False))
            .options(selectinload(Repository.branch_rules), joinedload(Repository.auth))
        )
        repo = (await self._db.execute(stmt)).scalar_one_or_none()
        if repo is None:
            raise KeyError(f"Repository {repo_id} not found.")

        repo.name = req.name
        repo.provider_id = req.provider_id
        repo.web_url = req.web_url
        repo.clone_url = req.clone_url
        repo.default_branch = req.default_branch
        if req.provider_repo_id:
            repo.provider_repo_id = req.provider_repo_id
        repo.touch_updated()

        if repo.auth:
            repo.auth.auth_type = req.authentication_type.value
            repo.auth.secret_ref = req.secret_ref
        else:
            repo.auth = RepositoryAuth.create(repo_id, req.authentication_type.value, req.secret_ref)

        requested_patterns = {r.pattern.strip().lower() for r in req.branch_rules}
        rules_to_delete = [r for r in repo.branch_rules if r.pattern.lower() not in requested_patterns]
        for rule in rules_to_delete:
            await self._db.delete(rule)

        existing_by_pattern = {r.pattern.lower(): r for r in repo.branch_rules}
        for dto in req.branch_rules:
            pattern = dto.pattern.strip()
            existing = existing_by_pattern.get(pattern.lower())
            if existing:
                existing.scan_on_push = dto.scan_on_push
                existing.is_enabled = True
            else:
                new_rule = BranchTrackingRule.create(repo_id, pattern, dto.scan_on_push)
                repo.branch_rules.append(new_rule)
                self._db.add(new_rule)

        await self._db.commit()
        await self._db.refresh(repo)
        return UpdateRepositoryResponse(
            id=repo.id,
            name=repo.name,
            provider_id=repo.provider_id,
            web_url=repo.web_url,
            updated_at=repo.updated_at or datetime.now(timezone.utc),
        )

    # ── DELETE ───────────────────────────────────────────────────────────────

    async def delete(self, repo_id: uuid.UUID) -> None:
        stmt = (
            select(Repository)
            .where(Repository.id == repo_id)
            .options(selectinload(Repository.branch_rules), joinedload(Repository.auth))
        )
        repo = (await self._db.execute(stmt)).scalar_one_or_none()
        if repo is None:
            raise KeyError(f"Repository {repo_id} not found.")
        await self._db.delete(repo)
        await self._db.commit()

    # ── TEST CONNECTION ───────────────────────────────────────────────────────

    async def test_connection(self, req: TestConnectionRequest) -> TestConnectionResponse:
        provider = (
            await self._db.execute(
                select(SourceProvider).where(
                    SourceProvider.id == req.provider_id, SourceProvider.is_active.is_(True)
                )
            )
        ).scalar_one_or_none()

        if provider is None:
            return self._fail("Provider not found or inactive.")

        try:
            client = self._factory.get_client(provider.code, provider.api_base_url)
            auth = ProviderAuth(auth_type=req.auth_type, secret_ref_or_token=req.secret_ref_or_token)
            meta = await client.get_repo_meta(req.web_url, auth)
            branch_names = await client.get_branches(meta, auth)
            return TestConnectionResponse(
                success=True,
                repo_name=meta.name,
                provider_repo_id=meta.provider_repo_id,
                provider_workspace_id=meta.provider_workspace_id,
                default_branch=meta.default_branch,
                clone_url=meta.clone_url,
                web_url_normalized=meta.web_url_normalized,
                error_message=None,
                branches=[GitBranchDto(name=b) for b in branch_names],
            )
        except Exception as exc:
            return self._fail(str(exc))

    # ── WEBHOOK LOOKUP ────────────────────────────────────────────────────────

    async def resolve_by_provider_id(self, provider_code: str, external_repo_id: str) -> uuid.UUID:
        stmt = (
            select(Repository.id)
            .join(SourceProvider, Repository.provider_id == SourceProvider.id)
            .where(
                SourceProvider.code == provider_code.lower(),
                Repository.provider_repo_id == external_repo_id,
            )
        )
        result = (await self._db.execute(stmt)).scalar_one_or_none()
        if result is None:
            raise KeyError(
                f"No repository found for provider '{provider_code}' with external ID '{external_repo_id}'."
            )
        return result

    # ── HELPERS ───────────────────────────────────────────────────────────────

    @staticmethod
    def _fail(msg: str) -> TestConnectionResponse:
        return TestConnectionResponse(
            success=False,
            repo_name=None,
            provider_repo_id=None,
            provider_workspace_id=None,
            default_branch=None,
            clone_url=None,
            web_url_normalized=None,
            error_message=msg,
            branches=[],
        )

    @staticmethod
    def _to_full_dto(repo: Repository) -> GetRepositoryResponse:
        from app.schemas.repository import AuthType as SchemaAuthType
        auth_type = SchemaAuthType(repo.auth.auth_type) if repo.auth else None
        return GetRepositoryResponse(
            id=repo.id,
            name=repo.name,
            provider_id=repo.provider_id,
            web_url=repo.web_url,
            clone_url=repo.clone_url,
            default_branch=repo.default_branch,
            provider_repo_id=repo.provider_repo_id,
            provider_workspace_id=repo.provider_workspace_id,
            is_active=repo.is_active,
            cloned_directory=repo.cloned_directory,
            last_seen_at_utc=repo.last_seen_at_utc,
            created_at=repo.created_at,
            updated_at=repo.updated_at,
            is_deleted=repo.is_deleted,
            authentication_type=auth_type,
            secret_ref=repo.auth.secret_ref if repo.auth else None,
            branch_rules=[
                BranchRuleDto(
                    id=br.id,
                    pattern=br.pattern,
                    scan_on_push=br.scan_on_push,
                    is_enabled=br.is_enabled,
                )
                for br in (repo.branch_rules or [])
                if not br.is_deleted
            ],
        )
