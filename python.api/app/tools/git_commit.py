from __future__ import annotations

import asyncio
import subprocess
from typing import Any

from ._base import BaseTool, ToolDef


class GitCommitTool(BaseTool):
    name = "git_commit"
    description = (
        "Stage files and create a git commit in the repository. "
        "Optionally stages specific paths or all tracked modified files before committing. "
        "Returns the commit hash and summary on success, or a descriptive error."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "message": {
                    "type": "string",
                    "description": "Commit message (required)",
                },
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File paths to stage with 'git add' before committing",
                },
                "all_tracked": {
                    "type": "boolean",
                    "description": "If true, run 'git add -u' to stage all modified tracked files",
                },
                "working_dir": {
                    "type": "string",
                    "description": "Git repository root (default: current directory)",
                },
                "author": {
                    "type": "string",
                    "description": "Override commit author in 'Name <email>' format",
                },
                "allow_empty": {
                    "type": "boolean",
                    "description": "Allow creating a commit even when there are no staged changes",
                },
            },
            required=["message"],
        )

    async def _run(self, args: dict[str, Any]) -> str:
        return await asyncio.to_thread(self._run_sync, args)

    def _run_sync(self, args: dict[str, Any]) -> str:
        import os
        from pathlib import Path

        message: str = args["message"]
        paths: list[str] = args.get("paths") or []
        all_tracked: bool = args.get("all_tracked") or False
        working_dir: str | None = args.get("working_dir")
        author: str | None = args.get("author")
        allow_empty: bool = args.get("allow_empty") or False

        cwd = str(Path(working_dir).resolve()) if working_dir else os.getcwd()

        def _run(cmd: list[str]) -> tuple[int, str]:
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
            return r.returncode, (r.stdout + r.stderr).strip()

        rc, out = _run(["git", "rev-parse", "--git-dir"])
        if rc != 0:
            return f"Not a git repository: {cwd}"

        if paths:
            for p in paths:
                rc, out = _run(["git", "add", "--", p])
                if rc != 0:
                    return f"git add failed for '{p}':\n{out}"
        elif all_tracked:
            rc, out = _run(["git", "add", "-u"])
            if rc != 0:
                return f"git add -u failed:\n{out}"

        commit_cmd = ["git", "commit", "-m", message]
        if author:
            commit_cmd += ["--author", author]
        if allow_empty:
            commit_cmd.append("--allow-empty")

        rc, out = _run(commit_cmd)
        if rc != 0:
            if "nothing to commit" in out or "nothing added to commit" in out:
                return f"Nothing to commit — working tree is clean.\n{out}"
            return f"git commit failed (exit {rc}):\n{out}"

        return f"Commit created:\n{out}"
