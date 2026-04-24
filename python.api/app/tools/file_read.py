from __future__ import annotations

import asyncio
import base64
import json
from pathlib import Path
from typing import Any

from ._base import BaseTool, ToolDef

_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico"}
_MIME = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml",
    ".bmp": "image/bmp", ".ico": "image/x-icon",
}


def _read_pdf(path: Path, pages: str | None) -> str:
    try:
        import pypdf
    except ImportError:
        return "pypdf not installed."
    reader = pypdf.PdfReader(str(path))
    total = len(reader.pages)
    if pages:
        parts = pages.split("-")
        start = max(0, int(parts[0]) - 1)
        end = int(parts[1]) if len(parts) > 1 else start + 1
        rng = range(start, min(end, total))
    else:
        rng = range(total)
    return "\n\n".join(
        reader.pages[i].extract_text() or f"[Page {i+1}: no text]" for i in rng
    )


def _read_notebook(path: Path) -> str:
    nb = json.loads(path.read_text(encoding="utf-8"))
    chunks = []
    for i, cell in enumerate(nb.get("cells", [])):
        src = cell.get("source", "")
        if isinstance(src, list):
            src = "".join(src)
        chunks.append(f"# Cell {i} [{cell.get('cell_type','code')}]\n{src}")
    return "\n\n".join(chunks)


class FileReadTool(BaseTool):
    name = "file_read"
    description = (
        "Read a file from the filesystem. Supports text, images (returns base64 data URI), "
        "PDFs (with optional page ranges), and Jupyter notebooks."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "file_path": {"type": "string", "description": "Absolute path to the file"},
                "offset": {"type": "integer", "description": "1-based line number to start reading"},
                "limit": {"type": "integer", "description": "Maximum number of lines to return"},
                "pages": {"type": "string", "description": "PDF page range, e.g. '1-5'"},
            },
            required=["file_path"],
        )

    async def _run(self, args: dict[str, Any]) -> Any:
        file_path = args.get("file_path") or args.get("path") or args.get("file") or ""
        if not file_path:
            raise ValueError("file_path is required")
        path = Path(file_path)
        if not path.is_absolute() and self.working_dir:
            path = Path(self.working_dir) / file_path

        if not path.exists():
            # Try to find the file by name anywhere in the working directory
            if self.working_dir:
                matches = list(Path(self.working_dir).rglob(path.name))
                if matches:
                    path = matches[0]
                else:
                    raise FileNotFoundError(
                        f"File '{path.name}' not found anywhere in {self.working_dir}"
                    )
            else:
                raise FileNotFoundError(f"File not found: {path}")
        suffix = path.suffix.lower()
        if suffix in _IMAGE_EXT:
            raw = await asyncio.to_thread(path.read_bytes)
            mime = _MIME.get(suffix, "image/octet-stream")
            return f"data:{mime};base64,{base64.b64encode(raw).decode()}"
        if suffix == ".pdf":
            return await asyncio.to_thread(_read_pdf, path, args.get("pages"))
        if suffix == ".ipynb":
            return await asyncio.to_thread(_read_notebook, path)
        text: str = await asyncio.to_thread(
            lambda: path.read_text(encoding="utf-8", errors="replace")
        )
        lines = text.splitlines(keepends=True)
        offset = max(0, (args.get("offset") or 1) - 1)
        lines = lines[offset:]
        limit = args.get("limit")
        if limit is not None:
            lines = lines[:limit]
        return "".join(lines)
