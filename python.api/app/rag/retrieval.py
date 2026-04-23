"""Retrieval pipeline — runs on every user request.

The embedding model and MongoDB collection handle are cached per session_id
so they are created once per session, not once per request.

Public API
----------
query_rag(question, session_id, top_k=None) -> RAGResult
invalidate_session(session_id)              -> None
"""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.rag import vector_store as vs
from app.services.ai_service import AIChatService
from app.services.tool_service import ToolService

# retrieval.py NEVER imports from indexing.py — strict one-way separation.

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a senior software engineer analyzing a real codebase.
You have been provided with initial code snippets from a vector search, but you also have TOOLS to read complete files or analyze the repository structure.

Rules:
- If the provided snippets are not enough, use the 'read_file' tool to see the full content of relevant files.
- Always reference specific file paths and code entities.
- Be concise, precise, and developer-focused.
- If you still cannot find the answer after using your tools, say so explicitly.\
"""

_CONTEXT_TEMPLATE = """\
## Retrieved code from the repository

{context}

---

## Question

{question}\
"""

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class RAGResult:
    answer: str
    sources: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {"answer": self.answer, "sources": self.sources}


# ---------------------------------------------------------------------------
# Per-session retriever cache
# ---------------------------------------------------------------------------
# session_id → _SessionRetriever
# The cache avoids rebuilding the embedding model and re-opening the
# collection handle on every request for the same session.

@dataclass
class _SessionRetriever:
    session_id: str
    repo_id: str
    collection: AsyncIOMotorCollection
    ai: AIChatService
    created_at: float = field(default_factory=time.monotonic)


_session_cache: dict[str, _SessionRetriever] = {}


def _get_or_create_session(session_id: str, repo_id: str) -> _SessionRetriever:
    """Return a cached retriever for this session, or create one if needed."""
    if session_id in _session_cache:
        cached = _session_cache[session_id]
        if cached.repo_id == repo_id:
            return cached
        # repo_id changed for this session — evict and rebuild
        log.debug("Session %s changed repo — evicting cache", session_id)

    retriever = _SessionRetriever(
        session_id=session_id,
        repo_id=repo_id,
        collection=vs.get_collection(repo_id),
        ai=AIChatService(),
    )
    _session_cache[session_id] = retriever
    log.debug("Session %s: retriever created for repo %s", session_id, repo_id)
    return retriever


def invalidate_session(repo_id: str) -> None:
    """Evict all cached sessions that use repo_id (called after re-indexing or clear)."""
    stale = [sid for sid, s in _session_cache.items() if s.repo_id == repo_id]
    for sid in stale:
        _session_cache.pop(sid, None)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def query_rag(
    question: str,
    session_id: str,
    repo_id: str,
    db: AsyncSession,
    top_k: int | None = None,
) -> RAGResult:
    """Embed the question, retrieve top-k chunks, and synthesize an answer.

    This function runs on every user request. It never triggers indexing.

    Args:
        question:   The user's natural-language question.
        session_id: Caller-supplied session identifier (for cache keying).
        repo_id:    Repository UUID — determines which collection to search.
        top_k:      Number of chunks to retrieve (defaults to settings.rag_top_k).

    Returns:
        RAGResult with answer text and list of source references.

    Raises:
        RuntimeError: If the embedding call fails.
    """
    k = top_k if top_k is not None else settings.rag_top_k
    session = _get_or_create_session(session_id, repo_id)

    # Guard: repo must be indexed
    try:
        chunk_count = await vs.count_chunks(session.collection)
    except Exception as exc:
        raise RuntimeError(f"MongoDB unavailable: {exc}") from exc

    if chunk_count == 0:
        return RAGResult(
            answer=(
                "This repository has not been indexed yet. "
                "Trigger POST /api/rag/index first, then retry."
            )
        )

    # Embedding + retrieval handled together by vector_store (Atlas search or cosine fallback)
    chunks = await vs.similarity_search(session.collection, question, top_k=k)

    if not chunks:
        return RAGResult(answer="No relevant code found for this query.", sources=[])

    # 3. Build context block
    context = "\n\n---\n\n".join(
        f"// {c.get('metadata', {}).get('file_path', 'unknown')}\n{c['content']}"
        for c in chunks
    )
    # 4. Agentic synthesis with Tools
    tool_svc = ToolService(db, uuid.UUID(repo_id))
    prompt = _CONTEXT_TEMPLATE.format(context=context, question=question)
    
    messages = [
        ("system", _SYSTEM_PROMPT),
        ("user", prompt)
    ]
    
    answer = await session.ai.chat_with_history(
        messages=messages,
        tool_executor=tool_svc.execute_tool
    )

    sources = [
        {
            "file_path": c.get("metadata", {}).get("file_path", ""),
            "score": round(c.get("score", 0.0), 4),
        }
        for c in chunks
    ]

    return RAGResult(answer=answer, sources=sources)
