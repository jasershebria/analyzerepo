"""Indexing pipeline: source files → LangChain Documents → embeddings → MongoDB.

Usage:
    indexer = CodebaseIndexer(repo_id="<uuid>")
    stats = await indexer.index("/path/to/workspace")
    await indexer.close()
"""
from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.rag.mongo_store import MongoVectorStore

log = logging.getLogger(__name__)

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


class CodebaseIndexer:
    """Loads all source files in a workspace, splits them into LangChain Documents,
    and stores them in MongoDB via MongoVectorStore (which handles embedding)."""

    def __init__(self, repo_id: str) -> None:
        self._repo_id = repo_id
        self._store = MongoVectorStore(repo_id)

    async def index(self, workspace_path: str | Path, clear_existing: bool = False) -> dict[str, Any]:
        """Index all code files in workspace_path.

        Args:
            workspace_path: Root directory of the cloned repository.
            clear_existing: Drop and rebuild the collection if True.

        Returns:
            Dict with files_indexed, chunks_created, chunks_upserted.
        """
        workspace = Path(workspace_path)
        if not workspace.exists():
            raise ValueError(f"Workspace not found: {workspace}")

        if clear_existing:
            await self._store.clear()

        await self._store.ensure_indexes()

        files = list(_collect_files(workspace))
        log.info("Indexing %d files for repo %s", len(files), self._repo_id)

        all_docs: list[Document] = []
        for path in files:
            all_docs.extend(_split_file(path, workspace))

        log.info("Generated %d chunks from %d files", len(all_docs), len(files))

        total_upserted = await self._store.add_documents(all_docs)

        return {
            "repo_id": self._repo_id,
            "files_indexed": len(files),
            "chunks_created": len(all_docs),
            "chunks_upserted": total_upserted,
        }

    async def close(self) -> None:
        await self._store.close()


# ------------------------------------------------------------------
# File collection + splitting helpers
# ------------------------------------------------------------------

def _collect_files(workspace: Path):
    """Walk workspace, yield all files with supported extensions."""
    for dirpath, dirnames, filenames in os.walk(workspace):
        dirnames[:] = [
            d for d in dirnames
            if d not in _SKIP_DIRS and not d.startswith(".")
        ]
        for fname in filenames:
            p = Path(dirpath) / fname
            if p.suffix.lower() in _SUPPORTED_EXTENSIONS:
                yield p


def _split_file(path: Path, workspace: Path) -> list[Document]:
    """Read a file and return a list of LangChain Documents (without embeddings)."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    if not text.strip():
        return []

    ext = path.suffix.lower()
    separators = _LANGUAGE_SEPARATORS.get(ext, _DEFAULT_SEPARATORS)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
        separators=separators,
    )

    rel_path = str(path.relative_to(workspace))
    raw_chunks = splitter.split_text(text)

    return [
        Document(
            page_content=content,
            metadata={
                "chunk_id": _chunk_id(rel_path, idx, content),
                "file_path": rel_path,
                "chunk_index": idx,
                "extension": ext,
            },
        )
        for idx, content in enumerate(raw_chunks)
    ]


def _chunk_id(file_path: str, idx: int, content: str) -> str:
    key = f"{file_path}:{idx}:{content[:64]}"
    return hashlib.sha256(key.encode()).hexdigest()
