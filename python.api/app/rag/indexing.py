"""Indexing pipeline — run ONCE at deployment/trigger time, never during queries.

Public API
----------
build_index(workspace_path, repo_id, clear_existing=False) -> IndexStats
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.rag import vector_store as vs

# indexing.py NEVER imports from retrieval.py — one-way dependency only.

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SKIP_DIRS = {
    "node_modules", ".git", "bin", "obj", "dist", "build",
    ".angular", "__pycache__", ".venv", "venv", ".vs", ".idea",
    "coverage", "migrations", "Migrations",
}

_SUPPORTED_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx", ".py", ".cs", ".go",
    ".java", ".rs", ".html", ".css", ".scss", ".swift", ".kt", ".dart",
    ".json", ".yaml", ".yml", ".toml", ".md",
}

_LANGUAGE_SEPARATORS: dict[str, list[str]] = {
    ".py":  ["\nclass ", "\ndef ", "\nasync def ", "\n\n", "\n", " ", ""],
    ".ts":  ["\nclass ", "\nfunction ", "\nconst ", "\nexport ", "\n\n", "\n", " ", ""],
    ".tsx": ["\nclass ", "\nfunction ", "\nconst ", "\nreturn ", "\nexport ", "\n\n", "\n", " ", ""],
    ".js":  ["\nclass ", "\nfunction ", "\nconst ", "\nexport ", "\n\n", "\n", " ", ""],
    ".jsx": ["\nclass ", "\nfunction ", "\nconst ", "\nreturn ", "\nexport ", "\n\n", "\n", " ", ""],
    ".cs":  ["\nclass ", "\npublic ", "\nprivate ", "\nprotected ", "\nnamespace ", "\n\n", "\n", " ", ""],
    ".go":  ["\nfunc ", "\ntype ", "\nvar ", "\nconst ", "\n\n", "\n", " ", ""],
    ".rs":  ["\nfn ", "\nstruct ", "\nimpl ", "\npub ", "\n\n", "\n", " ", ""],
    ".java": ["\nclass ", "\npublic ", "\nprivate ", "\nprotected ", "\n\n", "\n", " ", ""],
}
_DEFAULT_SEPARATORS = ["\n\n", "\n", " ", ""]


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class IndexStats:
    repo_id: str
    files_indexed: int
    chunks_created: int
    chunks_upserted: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "repo_id": self.repo_id,
            "files_indexed": self.files_indexed,
            "chunks_created": self.chunks_created,
            "chunks_upserted": self.chunks_upserted,
        }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def build_index(
    workspace_path: str | Path,
    repo_id: str,
    *,
    clear_existing: bool = False,
    on_progress: Callable[[int], None] | None = None,
) -> IndexStats:
    """Load all source files in workspace_path, chunk them, embed, and store.

    This function must be called ONCE (deployment time or manual trigger).
    It is NEVER called from the query path.

    Args:
        workspace_path: Root directory of the cloned repository.
        repo_id:        Repository UUID — determines the MongoDB collection.
        clear_existing: Drop and rebuild the collection when True.
        on_progress:    Optional callback called with an integer 0–100 as work progresses.

    Returns:
        IndexStats with counts of files/chunks processed.

    Raises:
        ValueError: If workspace_path does not exist.
        RuntimeError: If embedding fails.
    """
    def _report(pct: int) -> None:
        log.info("build_index [%s]: %d%%", repo_id, pct)
        if on_progress:
            on_progress(pct)

    workspace = Path(workspace_path)
    if not workspace.exists():
        raise ValueError(f"Workspace not found: {workspace}")

    _report(0)
    col = vs.get_collection(repo_id)

    if clear_existing:
        await vs.drop_collection(col)
        log.info("Dropped existing index for repo %s", repo_id)

    await vs.ensure_indexes(col)

    files = list(_collect_files(workspace))
    log.info("build_index: found %d files for repo %s", len(files), repo_id)
    _report(5)

    all_chunks: list[dict[str, Any]] = []
    for path in files:
        all_chunks.extend(_split_file(path, workspace))

    log.info("build_index: %d chunks from %d files", len(all_chunks), len(files))
    _report(15)

    try:
        upserted = await _embed_and_store(col, all_chunks, repo_id, _report)
    except Exception as exc:
        raise RuntimeError(f"Embedding failed for repo {repo_id}: {exc}") from exc

    stats = IndexStats(
        repo_id=repo_id,
        files_indexed=len(files),
        chunks_created=len(all_chunks),
        chunks_upserted=upserted,
    )
    _report(100)
    log.info("build_index complete: %s", stats)
    return stats


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_embeddings() -> OllamaEmbeddings:
    # Remove /v1 suffix from base_url for native Ollama API if present
    base_url = settings.ai_base_url.replace("/v1", "").rstrip("/")
    return OllamaEmbeddings(
        base_url=base_url,
        model=settings.embedding_model,
    )


async def _embed_and_store(
    col: Any,
    chunks: list[dict[str, Any]],
    repo_id: str,
    report: Callable[[int], None],
) -> int:
    embeddings = _make_embeddings()
    batch_size = settings.rag_embedding_batch_size
    total = 0
    total_batches = max(1, -(-len(chunks) // batch_size))  # ceil division

    for batch_num, i in enumerate(range(0, len(chunks), batch_size)):
        # Filter out empty or whitespace-only chunks to prevent provider errors
        batch = [c for c in chunks[i : i + batch_size] if c["content"] and c["content"].strip()]
        if not batch:
            continue

        texts = [c["content"] for c in batch]

        raw_embeddings: list[list[float]] = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda t=texts: embeddings.embed_documents(t),
        )

        for chunk, emb in zip(batch, raw_embeddings):
            chunk["embedding"] = emb

        total += await vs.upsert_chunks(col, batch)

        pct = 15 + int(85 * (batch_num + 1) / total_batches)
        report(min(pct, 99))
        log.info("build_index: stored batch %d/%d for repo %s", batch_num + 1, total_batches, repo_id)

    return total


def _collect_files(workspace: Path):
    for dirpath, dirnames, filenames in os.walk(workspace):
        dirnames[:] = [
            d for d in dirnames
            if d not in _SKIP_DIRS and not d.startswith(".")
        ]
        for fname in filenames:
            p = Path(dirpath) / fname
            if p.suffix.lower() in _SUPPORTED_EXTENSIONS:
                yield p


def _split_file(path: Path, workspace: Path) -> list[dict[str, Any]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    if not text.strip():
        return []

    ext = path.suffix.lower()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
        separators=_LANGUAGE_SEPARATORS.get(ext, _DEFAULT_SEPARATORS),
    )

    rel_path = str(path.relative_to(workspace))
    return [
        {
            "chunk_id": _make_chunk_id(rel_path, idx, content),
            "content": content,
            "metadata": {"file_path": rel_path, "chunk_index": idx, "extension": ext},
            "embedding": [],
        }
        for idx, content in enumerate(splitter.split_text(text))
    ]


def _make_chunk_id(file_path: str, idx: int, content: str) -> str:
    return hashlib.sha256(f"{file_path}:{idx}:{content[:64]}".encode()).hexdigest()
