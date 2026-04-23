from __future__ import annotations

import shutil
import subprocess
from typing import Any

from ._base import BaseTool, ToolDef

_MAX_OUTPUT = 30_000


def _ps_exe() -> str:
    for candidate in ("pwsh", "powershell"):
        if shutil.which(candidate):
            return candidate
    return "powershell"


class PowerShellTool(BaseTool):
    name = "powershell"
    description = (
        "Execute a Windows PowerShell command. Returns combined stdout + stderr. "
        "Uses pwsh (PowerShell 7) if available, falls back to powershell.exe."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "command": {"type": "string", "description": "PowerShell command to run"},
                "description": {"type": "string", "description": "Short description"},
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in milliseconds (default 120000)",
                },
                "run_in_background": {
                    "type": "boolean",
                    "description": "Launch detached; returns PID immediately",
                },
            },
            required=["command"],
        )

    async def _run(self, args: dict[str, Any]) -> str:
        import asyncio
        return await asyncio.to_thread(self._run_sync, args)

    def _run_sync(self, args: dict[str, Any]) -> str:
        command: str = args["command"]
        timeout_s = (args.get("timeout") or 120_000) / 1000
        exe = _ps_exe()

        if args.get("run_in_background"):
            proc = subprocess.Popen(
                [exe, "-NonInteractive", "-Command", command],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return f"Started in background (PID={proc.pid})"

        try:
            result = subprocess.run(
                [exe, "-NonInteractive", "-Command", command],
                capture_output=True,
                timeout=timeout_s,
            )
            output = (result.stdout + result.stderr).decode(errors="replace")
            if len(output) > _MAX_OUTPUT:
                output = output[:_MAX_OUTPUT] + f"\n[...truncated at {_MAX_OUTPUT} chars]"
            return output or "(no output)"
        except subprocess.TimeoutExpired:
            return f"Command timed out after {timeout_s:.0f}s"
