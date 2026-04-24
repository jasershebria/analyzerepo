from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from app.core.config import settings

log = logging.getLogger(__name__)


class GitCloneService:
    def __init__(self) -> None:
        self._base_path = Path(settings.git_clone_base_path)

    async def clone_or_update(
        self,
        repo_url: str,
        token: str | None = None,
        branch: str | None = None,
        repo_id: str | None = None,
    ) -> str:
        local_path = self._derive_local_path(repo_url)
        git_dir = local_path / ".git"

        if git_dir.exists():
            await self._run_git(local_path, ["fetch", "--prune"])
            target = branch or await self._get_default_branch(local_path)
            await self._run_git(local_path, ["reset", "--hard", f"origin/{target}"])
            is_fresh = False
        else:
            local_path.mkdir(parents=True, exist_ok=True)
            auth_url = self._build_auth_url(repo_url, token)
            args = (
                ["clone", "--branch", branch, "--single-branch", auth_url, str(local_path)]
                if branch
                else ["clone", auth_url, str(local_path)]
            )
            parent = local_path.parent
            await self._run_git(parent, args)
            is_fresh = True

        if repo_id:
            await self._index(str(local_path), repo_id, clear_existing=is_fresh)

        return str(local_path)

    @staticmethod
    async def _index(workspace_path: str, repo_id: str, *, clear_existing: bool) -> None:
        try:
            from app.rag.indexing import build_index
            stats = await build_index(workspace_path=workspace_path, repo_id=repo_id, clear_existing=clear_existing)
            log.info("RAG index built for %s: %s", repo_id, stats)
        except Exception:
            log.exception("RAG indexing failed for %s — continuing without index", repo_id)

    def _derive_local_path(self, repo_url: str) -> Path:
        uri = urlparse(repo_url.rstrip("/"))
        segments = uri.path.strip("/").rstrip("/")
        if segments.endswith(".git"):
            segments = segments[:-4]
        return self._base_path / uri.hostname / Path(segments)

    @staticmethod
    def _build_auth_url(repo_url: str, token: str | None) -> str:
        if not token:
            return repo_url
        uri = urlparse(repo_url)
        return f"{uri.scheme}://{token}@{uri.hostname}{uri.path}"

    async def _get_default_branch(self, repo_path: Path) -> str:
        result = await self._run_git_capture(repo_path, ["symbolic-ref", "refs/remotes/origin/HEAD"])
        return result.strip().split("/")[-1]

    @staticmethod
    async def _run_git(work_dir: Path, args: list[str]) -> None:
        proc = await asyncio.create_subprocess_exec(
            "git",
            *args,
            cwd=str(work_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed: {stderr.decode()}")

    @staticmethod
    async def _run_git_capture(work_dir: Path, args: list[str]) -> str:
        proc = await asyncio.create_subprocess_exec(
            "git",
            *args,
            cwd=str(work_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        return stdout.decode()
