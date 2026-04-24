from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from ._base import BaseTool, ToolDef


class FileEditTool(BaseTool):
    name = "file_edit"
    description = (
        "Replace a specific string inside a file. old_string must match exactly "
        "(including whitespace and indentation)."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "file_path": {"type": "string", "description": "Absolute path to the file"},
                "old_string": {"type": "string", "description": "Exact text to find and replace"},
                "new_string": {"type": "string", "description": "Replacement text"},
                "replace_all": {
                    "type": "boolean",
                    "description": "Replace every occurrence (default false)",
                },
            },
            required=["file_path", "old_string", "new_string"],
        )

    async def _run(self, args: dict[str, Any]) -> str:
        fp = args.get("file_path") or args.get("path") or args.get("file") or ""
        if not fp:
            raise ValueError("file_path is required")
        path = Path(fp)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        old: str = args.get("old_string") or args.get("old") or args.get("search") or ""
        new: str = args.get("new_string") or args.get("new") or args.get("replacement") or ""
        if not old:
            raise ValueError("old_string is required")
        replace_all: bool = args.get("replace_all", False)

        text: str = await asyncio.to_thread(
            lambda: path.read_text(encoding="utf-8", errors="replace")
        )
        if old not in text:
            raise ValueError(
                f"old_string not found in {args['file_path']}. "
                "Ensure you are using the exact text from the file."
            )
        count = text.count(old) if replace_all else 1
        new_text = text.replace(old, new) if replace_all else text.replace(old, new, 1)
        await asyncio.to_thread(lambda: path.write_text(new_text, encoding="utf-8"))
        return f"Edited {args['file_path']} ({count} replacement{'s' if count != 1 else ''})"
