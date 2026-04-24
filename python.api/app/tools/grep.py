from __future__ import annotations

import fnmatch
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from ._base import BaseTool, ToolDef


class GrepTool(BaseTool):
    name = "grep"
    description = (
        "Search file contents with a regex pattern using ripgrep (fallback: Python re). "
        "Supports context lines, case-insensitive, multiline, and multiple output modes."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "pattern": {"type": "string", "description": "Regular expression pattern"},
                "path": {"type": "string", "description": "File or directory to search"},
                "glob": {"type": "string", "description": "Glob filter, e.g. '*.py'"},
                "output_mode": {
                    "type": "string",
                    "enum": ["content", "files_with_matches", "count"],
                    "description": "Output format (default: files_with_matches)",
                },
                "context": {"type": "integer", "description": "Lines before and after each match (-C)"},
                "before_context": {"type": "integer", "description": "Lines before each match (-B)"},
                "after_context": {"type": "integer", "description": "Lines after each match (-A)"},
                "show_line_numbers": {
                    "type": "boolean",
                    "description": "Show line numbers in content mode (default true)",
                },
                "case_insensitive": {"type": "boolean", "description": "Case-insensitive search"},
                "multiline": {"type": "boolean", "description": "Allow patterns to span multiple lines"},
                "file_type": {"type": "string", "description": "ripgrep file type, e.g. 'py', 'js'"},
                "head_limit": {
                    "type": "integer",
                    "description": "Limit output to first N lines (default 250, 0 = unlimited)",
                },
                "offset": {"type": "integer", "description": "Skip first N results"},
            },
            required=["pattern"],
        )

    async def _run(self, args: dict[str, Any]) -> Any:
        import asyncio
        return await asyncio.to_thread(self._run_sync, args)

    def _run_sync(self, args: dict[str, Any]) -> Any:
        try:
            return self._rg(args)
        except (FileNotFoundError, subprocess.SubprocessError):
            return self._fallback(args)

    def _rg(self, args: dict[str, Any]) -> Any:
        mode = args.get("output_mode", "files_with_matches")
        cmd = ["rg"]
        if mode == "count":
            cmd.append("--count")
        elif mode == "files_with_matches":
            cmd.append("--files-with-matches")
        else:
            if args.get("show_line_numbers", True):
                cmd.append("-n")
        if args.get("case_insensitive"):
            cmd.append("-i")
        if args.get("multiline"):
            cmd += ["-U", "--multiline-dotall"]
        if args.get("context") is not None:
            cmd += ["-C", str(args["context"])]
        if args.get("before_context") is not None:
            cmd += ["-B", str(args["before_context"])]
        if args.get("after_context") is not None:
            cmd += ["-A", str(args["after_context"])]
        if args.get("glob"):
            cmd += ["--glob", args["glob"]]
        if args.get("file_type"):
            cmd += ["--type", args["file_type"]]
        cmd.append(args["pattern"])
        if args.get("path"):
            cmd.append(args["path"])

        result = subprocess.run(cmd, capture_output=True, timeout=30)
        raw = result.stdout.decode(errors="replace")
        lines = raw.splitlines()

        offset = args.get("offset") or 0
        if offset:
            lines = lines[offset:]

        if mode == "files_with_matches":
            return lines
        if mode == "count":
            counts: dict[str, int] = {}
            for line in lines:
                if ":" in line:
                    f, _, c = line.rpartition(":")
                    try:
                        counts[f] = int(c)
                    except ValueError:
                        pass
            return counts
        return "\n".join(lines)

    def _fallback(self, args: dict[str, Any]) -> Any:
        mode = args.get("output_mode", "files_with_matches")
        flags = re.MULTILINE
        if args.get("case_insensitive"):
            flags |= re.IGNORECASE
        if args.get("multiline"):
            flags |= re.DOTALL
        try:
            pattern = re.compile(args["pattern"], flags)
        except re.error as exc:
            return f"Invalid regex: {exc}"

        root = args.get("path") or "."
        glob_pat = args.get("glob") or "*"
        matched_files: list[str] = []
        content_lines: list[str] = []
        counts: dict[str, int] = {}

        for dirpath, _, filenames in os.walk(root):
            if any(p in {".git", ".svn", ".hg"} for p in Path(dirpath).parts):
                continue
            for fn in filenames:
                if not fnmatch.fnmatch(fn, glob_pat):
                    continue
                fp = os.path.join(dirpath, fn)
                try:
                    text = Path(fp).read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                if not pattern.search(text):
                    continue
                matched_files.append(fp)
                counts[fp] = len(pattern.findall(text))
                if mode == "content":
                    show_n = args.get("show_line_numbers", True)
                    for lineno, line in enumerate(text.splitlines(), 1):
                        if pattern.search(line):
                            content_lines.append(
                                f"{fp}:{lineno}:{line}" if show_n else f"{fp}:{line}"
                            )

        offset = args.get("offset") or 0

        if mode == "files_with_matches":
            return matched_files[offset:]
        if mode == "count":
            return dict(list(counts.items())[offset:])
        return "\n".join(content_lines[offset:])
