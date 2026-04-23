from __future__ import annotations

from app.schemas.common import CamelModel


class IndexRequest(CamelModel):
    repo_id: str
    workspace_path: str
    clear_existing: bool = False


class IndexResponse(CamelModel):
    repo_id: str
    files_indexed: int
    chunks_created: int
    chunks_upserted: int


class QueryRequest(CamelModel):
    repo_id: str
    question: str
    session_id: str          # used to cache the embedding model per user session
    top_k: int = 5


class SourceReference(CamelModel):
    file_path: str
    score: float


class QueryResponse(CamelModel):
    answer: str
    sources: list[SourceReference]


class IndexStatusResponse(CamelModel):
    repo_id: str
    chunk_count: int
    is_indexed: bool
