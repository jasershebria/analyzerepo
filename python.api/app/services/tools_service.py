from __future__ import annotations

import asyncio
import base64
import glob as glob_module
import json
import os
import re
import shutil
import subprocess
import uuid
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import httpx

from app.schemas.tools import (
    AgentInput,
    AskUserQuestionInput,
    BashInput,
    BriefInput,
    ConfigInput,
    CronCreateInput,
    CronDeleteInput,
    FileEditInput,
    FileReadInput,
    FileWriteInput,
    GlobInput,
    GrepInput,
    GrepOutputMode,
    LspInput,
    NotebookEditInput,
    PowerShellInput,
    RemoteTriggerInput,
    SendMessageInput,
    SleepInput,
    TaskCreateInput,
    TaskGetInput,
    TaskStopInput,
    TaskUpdateInput,
    ToolCallResponse,
    ToolDefinition,
    ToolFunctionDefinition,
    ToolParameterSchema,
    TodoItem,
    TodoWriteInput,
    ToolSearchInput,
    WebFetchInput,
    WebSearchInput,
)

_TODO_STORE: list[dict] = []

# In-memory stores (reset on server restart)
_TASK_STORE: dict[str, dict] = {}
_CRON_STORE: dict[str, dict] = {}
_CONFIG_STORE: dict[str, Any] = {}
_MESSAGE_LOG: list[dict] = []

_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico"}
_NOTEBOOK_EXTENSIONS = {".ipynb"}
_PDF_EXTENSIONS = {".pdf"}


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        self._chunks.append(data)

    def get_text(self) -> str:
        return " ".join(chunk.strip() for chunk in self._chunks if chunk.strip())


class ToolsService:

    async def execute(self, name: str, arguments: dict[str, Any]) -> ToolCallResponse:
        dispatch: dict[str, tuple[type, Any]] = {
            "file_read": (FileReadInput, self._run_file_read),
            "file_write": (FileWriteInput, self._run_file_write),
            "file_edit": (FileEditInput, self._run_file_edit),
            "glob": (GlobInput, self._run_glob),
            "grep": (GrepInput, self._run_grep),
            "bash": (BashInput, self._run_bash),
            "powershell": (PowerShellInput, self._run_powershell),
            "web_fetch": (WebFetchInput, self._run_web_fetch),
            "web_search": (WebSearchInput, self._run_web_search),
            "todo_write": (TodoWriteInput, self._run_todo_write),
            "notebook_edit": (NotebookEditInput, self._run_notebook_edit),
            "ask_user_question": (AskUserQuestionInput, self._run_ask_user_question),
            # Additional tools
            "sleep": (SleepInput, self._run_sleep),
            "config": (ConfigInput, self._run_config),
            "brief": (BriefInput, self._run_brief),
            "send_message": (SendMessageInput, self._run_send_message),
            "task_create": (TaskCreateInput, self._run_task_create),
            "task_get": (TaskGetInput, self._run_task_get),
            "task_list": (dict, self._run_task_list),
            "task_update": (TaskUpdateInput, self._run_task_update),
            "task_stop": (TaskStopInput, self._run_task_stop),
            "cron_create": (CronCreateInput, self._run_cron_create),
            "cron_delete": (CronDeleteInput, self._run_cron_delete),
            "cron_list": (dict, self._run_cron_list),
            "tool_search": (ToolSearchInput, self._run_tool_search),
            "lsp": (LspInput, self._run_lsp),
            "remote_trigger": (RemoteTriggerInput, self._run_remote_trigger),
            "agent": (AgentInput, self._run_agent),
            "enter_plan_mode": (dict, self._run_enter_plan_mode),
            "exit_plan_mode": (dict, self._run_exit_plan_mode),
        }

        if name not in dispatch:
            return ToolCallResponse(tool=name, error=f"Unknown tool '{name}'")

        input_cls, handler = dispatch[name]
        try:
            parsed = input_cls.model_validate(arguments)
        except Exception as exc:
            return ToolCallResponse(tool=name, error=f"Invalid arguments: {exc}")

        try:
            result = await handler(parsed)
            return ToolCallResponse(tool=name, result=result)
        except Exception as exc:
            return ToolCallResponse(tool=name, error=str(exc))

    # ── File tools ────────────────────────────────────────────────────────────

    async def _run_file_read(self, inp: FileReadInput) -> Any:
        path = Path(inp.file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {inp.file_path}")

        suffix = path.suffix.lower()

        if suffix in _IMAGE_EXTENSIONS:
            raw = await asyncio.to_thread(path.read_bytes)
            b64 = base64.b64encode(raw).decode()
            mime = _image_mime(suffix)
            return f"data:{mime};base64,{b64}"

        if suffix in _PDF_EXTENSIONS:
            return await asyncio.to_thread(_read_pdf, path, inp.pages)

        if suffix in _NOTEBOOK_EXTENSIONS:
            return await asyncio.to_thread(_read_notebook, path)

        text: str = await asyncio.to_thread(
            lambda: path.read_text(encoding="utf-8", errors="replace")
        )
        lines = text.splitlines(keepends=True)

        offset = max(0, (inp.offset or 1) - 1)  # convert 1-based to 0-based
        lines = lines[offset:]
        if inp.limit is not None:
            lines = lines[: inp.limit]

        return "".join(lines)

    async def _run_file_write(self, inp: FileWriteInput) -> str:
        path = Path(inp.file_path)
        await asyncio.to_thread(lambda: (
            path.parent.mkdir(parents=True, exist_ok=True),
            path.write_text(inp.content, encoding="utf-8"),
        ))
        return f"Written {len(inp.content.encode())} bytes to {inp.file_path}"

    async def _run_file_edit(self, inp: FileEditInput) -> str:
        path = Path(inp.file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {inp.file_path}")

        text: str = await asyncio.to_thread(
            lambda: path.read_text(encoding="utf-8", errors="replace")
        )

        if inp.old_string not in text:
            raise ValueError(
                f"old_string not found in {inp.file_path}. "
                "Ensure you are using the exact text from the file."
            )

        if inp.replace_all:
            count = text.count(inp.old_string)
            new_text = text.replace(inp.old_string, inp.new_string)
        else:
            count = 1
            new_text = text.replace(inp.old_string, inp.new_string, 1)

        await asyncio.to_thread(
            lambda: path.write_text(new_text, encoding="utf-8")
        )
        return f"Edited {inp.file_path} ({count} replacement{'s' if count != 1 else ''})"

    # ── Search tools ──────────────────────────────────────────────────────────

    async def _run_glob(self, inp: GlobInput) -> list[str]:
        def _do_glob() -> list[str]:
            if inp.path:
                matches = glob_module.glob(
                    inp.pattern, root_dir=inp.path, recursive=True
                )
                return sorted(
                    str(Path(inp.path) / m) for m in matches
                )
            return sorted(glob_module.glob(inp.pattern, recursive=True))

        return await asyncio.to_thread(_do_glob)

    async def _run_grep(self, inp: GrepInput) -> Any:
        if shutil.which("rg"):
            return await asyncio.to_thread(_grep_with_rg, inp)
        return await asyncio.to_thread(_grep_python_fallback, inp)

    # ── Shell tools ───────────────────────────────────────────────────────────

    async def _run_bash(self, inp: BashInput) -> str:
        timeout_secs = (inp.timeout or 120_000) / 1000

        if inp.run_in_background:
            proc = subprocess.Popen(
                inp.command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return f"Started in background (PID={proc.pid})"

        def _run() -> str:
            try:
                result = subprocess.run(
                    inp.command,
                    shell=True,
                    capture_output=True,
                    timeout=timeout_secs,
                )
                out = result.stdout.decode(errors="replace")
                err = result.stderr.decode(errors="replace")
                return (out + err).rstrip()
            except subprocess.TimeoutExpired:
                return f"Command timed out after {timeout_secs:.0f} seconds"

        return await asyncio.to_thread(_run)

    async def _run_powershell(self, inp: PowerShellInput) -> str:
        timeout_secs = (inp.timeout or 120_000) / 1000

        ps_exe = shutil.which("pwsh") or shutil.which("powershell") or "powershell.exe"
        cmd = [ps_exe, "-NonInteractive", "-Command", inp.command]

        if inp.run_in_background:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return f"Started in background (PID={proc.pid})"

        def _run() -> str:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=timeout_secs,
                )
                out = result.stdout.decode(errors="replace")
                err = result.stderr.decode(errors="replace")
                return (out + err).rstrip()
            except subprocess.TimeoutExpired:
                return f"Command timed out after {timeout_secs:.0f} seconds"

        return await asyncio.to_thread(_run)

    # ── Web tools ─────────────────────────────────────────────────────────────

    async def _run_web_fetch(self, inp: WebFetchInput) -> str:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            resp = await client.get(inp.url)
            resp.raise_for_status()

        content_type = resp.headers.get("content-type", "")
        if "html" in content_type:
            extractor = _HTMLTextExtractor()
            extractor.feed(resp.text)
            text = extractor.get_text()
        else:
            text = resp.text

        if inp.prompt:
            text = f"# Fetch context: {inp.prompt}\n\n{text}"

        return text

    async def _run_web_search(self, inp: WebSearchInput) -> list[dict]:
        try:
            from duckduckgo_search import DDGS  # type: ignore[import]
        except ImportError:
            return [{"error": "duckduckgo-search not installed. Run: pip install duckduckgo-search"}]

        def _search() -> list[dict]:
            results = list(DDGS().text(inp.query, max_results=10))
            if inp.allowed_domains:
                results = [
                    r for r in results
                    if any(d in r.get("href", "") for d in inp.allowed_domains)
                ]
            return results

        return await asyncio.to_thread(_search)

    # ── Task / notebook tools ─────────────────────────────────────────────────

    async def _run_todo_write(self, inp: TodoWriteInput) -> list[dict]:
        global _TODO_STORE
        _TODO_STORE = [item.model_dump() for item in inp.todos]
        return _TODO_STORE

    async def _run_notebook_edit(self, inp: NotebookEditInput) -> str:
        path = Path(inp.notebook_path)
        if not path.exists():
            raise FileNotFoundError(f"Notebook not found: {inp.notebook_path}")

        nb = json.loads(path.read_text(encoding="utf-8"))
        cells: list[dict] = nb.get("cells", [])

        # Find cell by id or by numeric index
        target: dict | None = None
        if inp.cell_id.isdigit():
            idx = int(inp.cell_id)
            if 0 <= idx < len(cells):
                target = cells[idx]
        else:
            for cell in cells:
                if cell.get("id") == inp.cell_id:
                    target = cell
                    break

        if target is None:
            raise ValueError(f"Cell '{inp.cell_id}' not found in {inp.notebook_path}")

        target["source"] = inp.new_source.splitlines(keepends=True)
        path.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
        return f"Updated cell '{inp.cell_id}' in {inp.notebook_path}"

    async def _run_ask_user_question(self, inp: AskUserQuestionInput) -> dict:
        if inp.answer is not None:
            return {"answer": inp.answer}
        return {
            "type": "ask_user_question",
            "question": inp.question,
            "options": inp.options,
            "note": (
                "This tool requires interactive user input. "
                "Render the question in your UI, then call this tool again "
                "with the 'answer' field populated."
            ),
        }

    # ── Tool definitions (OpenAI function-calling spec) ───────────────────────

    def get_definitions(self) -> list[ToolDefinition]:
        return [
            _def(
                "file_read",
                "Read a file from the filesystem. Supports text, images (returns base64 data URI), PDFs, and Jupyter notebooks.",
                {
                    "file_path": {"type": "string", "description": "Absolute path to the file"},
                    "offset": {"type": "integer", "description": "1-based line number to start reading from"},
                    "limit": {"type": "integer", "description": "Maximum number of lines to return"},
                    "pages": {"type": "string", "description": "Page range for PDFs, e.g. '1-5'"},
                },
                required=["file_path"],
            ),
            _def(
                "file_write",
                "Create a new file or completely overwrite an existing file with the given content.",
                {
                    "file_path": {"type": "string", "description": "Absolute path to the file"},
                    "content": {"type": "string", "description": "Content to write"},
                },
                required=["file_path", "content"],
            ),
            _def(
                "file_edit",
                "Replace a specific string inside a file. The old_string must match exactly.",
                {
                    "file_path": {"type": "string", "description": "Absolute path to the file"},
                    "old_string": {"type": "string", "description": "Exact text to find and replace"},
                    "new_string": {"type": "string", "description": "Replacement text"},
                    "replace_all": {"type": "boolean", "description": "Replace every occurrence (default false)"},
                },
                required=["file_path", "old_string", "new_string"],
            ),
            _def(
                "glob",
                "Find files matching a glob pattern (e.g. '**/*.py'). Returns a sorted list of matching paths.",
                {
                    "pattern": {"type": "string", "description": "Glob pattern"},
                    "path": {"type": "string", "description": "Root directory to search (default: cwd)"},
                },
                required=["pattern"],
            ),
            _def(
                "grep",
                "Search file contents with a regex pattern using ripgrep (fallback: Python re). Supports context lines, case-insensitive, multiline, and output mode selection.",
                {
                    "pattern": {"type": "string", "description": "Regular expression pattern"},
                    "path": {"type": "string", "description": "File or directory to search"},
                    "glob": {"type": "string", "description": "Glob filter, e.g. '*.py'"},
                    "output_mode": {"type": "string", "enum": ["content", "files_with_matches", "count"], "description": "Output format"},
                    "context": {"type": "integer", "description": "Lines of context around each match (-C)"},
                    "before_context": {"type": "integer", "description": "Lines before each match (-B)"},
                    "after_context": {"type": "integer", "description": "Lines after each match (-A)"},
                    "case_insensitive": {"type": "boolean", "description": "Case-insensitive search"},
                    "multiline": {"type": "boolean", "description": "Allow patterns to span multiple lines"},
                    "head_limit": {"type": "integer", "description": "Limit output to first N lines (default 250)"},
                    "offset": {"type": "integer", "description": "Skip first N results"},
                },
                required=["pattern"],
            ),
            _def(
                "bash",
                "Execute a bash shell command. Returns stdout + stderr. Use run_in_background for fire-and-forget.",
                {
                    "command": {"type": "string", "description": "Shell command to run"},
                    "timeout": {"type": "integer", "description": "Timeout in milliseconds (default 120000)"},
                    "run_in_background": {"type": "boolean", "description": "Launch detached; returns PID immediately"},
                },
                required=["command"],
            ),
            _def(
                "powershell",
                "Execute a Windows PowerShell command. Returns stdout + stderr.",
                {
                    "command": {"type": "string", "description": "PowerShell command to run"},
                    "timeout": {"type": "integer", "description": "Timeout in milliseconds (default 120000)"},
                    "run_in_background": {"type": "boolean", "description": "Launch detached; returns PID immediately"},
                },
                required=["command"],
            ),
            _def(
                "web_fetch",
                "Fetch the content of a URL and return it as plain text (HTML is stripped).",
                {
                    "url": {"type": "string", "description": "URL to fetch"},
                    "prompt": {"type": "string", "description": "Optional context hint prepended to the result"},
                },
                required=["url"],
            ),
            _def(
                "web_search",
                "Search the web using DuckDuckGo. Returns up to 10 results with title, URL, and snippet.",
                {
                    "query": {"type": "string", "description": "Search query"},
                    "allowed_domains": {"type": "array", "items": {"type": "string"}, "description": "Filter results to these domains only"},
                },
                required=["query"],
            ),
            _def(
                "todo_write",
                "Replace the entire task list with a new list. Each todo has id, content, status, and priority.",
                {
                    "todos": {
                        "type": "array",
                        "description": "Full list of todos (replaces existing list)",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "content": {"type": "string"},
                                "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                                "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                            },
                            "required": ["id", "content", "status", "priority"],
                        },
                    }
                },
                required=["todos"],
            ),
            _def(
                "notebook_edit",
                "Replace the source of a specific cell in a Jupyter notebook (.ipynb).",
                {
                    "notebook_path": {"type": "string", "description": "Absolute path to the .ipynb file"},
                    "cell_id": {"type": "string", "description": "Cell id (string) or 0-based index (integer as string)"},
                    "new_source": {"type": "string", "description": "New source code / markdown for the cell"},
                },
                required=["notebook_path", "cell_id", "new_source"],
            ),
            _def(
                "ask_user_question",
                "Present a question with options to the user. Returns a sentinel for the caller to render its own UI, then call again with 'answer' to complete the round-trip.",
                {
                    "question": {"type": "string", "description": "Question to ask the user"},
                    "options": {"type": "array", "items": {"type": "string"}, "description": "Answer options to present"},
                    "answer": {"type": "string", "description": "Populate this on the second call with the user's selected answer"},
                },
                required=["question"],
            ),
        ]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _def(
    name: str,
    description: str,
    properties: dict[str, Any],
    required: list[str] | None = None,
) -> ToolDefinition:
    return ToolDefinition(
        function=ToolFunctionDefinition(
            name=name,
            description=description,
            parameters=ToolParameterSchema(
                properties=properties,
                required=required or [],
            ),
        )
    )


def _image_mime(suffix: str) -> str:
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".bmp": "image/bmp",
        ".ico": "image/x-icon",
    }.get(suffix, "image/octet-stream")


def _read_pdf(path: Path, pages: str | None) -> str:
    try:
        import pypdf  # type: ignore[import]
    except ImportError:
        return "pypdf not installed. Run: pip install pypdf"

    reader = pypdf.PdfReader(str(path))
    total = len(reader.pages)

    if pages:
        parts = pages.split("-")
        start = max(0, int(parts[0]) - 1)
        end = int(parts[1]) if len(parts) > 1 else start + 1
        page_range = range(start, min(end, total))
    else:
        page_range = range(total)

    return "\n\n".join(
        reader.pages[i].extract_text() or f"[Page {i + 1}: no text extracted]"
        for i in page_range
    )


def _read_notebook(path: Path) -> str:
    nb = json.loads(path.read_text(encoding="utf-8"))
    chunks: list[str] = []
    for i, cell in enumerate(nb.get("cells", [])):
        cell_type = cell.get("cell_type", "code")
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)
        chunks.append(f"# Cell {i} [{cell_type}]\n{source}")
    return "\n\n".join(chunks)


def _grep_with_rg(inp: GrepInput) -> Any:
    cmd: list[str] = ["rg"]

    if inp.output_mode == GrepOutputMode.count:
        cmd.append("--count")
    elif inp.output_mode == GrepOutputMode.files_with_matches:
        cmd.append("--files-with-matches")

    if inp.case_insensitive:
        cmd.append("-i")
    if inp.multiline:
        cmd += ["-U", "--multiline-dotall"]
    if inp.context is not None:
        cmd += ["-C", str(inp.context)]
    if inp.before_context is not None:
        cmd += ["-B", str(inp.before_context)]
    if inp.after_context is not None:
        cmd += ["-A", str(inp.after_context)]
    if inp.glob:
        cmd += ["--glob", inp.glob]

    cmd.append(inp.pattern)

    if inp.path:
        cmd.append(inp.path)

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        raw = result.stdout.decode(errors="replace")
    except subprocess.TimeoutExpired:
        return "grep timed out"

    lines = raw.splitlines()

    offset = inp.offset or 0
    if offset:
        lines = lines[offset:]

    if inp.output_mode == GrepOutputMode.files_with_matches:
        return lines
    if inp.output_mode == GrepOutputMode.count:
        counts: dict[str, int] = {}
        for line in lines:
            if ":" in line:
                file, _, count_str = line.rpartition(":")
                try:
                    counts[file] = int(count_str)
                except ValueError:
                    pass
        return counts
    return "\n".join(lines)


def _grep_python_fallback(inp: GrepInput) -> Any:
    flags = re.MULTILINE
    if inp.case_insensitive:
        flags |= re.IGNORECASE
    if inp.multiline:
        flags |= re.DOTALL

    try:
        pattern = re.compile(inp.pattern, flags)
    except re.error as exc:
        return f"Invalid regex: {exc}"

    search_root = inp.path or "."
    matched_files: list[str] = []
    content_lines: list[str] = []
    file_counts: dict[str, int] = {}

    glob_pattern = inp.glob or "*"

    for dirpath, _, filenames in os.walk(search_root):
        # Skip VCS directories
        dirpath_parts = Path(dirpath).parts
        if any(p in {".git", ".svn", ".hg", ".bzr"} for p in dirpath_parts):
            continue

        for filename in filenames:
            if not _match_glob(filename, glob_pattern):
                continue
            filepath = os.path.join(dirpath, filename)
            try:
                text = Path(filepath).read_text(encoding="utf-8", errors="replace")
            except (OSError, PermissionError):
                continue

            matches = list(pattern.finditer(text))
            if not matches:
                continue

            matched_files.append(filepath)
            file_counts[filepath] = len(matches)

            if inp.output_mode == GrepOutputMode.content:
                for lineno, line in enumerate(text.splitlines(), 1):
                    if pattern.search(line):
                        content_lines.append(f"{filepath}:{lineno}:{line}")

    offset = inp.offset or 0
    limit = inp.head_limit or 999_999

    if inp.output_mode == GrepOutputMode.files_with_matches:
        return matched_files[offset: offset + limit]
    if inp.output_mode == GrepOutputMode.count:
        items = list(file_counts.items())[offset: offset + limit]
        return dict(items)
    return "\n".join(content_lines[offset: offset + limit])


def _match_glob(filename: str, pattern: str) -> bool:
    import fnmatch
    return fnmatch.fnmatch(filename, pattern)
