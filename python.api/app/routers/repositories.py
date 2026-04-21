from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.routing import CamelCaseRoute
from app.db.session import get_db
from app.schemas.common import PagedResult
from app.schemas.repository import (
    CreateRepositoryRequest,
    CreateRepositoryResponse,
    GetAllRepositoriesQuery,
    GetRepositoryResponse,
    RepositoryDto,
    TestConnectionRequest,
    TestConnectionResponse,
    UpdateRepositoryRequest,
    UpdateRepositoryResponse,
)
from app.services.provider_clients.factory import RepoProviderClientFactory
from app.services.repository_service import RepositoryService
from app.services.repo_sync_service import RepoSyncService

router = APIRouter(prefix="/repositories", tags=["Repositories"], route_class=CamelCaseRoute)

_factory = RepoProviderClientFactory()


def get_repo_service(db: AsyncSession = Depends(get_db)) -> RepositoryService:
    return RepositoryService(db, _factory)


def get_sync_service(db: AsyncSession = Depends(get_db)) -> RepoSyncService:
    return RepoSyncService(db)


@router.get("", response_model=PagedResult[RepositoryDto], summary="Get all repositories")
async def get_all_repositories(
    page_index: int = Query(default=1, ge=1),
    skip_count: int = Query(default=0, ge=0),
    max_result_count: int = Query(default=10, ge=1, le=500),
    include_deleted: bool = Query(default=False),
    search_term: str | None = Query(default=None),
    provider_id: uuid.UUID | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    service: RepositoryService = Depends(get_repo_service),
) -> PagedResult[RepositoryDto]:
    query = GetAllRepositoriesQuery(
        page_index=page_index,
        skip_count=skip_count,
        max_result_count=max_result_count,
        include_deleted=include_deleted,
        search_term=search_term,
        provider_id=provider_id,
        is_active=is_active,
    )
    return await service.get_all(query)


@router.get("/{repo_id}", response_model=GetRepositoryResponse, summary="Get a repository by ID")
async def get_repository(
    repo_id: uuid.UUID,
    service: RepositoryService = Depends(get_repo_service),
) -> GetRepositoryResponse:
    result = await service.get_by_id(repo_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found.")
    return result


@router.post(
    "",
    response_model=CreateRepositoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new repository",
)
async def create_repository(
    req: CreateRepositoryRequest,
    service: RepositoryService = Depends(get_repo_service),
) -> CreateRepositoryResponse:
    try:
        return await service.create(req)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.put("/{repo_id}", response_model=UpdateRepositoryResponse, summary="Update a repository")
async def update_repository(
    repo_id: uuid.UUID,
    req: UpdateRepositoryRequest,
    service: RepositoryService = Depends(get_repo_service),
) -> UpdateRepositoryResponse:
    try:
        return await service.update(repo_id, req)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/{repo_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a repository")
async def delete_repository(
    repo_id: uuid.UUID,
    service: RepositoryService = Depends(get_repo_service),
) -> None:
    try:
        await service.delete(repo_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/test-connection", response_model=TestConnectionResponse, summary="Test repository connection")
async def test_connection(
    req: TestConnectionRequest,
    service: RepositoryService = Depends(get_repo_service),
) -> TestConnectionResponse:
    return await service.test_connection(req)


@router.post("/{repo_id}/sync", summary="Clone or pull the repository to the local workspace")
async def sync_repository(
    repo_id: uuid.UUID,
    svc: RepoSyncService = Depends(get_sync_service),
) -> dict:
    return await svc.sync(repo_id)


@router.get("/{repo_id}/analyze", summary="Analyze the local workspace for a repository")
async def analyze_repository(
    repo_id: uuid.UUID,
    svc: RepoSyncService = Depends(get_sync_service),
) -> dict:
    return await svc.analyze(repo_id)
