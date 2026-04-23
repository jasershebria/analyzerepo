from __future__ import annotations

import os
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any

from ._base import BaseTool, ToolDef
from . import _state


class EnterWorktreeTool(BaseTool):
    name = "enter_worktree"
    description = (
        "Create an isolated git worktree and switch the session into it. "
        "Useful for making changes on a separate branch without affecting the main working tree."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "name": {
                    "type": "string",
                    "description": "Optional slug for the worktree branch (alphanumeric, dashes, dots)",
                }
            },
        )

    async def _run(self, args: dict[str, Any]) -> dict:
        import asyncio
        return await asyncio.to_thread(self._run_sync, args)

    def _run_sync(self, args: dict[str, Any]) -> dict:
        if _state.WORKTREE is not None:
            raise ValueError(f"Already in worktree at {_state.WORKTREE['path']}")

        # Find git root
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError("Not inside a git repository")
        git_root = result.stdout.strip()

        slug = args.get("name") or f"worktree-{uuid.uuid4().hex[:8]}"
        branch = f"claude-worktree/{slug}"
        worktree_path = os.path.join(tempfile.gettempdir(), slug)

        subprocess.run(
            ["git", "worktree", "add", "-b", branch, worktree_path],
            cwd=git_root, check=True,
        )

        original_cwd = os.getcwd()
        os.chdir(worktree_path)
        _state.WORKTREE = {
            "path": worktree_path,
            "branch": branch,
            "original_cwd": original_cwd,
        }
        return {
            "path": worktree_path,
            "branch": branch,
            "message": f"Switched to worktree at {worktree_path} (branch: {branch})",
        }
