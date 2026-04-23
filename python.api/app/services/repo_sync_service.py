from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import uuid
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.repository import Repository

log = logging.getLogger(__name__)

_SKIP_DIRS = {
    "node_modules", ".git", "bin", "obj", "dist", "build",
    ".angular", "__pycache__", ".venv", "venv", ".vs", ".idea",
    "coverage", "migrations", "Migrations",
}

_CODE_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx", ".py", ".cs", ".go",
    ".java", ".rs", ".html", ".css", ".scss", ".swift", ".kt", ".dart",
}


class RepoSyncService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def sync(self, repo_id: uuid.UUID) -> dict:
        repo = await self._get_repo(repo_id)
        token = repo.auth.secret_ref if repo.auth else None
        clone_url = repo.clone_url or repo.web_url
        auth_url = _build_auth_url(clone_url, token)
        masked_url = _mask_url(auth_url)
        workspace = Path(settings.git_clone_base_path)

        try:
            if (workspace / ".git").exists():
                # Already a git repo — pull latest
                log.info("Pulling repo at %s", workspace)
                code, out, err = await _run("git", ["pull", "--rebase"], cwd=workspace)
                if code != 0:
                    return {"status": "error", "workspacePath": str(workspace), "message": f"git pull failed: {err}", "repoUrl": masked_url}
                changed = "Already up to date" not in out
                return {"status": "updated" if changed else "unchanged", "workspacePath": str(workspace), "message": out.strip(), "repoUrl": masked_url}

            elif workspace.exists():
                # Directory exists without .git — files are already present locally
                log.info("Workspace %s exists (no .git), skipping clone", workspace)
                return {"status": "unchanged", "workspacePath": str(workspace), "message": "Workspace already exists locally.", "repoUrl": masked_url}

            else:
                # Fresh clone — let git create the directory itself
                log.info("Cloning %s → %s", masked_url, workspace)
                workspace.parent.mkdir(parents=True, exist_ok=True)
                code, out, err = await _run("git", ["clone", auth_url, str(workspace)], cwd=workspace.parent)
                if code != 0:
                    # Clean up empty dir git may have created before failing
                    if workspace.exists() and not any(workspace.iterdir()):
                        workspace.rmdir()
                    return {"status": "error", "workspacePath": str(workspace), "message": f"git clone failed: {err}", "repoUrl": masked_url}
                return {"status": "cloned", "workspacePath": str(workspace), "message": "Repository cloned successfully.", "repoUrl": masked_url}

        except Exception as exc:
            log.exception("Sync error")
            return {"status": "error", "workspacePath": str(workspace), "message": str(exc), "repoUrl": masked_url}

    async def analyze(self, repo_id: uuid.UUID) -> dict:
        repo = await self._get_repo(repo_id)
        workspace = Path(settings.git_clone_base_path)

        if not workspace.exists():
            raise ValueError(f"Workspace '{workspace}' does not exist. Run sync first.")

        file_tree: list[str] = []
        lang_count: dict[str, int] = defaultdict(int)
        all_files: list[Path] = []

        for dirpath, dirnames, filenames in os.walk(workspace):
            dirnames[:] = sorted(d for d in dirnames if d not in _SKIP_DIRS and not d.startswith("."))
            rel_dir = Path(dirpath).relative_to(workspace)
            if rel_dir != Path("."):
                file_tree.append(str(rel_dir).replace("\\", "/") + "/")
            for fname in sorted(filenames):
                p = Path(dirpath) / fname
                file_tree.append(str(rel_dir / fname).replace("\\", "/"))
                ext = p.suffix.lower()
                if ext in _CODE_EXTENSIONS:
                    lang_count[ext] += 1
                    all_files.append(p)

        insights = _build_insights(workspace, all_files)

        return {
            "repoUrl": _mask_url(repo.clone_url or repo.web_url),
            "workspacePath": str(workspace),
            "totalFiles": len(file_tree),
            "fileTree": file_tree,
            "languages": dict(lang_count),
            "insights": insights,
        }

    async def _get_repo(self, repo_id: uuid.UUID) -> Repository:
        row = (await self._db.execute(
            select(Repository).where(Repository.id == repo_id, Repository.is_deleted.is_(False))
        )).scalar_one_or_none()
        if row is None:
            raise KeyError(f"Repository '{repo_id}' not found.")
        return row


def _build_insights(workspace: Path, files: list[Path]) -> list[dict]:
    insights: list[dict] = []

    insights.append({"category": "structure", "title": "Total code files", "detail": f"{len(files)} source files found."})

    pkg_json = workspace / "package.json"
    if pkg_json.exists():
        try:
            import json
            pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            frameworks = [k for k in deps if k in ("react", "react-native", "vue", "@angular/core", "next", "expo")]
            if frameworks:
                insights.append({"category": "framework", "title": "Detected framework(s)", "detail": ", ".join(frameworks)})
        except Exception:
            pass

    src = workspace / "src"
    if src.exists():
        features = [d.name for d in src.iterdir() if d.is_dir() and d.name not in _SKIP_DIRS]
        if features:
            insights.append({"category": "architecture", "title": "Top-level source folders", "detail": ", ".join(sorted(features))})

    api_files = [f for f in files if any(k in f.stem.lower() for k in ("api", "route", "controller", "endpoint", "service"))]
    if api_files:
        insights.append({"category": "api", "title": "Likely API / service files", "detail": "\n".join(str(f.relative_to(workspace)) for f in api_files[:20])})

    return insights


def _build_auth_url(clone_url: str, token: str | None) -> str:
    if not token:
        return clone_url
    u = urlparse(clone_url)
    return f"{u.scheme}://{token}@{u.netloc}{u.path}"


def _mask_url(url: str) -> str:
    u = urlparse(url)
    if u.password:
        return url.replace(u.password, "***")
    return url


async def _run(cmd: str, args: list[str], cwd: Path) -> tuple[int, str, str]:
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: subprocess.run(
            [cmd, *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            errors="replace",
        ),
    )
    return result.returncode, result.stdout, result.stderr
