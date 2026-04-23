"""LangChain-backed MongoDB vector store for the RAG pipeline.

Uses MongoDBAtlasVectorSearch for vector similarity search (Atlas or MongoDB 7+
with Atlas Search). Falls back to Python cosine similarity on plain MongoDB.

Public API
----------
MongoVectorStore(repo_id)
    .ensure_indexes()            -> None
    .add_documents(docs)         -> int   (chunks upserted)
    .similarity_search(q, top_k) -> list[dict]
    .count()                     -> int
    .clear()                     -> None
    .close()                     -> None
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import numpy as np
from langchain_core.documents import Document
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_openai import OpenAIEmbeddings
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient, ReplaceOne

from app.core.config import settings

log = logging.getLogger(__name__)

_COLLECTION_PREFIX = "rag_chunks"
_COSINE_FETCH_LIMIT = 20_000


def _collection_name(repo_id: str) -> str:
    return f"{_COLLECTION_PREFIX}_{repo_id.replace('-', '_')}"


class MongoVectorStore:
    """Per-repo vector store backed by MongoDB via LangChain's MongoDBAtlasVectorSearch.

    Each stored document has the shape:
        {
            chunk_id:  str,       # sha256 — upsert key
            content:   str,       # raw text (LangChain text_key)
            embedding: [float],   # dense vector (LangChain embedding_key)
            metadata: {
                file_path:   str,
                chunk_index: int,
                extension:   str,
            }
        }
    """

    def __init__(self, repo_id: str) -> None:
        self._repo_id = repo_id
        col_name = _collection_name(repo_id)

        # Sync pymongo collection — required by MongoDBAtlasVectorSearch
        self._sync_client = MongoClient(settings.mongodb_url)
        sync_col = self._sync_client[settings.mongodb_db][col_name]

        # Async motor collection — for index management, count, drop, upsert
        self._async_client = AsyncIOMotorClient(settings.mongodb_url)
        self._async_col = self._async_client[settings.mongodb_db][col_name]

        self._embeddings = OpenAIEmbeddings(
            openai_api_base=settings.ai_base_url,
            openai_api_key=settings.ai_api_key,
            model=settings.embedding_model,
            chunk_size=settings.rag_embedding_batch_size,
        )

        self._lc_store = MongoDBAtlasVectorSearch(
            collection=sync_col,
            embedding=self._embeddings,
            index_name=f"rag_vector_{repo_id[:8]}",
            text_key="content",
            embedding_key="embedding",
            relevance_score_fn="cosine",
        )

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    async def ensure_indexes(self) -> None:
        await self._async_col.create_index("chunk_id", unique=True)
        await self._async_col.create_index("metadata.file_path")

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def add_documents(self, documents: list[Document]) -> int:
        """Embed documents via LangChain and upsert to MongoDB by chunk_id.

        Returns the number of affected (inserted + modified) documents.
        """
        if not documents:
            return 0

        texts = [doc.page_content for doc in documents]
        metas = [doc.metadata for doc in documents]

        embeddings: list[list[float]] = await asyncio.get_event_loop().run_in_executor(
            None, lambda: self._embeddings.embed_documents(texts)
        )

        ops = []
        for doc, emb, meta in zip(documents, embeddings, metas):
            chunk_id = meta.get("chunk_id", "")
            raw = {
                "chunk_id": chunk_id,
                "content": doc.page_content,
                "embedding": emb,
                "metadata": {k: v for k, v in meta.items() if k != "chunk_id"},
            }
            ops.append(ReplaceOne({"chunk_id": chunk_id}, raw, upsert=True))

        result = await self._async_col.bulk_write(ops, ordered=False)
        return result.upserted_count + result.modified_count

    async def clear(self) -> None:
        await self._async_col.drop()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def count(self) -> int:
        return await self._async_col.count_documents({})

    async def similarity_search(
        self, query: str, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """Return top-k chunks most similar to query.

        Tries Atlas $vectorSearch via LangChain; falls back to Python cosine
        similarity so the system works on any MongoDB instance.
        """
        try:
            results = await self._lc_store.asimilarity_search_with_relevance_scores(
                query, k=top_k
            )
            if not results:
                raise ValueError("Atlas vector search returned no results")
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": round(score, 4),
                }
                for doc, score in results
            ]
        except Exception:
            log.debug(
                "Atlas $vectorSearch unavailable for repo %s — using cosine fallback",
                self._repo_id,
            )
            return await self._cosine_fallback(query, top_k)

    async def _cosine_fallback(self, query: str, top_k: int) -> list[dict[str, Any]]:
        query_emb: list[float] = await asyncio.get_event_loop().run_in_executor(
            None, lambda: self._embeddings.embed_query(query)
        )
        q = np.array(query_emb, dtype=np.float32)
        q_unit = q / (np.linalg.norm(q) + 1e-10)

        docs = await self._async_col.find(
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

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        self._sync_client.close()
        self._async_client.close()
