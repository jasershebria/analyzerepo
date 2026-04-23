"""Functional MongoDB vector store module — shared by indexing.py and retrieval.py.

Async raw operations (ensure_indexes, upsert_chunks, count_chunks, drop_collection)
use Motor. Similarity search uses LangChain's MongoDBAtlasVectorSearch ($vectorSearch)
and falls back to Python cosine similarity on plain MongoDB instances.

Public API
----------
get_collection(repo_id)                            -> AsyncIOMotorCollection
ensure_indexes(col)                                -> None
upsert_chunks(col, chunks)                         -> int
count_chunks(col)                                  -> int
drop_collection(col)                               -> None
similarity_search(col, query, top_k)               -> list[dict]
close()                                            -> None
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import numpy as np
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_ollama import OllamaEmbeddings
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo import MongoClient, ReplaceOne

from app.core.config import settings

log = logging.getLogger(__name__)

_COLLECTION_PREFIX = "rag_chunks"
_COSINE_FETCH_LIMIT = 20_000

# ---------------------------------------------------------------------------
# Singleton clients and LangChain store cache
# ---------------------------------------------------------------------------

_motor_client: AsyncIOMotorClient | None = None
_sync_client: MongoClient | None = None
# col_name → (MongoDBAtlasVectorSearch, OllamaEmbeddings)
_lc_stores: dict[str, tuple[MongoDBAtlasVectorSearch, OllamaEmbeddings]] = {}


def _get_motor_client() -> AsyncIOMotorClient:
    global _motor_client
    if _motor_client is None:
        _motor_client = AsyncIOMotorClient(settings.mongodb_url)
        log.info("Motor client created: %s / %s", settings.mongodb_url, settings.mongodb_db)
    return _motor_client


def _get_sync_client() -> MongoClient:
    global _sync_client
    if _sync_client is None:
        _sync_client = MongoClient(settings.mongodb_url)
    return _sync_client


def _get_lc_store(col: AsyncIOMotorCollection) -> tuple[MongoDBAtlasVectorSearch, OllamaEmbeddings]:
    col_name = col.name
    if col_name not in _lc_stores:
        base_url = settings.ai_base_url.replace("/v1", "").rstrip("/")
        embeddings = OllamaEmbeddings(
            base_url=base_url,
            model=settings.embedding_model,
        )
        sync_col = _get_sync_client()[settings.mongodb_db][col_name]
        lc_store = MongoDBAtlasVectorSearch(
            collection=sync_col,
            embedding=embeddings,
            index_name=f"rag_vector_{col_name[-8:]}",
            text_key="content",
            embedding_key="embedding",
            relevance_score_fn="cosine",
        )
        _lc_stores[col_name] = (lc_store, embeddings)
    return _lc_stores[col_name]


# ---------------------------------------------------------------------------
# Collection helpers
# ---------------------------------------------------------------------------

def get_collection(repo_id: str) -> AsyncIOMotorCollection:
    """Return the Motor collection for the given repo_id."""
    name = f"{_COLLECTION_PREFIX}_{repo_id.replace('-', '_')}"
    return _get_motor_client()[settings.mongodb_db][name]


async def close() -> None:
    """Close all singleton clients. Call once at application shutdown."""
    global _motor_client, _sync_client
    if _motor_client is not None:
        _motor_client.close()
        _motor_client = None
    if _sync_client is not None:
        _sync_client.close()
        _sync_client = None
    _lc_stores.clear()
    log.info("vector_store clients closed")


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

async def ensure_indexes(col: AsyncIOMotorCollection) -> None:
    await col.create_index("chunk_id", unique=True)
    await col.create_index("metadata.file_path")


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

async def upsert_chunks(col: AsyncIOMotorCollection, chunks: list[dict[str, Any]]) -> int:
    """Bulk-upsert chunks by chunk_id. Returns number of affected documents."""
    if not chunks:
        return 0
    ops = [ReplaceOne({"chunk_id": c["chunk_id"]}, c, upsert=True) for c in chunks]
    result = await col.bulk_write(ops, ordered=False)
    return result.upserted_count + result.modified_count


async def drop_collection(col: AsyncIOMotorCollection) -> None:
    col_name = col.name
    await col.drop()
    _lc_stores.pop(col_name, None)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

async def count_chunks(col: AsyncIOMotorCollection) -> int:
    return await col.count_documents({})


async def similarity_search(
    col: AsyncIOMotorCollection,
    query: str,
    top_k: int,
) -> list[dict[str, Any]]:
    """Return top-k chunks most similar to query text.

    Tries Atlas $vectorSearch via LangChain's MongoDBAtlasVectorSearch;
    falls back to Python cosine similarity on plain MongoDB instances.
    """
    lc_store, embeddings = _get_lc_store(col)
    try:
        pairs = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: lc_store.similarity_search_with_score(query, k=top_k),
        )
        if not pairs:
            raise ValueError("Atlas $vectorSearch returned no results")
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": round(score, 4),
            }
            for doc, score in pairs
        ]
    except Exception:
        log.debug("Atlas $vectorSearch unavailable — using cosine fallback")
        return await _python_cosine_search(col, query, embeddings, top_k)


async def _python_cosine_search(
    col: AsyncIOMotorCollection,
    query: str,
    embeddings: OllamaEmbeddings,
    top_k: int,
) -> list[dict[str, Any]]:
    query_emb: list[float] = await asyncio.get_event_loop().run_in_executor(
        None, lambda: embeddings.embed_query(query)
    )
    q = np.array(query_emb, dtype=np.float32)
    q_unit = q / (np.linalg.norm(q) + 1e-10)

    docs = await col.find(
        {}, {"_id": 0, "content": 1, "metadata": 1, "embedding": 1}
    ).limit(_COSINE_FETCH_LIMIT).to_list(length=_COSINE_FETCH_LIMIT)

    if not docs:
        return []

    scored: list[tuple[float, dict]] = []
    for doc in docs:
        emb = np.array(doc["embedding"], dtype=np.float32)
        emb_unit = emb / (np.linalg.norm(emb) + 1e-10)
        scored.append((float(np.dot(q_unit, emb_unit)), doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {"content": d["content"], "metadata": d["metadata"], "score": s}
        for s, d in scored[:top_k]
    ]
