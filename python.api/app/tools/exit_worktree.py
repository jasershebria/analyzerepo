from __future__ import annotations

import os
import subprocess
from typing import Any

from ._base import BaseTool, ToolDef
from . import _state


class ExitWorktreeTool(BaseTool):
    name = "exit_worktree"
    description = (
        "Exit the current git worktree and return to the main repository. "
        "Use action='keep' to preserve the branch, 'remove' to clean up."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "action": {
                    "type": "string",
                    "enum": ["keep", "remove"],
                    "description": "Whether to keep or remove the worktree after exiting",
                },
                "discard_changes": {
                    "type": "boolean",
                    "description": "Required when removing a worktree that has uncommitted changes",
                },
            },
            required=["action"],
        )

    async def _run(self, args: dict[str, Any]) -> str:
        import asyncio
        return await asyncio.to_thread(self._run_sync, args)

    def _run_sync(self, args: dict[str, Any]) -> str:
        if _state.WORKTREE is None:
            raise ValueError("Not currently in a worktree")

        wt = _state.WORKTREE
        action: str = args["action"]
        discard: bool = args.get("discard_changes", False)

        # Restore original cwd
        original_cwd = wt["original_cwd"]
        os.chdir(original_cwd)
        _state.WORKTREE = None

        if action == "remove":
            cmd = ["git", "worktree", "remove", wt["path"]]
            if discard:
                cmd.append("--force")
            result = subprocess.run(cmd, cwd=original_cwd, capture_output=True, text=True)
            if result.returncode != 0:
                return (
                    f"Returned to {original_cwd} but failed to remove worktree: {result.stderr}. "
                    "Use discard_changes=true to force removal."
                )
            return f"Worktree {wt['path']} removed. Back at {original_cwd}"

        return f"Exited worktree (kept branch '{wt['branch']}'). Back at {original_cwd}"
