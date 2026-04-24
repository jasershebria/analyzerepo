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
        "Returns matching paths as a directory tree."
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
        root: str = args.get("path") or self.working_dir or os.getcwd()

        def _search() -> list[str]:
            base = Path(root)
            matches = list(base.glob(pattern))
            if not matches and not pattern.startswith("**"):
                matches = [Path(p) for p in _glob.glob(pattern, recursive=True)]
            matches.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
            return [str(p) for p in matches]

        return await asyncio.to_thread(_search)

    async def call(self, args: dict[str, Any]) -> str:
        print(f"DEBUG: Tool Fired: {self.name}({args})")
        paths = await self._run(args)
        if not paths:
            return "No files found."
        root = args.get("path") or self.working_dir or os.getcwd()
        return _format_tree(paths, root)


def _format_tree(paths: list[str], root: str) -> str:
    """Render a flat list of absolute paths as an ASCII directory tree."""
    root_path = Path(root)

    # Build nested dict: {"dir": {"subdir": {"file.py": None}}}
    tree: dict = {}
    for p in paths:
        try:
            rel = Path(p).relative_to(root_path)
        except ValueError:
            rel = Path(p)
        parts = rel.parts
        node = tree
        for part in parts:
            node = node.setdefault(part, {})

    lines: list[str] = [root_path.name + "/"]
    _render(tree, lines, prefix="")
    return "\n".join(lines)


def _render(node: dict, lines: list[str], prefix: str) -> None:
    entries = sorted(node.keys(), key=lambda k: (not node[k], k.lower()))
    for i, name in enumerate(entries):
        is_last = i == len(entries) - 1
        connector = "└── " if is_last else "├── "
        child = node[name]
        label = name + ("/" if child else "")
        lines.append(prefix + connector + label)
        if child:
            extension = "    " if is_last else "│   "
            _render(child, lines, prefix + extension)
