from __future__ import annotations

from fastapi import APIRouter

from app.core.routing import CamelCaseRoute
import app.rag.vector_store as vs
from app.rag.indexing import build_index
from app.rag.retrieval import invalidate_session, query_rag
from app.routers.ai import get_db
from app.schemas.rag import (
    IndexRequest,
    IndexResponse,
    IndexStatusResponse,
    QueryRequest,
    QueryResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

router = APIRouter(prefix="/rag", tags=["RAG"], route_class=CamelCaseRoute)


@router.post("/index", response_model=IndexResponse)
async def index_repository(request: IndexRequest) -> IndexResponse:
    """Build the vector index for a repository workspace.

    Must be called ONCE before any /rag/query calls for this repo.
    Re-calling with clear_existing=true rebuilds from scratch.
    """
    stats = await build_index(
        workspace_path=request.workspace_path,
        repo_id=request.repo_id,
        clear_existing=request.clear_existing,
    )
    # Invalidate any cached retriever so the next query picks up fresh chunks.
    invalidate_session(request.repo_id)
    return IndexResponse(**stats.as_dict())


@router.post("/query", response_model=QueryResponse)
async def query_repository(request: QueryRequest, db: AsyncSession = Depends(get_db)) -> QueryResponse:
    """Answer a question using RAG over the indexed repository.

    session_id is used to cache the embedding model and DB handle
    across requests from the same user session.
    """
    result = await query_rag(
        question=request.question,
        session_id=request.session_id,
        repo_id=request.repo_id,
        db=db,
        top_k=request.top_k,
    )
    return QueryResponse(**result.as_dict())


@router.get("/status/{repo_id}", response_model=IndexStatusResponse)
async def index_status(repo_id: str) -> IndexStatusResponse:
    """Return how many chunks are indexed for a repository."""
    col = vs.get_collection(repo_id)
    count = await vs.count_chunks(col)
    return IndexStatusResponse(repo_id=repo_id, chunk_count=count, is_indexed=count > 0)


@router.delete("/index/{repo_id}", status_code=204)
async def clear_index(repo_id: str) -> None:
    """Drop all indexed chunks for a repository and evict the session cache."""
    col = vs.get_collection(repo_id)
    await vs.drop_collection(col)
    invalidate_session(repo_id)
