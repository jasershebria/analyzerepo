"""
tools/ — modular Python port of every claude-code TypeScript tool.

Each tool is a BaseTool subclass with:
  • name          — snake_case tool identifier (matches OpenAI function name)
  • description   — human-readable purpose string
  • definition()  — returns a ToolDef (OpenAI function-calling schema)
  • _run(args)    — async execution, returns str or JSON-serialisable value
  • call(args)    — public entry point (validates + serialises to str)

Registry helpers:
  get_all()       → list[BaseTool]
  get_registry()  → dict[str, BaseTool]
  execute(name, args) → str   (async)
  definitions()   → list[dict]  (OpenAI format)
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
from .glob_tool import GlobTool
from .grep import GrepTool
from .lsp import LSPTool
from .notebook_edit import NotebookEditTool
from .powershell import PowerShellTool
from .remote_trigger import RemoteTriggerTool
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

__all__ = [
    "BaseTool",
    "ToolDef",
    "get_all",
    "get_registry",
    "execute",
    "definitions",
]

_ALL_TOOLS: list[BaseTool] = [
    # File operations
    FileReadTool(),
    FileWriteTool(),
    FileEditTool(),
    # Search
    GlobTool(),
    GrepTool(),
    # Shell execution
    BashTool(),
    PowerShellTool(),
    # Web
    WebFetchTool(),
    WebSearchTool(),
    # Notebooks & structured content
    NotebookEditTool(),
    TodoWriteTool(),
    AskUserQuestionTool(),
    # Utilities
    SleepTool(),
    ConfigTool(),
    BriefTool(),
    SendMessageTool(),
    # Task management
    TaskCreateTool(),
    TaskGetTool(),
    TaskListTool(),
    TaskUpdateTool(),
    TaskStopTool(),
    # Scheduling
    ScheduleCronTool(),
    CronDeleteTool(),
    CronListTool(),
    # Tool discovery
    ToolSearchTool(),
    # Remote & mode management
    RemoteTriggerTool(),
    EnterPlanModeTool(),
    ExitPlanModeTool(),
    EnterWorktreeTool(),
    ExitWorktreeTool(),
    # Multi-agent
    AgentTool(),
    SkillTool(),
    TeamCreateTool(),
    TeamDeleteTool(),
    # Code intelligence (stub)
    LSPTool(),
]

_REGISTRY: dict[str, BaseTool] = {t.name: t for t in _ALL_TOOLS}


def get_all() -> list[BaseTool]:
    return _ALL_TOOLS


def get_registry() -> dict[str, BaseTool]:
    return _REGISTRY


async def execute(name: str, arguments: dict[str, Any]) -> str:
    if name not in _REGISTRY:
        raise ValueError(f"Unknown tool: '{name}'. Available: {', '.join(_REGISTRY)}")
    return await _REGISTRY[name].call(arguments)


def definitions() -> list[dict[str, Any]]:
    return [t.definition().to_dict() for t in _ALL_TOOLS]
