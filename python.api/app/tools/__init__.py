"""
tools/ — modular Python port of every claude-code TypeScript tool.

Each tool is a BaseTool subclass with:
  • name          — snake_case tool identifier (matches OpenAI function name)
  • description   — human-readable purpose string
  • definition()  — returns a ToolDef (OpenAI function-calling schema)
  • _run(args)    — async execution, returns str or JSON-serialisable value
  • call(args)    — public entry point (validates + serialises to str)
  • to_langchain_tool() — wraps as a LangChain StructuredTool

Registry helpers:
  get_all()            → list[BaseTool]
  get_registry()       → dict[str, BaseTool]
  execute(name, args)  → str   (async)
  definitions()        → list[dict]  (OpenAI format)
  as_langchain_tools() → list[StructuredTool]
"""
from __future__ import annotations

from typing import Any

from ._base import BaseTool, ToolDef
from .ask_user_question import AskUserQuestionTool
from .agent import AgentTool
from .bash import BashTool
from .brief import BriefTool
from .config import ConfigTool
from .enter_plan_mode import EnterPlanModeTool
from .enter_worktree import EnterWorktreeTool
from .exit_plan_mode import ExitPlanModeTool
from .exit_worktree import ExitWorktreeTool
from .file_edit import FileEditTool
from .file_read import FileReadTool
from .file_write import FileWriteTool
from .git_commit import GitCommitTool
from .glob_tool import GlobTool
from .grep import GrepTool
from .lsp import LSPTool
from .notebook_edit import NotebookEditTool
from .powershell import PowerShellTool
from .remote_trigger import RemoteTriggerTool
from .run_tests import RunTestsTool
from .schedule_cron import CronDeleteTool, CronListTool, ScheduleCronTool
from .send_message import SendMessageTool
from .skill import SkillTool
from .sleep import SleepTool
from .task_create import TaskCreateTool
from .task_get import TaskGetTool
from .task_list import TaskListTool
from .task_stop import TaskStopTool
from .task_update import TaskUpdateTool
from .team_create import TeamCreateTool, TeamDeleteTool
from .todo_write import TodoWriteTool
from .tool_search import ToolSearchTool
from .web_fetch import WebFetchTool
from .web_search import WebSearchTool
from .rag_search import RagSearchTool

__all__ = [
    "BaseTool",
    "ToolDef",
    "get_all",
    "get_registry",
    "execute",
    "definitions",
    "as_langchain_tools",
]

def get_all(working_dir: str | None = None) -> list[BaseTool]:
    """Return fresh instances of all tools, optionally tied to a working directory."""
    return [
        # File operations
        FileReadTool(working_dir),
        FileWriteTool(working_dir),
        FileEditTool(working_dir),
        # Search
        GlobTool(working_dir),
        GrepTool(working_dir),
        # Shell execution
        BashTool(working_dir),
        PowerShellTool(working_dir),
        # Web
        WebFetchTool(working_dir),
        WebSearchTool(working_dir),
        # Notebooks & structured content
        NotebookEditTool(working_dir),
        TodoWriteTool(working_dir),
        AskUserQuestionTool(working_dir),
        # Utilities
        SleepTool(working_dir),
        ConfigTool(working_dir),
        BriefTool(working_dir),
        SendMessageTool(working_dir),
        # Task management
        TaskCreateTool(working_dir),
        TaskGetTool(working_dir),
        TaskListTool(working_dir),
        TaskUpdateTool(working_dir),
        TaskStopTool(working_dir),
        # Scheduling
        ScheduleCronTool(working_dir),
        CronDeleteTool(working_dir),
        CronListTool(working_dir),
        # Tool discovery
        ToolSearchTool(working_dir),
        # Remote & mode management
        RemoteTriggerTool(working_dir),
        EnterPlanModeTool(working_dir),
        ExitPlanModeTool(working_dir),
        EnterWorktreeTool(working_dir),
        ExitWorktreeTool(working_dir),
        # Multi-agent
        AgentTool(working_dir),
        SkillTool(working_dir),
        TeamCreateTool(working_dir),
        TeamDeleteTool(working_dir),
        # Code intelligence (stub)
        LSPTool(working_dir),
        # Dev tools
        RunTestsTool(working_dir),
        GitCommitTool(working_dir),
        # RAG
        RagSearchTool(working_dir),
    ]


def get_registry(working_dir: str | None = None) -> dict[str, BaseTool]:
    return {t.name: t for t in get_all(working_dir)}


async def execute(name: str, arguments: dict[str, Any], working_dir: str | None = None) -> str:
    registry = get_registry(working_dir)
    if name not in registry:
        raise ValueError(f"Unknown tool: '{name}'. Available: {', '.join(registry)}")
    return await registry[name].call(arguments)


def definitions(working_dir: str | None = None) -> list[dict[str, Any]]:
    return [t.definition().to_dict() for t in get_all(working_dir)]


def as_langchain_tools(working_dir: str | None = None) -> list:
    """Return all registered tools as LangChain StructuredTool objects."""
    return [t.to_langchain_tool() for t in get_all(working_dir)]
