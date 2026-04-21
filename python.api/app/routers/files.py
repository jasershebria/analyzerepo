from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import settings
from app.core.routing import CamelCaseRoute

router = APIRouter(prefix="/files", tags=["Files"], route_class=CamelCaseRoute)

_ALLOWED_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx", ".py", ".cs", ".go", ".java", ".rs",
    ".html", ".css", ".scss", ".sass", ".json", ".yaml", ".yml",
    ".toml", ".md", ".swift", ".kt", ".dart", ".env.example", ".txt",
}

_SKIP_DIRS = {
    "node_modules", ".git", "bin", "obj", "dist", "build",
    ".angular", "__pycache__", ".venv", "venv", ".vs", ".idea",
}


@router.get("/read", summary="Read a specific file from the local codebase")
async def read_file(path: str = Query(..., description="Relative or absolute file path")) -> dict:
    base = Path(settings.git_clone_base_path).resolve()
    target = (base / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()

    # Safety: only read files inside the configured base path or exact absolute paths on local disk
    if target.suffix.lower() not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type '{target.suffix}' is not allowed.")

    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {target}")

    try:
        content = target.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {"path": str(target), "content": content}


@router.get("/find", summary="Find a file by name anywhere in the local workspace and return its content")
async def find_file(name: str = Query(..., description="Filename to search for, e.g. App.tsx")) -> dict:
    base = Path(settings.git_clone_base_path).resolve()
    if not base.exists():
        raise HTTPException(status_code=404, detail=f"Workspace '{base}' not found.")

    name_lower = name.lower()
    for dirpath, dirnames, filenames in base.walk() if hasattr(base, "walk") else _os_walk(base):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
        for fname in filenames:
            if fname.lower() == name_lower:
                target = Path(dirpath) / fname
                if target.suffix.lower() not in _ALLOWED_EXTENSIONS:
                    continue
                try:
                    content = target.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue
                return {"path": str(target), "content": content}

    raise HTTPException(status_code=404, detail=f"File '{name}' not found in workspace.")


def _os_walk(root: Path):
    import os
    for dirpath, dirnames, filenames in os.walk(root):
        yield Path(dirpath), dirnames, filenames


@router.get("/tree", summary="Get the file tree of the local codebase")
async def file_tree(max_depth: int = Query(default=4, ge=1, le=8)) -> dict:
    base = Path(settings.git_clone_base_path).resolve()
    if not base.exists():
        raise HTTPException(status_code=404, detail=f"Path '{base}' not found.")
    return {"tree": _build_tree(base, max_depth)}


def _build_tree(root: Path, max_depth: int, depth: int = 0) -> list[dict]:
    if depth > max_depth:
        return []
    result = []
    try:
        entries = sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name))
    except PermissionError:
        return []
    for entry in entries:
        if entry.name in _SKIP_DIRS or entry.name.startswith("."):
            continue
        node: dict = {"name": entry.name, "path": str(entry), "type": "file" if entry.is_file() else "dir"}
        if entry.is_dir():
            node["children"] = _build_tree(entry, max_depth, depth + 1)
        result.append(node)
    return result
