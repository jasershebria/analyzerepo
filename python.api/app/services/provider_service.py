from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source_provider import SourceProvider
from app.schemas.common import PagedResult
from app.schemas.provider import CreateProviderRequest, GetAllProvidersQuery, ProviderDto


class ProviderService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_all(self, query: GetAllProvidersQuery) -> PagedResult[ProviderDto]:
        stmt = select(SourceProvider).where(SourceProvider.is_deleted.is_(False))

        if query.is_active is not None:
            stmt = stmt.where(SourceProvider.is_active == query.is_active)

        if query.search_term:
            term = query.search_term.lower()
            stmt = stmt.where(
                SourceProvider.name.ilike(f"%{term}%")
                | SourceProvider.code.ilike(f"%{term}%")
            )

        stmt = stmt.order_by(SourceProvider.name)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count: int = (await self._db.execute(count_stmt)).scalar_one()

        offset = max(0, (query.page_index - 1) * query.max_result_count)
        rows = (await self._db.execute(stmt.offset(offset).limit(query.max_result_count))).scalars().all()

        return PagedResult(
            total_count=total_count,
            items=[self._to_dto(p) for p in rows],
        )

    async def create(self, req: CreateProviderRequest) -> ProviderDto:
        exists = (
            await self._db.execute(
                select(SourceProvider).where(
                    SourceProvider.code == req.code.lower(),
                    SourceProvider.is_deleted.is_(False),
                )
            )
        ).scalar_one_or_none()

        if exists:
            raise ValueError(f"A provider with code '{req.code}' already exists.")

        provider = SourceProvider.create(req.name, req.code, req.api_base_url)
        self._db.add(provider)
        await self._db.commit()
        await self._db.refresh(provider)
        return self._to_dto(provider)

    async def delete(self, provider_id: uuid.UUID) -> None:
        provider = (
            await self._db.execute(
                select(SourceProvider).where(
                    SourceProvider.id == provider_id,
                    SourceProvider.is_deleted.is_(False),
                )
            )
        ).scalar_one_or_none()

        if provider is None:
            raise KeyError(f"Provider '{provider_id}' not found.")

        provider.soft_delete()
        await self._db.commit()

    @staticmethod
    def _to_dto(p: SourceProvider) -> ProviderDto:
        return ProviderDto(
            id=p.id,
            name=p.name,
            code=p.code,
            api_base_url=p.api_base_url,
            is_active=p.is_active,
            created_at=p.created_at,
        )
