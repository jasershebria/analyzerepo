from __future__ import annotations

import asyncio
import shutil
import subprocess
from typing import Any

from ._base import BaseTool, ToolDef

_MAX_OUTPUT = 50_000


class RunTestsTool(BaseTool):
    name = "run_tests"
    description = (
        "Run the project's test suite using pytest, unittest, npm test, cargo test, or go test. "
        "Auto-detects the runner from project files (pyproject.toml, package.json, Cargo.toml, go.mod). "
        "Returns combined stdout + stderr with a PASSED/FAILED status prefix."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "working_dir": {
                    "type": "string",
                    "description": "Directory to run tests from (default: current directory)",
                },
                "test_path": {
                    "type": "string",
                    "description": "Specific test file, directory, or node ID (e.g. 'tests/test_api.py::test_health')",
                },
                "runner": {
                    "type": "string",
                    "enum": ["pytest", "unittest", "npm", "cargo", "go", "auto"],
                    "description": "Test runner to use (default: auto-detect from project files)",
                },
                "extra_args": {
                    "type": "string",
                    "description": "Additional arguments passed directly to the test runner",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in milliseconds (default: 120000)",
                },
            },
            required=[],
        )

    async def _run(self, args: dict[str, Any]) -> str:
        return await asyncio.to_thread(self._run_sync, args)

    def _run_sync(self, args: dict[str, Any]) -> str:
        import os
        from pathlib import Path

        working_dir: str | None = args.get("working_dir")
        test_path: str | None = args.get("test_path")
        runner: str = args.get("runner") or "auto"
        extra_args: str = args.get("extra_args") or ""
        timeout_ms: int = args.get("timeout") or 120_000
        timeout_s: float = timeout_ms / 1000

        cwd = str(Path(working_dir).resolve()) if working_dir else os.getcwd()

        if runner == "auto":
            runner = self._detect_runner(cwd)

        cmd = self._build_command(runner, test_path, extra_args)

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                timeout=timeout_s,
                cwd=cwd,
            )
            output = (result.stdout + result.stderr).decode(errors="replace")
            exit_code = result.returncode
        except subprocess.TimeoutExpired:
            return f"Test run timed out after {timeout_s:.0f}s"
        except Exception as exc:
            return f"Failed to run tests: {exc}"

        if len(output) > _MAX_OUTPUT:
            output = output[:_MAX_OUTPUT] + f"\n[...truncated at {_MAX_OUTPUT} chars]"

        status = "PASSED" if exit_code == 0 else f"FAILED (exit code {exit_code})"
        return f"[{status}]\n{output}" if output.strip() else f"[{status}] (no output)"

    def _detect_runner(self, cwd: str) -> str:
        from pathlib import Path
        p = Path(cwd)
        if (p / "pyproject.toml").exists() or (p / "pytest.ini").exists() or (p / "setup.cfg").exists():
            return "pytest"
        if (p / "setup.py").exists():
            return "pytest"
        if (p / "package.json").exists():
            return "npm"
        if (p / "Cargo.toml").exists():
            return "cargo"
        if (p / "go.mod").exists():
            return "go"
        if shutil.which("pytest"):
            return "pytest"
        return "unittest"

    def _build_command(self, runner: str, test_path: str | None, extra_args: str) -> str:
        parts: list[str]
        if runner == "pytest":
            parts = ["pytest", "-v"]
            if test_path:
                parts.append(test_path)
        elif runner == "unittest":
            parts = ["python", "-m", "unittest"]
            if test_path:
                parts.append(test_path)
            else:
                parts.append("discover")
        elif runner == "npm":
            parts = ["npm", "test", "--"]
            if test_path:
                parts.append(test_path)
        elif runner == "cargo":
            parts = ["cargo", "test"]
            if test_path:
                parts.append(test_path)
        elif runner == "go":
            parts = ["go", "test", test_path or "./..."]
        else:
            parts = [runner]
            if test_path:
                parts.append(test_path)

        if extra_args:
            parts.append(extra_args)
        return " ".join(parts)
