from __future__ import annotations

import subprocess
from typing import Any

from ._base import BaseTool, ToolDef



class BashTool(BaseTool):
    name = "bash"
    description = (
        "Execute a bash shell command. Returns combined stdout + stderr. "
        "Use run_in_background=true for fire-and-forget commands."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "command": {"type": "string", "description": "Shell command to run"},
                "description": {
                    "type": "string",
                    "description": "Short description of what the command does",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in milliseconds (default 120000, max 600000)",
                },
                "run_in_background": {
                    "type": "boolean",
                    "description": "Launch detached process; returns PID immediately",
                },
            },
            required=["command"],
        )

    async def _run(self, args: dict[str, Any]) -> str:
        import asyncio
        return await asyncio.to_thread(self._run_sync, args)

    def _run_sync(self, args: dict[str, Any]) -> str:
        command: str = args["command"]
        timeout_ms: int = min(args.get("timeout") or 120_000, 600_000)
        timeout_s: float = timeout_ms / 1000

        if args.get("run_in_background"):
            proc = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                cwd=self.working_dir,
            )
            return f"Started in background (PID={proc.pid})"

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                timeout=timeout_s,
                cwd=self.working_dir,
            )
            output = (result.stdout + result.stderr).decode(errors="replace")
            return output or "(no output)"
        except subprocess.TimeoutExpired:
            return f"Command timed out after {timeout_s:.0f}s"
