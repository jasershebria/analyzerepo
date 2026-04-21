from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.routing import CamelCaseRoute
from app.db.session import get_db
from app.schemas.common import PagedResult
from app.schemas.provider import CreateProviderRequest, GetAllProvidersQuery, ProviderDto
from app.services.provider_service import ProviderService

router = APIRouter(prefix="/providers", tags=["Providers"], route_class=CamelCaseRoute)


def get_provider_service(db: AsyncSession = Depends(get_db)) -> ProviderService:
    return ProviderService(db)


@router.get("", response_model=PagedResult[ProviderDto], summary="Get all providers")
async def get_all_providers(
    page_index: int = Query(default=1, ge=1),
    max_result_count: int = Query(default=50, ge=1, le=500),
    search_term: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    service: ProviderService = Depends(get_provider_service),
) -> PagedResult[ProviderDto]:
    query = GetAllProvidersQuery(
        page_index=page_index,
        max_result_count=max_result_count,
        search_term=search_term,
        is_active=is_active,
    )
    return await service.get_all(query)


@router.post("", response_model=ProviderDto, status_code=status.HTTP_201_CREATED, summary="Create a new provider")
async def create_provider(
    req: CreateProviderRequest,
    service: ProviderService = Depends(get_provider_service),
) -> ProviderDto:
    try:
        return await service.create(req)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a provider")
async def delete_provider(
    provider_id: uuid.UUID,
    service: ProviderService = Depends(get_provider_service),
) -> None:
    try:
        await service.delete(provider_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
