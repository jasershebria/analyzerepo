from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from ._base import BaseTool, ToolDef


class FileWriteTool(BaseTool):
    name = "file_write"
    description = "Create a new file or completely overwrite an existing file with the given content."

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "file_path": {"type": "string", "description": "Absolute path to the file"},
                "content": {"type": "string", "description": "Content to write"},
            },
            required=["file_path", "content"],
        )

    async def _run(self, args: dict[str, Any]) -> str:
        path = Path(args["file_path"])
        content: str = args["content"]
        await asyncio.to_thread(
            lambda: (
                path.parent.mkdir(parents=True, exist_ok=True),
                path.write_text(content, encoding="utf-8"),
            )
        )
        return f"Written {len(content.encode())} bytes to {args['file_path']}"
