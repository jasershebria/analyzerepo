from __future__ import annotations

import asyncio
import glob as _glob
import os
from pathlib import Path
from typing import Any

from ._base import BaseTool, ToolDef


class GlobTool(BaseTool):
    name = "glob"
    description = (
        "Find files matching a glob pattern (e.g. '**/*.py'). "
        "Returns matching paths sorted by modification time."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "pattern": {"type": "string", "description": "Glob pattern, e.g. '**/*.ts'"},
                "path": {"type": "string", "description": "Root directory to search (default: cwd)"},
            },
            required=["pattern"],
        )

    async def _run(self, args: dict[str, Any]) -> list[str]:
        pattern: str = args["pattern"]
        root: str = args.get("path") or os.getcwd()

        def _search() -> list[str]:
            base = Path(root)
            matches = list(base.glob(pattern))
            # Also try absolute glob pattern
            if not matches and not pattern.startswith("**"):
                matches = [Path(p) for p in _glob.glob(pattern, recursive=True)]
            matches.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
            return [str(p) for p in matches[:100]]

        return await asyncio.to_thread(_search)
