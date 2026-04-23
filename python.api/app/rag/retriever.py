"""Retrieval pipeline: query → top-k chunks (via LangChain vector store) → LLM synthesis.

Usage:
    retriever = RAGRetriever(repo_id="<uuid>")
    result = await retriever.query("How does authentication work?")
    await retriever.close()
    # result = {"answer": "...", "sources": [{"file_path": "...", "score": 0.91}, ...]}
"""
from __future__ import annotations

import logging

from app.core.config import settings
from app.rag.mongo_store import MongoVectorStore
from app.services.ai_service import AIChatService

log = logging.getLogger(__name__)

_RAG_SYSTEM_PROMPT = """\
You are a senior software engineer analyzing a real codebase.
You are given code snippets retrieved from the repository that are relevant to the user's question.

Rules:
- Answer using ONLY the provided context — do not invent code or logic.
- Reference specific file paths and function/class names when they appear in the context.
- If the answer cannot be determined from the provided context, say so clearly.
- Be concise, precise, and developer-focused.\
"""

_CONTEXT_TEMPLATE = """\
## Retrieved code from the repository

{context}

---

## Question

{question}\
"""


class RAGRetriever:
    """Retrieves the top-k most relevant chunks from MongoDB via LangChain vector search
    and synthesizes a grounded answer via the configured LLM."""

    def __init__(self, repo_id: str) -> None:
        self._repo_id = repo_id
        self._store = MongoVectorStore(repo_id)
        self._ai = AIChatService()

    async def query(
        self,
        question: str,
        top_k: int | None = None,
    ) -> dict:
        """Retrieve relevant chunks and generate a grounded answer.

        Returns:
            {
                "answer": str,
                "sources": [{"file_path": str, "score": float}, ...]
            }
        """
        k = top_k if top_k is not None else settings.rag_top_k

        chunk_count = await self._store.count()
        if chunk_count == 0:
            return {
                "answer": (
                    "This repository has not been indexed yet. "
                    "Call POST /api/rag/index first."
                ),
                "sources": [],
            }

        # Embedding + retrieval handled by the store (Atlas search or cosine fallback)
        chunks = await self._store.similarity_search(question, top_k=k)

        if not chunks:
            return {
                "answer": "No relevant code found for this query.",
                "sources": [],
            }

        # Build context block — each chunk prefixed with its file path
        context_parts = []
        for chunk in chunks:
            file_path = chunk.get("metadata", {}).get("file_path", "unknown")
            context_parts.append(f"// {file_path}\n{chunk['content']}")
        context = "\n\n---\n\n".join(context_parts)

        prompt = _CONTEXT_TEMPLATE.format(context=context, question=question)

        answer = await self._ai.chat(prompt, system_prompt=_RAG_SYSTEM_PROMPT)

        sources = [
            {
                "file_path": c.get("metadata", {}).get("file_path", ""),
                "score": round(c.get("score", 0.0), 4),
            }
            for c in chunks
        ]

        return {"answer": answer, "sources": sources}

    async def close(self) -> None:
        await self._store.close()
